# Checks

- PASS: 28 chain-states; unique chain+vault+date rows; positive assets; S-zero exclusion; D identity and [0,1] bounds verified.
- PASS: All leave-one-vault-out joint budgets agree with independent deletion and regrouping of the position data.
- PASS: b_chain_state_FE: coefficients, clustered SEs, p-values and FE rank verified using independent explicit-dummy OLS.
- PASS: c_vault_chain_state_FE: coefficients, clustered SEs, p-values and FE rank verified using independent explicit-dummy OLS.
- PASS: All displayed t statistics and p-values agree with reported inference degrees of freedom.
- PASS: Mechanism a-d numeric results retained; e uses 495 observations/93 transactions; every paper-table coefficient, t statistic and significance star matches the numeric CSV.
- PASS: Descriptive counts reconcile with the complete positive-assets sample and every S-zero exclusion.
- PASS: Manuscript source workspace hashes match the unchanged Word and PDF; manuscripts are excluded from the results archive.
