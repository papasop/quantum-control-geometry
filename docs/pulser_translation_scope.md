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
