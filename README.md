# Quantum Control Geometry


## Reviewer quick path

Start with [`REVIEWER_GUIDE.md`](REVIEWER_GUIDE.md) for the theorem hierarchy,
three-minute artifact verification, full formal reproduction, and exact scope
boundary.

## Evidence layers

| Evidence layer | Result | Logical status |
|---|---|---|
| Arb/Krawczyk certificate | 12/12 locally unique roots and 66/66 finite-error pair orderings | Rigorous model-conditional proof |
| Pulser translation diagnostic | 12 paths x 6 errors; complete order and 66/66 pair directions preserved | Independent numerical translation cross-check |
| Blind Pulser prospective test | 20 paths x 6 errors; preregistered ranking supported | Prospective numerical validation through an independent code path |
| Open-system QuTiP stress audit | 12 paths x 6 errors over 29 decay/dephasing stress conditions | Empirical open-system sensitivity stress test within a declared Lindblad extension |
| Prospective dissipative-susceptibility reveal | 1715/1716 directions, C-index 1.000, factor-two 19/20 | Frozen prospective QuTiP Lindblad validation |
| PASQAL Cloud/QPU | Not executed | No hardware claim |

Arb/Krawczyk is the strict interval proof layer. Pulser uses independent local
numerical execution paths and is not a second interval proof. The GitHub
Actions runs execute on GitHub-hosted CPUs. The open-system stress audit is not
an interval proof, Pulser run, PASQAL Cloud run, or physical QPU result.

**Response fibre in one sentence.** The response fibre is the family of control
schedules that share the same nominal projective output state and complete
first-order projective response to the declared error coordinates, while
retaining different higher-order finite-error behaviour.

Reproducible research artifacts for covariant local response jets and
exact-root finite-error certification in a serialized two-atom neutral-atom
control model.

This repository accompanies the manuscript:

> **Exact-Root Certification of Finite-Error Ordering in Quantum Control**

Canonical v0.3.1 commit:

```text
284974c9f6b952f4e114c8c5bdc9c2c299c4065c
```

