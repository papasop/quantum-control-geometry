# L4 Exact-Root Certificate Bundle v1.3.0

This bundle was regenerated from the repository audit scripts with:

- `python-flint==0.8.0`
- outward-rounded Arb arithmetic at 192-bit precision
- 12 declared paths
- a uniform Krawczyk box radius of `3e-12`
- the previously frozen formal finite-error order

## Certified results

- Exact response-fibre Krawczyk inclusion: **12/12**
- Direct exact-root finite-error ordering: **66/66**
- Order-30 local-jet partial ordering: **52/66**
- Incorrect order-30 certified pairs: **0**

The uniform radius is a numerical-conditioning choice. It produces a new
protocol and new certificate hashes; this bundle does not claim to reproduce
the byte identity of an earlier adaptive-radius run.

## Claim boundary

The certificates apply to the serialized two-atom neutral-atom model. They do
not certify PASQAL Cloud execution, QPU behaviour, hardware calibration, model
discrepancy, or exact optimizer identities outside the certified interval
boxes.

## Repository placement

Copy the two directories under `results/` into the repository's `results/`
directory. Keep the six JSON files together so that protocol, certificate and
report remain auditable as one unit.
