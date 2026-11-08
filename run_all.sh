#!/usr/bin/env bash
set -euo pipefail
PACKAGE_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
if [[ -z "${MORPHO_VERIFY_OUTPUT:-}" ]]; then
  if [[ -d '/Volumes/Extreme SSD/T9/_tmp' ]]; then
    MORPHO_VERIFY_OUTPUT='/Volumes/Extreme SSD/T9/_tmp/305/morpho-verification'
  else
    MORPHO_VERIFY_OUTPUT="$(mktemp -d "${TMPDIR:-/tmp}/morpho-verification.XXXXXX")"
  fi
fi
python3 "$PACKAGE_ROOT/code/verify_current_tables.py" --output "$MORPHO_VERIFY_OUTPUT"
printf 'Verification files: %s\n' "$MORPHO_VERIFY_OUTPUT"
