# R23 bounded minor-revision plan

Freeze the R22 94-deposit cohort, eight gross-withdrawal-selected dates, 319 daily
states and 46 peer states. No new collection, cohort expansion or regressions.

1. Compare attributing all 94 same-transaction vault deposits to arrivals with
   the original feasible joint interval. Calculate gross attribution minus each
   endpoint from integers. These are bounds on excess attribution, not an
   observed true error. Report that zero lower bounds permit other-cash funding.
2. Classify all 94 deposits into both adjacent closes below 25%, prior only,
   same-day only, neither. Use the exact strict inequality 4*capacity < claim.
   Report counts, positive marginal lower-bound counts, deposit amounts and
   jointly optimized funding intervals for each cell. Also solve the all-vault,
   prior-positive/low and same-day-positive/low groups (36 and 43 previously).
   Keep all ordered transaction cash constraints fixed, changing only selected
   target outflows. Check integer endpoint allocations with the independent LP.
   Do not treat temporal agreement as proof about the unobserved entry state.
3. Add daily net withdrawal = account withdrawal - account deposit for the
   original eight dates. Never reselect on the net measure. Retain unmatched
   common-market flows and the complete market sequence unchanged.
4. Retain original residual gaps and actual raw fee coverage. Replace the 170-day
   PDF schedule with a summary; supply every original row in a machine-readable
   supplement. Explicitly map raw and previously prepared inputs to replay steps.

This is a revision plan responding to known referee comments, not preregistration.
