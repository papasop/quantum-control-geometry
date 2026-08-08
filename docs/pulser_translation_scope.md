# Pulser Translation Scope

The Pulser external validation layer is a numerical translation and
ordering-robustness cross-check for the frozen exact-root result. It is kept
separate from the Arb/Krawczyk certificate of record.

## What It Checks

- The twelve 24-segment schedules are evaluated under Pulser 1.9 numerical
  translation semantics.
- All 72 path/error-point values are finite.
- The complete twelve-path ordering matches the frozen certificate ordering.
- All 66 certified pair directions agree with the frozen ordering.
- Pulser quantized-distance means do not lie inside the original continuous
  Arb intervals: 0/12 means are inside those intervals.

The current status is:

```text
ORDERING_ROBUST_UNDER_PULSER_QUANTIZATION
```

The exact-translation gate is false, while the ordering-robustness gate is
true. This distinction is intentional and is recorded in
`results/external/pulser_translation_report.json`.

## Committed Report And Recalculation

`tools/validate_pulser_translation_report.py` checks the committed JSON report
for the declared gate values and forbidden overclaims. It does not rerun
Pulser.

`tests/external/recompute_pulser_translation.py` performs the numerical
recalculation. It reads the twelve candidate phase schedules from the frozen
Krawczyk certificate, rebuilds the two-atom Pulser register and 24-segment
global Rydberg pulse sequence, runs 12 paths times 6 finite-error points, and
writes a fresh report to the path given by `--output`.

The interaction-error translation uses the Pulser
`DigitalAnalogDevice.interaction_coeff` value and

```text
r = round((r0 / (1 + epsilon_V)^(1/6)) / 0.01 um) * 0.01 um.
```

The two-decimal-micrometre coordinate quantization is part of this external
Pulser translation layer. It is not an Arb/Krawczyk interval operation and is
one reason the exact-translation gate remains false.

`tools/compare_pulser_translation_reports.py` compares a recomputed report
against the committed report. It requires the structural gates to match and
also compares every one of the 72 losses and all 12 path means. Pulser point
values are not formal interval certificates, and the point-level cell losses
allow `2e-8` absolute drift across BLAS/ODE runners. Path means keep the
stricter `5e-9` absolute tolerance. The complete ordering and all 66 pair
directions remain exact hard gates. The `2e-8` cell-loss tolerance is far below
the smallest committed path-mean ordering gap, about `1.05078e-4`, and is not a
physical uncertainty or experimental error. The formal Arb/Krawczyk certificate
does not use this tolerance.

## What It Does Not Check

This layer is not a formal interval proof and does not replace the
Arb/Krawczyk certificate. It does not modify the physical model, exact-root
boxes, proof engines, manuscript theorem, or immutable release tags.

It is also not a PASQAL Cloud run, not a QPU execution result, and not evidence
about calibration, decoherence, model discrepancy, open-system dynamics, or
many-body scaling.

## Relationship To The Formal Certificate

- Arb/Krawczyk: frozen-model strict mathematical certificate.
- Pulser: external numerical translation and ordering-robustness cross-check.
- PASQAL QPU execution: not tested in this repository.
