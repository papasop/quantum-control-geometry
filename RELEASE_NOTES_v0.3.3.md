# Release notes -- v0.3.3 (P0 deterministic artifact)

Version v0.3.3 is a reproducibility maintenance release for the v0.3.2 P0
audit. It does not change the frozen physical model, exact-root boxes,
Krawczyk or Arb proof engines, manuscript, numerical certificates, or the
certified 12/12 and 66/66 conclusions.

## What is fixed

- The P0 audit no longer computes `numpy.linalg.inv` at runtime.
- The binary64 approximate inverse matrices `R` are frozen once as exact
  `float.hex()` strings in
  `tests/audit_closure/data/p0_frozen_inverse_hex.json`.
- P0 reconstructs those entries only with `float.fromhex(...)`, then
  rigorously recomputes `rho = ||I - R B||_inf` with 256-bit outward-rounded
  Arb arithmetic from the production preconditioner representation.
- The frozen inverse data is bound to the cohort SHA-256, production
  preconditioner payload SHA-256, matrix dimensions, and path names.
- The default P0 command is read-only and verifies the committed certificate
  without overwriting tracked files. Maintainers must pass
  `--write-certificate` to regenerate the JSON payload.

## Verification

```bash
python tools/verify_reference_results.py
python -m unittest discover -s tests -v
python tests/audit_closure/p0_preconditioner_nonsingularity.py
python tests/audit_closure/p2_krawczyk_unit_tests.py
python tests/audit_closure/run_mutation_tests.py
python tests/audit_closure/p1_independent_model.py
sha256sum -c SHA256SUMS.txt
```

Do not move `v0.3.1` or `v0.3.2`. Tag v0.3.3 only after the focused
reproducibility PR is merged and CI is green.
