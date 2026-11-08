"""Read-only destination census for the frozen Spark source cohort.

Blockscout discovers mint candidates; official public RPC receipts authenticate
their messages and all same-transaction logs. No signing or transaction writes.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd

from fetch_ethereum_full import SSL_CONTEXT, TRANSFER_TOPIC, ZERO_TOPIC, utc_now
from revision4_collect_spark_cases import registry, REG

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / 'data/raw/revision6'
OUT = ROOT / 'reports/revision6'
CUTOFF = 1764547200
NETWORKS = {
    2: ('optimism', 'https://mainnet.optimism.io', 10),
    3: ('arbitrum', 'https://arb1.arbitrum.io/rpc', 42161),
    6: ('base', 'https://mainnet.base.org', 8453),
    10: ('unichain', 'https://mainnet.unichain.org', 130),
}
RECEIVED = '0x58200b4c34ae05ee816d710053fff3fb75af4395915d3d2a771b24aa10e3cc5d'
SOURCE_MESSENGER = '0x' + 'bd3fa81b58ba92a82136038b25adec7066af3155'.rjust(64, '0')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def cached_request(folder, name, url, payload=None):
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f'{name}.json.gz'
    request = {'url': url, 'payload': payload}
    retry_number = 0
    while path.exists():
        with gzip.open(path, 'rt') as f:
            obj = json.load(f)
        assert obj['request'] == request
        response = obj['response']
        responses = response if isinstance(response, list) else [response]
        if not any(isinstance(r, dict) and 'error' in r for r in responses):
            return response, path
        # Preserve an errored RPC response as evidence; never reuse it as data.
        retry_number += 1
        path = folder / f'{name}_retry_{retry_number:02}.json.gz'
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                url, data=None if payload is None else json.dumps(payload).encode(),
                headers={'User-Agent': 'stablecoin-research-read-only/1.0',
                         'Accept-Encoding': 'gzip', 'Content-Type': 'application/json'})
            with urllib.request.urlopen(req, timeout=45, context=SSL_CONTEXT) as f:
                body = f.read()
                if f.headers.get('Content-Encoding') == 'gzip':
                    body = gzip.decompress(body)
                obj = json.loads(body)
            # A provider limit is a stopped job, not an empty historical window.
            if isinstance(obj, dict) and ('too many requests' in str(obj).lower()
                                          or 'rate limit' in str(obj).lower()):
                error_path = folder / f'{name}_rpc_limit_{time.time_ns()}.json.gz'
                with gzip.open(error_path, 'wt') as handle:
                    json.dump({'request': request, 'queried_at_utc': utc_now(),
                               'response': obj, 'classification': 'provider_rate_limit'}, handle)
                raise RuntimeError('Provider rate limit; stop and resume later')
            break
        except urllib.error.HTTPError as e:
            # Retain public error responses and Retry-After hints for an access
            # audit. An error is never a zero-event observation.
            error_record = {'request': request, 'queried_at_utc': utc_now(),
                            'http_status': e.code, 'retry_after': e.headers.get('Retry-After'),
                            'body': e.read().decode('utf-8', errors='replace')}
            error_path = folder / f'{name}_http_error_{time.time_ns()}.json.gz'
            with gzip.open(error_path, 'wt') as handle:
                json.dump(error_record, handle)
            if e.code in (401, 403, 429) or attempt == 2:
                raise
            time.sleep(3 * (attempt + 1))
        except (urllib.error.URLError, TimeoutError) as e:
            if attempt == 2:
                raise
            time.sleep(3 * (attempt + 1))
    record = {'request': request, 'queried_at_utc': utc_now(), 'response': obj}
    with gzip.open(path, 'wt') as f:
        json.dump(record, f)
    # Batch RPC calls count as several reads. Space batches below public limits.
    time.sleep(8.0 if '.blockscout.com/' in url else 2.0)
    return obj, path


def rpc(domain, method, params, name):
    assert method in {'eth_chainId', 'eth_getTransactionReceipt', 'eth_getBlockByNumber'}
    _, url, _ = NETWORKS[domain]
    r, path = cached_request(RAW / f'domain_{domain}/rpc', name, url,
                            {'jsonrpc': '2.0', 'id': 1, 'method': method, 'params': params})
    if 'error' in r or r.get('result') is None:
        raise RuntimeError({'rpc': method, 'response': r})
    return r['result'], path


def bounds(domain, first):
    base = f"https://portal.sqd.dev/datasets/{REG[str(domain)]['dataset']}"
    vals = []
    for ts in (first, CUTOFF):
        obj, _ = cached_request(RAW / f'domain_{domain}/bounds', str(ts),
                                f'{base}/timestamps/{ts}/block')
        vals.append(int(obj['block_number']))
    # Query one extra boundary block; exact timestamps, not block approximations,
    # determine eligibility in the analysis.
    return max(0, vals[0] - 1), vals[1]


def mint_windows(domain, start, end):
    # Large sparse log scans can spend minutes awaiting an explorer response.
    # Split by coverage, independent of observed economic outcomes.
    cached_path = RAW / f'domain_{domain}/mints' / f'{start}_{end}.json.gz'
    max_span = 100_000 if domain == 6 else 2_000_000
    if end - start > max_span and not cached_path.exists():
        mid = (start + end) // 2
        left, lf = mint_windows(domain, start, mid)
        right, rf = mint_windows(domain, mid + 1, end)
        return left + right, lf + rf
    network = NETWORKS[domain][0]
    addresses = registry()[domain]
    params = dict(module='logs', action='getLogs', fromBlock=start, toBlock=end,
                  address=addresses['USDC'], topic0=TRANSFER_TOPIC,
                  topic1=ZERO_TOPIC,
                  topic2='0x' + addresses['ALM_PROXY'][2:].rjust(64, '0'),
                  topic0_1_opr='and', topic0_2_opr='and', topic1_2_opr='and')
    url = f'https://{network}.blockscout.com/api?' + urllib.parse.urlencode(params)
    obj, path = cached_request(RAW / f'domain_{domain}/mints', f'{start}_{end}', url)
    rows = obj.get('result')
    if not isinstance(rows, list):
        raise RuntimeError({'window': [start, end], 'response': obj})
    if obj.get('status') != '1' and not (not rows and obj.get('message') == 'No logs found'):
        raise RuntimeError(obj)
    for log in rows:
        assert start <= int(log['blockNumber'], 16) <= end
        assert log['address'].lower() == addresses['USDC']
        assert log['topics'][:3] == [params['topic0'], params['topic1'], params['topic2']]
    print('mint window', domain, start, end, len(rows), flush=True)
    if len(rows) >= 1000:
        assert start < end, 'Provider cap within one block; do not truncate'
        mid = (start + end) // 2
        left, lf = mint_windows(domain, start, mid)
        right, rf = mint_windows(domain, mid + 1, end)
        return left + right, lf + rf
    return rows, [{'from_block': start, 'to_block': end, 'rows': len(rows),
                   'file': str(path.relative_to(ROOT)), 'sha256': sha(path)}]


def discover(domain):
    frame = pd.read_parquet(ROOT / 'reports/revision4/spark_source_burns.parquet')
    frame = frame[frame.destination_domain.eq(domain)]
    assert frame.version.eq(1).all()
    chain, _ = rpc(domain, 'eth_chainId', [], 'chain_identity')
    assert int(chain, 16) == NETWORKS[domain][2]
    first = int(frame.timestamp.min())
    start, end = bounds(domain, first)
    rows, leaves = mint_windows(domain, start, end)
    keys = {(r['transactionHash'], r['logIndex']) for r in rows}
    assert len(rows) == len(keys)
    leaves.sort(key=lambda x: x['from_block'])
    assert leaves[0]['from_block'] == start and leaves[-1]['to_block'] == end
    assert all(a['to_block'] + 1 == b['from_block'] for a, b in zip(leaves, leaves[1:]))
    chosen = [r for r in rows if first <= int(r['timeStamp'], 16) < CUTOFF]
    path = OUT / f'domain_{domain}_mint_candidates.json'
    path.write_text(json.dumps(chosen, indent=2) + '\n')
    manifest = {'domain': domain, 'chain_id': NETWORKS[domain][2],
                'first_source_timestamp': first, 'cutoff_exclusive': CUTOFF,
                'source_events': len(frame), 'candidate_mints': len(chosen),
                'candidate_transactions': len({r['transactionHash'] for r in chosen}),
                'complete_mint_discovery': True, 'leaves': leaves,
                'scope': 'All native USDC mints to the registered proxy; not all are frame arrivals.'}
    (OUT / f'domain_{domain}_discovery.json').write_text(json.dumps(manifest, indent=2)+'\n')
    print(json.dumps({k: v for k, v in manifest.items() if k != 'leaves'}), flush=True)


def receipts(domain):
    rows = json.loads((OUT / f'domain_{domain}_mint_candidates.json').read_text())
    hashes = sorted({r['transactionHash'] for r in rows})
    items = []
    for i, tx in enumerate(hashes):
        obj, path = rpc(domain, 'eth_getTransactionReceipt', [tx], tx)
        assert obj['transactionHash'] == tx and int(obj['status'], 16) == 1
        assert all(x['transactionHash'] == tx and not x.get('removed', False)
                   for x in obj['logs'])
        by_index = {int(x['logIndex'], 16): x for x in obj['logs']}
        assert len(by_index) == len(obj['logs'])
        for mint in [r for r in rows if r['transactionHash'] == tx]:
            log = by_index[int(mint['logIndex'], 16)]
            assert log['address'] == mint['address'] and log['data'] == mint['data']
            assert log['topics'] == [t for t in mint['topics'] if t is not None]
            assert int(obj['blockNumber'], 16) == int(mint['blockNumber'], 16)
        items.append({'tx_hash': tx, 'file': str(path.relative_to(ROOT)), 'sha256': sha(path)})
        if (i + 1) % 20 == 0:
            print('receipts', domain, i + 1, len(hashes), flush=True)
    manifest = {'domain': domain, 'candidate_transactions': len(hashes),
                'complete_receipts': True, 'items': items}
    (OUT / f'domain_{domain}_receipts.json').write_text(json.dumps(manifest, indent=2)+'\n')
    print('complete receipts', domain, len(hashes), flush=True)


def match(domain):
    frame = pd.read_parquet(ROOT / 'reports/revision4/spark_source_burns.parquet')
    frame = frame[frame.destination_domain.eq(domain)]
    sources = {int(r.nonce_hex, 16): r for r in frame.itertuples()}
    assert len(sources) == len(frame)
    candidates = json.loads((OUT / f'domain_{domain}_mint_candidates.json').read_text())
    times = {r['transactionHash']: int(r['timeStamp'], 16) for r in candidates}
    manifest = json.loads((OUT / f'domain_{domain}_receipts.json').read_text())
    found = {}
    for item in manifest['items']:
        path = ROOT / item['file']
        assert sha(path) == item['sha256']
        with gzip.open(path, 'rt') as f:
            receipt = json.load(f)['response']['result']
        used = set()
        for log in sorted(receipt['logs'], key=lambda z: int(z['logIndex'], 16)):
            if log['address'] != REG[str(domain)]['transmitter'] or log['topics'][0] != RECEIVED:
                continue
            nonce = int(log['topics'][2], 16)
            if nonce not in sources:
                continue
            raw = bytes.fromhex(log['data'][2:])
            off = int.from_bytes(raw[64:96]); size = int.from_bytes(raw[off:off+32])
            body = raw[off+32:off+32+size]
            r = sources[nonce]
            if int.from_bytes(raw[:32]) != 0 or '0x'+raw[32:64].hex() != SOURCE_MESSENGER:
                continue
            assert '0x'+body.hex() == r.body_hex, 'Frame nonce has different message body'
            mint = [x for x in receipt['logs'] if x['address'] == REG[str(domain)]['usdc']
                    and x['topics'] == [TRANSFER_TOPIC, ZERO_TOPIC, r.mint_recipient]
                    and int(x['data'], 16) == int(r.amount_micro_usdc)
                    and int(x['logIndex'], 16) < int(log['logIndex'], 16)
                    and int(x['logIndex'], 16) not in used]
            assert mint, 'Authenticated receipt without exact native mint'
            chosen = max(mint, key=lambda z: int(z['logIndex'], 16))
            used.add(int(chosen['logIndex'], 16))
            assert nonce not in found
            ts = times[receipt['transactionHash']]
            assert int(r.timestamp) <= ts < CUTOFF
            found[nonce] = {'domain': domain, 'source_tx': r.transaction_hash,
                           'source_log': int(r.log_index), 'nonce': str(nonce),
                           'source_timestamp': int(r.timestamp), 'destination_timestamp': ts,
                           'amount_micro_usdc': int(r.amount_micro_usdc),
                           'destination_tx': receipt['transactionHash'],
                           'destination_block': int(receipt['blockNumber'], 16),
                           'mint_log': int(chosen['logIndex'], 16),
                           'receipt_log': int(log['logIndex'], 16), 'status': 'exact_mint'}
    result = []
    for nonce, r in sources.items():
        result.append(found.get(nonce, {'domain': domain, 'source_tx': r.transaction_hash,
                      'source_log': int(r.log_index), 'nonce': str(nonce),
                      'source_timestamp': int(r.timestamp),
                      'amount_micro_usdc': int(r.amount_micro_usdc),
                      'status': 'no_exact_mint_before_cutoff'}))
    pd.DataFrame(result).to_csv(OUT / f'domain_{domain}_matches.csv', index=False)
    print('matched', domain, len(found), len(frame), flush=True)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('stage', choices=['discover', 'receipts', 'match', 'all'])
    p.add_argument('--domains', type=int, nargs='+', default=[6, 2, 3, 10])
    args = p.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    for domain in args.domains:
        try:
            if args.stage in ('discover', 'all'):
                discover(domain)
            if args.stage in ('receipts', 'all'):
                receipts(domain)
            if args.stage in ('match', 'all'):
                match(domain)
        except Exception as e:
            record = {'domain': domain, 'stage': args.stage, 'at': utc_now(), 'error': repr(e)}
            (OUT / f'domain_{domain}_{args.stage}_error.json').write_text(json.dumps(record, indent=2)+'\n')
            print('STOPPED', json.dumps(record), flush=True)
            raise


if __name__ == '__main__':
    main()
