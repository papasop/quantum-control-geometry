# Exact-root closure update

This source package is based on repository commit
`beb7dc699705df6034831d80370f273adc911f7f` and prepares version `0.3.0`.

## Added

- `scripts/core/pasqal_L4_exact_root_ordering_audit.py`
- `scripts/standalone/pasqal_L4_exact_root_ordering_standalone_colab.py`
- recorded exact-fibre Krawczyk and exact-root ordering summaries
- regression checks for both new summaries

## Scientific status represented by this package

- 12/12 strict Krawczyk inclusions certify one locally unique exact
  state-and-first-response-matched root in each declared transverse box.
- Direct outward-rounded Arb propagation of the exact-root phase boxes
  certifies the frozen order for all 66 path pairs.
- The order-30 phase-box mechanism certificate resolves 42/66 pairs, all in
  the frozen direction, with zero reversed pairs.
- Claims remain conditional on the serialized finite-dimensional two-atom
  model and declared six-axis mean error functional. No PASQAL hardware,
  model-discrepancy, global-fibre, or many-body theorem is claimed.

## Reproduction order

Run the following standalone files in the same working directory:

```bash
python scripts/standalone/pasqal_L4_formal_arb_standalone_colab.py
python scripts/standalone/pasqal_L4_exact_fibre_krawczyk_standalone_colab_v1_2.py
python scripts/standalone/pasqal_L4_exact_root_ordering_standalone_colab.py
```

The last audit consumes the formal-order and Krawczyk certificate JSON files
created by the preceding stages.

## Package verification

```bash
python tools/verify_reference_results.py
python -m unittest discover -s tests -v
```

The bundled summary checks validate recorded fields. Re-running the
standalone audits is required to regenerate the complete formal certificates.
