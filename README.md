# Quantum Control Geometry


## Reviewer quick path

Start with [`REVIEWER_GUIDE.md`](REVIEWER_GUIDE.md) for the theorem hierarchy,
three-minute artifact verification, full formal reproduction, and exact scope
boundary.

Reproducible research artifacts for covariant local response jets and
exact-root finite-error certification in a serialized two-atom neutral-atom
control model.

This repository accompanies the manuscript:

> **Geometric Prediction and Exact-Root Certification of
> Finite-Error Ordering in Quantum Control**

Canonical v0.3.1 commit:

```text
284974c9f6b952f4e114c8c5bdc9c2c299c4065c
```

Version `v0.3.1` freezes the scientific artifacts. The manuscript on `main`
may contain later expository and formula-level corrections without changes to
the frozen numerical certificates. A separate immutable paper-exact tag, for
example `paper-exact-root-v1.0`, should freeze the synchronized submission
manuscript source and PDF without moving `v0.3.1`.

## Strongest Result

For the frozen finite-dimensional two-atom Hamiltonian model and declared
six-axis mean error functional, direct outward-rounded Arb propagation over
twelve locally unique projectively matched root boxes certifies the
predeclared finite-error ordering for all 66 unordered path pairs.

The main theorem-level certificate is:

- 12/12 strict Krawczyk inclusions certify one locally unique projectively
  matched root in each declared transverse phase box.
- 66/66 direct finite-error pairwise orderings are certified by 192-bit
  outward-rounded Arb propagation over those exact-root boxes.
- Two complete v1.3 formal runs produce byte-identical protocols,
  certificates, and reports.

This is a formal, model-conditional certificate. It is not PASQAL Cloud,
QPU, calibration, or model-discrepancy evidence.

## Counts At A Glance

| Certificate layer | Coverage | Meaning |
|---|---:|---|
| Quartic-only serialized-control audit | 34/66 (51.52%) | Low-order G4 comparison certifies a substantial subset, but not all close pairs |
| Frozen-point order-30 Arb certificate | 66/66 | Order-30 zero-error jet plus alias and tail bounds certifies the frozen serialized controls |
| Exact-root order-30 mechanism certificate | 52/66 | Order-30 jet propagated over exact-root Krawczyk boxes certifies 52 pairs with zero reversals |
| Exact-root direct finite-error certificate | 66/66 | Primary result: direct Arb propagation over certified exact-root boxes closes all pairwise orderings |
| Reproducibility closure | PASS | Two complete v1.3 executions produce byte-identical proof artifacts |

Do not conflate these numbers. The 34/66 quartic result, the 52/66
exact-root order-30 mechanism result, and the 66/66 direct exact-root result
come from different certificate layers.

## Quick Verification

No PASQAL account is required to verify the bundled artifacts.

```bash
python tools/verify_reference_results.py
python -m unittest discover -s tests -v
```

Linux / Colab:

```bash
sha256sum -c SHA256SUMS.txt
```

macOS:

```bash
shasum -a 256 -c SHA256SUMS.txt
```

The verifier recomputes canonical JSON hashes, checks the scientific gates,
rejects runtime fields inside hashed proof objects, and confirms the recorded
two-run identity result.

## Reproduce The Certificates

The complete deterministic v1.3 audit is packaged as a single Colab/Jupyter
entry point:

```bash
python scripts/standalone/pasqal_L4_reproducible_certificate_v1_3_colab.py
```

In Colab:

```python
%run /content/pasqal_L4_reproducible_certificate_v1_3_colab.py
```

This script embeds the frozen cohort and predecessor formal ordering
certificate, fixes the common Krawczyk radius at `3e-12`, generates the
Krawczyk and exact-root certificates twice, and requires byte-identical proof
artifacts.

Formal audits require:

```bash
python -m pip install -r requirements.txt
```

For review-time reproduction of the formal certificate environment, use the
exact lock file:

```bash
python -m pip install -r requirements-lock.txt
```

`requirements.txt` records the supported compatibility range. The
`requirements-lock.txt` file records the exact dependency versions used for
the formal submission certificate environment.

The full exact-root certificate reproduction is also available as a manual
GitHub Actions workflow, `Full exact-root certificate reproduction`. It runs
`scripts/standalone/pasqal_L4_reproducible_certificate_v1_3_colab.py` and
uploads the generated log and certificate directory.

## External Clean-Environment Reproduction

No PASQAL account is required. The external runner checks out the frozen
`v0.3.1` tag, verifies its commit and SHA-256 snapshot, runs the regression
tests, and recomputes the complete formal certificate twice.

[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/papasop/quantum-control-geometry/blob/main/notebooks/reproduce_v0_3_1.ipynb)

Expected frozen commit:

```text
284974c9f6b952f4e114c8c5bdc9c2c299c4065c
```

To run the same clean-environment reproduction script manually in Colab,
upload and run:

```python
%run /content/external_reproduce_v0_3_1.py
```

This remains a reproduction of the same frozen model, code, and certificate
pipeline; it is not independent scientific validation or PASQAL hardware
evidence.

## Stage-Specific Entry Points

