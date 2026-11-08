from __future__ import annotations

import gzip
import hashlib
import json
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from copy import deepcopy

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = PROJECT_ROOT / "config" / "contracts.json"
RAW_ROOT = PROJECT_ROOT / "data" / "raw" / "sqd" / "ethereum" / "mintburn"
LOG_PATH = PROJECT_ROOT / "data" / "metadata" / "ethereum_full_download_log.csv"
TRANSFER_TOPIC = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
ZERO_TOPIC = "0x" + "0" * 64
SSL_CONTEXT = ssl.create_default_context()


def utc_now() -> str:
    return pd.Timestamp.now(tz="UTC").isoformat()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def get_json(url: str, attempts: int = 7) -> dict[str, Any]:
    error: Exception | None = None
    for attempt in range(attempts):
        try:
            request = urllib.request.Request(
                url, headers={"User-Agent": "ghost-redemptions-research/1.0"}
            )
            with urllib.request.urlopen(request, timeout=90, context=SSL_CONTEXT) as response:
                return json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
            error = exc
            if attempt + 1 < attempts:
                time.sleep(min(2**attempt, 30))
    raise RuntimeError(f"GET failed after {attempts} attempts: {url}: {error}")


def block_for_timestamp(timestamp: int, closest: str) -> int:
    params = urllib.parse.urlencode(
        {"module": "block", "action": "getblocknobytime", "timestamp": timestamp, "closest": closest}
    )
    payload = get_json(f"https://eth.blockscout.com/api?{params}")
    if str(payload.get("status")) != "1":
        raise RuntimeError(f"Blockscout timestamp lookup failed: {payload}")
    result = payload["result"]
    return int(result["blockNumber"] if isinstance(result, dict) else result)


def post_sqd(endpoint: str, payload: dict[str, Any], attempts: int = 9) -> bytes:
    error: Exception | None = None
    for attempt in range(attempts):
        body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        request = urllib.request.Request(
            endpoint,
            data=body,
            headers={
                "Content-Type": "application/json",
                "Accept-Encoding": "gzip",
                "User-Agent": "ghost-redemptions-research/1.0",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=120, context=SSL_CONTEXT) as response:
                content = response.read()
                if response.headers.get("Content-Encoding", "").lower() == "gzip":
                    content = gzip.decompress(content)
                return content
        except urllib.error.HTTPError as exc:
            error = exc
            if exc.code not in {408, 409, 425, 429, 500, 502, 503, 504, 529}:
                raise
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            error = exc
        if attempt + 1 < attempts:
            time.sleep(min(2**attempt, 35))
    raise RuntimeError(f"SQD request failed after {attempts} attempts: {error}")


def fetch_range(endpoint: str, payload: dict[str, Any], start: int, end: int, target: Path) -> dict[str, Any]:
    if target.exists():
        return {
            "status": "CACHED",
            "sha256": sha256_file(target),
            "compressed_bytes": target.stat().st_size,
            "pages": None,
            "records": None,
            "logs": None,
        }
    target.parent.mkdir(parents=True, exist_ok=True)
    partial = target.with_suffix(target.suffix + ".part")
    cursor = start
    pages = records = logs = 0
    request_payload = deepcopy(payload)
    with gzip.open(partial, "wb", compresslevel=6) as handle:
        while cursor <= end:
            request_payload["fromBlock"] = cursor
            request_payload["toBlock"] = end
            content = post_sqd(endpoint, request_payload)
            last_block = -1
            page_records = 0
            for line in content.splitlines():
                if not line.strip():
                    continue
                record = json.loads(line)
                if "header" not in record or "number" not in record["header"]:
                    raise RuntimeError(f"Unexpected SQD record: {record}")
                last_block = max(last_block, int(record["header"]["number"]))
                page_records += 1
                logs += len(record.get("logs", []))
                handle.write(json.dumps(record, separators=(",", ":")).encode("utf-8") + b"\n")
            if page_records == 0 or last_block < cursor:
                raise RuntimeError(f"SQD stream failed to advance at block {cursor}")
            pages += 1
            records += page_records
            if last_block >= end:
                break
            cursor = last_block + 1
    partial.replace(target)
    return {
        "status": "DOWNLOADED",
        "sha256": sha256_file(target),
        "compressed_bytes": target.stat().st_size,
        "pages": pages,
        "records": records,
        "logs": logs,
    }


def main() -> None:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    chain = config["ethereum"]
    sample = config["sample"]
    start = pd.Timestamp(sample["start_utc"])
    end = pd.Timestamp(sample["end_utc"])
    start_block = block_for_timestamp(int(start.timestamp()), "after")
    end_block = block_for_timestamp(int(end.timestamp()), "before")
    endpoint = f"https://portal.sqd.dev/datasets/{chain['sqd_dataset']}/stream"
    chunk_size = 100_000
    payload = {
        "type": "evm",
        "fields": {
            "block": {"number": True, "timestamp": True},
            "log": {
                "address": True,
                "topics": True,
                "data": True,
                "transactionHash": True,
                "logIndex": True,
            },
        },
        "logs": [
            {"address": [chain["usdc_contract"]], "topic0": [TRANSFER_TOPIC], "topic1": [ZERO_TOPIC]},
            {"address": [chain["usdc_contract"]], "topic0": [TRANSFER_TOPIC], "topic2": [ZERO_TOPIC]},
        ],
    }
    prior: dict[str, dict[str, Any]] = {}
    if LOG_PATH.exists():
        old = pd.read_csv(LOG_PATH)
        prior = {str(row["raw_file"]): row.to_dict() for _, row in old.iterrows()}
    tasks: list[tuple[int, int, Path]] = []
    for block_start in range(start_block, end_block + 1, chunk_size):
        block_end = min(block_start + chunk_size - 1, end_block)
        target = RAW_ROOT / f"blocks_{block_start}_{block_end}.jsonl.gz"
        tasks.append((block_start, block_end, target))

    def fetch_one(task: tuple[int, int, Path]) -> dict[str, Any]:
        block_start, block_end, target = task
        began = time.monotonic()
        stats = fetch_range(endpoint, payload, block_start, block_end, target)
        raw_file = str(target.relative_to(PROJECT_ROOT))
        row = {
            "retrieved_at_utc": utc_now(),
            "provider": "SQD portal",
            "endpoint": endpoint,
            "query": "Ethereum USDC Transfer logs with zero sender or receiver",
            "sample_start_utc": start.isoformat(),
            "sample_end_utc": end.isoformat(),
            "from_block": block_start,
            "to_block": block_end,
            "raw_file": raw_file,
            "elapsed_seconds": round(time.monotonic() - began, 3),
            **stats,
        }
        if stats["status"] == "CACHED" and raw_file in prior:
            for field in ("pages", "records", "logs"):
                if pd.isna(row[field]):
                    row[field] = prior[raw_file].get(field)
        return row

    rows: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=4) as executor:
        future_map = {executor.submit(fetch_one, task): task for task in tasks}
        for future in as_completed(future_map):
            row = future.result()
            rows.append(row)
            rows.sort(key=lambda value: int(value["from_block"]))
            LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
            pd.DataFrame(rows).to_csv(LOG_PATH, index=False)
            print(
                f"{row['from_block']}-{row['to_block']}: "
                f"{row['status']} logs={row['logs']}",
                flush=True,
            )
    print(json.dumps({"start_block": start_block, "end_block": end_block, "chunks": len(rows)}, indent=2))


if __name__ == "__main__":
    main()
