# Release notes -- v0.3.2 (audit closure)

Version v0.3.2 does not change the frozen physical model, exact-root boxes, or
66/66 ordering result of v0.3.1. It adds a rigorous regularity certificate for
the production Krawczyk preconditioners, an independent high-precision
reconstruction of all twelve finite-error means and their complete ordering, and
mutation-tested analytic unit tests for the Krawczyk operator.

## What is new

- **P0 -- preconditioner regularity certificate.** 256-bit outward-rounded Arb
  proof that every frozen Krawczyk preconditioner `B` used by `krawczyk_path` is
  non-singular (`||I - R B||_inf < 1`), with a verified inverse enclosure. This
  supplies the previously implicit regularity precondition of the Krawczyk
  uniqueness statement. Result: 12/12 non-singular.

- **P2 -- Krawczyk operator unit tests.** Analytic tests of the interval
  operator's matrix direction, sign, and strict-inclusion logic (linear,
  no-root, multi-root, edge-touching). Their discriminating power is verified by
  mutation testing (`MUTATION_TEST_REPORT.md`): the suite fails under both a
  defect-direction/sign mutation and a correction-sign mutation.

- **P1 -- independent reconstruction.** A separate code path (operators rebuilt
  from scratch, Hermitian-eigendecomposition propagation, 60-digit mpmath
  cross-check) reproduces all twelve finite-error means inside the certificate's
  full-precision enclosures, the complete best-to-worst ordering, and the six
  closest certified pairs.

## What is unchanged

- The frozen physical model, the twelve exact-root Krawczyk boxes, and the
  66/66 finite-error ordering of v0.3.1.
- The frozen v0.3.1 result directories and all files under `paper/`.
  A separate `results/audit_closure/` directory records the new P0 certificate.
- `tools/verify_reference_results.py` now verifies the additional P0
  production-preconditioner regularity certificate while preserving all v0.3.1
  artifact checks.

## Scope

P0 and P2 are rigorous. P1 is an independent code path on the same documented
physical model: it rules out a shared model-translation error and cross-checks
the frozen certificate; it does not re-derive the physics and does not replace
the frozen Arb interval certificate, which remains the certificate of record.

## Verify

```bash
# frozen v0.3.1 artifacts (unchanged)
python tools/verify_reference_results.py
python -m unittest discover -s tests -v

# v0.3.2 audit closure
python -m pip install -r requirements-lock.txt
python tests/audit_closure/p0_preconditioner_nonsingularity.py
python tests/audit_closure/p2_krawczyk_unit_tests.py
python tests/audit_closure/run_mutation_tests.py
python tests/audit_closure/p1_independent_model.py   # slower
```

## Tagging

Tag this commit `v0.3.2` without moving `v0.3.1`. The `v0.3.1` tag remains the
frozen scientific-certificate version; `v0.3.2` is the audit-closure version
built on top of it.