Earlier standalone audits remain available for inspecting individual layers:

```bash
python scripts/standalone/external_reproduce_v0_3_1.py
python scripts/standalone/pasqal_two_atom_G4_standalone_colab.py
python scripts/standalone/pasqal_L3_L4_standalone_colab.py
python scripts/standalone/pasqal_L4_order30_standalone_colab.py
python scripts/standalone/pasqal_L4_formal_arb_standalone_colab.py
python scripts/standalone/pasqal_L4_exact_fibre_krawczyk_standalone_colab_v1_2.py
python scripts/standalone/pasqal_L4_exact_root_ordering_standalone_colab.py
```

Readable core audit engines are in `scripts/core/`.

## Repository Navigation

```text
paper/
  main.tex            canonical editable manuscript entry point
  sec_front.tex       front matter, introduction, and scope
  sec_mid.tex         exact-root construction and theorem
  sec_back.tex        validation, availability, and references
  manuscript.pdf      public PDF version of record

scripts/
  standalone/       single-file Colab/Jupyter entry points
  core/             readable audit engines and shared model code

notebooks/
  reproduce_v0_3_1.ipynb

results/
  g4_prospective/          prospective quartic ranking artifacts
  l3_covariance/           tensor covariance and invariant contraction audit
  l4_order30/              floating order-30 reconstruction and tail audit
  l4_formal/               192-bit Arb frozen serialized-control certificate
  exact_fibre_krawczyk/    frozen cohort, protocol, Krawczyk certificate, report
  exact_root_ordering/     protocol, direct exact-root ordering certificate, report
  reproducibility_summary.json

tools/
  verify_reference_results.py

tests/
  test_manuscript_consistency.py
  test_reference_artifacts.py
```

`SHA256SUMS.txt` records byte hashes for the repository snapshot. The
certificate reports also store canonical JSON hashes for the proof payloads.
Those canonical hashes are recomputed by `tools/verify_reference_results.py`.

## Certificate Hierarchy

| Stage | Object | Supported conclusion |
|---|---|---|
| G4 prospective | Scalar fourth-order contraction | Strong mean-performance predictor on the frozen 20-path cohort |
| L3 tensor | Symmetric fourth-order response tensor | Coordinate-covariant tensor and invariant noise-moment contraction |
| L4 quartic | G4 interval with higher terms placed in the radius | Partial pairwise certification: 34/66 (51.52%) |
| L4 order 30 | Zero-error jet through order 30 plus alias and tail bounds | Complete 66/66 ordering for frozen serialized controls |
| Exact-fibre Krawczyk | Interval Newton/Krawczyk in transverse charts | 12/12 locally unique roots exactly matched in projective output state and first projective response |
| Exact-root order-30 mechanism | Jet propagation over certified root boxes | 52/66 pairs certified, zero reversals |
| Exact-root direct L4 | Direct Arb propagation over certified root boxes | Complete 66/66 frozen finite-error ordering |
| Reproducibility closure | Two complete frozen-cohort formal runs | Byte-identical protocols, certificates, and reports |

The direct exact-root propagation is the primary finite-radius theorem. The
exact-root order-30 calculation is a separate, computationally distinct
mechanism certificate; it does not need to resolve all pairs to support the
stronger direct result.

## Non-Claims

This repository does not certify:

- PASQAL hardware, FRESNEL, PASQAL Cloud, or QPU execution;
- calibration, waveform filtering, decoherence, Doppler effects, leakage,
  position fluctuations, or model discrepancy;
- global uniqueness of the full implementation fibre outside the certified
  local boxes;
- worst-case-error ranking;
- a universal fourth-order robustness law;
- many-body scaling.

The result is intentionally narrower: in one frozen serialized two-atom model,
the exact-root direct interval certificate closes the finite-error ordering
for all 66 path pairs, while lower-order geometric objects explain and
partially certify the same order.

## Code And Data Availability

All source code, frozen numerical inputs, outward-rounded interval
certificates, verification utilities, and manuscript source are included in
this repository. Version `v0.3.1` is fixed at commit
`284974c9f6b952f4e114c8c5bdc9c2c299c4065c`.

An archival DOI should be inserted after GitHub-Zenodo deposition. Once the
DOI is assigned, update only DOI/version metadata in the manuscript and
recompile the PDF; do not change numerical artifacts or scientific
conclusions.

## Citation

See [`CITATION.cff`](CITATION.cff). Until the archival DOI is assigned, cite
the repository, version `v0.3.1`, and the canonical commit above.

For submission freezing, keep `v0.3.1` as the scientific certificate version.
After the final manuscript source and PDF are synchronized, create a separate
immutable paper-exact tag such as `paper-exact-root-v1.0` and attach the final
PDF, LaTeX source package, SHA-256 hashes, reproduction entry point, and a
note relating that paper package to the `v0.3.1` scientific artifacts.

## License

Code is released under the MIT License. See [`LICENSE`](LICENSE).

The manuscript source, compiled manuscript PDF, and manuscript figures in
`paper/` are released under the Creative Commons Attribution 4.0 International
License (CC BY 4.0).
