# Audit closure (v0.3.2)

Three independent checks added in `v0.3.2`. They do **not** change the frozen
`v0.3.1` physical model, exact-root boxes, or the 66/66 ordering result. They
close verification gaps around that frozen result and are kept separate from the
frozen scientific artifacts.

| Layer | File | What it proves | CI |
|-------|------|----------------|----|
| **P0** | `p0_preconditioner_nonsingularity.py` | Every frozen Krawczyk preconditioner `B` (the `Y` actually used by `krawczyk_path`) is rigorously non-singular. | fast (every push) |
| **P2** | `p2_krawczyk_unit_tests.py` | The Krawczyk interval operator's matrix direction, sign, and strict-inclusion logic are correct, on analytic problems with known answers. | fast (every push) |
| **P1** | `p1_independent_model.py` | An independent code path reproduces all twelve finite-error means, the complete ordering, and the six closest pairs. | independent (manual / weekly) |
| mutation | `run_mutation_tests.py` | The P2 suite fails when the operator is wrong (sign/direction mutations are caught). | fast (every push) |

## P0 -- preconditioner regularity

The Krawczyk existence+uniqueness conclusion requires the preconditioner `Y` to
be regular. `krawczyk_path` uses `Y = B = point_preconditioner_decimal` rounded
to double. This script certifies each `B` non-singular by the standard verified
method: pick a floating approximate inverse `R`, then bound
`rho = ||I - R B||_inf` with 256-bit outward-rounded Arb. `rho < 1` implies `R B`
non-singular (Neumann series), hence `B` non-singular. It also emits a verified
inverse enclosure `||B^-1 - R||_inf <= rho ||R||_inf / (1 - rho)`.
Output: `results/audit_closure/p0_preconditioner_certificate.json`.

## P2 -- operator unit tests

`krawczyk_operator` in this file reproduces `krawczyk_path`'s interval operator
exactly (same `I - Y J` direction, same `-Y f` sign, same strict `<` interior
test), decoupled from the 16-dimensional physics chart. Four analytic families:
analytic linear (including wrong-sign `Y`, off-center direction, and contraction
margin), no root in box, multiple roots (single-root box certifies; box
straddling both roots refuses), and edge-touching (double root and a Krawczyk
image sitting exactly on the box wall). Coverage is verified by
`run_mutation_tests.py`.

## P1 -- independent reconstruction

Rebuilds the operators from scratch, propagates by Hermitian eigendecomposition
(a different numerical path from the formal repo engine's `acb_mat.exp()`), and
cross-checks three paths at 60-digit `mpmath` precision. Each independently
computed per-path binary64 mean must land inside the certificate enclosure,
whose decimal endpoints are parsed without binary64 truncation. The complete
ordering plus the six closest certified pairs must match. This is an independent **code path** on the same documented physical
model: it rules out a shared model-translation error; it does not re-derive the
physics and does not replace the frozen Arb interval certificate.

## Run locally

```bash
python -m pip install -r requirements.txt
python tests/audit_closure/p0_preconditioner_nonsingularity.py   # fast
python tests/audit_closure/p2_krawczyk_unit_tests.py             # fast
python tests/audit_closure/run_mutation_tests.py                # fast
python tests/audit_closure/p1_independent_model.py              # slower
```

Each script exits non-zero on failure.
