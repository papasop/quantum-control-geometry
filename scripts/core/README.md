# Core audit engine map

The files in this directory are readable core engines and shared audit code.
The frozen proof paths are preserved by filename; do not rename or move these
files when preparing a release.

The canonical proof engines for the frozen exact-root theorem are the two
`_v1_3.py` files. Files without the suffix are retained for historical
inspection and are not the certificate-of-record entry points.

| Scientific role | File | Purpose |
|---|---|---|
| Physical model | `pasqal_two_atom_matched_fibre_test.py` | Two-atom model, target, and matching structure. |
| Prospective ranking | `pasqal_two_atom_q2_prospective_ranking.py` | Frozen ranking and candidate cohort construction. |
| G4 mechanism | `pasqal_two_atom_G4_prospective_v3.py` | Fourth-order prospective predictor. |
| Covariant mechanism | `pasqal_two_atom_L3_L4_tensor_bound_audit.py` | Tensor representation and coordinate-covariance audit. |
| High-order formal certificate | `pasqal_L4_arb_formal_audit.py` | Order-30 Arb certificate at the frozen serialized controls. |
| Exact-root proof | `pasqal_L4_exact_fibre_krawczyk_audit_v1_3.py` | Certificate-of-record engine for the 12/12 Krawczyk root boxes. |
| Main ordering theorem | `pasqal_L4_exact_root_ordering_audit_v1_3.py` | Certificate-of-record engine for 66/66 direct root-box propagation. |
| Historical / compatibility entry | `pasqal_L4_exact_root_ordering_audit.py` | Earlier exact-root ordering audit retained for inspection; not the v0.3.1 certificate-of-record entry point. |

For reviewer reproduction, prefer the standalone wrapper
`scripts/standalone/pasqal_L4_reproducible_certificate_v1_3_colab.py`, which
executes the frozen exact-root proof pipeline twice and checks byte identity.
