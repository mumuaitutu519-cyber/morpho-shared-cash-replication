# Checks

- PASS: All 31 coefficient rows: t=coefficient/SE; p-values within [0,1].
- PASS: Transaction FE slope and clustered SE agree with independent explicit-dummy OLS.
- PASS: Market >= 2: coefficients and two-way clustered SEs agree with independent explicit-dummy OLS and statsmodels covariance.
- PASS: Market >= 3: coefficients and two-way clustered SEs agree with independent explicit-dummy OLS and statsmodels covariance.
- PASS: Daily N=439; 62 joint-exclusion dates; gap25=1-4 J/assets and gap10=1-10 J/assets, including corresponding coefficient identities.
- PASS: All 28 cross-protocol states reconcile S-J, duplication rate, S/assets and J/assets.
- PASS: Every cross-protocol vault count and total asset sum matches its address-level table and unique block/hash.
- PASS: All month-end and September 29 blocks precede UTC boundaries, with immediate next-block and finalized-head checks.
- PASS: Manuscript SHA-256 unchanged: Counting_the_same_cash.docx, Counting_the_same_cash.pdf
