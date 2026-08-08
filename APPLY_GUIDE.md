# Pulser Tolerance Calibration Apply Guide

## Baseline

Apply this patch on top of main commit:

```text
e88df60c8faf29b4effda8150a57c21caeb5a829
```

## Modified Files

```text
.github/workflows/pulser_translation_diagnostic.yml
APPLY_GUIDE.md
SHA256SUMS.txt
docs/pulser_translation_scope.md
tests/test_pulser_translation_report.py
tools/compare_pulser_translation_reports.py
```

## Scientific Scope

This patch calibrates only the Pulser point-loss comparison tolerance used by
the external numerical translation diagnostic. It is based on GitHub Actions
run `31234420564`, where the full 84-item comparison had zero scientific
hard-gate errors, zero path-mean exceedances, and a maximum cell-loss drift of
`1.43549e-8`.

The cell-loss absolute tolerance is set to `2e-8`, about `0.019%` of the
minimum committed path-mean ordering gap, approximately `1.05078e-4`.

This is not a physical uncertainty, experimental error, or formal interval
bound. The formal Arb/Krawczyk certificate does not use this tolerance.

This patch does not modify the physical model, Pulser propagation algorithm,
solver options, committed Pulser report, exact-root boxes, Arb/Krawczyk proof
engines, formal certificates, manuscript, release tags, or blind 120-point
summary.

## Verification

Run:

```bash
python -m unittest discover -s tests -v
python tools/verify_reference_results.py
sha256sum -c SHA256SUMS.txt
git diff --check
```

If the GitHub candidate report from run `31234420564` is available, also run:

```bash
python tools/compare_pulser_translation_reports.py \
  --reference results/external/pulser_translation_report.json \
  --candidate /path/to/pulser_recomputed_report.json \
  --summary /tmp/pulser_comparison_summary.json
```

Expected result for that candidate:

```text
hard gate errors = 0
loss exceedances = 0
mean exceedances = 0
exit code = 0
```

## Suggested Git Metadata

Commit message:

```text
Calibrate Pulser loss tolerance from exhaustive drift audit
```

Pull request title:

```text
Calibrate Pulser cross-runner loss tolerance
```

Pull request description should state:

- the calibration is based on run `31234420564`;
- maximum observed loss drift was `1.43549e-8`;
- mean exceedances were `0/12`;
- scientific hard-gate errors were `0`;
- `2e-8` is about `0.019%` of the minimum ordering gap;
- no physical model, propagator, result report, or formal proof changed;
- after merge, rerun the 72-point Pulser workflow;
- only after the 72-point workflow succeeds, rerun the 120-point blind test.

## Post-Merge Workflow Steps

1. Manually run `Pulser translation diagnostic` on the merge commit.
2. Confirm the log shows `12 paths × 6 error points = 72 simulations`.
3. Confirm the comparator reports:

   ```text
   hard gate errors: 0
   loss exceedances: 0
   mean exceedances: 0
   ```

4. Confirm the uploaded artifact contains:

   ```text
   /tmp/pulser_recomputed_report.json
   /tmp/pulser_recompute.log
   /tmp/pulser_compare.log
   /tmp/pulser_comparison_summary.json
   ```

5. After the 72-point workflow succeeds, rerun the
   `Blind Pulser response-fibre prospective test` workflow.
