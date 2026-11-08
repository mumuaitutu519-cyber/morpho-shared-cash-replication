# Counting the same cash replication package

**Counting the same cash: shared market liquidity and withdrawal capacity across decentralized lending vaults** — Zhang, Kang, Sun, Ryu. Authority: the filename-dated 1 November 2026, 22:00 manuscript. Its unchanged PDF is in `paper/`; the DOCX is not distributed.

This private GitHub package uses the existing Professor Check replication package and the preserved later descriptive, add-on, and discussant packages. All copied scientific programs, observations, and archived estimates preserve their source bytes. Task 305 performed packaging and read-only table comparison; it did not refit models or edit a paper/result.

## One command

With Python 3, from this directory:

```bash
bash run_all.sh
```

This command regenerates **frozen-archive table comparisons**, not model estimates. It checks the latest 16 numbered tables (1–10, A1, B1–B4, C1), compares every included displayed numeric cell at its printed precision, and writes a fresh `VERIFICATION.csv` and `TABLE_SUMMARY.csv` into task scratch. The committed delivery comparison is `verify/VERIFICATION.csv`. Table 1 uses the preserved descriptive CSV; other tables use explicitly mapped prior display archives. All comparisons match. This confirms packaging/version alignment and must not be presented as a new independent statistical replication. Read `verify/VERIFICATION_SCOPE.md`.

## Files and data

- `code/`, `additional_evidence/code/`, `enrichment/code/`, `joint_review/code/`: original research stages; paths in active analytical modules are relative to their package layouts. Historical online collectors and old manuscript-generation helpers are retained for provenance and are not run by the packaging command.
- `outputs/`, `additional_evidence/*/outputs/`, `reports/`, `raw/`: the existing Professor Check selection of analysis panels, archived estimates and public-chain evidence. These paths are retained because the original research code depends on that layout.
- `data/`: current manuscript table extracts, frozen prior table archive and explicit coordinate map. `desc/`: six regression-sample descriptive panels, full-precision values and sample definitions.
- `addon_package/`: self-contained CSV inputs and original programs for stress windows, refill times, regressions and a one-day recorded-operation replay.
- `addon_stress_refill/`: retained original add-on source and its analysis-ready outputs.
- `optional/table8/`: the existing portable borrow-event regression bundle, with relative paths and its own requirements/README.
- `verify/historical_professor_delivery/` and `verify/historical_discussant/`: unchanged historical receipts and checks; their dates, table numbers and scope are historical.
- `FILE_MANIFEST.csv`: exact relative paths, byte sizes and hashes; `EXCLUDED_FILES.md`: distribution exclusions; `SECURITY_SCAN.json`: no-value credential scan.

The core sample consists of ten Base USDC vaults over 439 days (16 January 2025–30 March 2026). Chain states, public API observations, decoded event states and analysis panels are public-chain derived; no paid/authorized provider raw data is packaged. This packaging does not grant new rights to the manuscript or code or override upstream terms.

## Statistical reruns and limits

Use Python 3.12 and the original pinned `requirements.txt` for the core research stages; add-on and portable bundles retain their own requirements. For example, `python code/09_desc_stats.py` rebuilds the six descriptive panels from the supplied regression-ready data; `python code/empirical/estimate.py` uses the supplied vault/daily panels; run other research modules according to `verify/README_original_package.md` and each bundle's README. These commands write regenerated scientific outputs, so use a separate working copy when preserving the archived delivery.

The Professor Check package intentionally omits bulk raw API archives and complete operation logs. `run_replication_original.py` is the preserved historical raw-to-paper orchestrator and is **not** a promised clean-clone command: raw decoding stages and legacy manuscript checks require omitted raw inputs and the original DOCX. The discussant full replay was not copied as runnable because its operation ledger files are absent from the M5 portable bundle; the supplied one-day add-on replay is self-contained. No missing observations or gates were fabricated. Existing historical validation receipts are not evidence of a fresh run in task 305.

No individual file exceeds 100 MB, so no GitHub Release attachment is needed. The large original source ZIPs are excluded; this repository holds the extracted reviewed selection. All new delivery checks use relative package paths. Scratch defaults to `/Volumes/Extreme SSD/T9/_tmp/305/morpho-verification` when this disk exists, otherwise a system temporary directory; override with `MORPHO_VERIFY_OUTPUT`.