Version `v0.3.1` freezes the main strict scientific certificate artifacts.
Version `v0.3.2` freezes the P0/P1/P2 audit-closure supplement. The current
`v0.4.1` tag marks the Pulser external model-validation layer. The published
reviewer-facing manuscript archive is `paper-exact-root-v1.2.1`, with Zenodo
version DOI [`10.5281/zenodo.21898645`](https://zenodo.org/records/21898645).
This v1.2.1 paper archive is a text and presentation-layer revision only: it
does not rerun Arb, change theorem-bearing assets, modify certified thresholds,
or add hardware/QPU claims. Separate immutable paper-exact tags freeze
manuscript source/PDF snapshots without moving `v0.3.1`.

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

## Mathematical Core

For each declared schedule, the exact-response problem is reduced in a
transverse chart to
```math
F_y(x)=0,\qquad x\in\mathbb{R}^{16},
```
where $y\in\mathbb{R}^{8}$ denotes the retained fibre coordinates and
$x$ denotes the transverse phase correction.

Local existence and uniqueness are certified by the Krawczyk operator
```math
K(X)=x_0-YF_y(x_0)
+\left(I-Y\,DF_y(X)\right)(X-x_0),
```
through the strict inclusion
```math
K(X)\subset\operatorname{int}(X).
```
The v0.3.2 P0 audit additionally verifies
```math
\rho=\left\|I-RY\right\|_\infty<1,
```
which rigorously certifies regularity of the production preconditioner
$Y$, where $R$ is a frozen binary64 approximate inverse reconstructed
exactly from hexadecimal data and independently verified using 256-bit
outward-rounded Arb arithmetic.

For two certified paths $i$ and $j$, let $I_i$ and $I_j$ be the
direct outward-rounded Arb intervals of the declared finite-error mean.
The pairwise order is certified whenever
```math
\sup I_i < \inf I_j.
```
For twelve paths there are
```math
\binom{12}{2}=66
```
unordered comparisons. The direct exact-root certificate proves strict
separation for all 66 pairs over the complete certified root boxes.

See the [manuscript](paper/manuscript.pdf),
[`docs/mathematical_hierarchy.md`](docs/mathematical_hierarchy.md), and
[`scripts/core/README.md`](scripts/core/README.md) for the full certificate
hierarchy and certificate-of-record implementations.

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

## Audit Closure v0.3.2

Version `v0.3.2` adds audit-closure checks without changing the frozen
physical model, exact-root boxes, manuscript, or the v0.3.1 66/66 ordering
certificate.

```bash
python -m pip install -r requirements-lock.txt
python tests/audit_closure/p0_preconditioner_nonsingularity.py
python tests/audit_closure/p2_krawczyk_unit_tests.py
python tests/audit_closure/run_mutation_tests.py
python tests/audit_closure/p1_independent_model.py
```

P0 certifies production-preconditioner regularity, P2 mutation-tests the
Krawczyk operator logic, and P1 independently reconstructs the twelve
finite-error means and complete ordering. The P1 check also has a manual and
weekly GitHub Actions workflow, `Audit closure (independent) -- P1
high-precision reconstruction`.

## Independent Pulser-model validation

The formal Arb/Krawczyk layer remains the frozen-model strict mathematical
certificate. Pulser is used as an external numerical translation and
prospective-validation layer, not as a replacement proof. PASQAL Cloud,
FRESNEL, and QPU execution are not tested in this repository.

Pulser 1.8 and Pulser 1.9 play different roles here. The manuscript's frozen
two-atom model uses the Pulser 1.8 `DigitalAnalogDevice` constant as the
serialized source of the $C_6$ parameter. The external validation workflows run
in locked Pulser 1.9 environments. This does not imply the formal certificate
and the external Pulser checks depend on identical software stacks.

### 1. Translation robustness

The committed Pulser 1.9 translation report records:

- 12 paths x 6 error points = 72 propagations.
- 72/72 numerical values are finite.
- The complete twelve-path ordering is identical to the frozen ordering.
- Certified pair directions agree for 66/66 unordered path pairs.
- 0/12 Pulser means lie inside the original Arb intervals.
- `exact_translation_pass = false`.
- `ordering_robustness_pass = true`.

Run the diagnostic locally with:

```bash
python -m pip install -r requirements-pulser.txt
python tools/validate_pulser_translation_report.py
```

This command validates the integrity and stated gates of the committed report.
To actually rerun the Pulser 1.9 propagation layer, use:

```bash
python tests/external/recompute_pulser_translation.py \
  --output /tmp/pulser_recomputed_report.json
python tools/validate_pulser_translation_report.py \
  --report /tmp/pulser_recomputed_report.json
python tools/compare_pulser_translation_reports.py \
  --reference results/external/pulser_translation_report.json \
  --candidate /tmp/pulser_recomputed_report.json
```

The manual GitHub Actions workflow `Pulser translation diagnostic` runs that
full recomputation, validates the recomputed report, compares every Pulser
loss and path mean to the committed report, and uploads the recomputed report
and run log. See
[`docs/pulser_translation_scope.md`](docs/pulser_translation_scope.md) and
[`results/external/pulser_translation_report.json`](results/external/pulser_translation_report.json).

Pulser and Arb have small absolute point-value offsets under the quantized
Pulser translation, so this layer supports ordering robustness, not pointwise
model equivalence.

One-click workflow:
[`Pulser translation diagnostic`](https://github.com/papasop/quantum-control-geometry/actions/workflows/pulser_translation_diagnostic.yml).
Use **Actions -> Run workflow -> main -> Run workflow**.

### 2. Blind prospective validation

The blind prospective Pulser summary records:

- 20 paths x 6 error points = 120 propagations.
- Spearman rho = `0.998496`.
- One-sided permutation p-value = `4.99975e-05`.
- Best-worst mean-loss advantage = `0.01131757`.
- Best-worst bootstrap 95% interval = `[0.007947237, 0.01522103]`.
- All preregistered gates pass.
- Protocol SHA-256 =
  `2bf2d193f9839a7f204984705d3ccef9ddead2bf3cf906e56b52138b402dd71c`.
- Prediction-freeze SHA-256 =
  `535f3ed5821997059f5568bab76e824aad12183414199ded755a40a2fa08dad1`.
- Outcomes were locked before Pulser reveal:
  `source_outcomes_unlocked = false`.

This is a prospective numerical validation through an independent code path.
It is not another Arb proof and not a QPU experiment. See
[`docs/blind_pulser_response_fibre_scope.md`](docs/blind_pulser_response_fibre_scope.md),
[`results/external/pasqal_blind_response_fibre_v1_0_summary.json`](results/external/pasqal_blind_response_fibre_v1_0_summary.json),
and [`tools/verify_blind_pulser_summary.py`](tools/verify_blind_pulser_summary.py).

One-click workflow:
[`Blind Pulser response-fibre prospective test`](https://github.com/papasop/quantum-control-geometry/actions/workflows/blind_pulser_response_fibre.yml).
Use **Actions -> Run workflow -> main -> Run workflow**.

### 3. Open-system ordering-survival stress audit

The open-system QuTiP stress audit records:

- 12 paths x 6 error points x 29 stress conditions = 2088 propagations.
- 2088/2088 values are finite.
- The unitary reconstruction preserves 66/66 pair directions and the complete
  frozen order.
- Declared decay, dephasing, and joint stress gates pass.
- 55/66 path pairs never flip on the declared stress grid.
- The minimum certificate-margin pair `pv08>pv11` never flips on the declared
  grid.
- `scientific_status = OPEN_SYSTEM_STRESS_AUDIT_COMPLETE`.

This is an empirical open-system sensitivity stress test within a declared
Lindblad extension. It is not an interval proof, not a Pulser execution, not
a PASQAL Cloud run, and not a physical QPU result. The original run was not
independently hash-frozen before outcome reveal, and the
differential-susceptibility follow-up is post-hoc exploratory.

Validate the committed protocol and summary locally with:

```bash
python tools/verify_open_system_ordering_survival_v1_0.py
```

The manual GitHub Actions workflow reruns the full 2088-propagation audit,
compares the generated scientific projection with the committed summary, and
uploads the full machine report as an artifact. See
[`docs/open_system_ordering_survival_scope.md`](docs/open_system_ordering_survival_scope.md),
[`results/external/open_system/pasqal_open_system_ordering_survival_v1_0_summary.json`](results/external/open_system/pasqal_open_system_ordering_survival_v1_0_summary.json),
and
[`tools/verify_open_system_ordering_survival_v1_0.py`](tools/verify_open_system_ordering_survival_v1_0.py).

One-click workflow:
[`Open-system ordering-survival stress audit`](https://github.com/papasop/quantum-control-geometry/actions/workflows/open_system_ordering_survival.yml).
Use **Actions -> Run workflow -> main -> Run workflow**.

### 4. Prospective dissipative-susceptibility reveal

The separately frozen v1.1.2 QuTiP Lindblad reveal records:

- 2,232/2,232 finite density-matrix propagations;
- 66/66 zero-noise certified pair directions reconstructed;
- 1,715/1,716 held-out pair-condition directions predicted correctly
  (`0.999417`, frozen gate `0.90`);
- pooled Harrell C-index `1.000` over 1,217 comparable items
  (frozen gate `0.75`);
- 19/20 eligible first-flip scales within a factor of two (`0.95`, frozen gate
  `0.70`);
- all frozen gates passed.

This is prospective numerical evidence in the declared two-atom QuTiP
Lindblad model. It is not an Arb proof, calibrated PASQAL hardware-noise
result, PASQAL Cloud run, FRESNEL run, or QPU experiment. See
[`docs/dissipative_susceptibility_reveal_status.md`](docs/dissipative_susceptibility_reveal_status.md)
and
[`results/external/open_system/dissipative_susceptibility_reveal_v1_1_2_summary.json`](results/external/open_system/dissipative_susceptibility_reveal_v1_1_2_summary.json).

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

APPLY_GUIDE.md        integration note for the Pulser tolerance calibration PR

scripts/
  standalone/       single-file Colab/Jupyter entry points
  core/             readable audit engines and shared model code
    README.md       core engine map and certificate-of-record entry points

notebooks/
  reproduce_v0_3_1.ipynb

results/
  g4_prospective/          prospective quartic ranking artifacts
  l3_covariance/           tensor covariance and invariant contraction audit
  l4_order30/              floating order-30 reconstruction and tail audit
  l4_formal/               192-bit Arb frozen serialized-control certificate
  exact_fibre_krawczyk/    frozen cohort, protocol, Krawczyk certificate, report
  exact_root_ordering/     protocol, direct exact-root ordering certificate, report
  audit_closure/           v0.3.2 production-preconditioner regularity certificate
  external/
    pulser_translation_report.json
    pasqal_blind_response_fibre_v1_0_summary.json
    open_system/
      pasqal_open_system_ordering_survival_v1_0_protocol.json
      pasqal_open_system_ordering_survival_v1_0_summary.json
      dissipative_susceptibility_reveal_v1_1_2_summary.json
  reproducibility_summary.json

tools/
  verify_reference_results.py
  validate_pulser_translation_report.py
  compare_pulser_translation_reports.py
  verify_blind_pulser_summary.py
  verify_open_system_ordering_survival_v1_0.py
  verify_dissipative_susceptibility_reveal_summary.py

tests/
  audit_closure/           P0, P1, P2, and mutation-tested audit supplement
  external/
    recompute_pulser_translation.py
    pasqal_blind_response_fibre_v1_0.py
    pasqal_open_system_ordering_survival_v1_0.py
    run_dissipative_susceptibility_reveal_v1_1_2.py
  test_dissipative_susceptibility_reveal_summary.py
  test_manuscript_consistency.py
  test_reference_artifacts.py

docs/
  pulser_translation_scope.md
  blind_pulser_response_fibre_scope.md
  open_system_ordering_survival_scope.md
  dissipative_susceptibility_reveal_status.md

.github/workflows/
  audit_closure_fast.yml         P0 + P2 + mutation tests on push/PR
  audit_closure_independent.yml  P1 manual/weekly independent reconstruction
  pulser_translation_diagnostic.yml  Pulser recomputation and report comparison
  blind_pulser_response_fibre.yml    blind 20-path prospective Pulser validation
  open_system_ordering_survival.yml  open-system ordering-survival stress audit
  dissipative_susceptibility_reveal.yml  manual v1.1.2 holdout reveal
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

The published v1.2.1 manuscript archive is available at Zenodo:

- Version DOI: [`10.5281/zenodo.21898645`](https://doi.org/10.5281/zenodo.21898645)
- Zenodo record: [`https://zenodo.org/records/21898645`](https://zenodo.org/records/21898645)
- Concept DOI: [`10.5281/zenodo.20713301`](https://doi.org/10.5281/zenodo.20713301)
- Resource type: Publication / Preprint
- Publication date: 2026-08-12
- PDF SHA-256: `41d783329f1ceb761dc81131127e5cff90720c4e60fbe6a17d21647b048a98ab`
- Source ZIP SHA-256: `4972a400f4a910d9e7a9fbe6d22cf3c252f5889c8041eba82671f9a5ca447f1e`

Historical version DOI [`10.5281/zenodo.21831180`](https://doi.org/10.5281/zenodo.21831180)
corresponds to an older PDF record and is not the v1.2.1 version DOI. The
repository keeps the frozen numerical certificates separate from manuscript
archive records. No GitHub Release URL is asserted here unless it has been
created separately.

## Citation

See [`CITATION.cff`](CITATION.cff). Cite the v1.2.1 manuscript DOI together
with the repository version or exact commit used for reproduction.

For submission freezing, keep `v0.3.1` as the scientific certificate version.
For manuscript archival, use a separate immutable paper-exact tag. The v1.2.1
paper archive records the final PDF, LaTeX source package, SHA-256 hashes,
reproduction entry point, and its relation to the unchanged `v0.3.1`
scientific artifacts.

## License

Code is released under the MIT License. See [`LICENSE`](LICENSE).

The manuscript source, compiled manuscript PDF, and manuscript figures in
`paper/` are released under the Creative Commons Attribution 4.0 International
License (CC BY 4.0).
