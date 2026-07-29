# Reproducible exact-root closure update

This source package is based on repository commit
`ef9d963dad3ef259f5f65b42d006f1491844775d` and prepares version `0.3.1`.

## Added

- `scripts/core/pasqal_L4_exact_root_ordering_audit.py`
- `scripts/standalone/pasqal_L4_exact_root_ordering_standalone_colab.py`
- recorded exact-fibre Krawczyk and exact-root ordering summaries
- regression checks for both new summaries
- frozen cohort, deterministic v1.3 protocols, and complete certificates
- single-file two-run reproducibility audit

## Scientific status represented by this package

- 12/12 strict Krawczyk inclusions certify one locally unique exact
  state-and-first-response-matched root in each declared transverse box.
- Direct outward-rounded Arb propagation of the exact-root phase boxes
  certifies the frozen order for all 66 path pairs.
- The order-30 phase-box mechanism certificate resolves 52/66 pairs, all in
  the frozen direction, with zero reversed pairs.
- Two complete formal executions produce byte-identical protocols,
  certificates, and reports.
- Claims remain conditional on the serialized finite-dimensional two-atom
  model and declared six-axis mean error functional. No PASQAL hardware,
  model-discrepancy, global-fibre, or many-body theorem is claimed.

## Reproduction order

Run the deterministic standalone audit:

```bash
python scripts/standalone/pasqal_L4_reproducible_certificate_v1_3_colab.py
```

It embeds the frozen cohort and predecessor formal ordering certificate,
generates the Krawczyk and exact-root certificates twice, and requires
byte-identical proof artifacts.

## Package verification

```bash
python tools/verify_reference_results.py
python -m unittest discover -s tests -v
```

The bundled checks recompute canonical hashes and validate the complete
formal certificates.
