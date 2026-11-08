# Delivery checks

- Word SHA-256: `00717048d887ed7892937758c7c1f67d117901b37cf2aa2fb9f3e5a8dc361224`.
- Main-text table and figure sequences: I–VII and 1–6. All 54 existing physical table blocks retain their complete data rows; specification footers were appended and two new tables inserted.
- Source-to-manuscript numeric checks: 262 existing cells, 39 new cells, and 999 supplementary numeric tokens pass. Main regression results were recomputed.
- Reference closure: 41 entries; cross-reference targets and 12 numbered equations pass the manuscript verifier.
- New chain census: 162 Base and 146 Ethereum positive native-USDC V1 vaults; all 308 reconstructed asset totals reconcile exactly. Archived request/response re-decoding passes.
- Embedded new plots match the generated PNGs. All 58 rendered pages were visually inspected for clipping, overlap, readable tables and captions; no blank pages.
- Format audit has 26 rule-detector flags adjudicated as follows: seven upright min/log operators, eighteen standard errors incorrectly classified as t statistics, and the existing Figure S.F.1 caption not recognized by the caption regex. Mathematical operators remain upright; standard errors retain three decimals. Audit warnings include proper nouns, repeated citations, official non-DOI sources and preserved layout conventions.
- Prose-pattern screening passes the requested paragraph-share threshold. No simulated observations were added; scale illustrations and historical contract requests retain their explicit definitions.
- Fresh extraction and complete offline execution are recorded in release_payload_replay.json; archive CRC and every member hash are checked during packaging.

Fresh-extracted candidate: all 19 offline jobs PASS; all tested payload files are byte-identical to the delivery inputs. Only validation records are added after this replay.
