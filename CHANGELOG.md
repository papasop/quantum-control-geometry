# Changelog

## [paper-exact-root-v1.2.1 archive candidate] -- textual archive alignment

This paper archive candidate is a text and presentation-layer revision only. It
does not change the frozen physical model, Arb/Krawczyk proof engines,
theorem-bearing JSON, exact-root boxes, protocols, numerical thresholds,
certified 12/12 roots, or certified 66/66 direct ordering theorem.

- Archived the 25-page v1.2.1 manuscript source/PDF candidate into `paper/`.
- Updated manuscript page/hash gates for the v1.2.1 PDF.
- Closed the legacy G4 manuscript-sample provenance status as corrected in the
  v1.2.1 textual revision while preserving the historical
  `original_colab_sample.mean_spearman = 0.996992` provenance value.
- Recorded that the historical DOI `10.5281/zenodo.21831180` corresponds to an
  older PDF; the v1.2.1 tag, GitHub Release URL, and DOI remain pending.

## [v0.4.2 release candidate] -- manuscript G4 qualification and release hygiene

The v0.4.2 release candidate is a manuscript and CI hygiene state. It does not
change the frozen physical model, exact-root boxes, Arb/Krawczyk proof engines,
result artifacts, audit-closure artifacts, or certified 12/12 and 66/66
conclusions.

- Qualified the prospective $G_4$ manuscript result across numerical
  architectures: the stable claim is the predeclared
  $\rho_{\mathrm{Spearman}}\ge0.95$ threshold, while exact correlations and
  named top paths are platform-dependent diagnostics.
- Removed the legacy platform-specific value 0.996992 from the manuscript
  source and PDF; it remains only as provenance metadata in
  `results/g4_prospective/provenance.json`.
- Replaced the two-panel Figure 2 with the exact-root interval panel
  `paper/fig2_exact_root.png`.
- Clarified that byte-identical reproducibility applies to the formal
  Arb/Krawczyk proof artifacts, not to ordinary float64 prospective
  cohort-generation diagnostics.
- Updated Artifact checks so the manuscript gate forbids 0.996992, checks the
  threshold-level G4 wording, and can be run manually with `workflow_dispatch`.

## [v0.3.2] -- audit closure

Version v0.3.2 does not change the frozen physical model, exact-root boxes, or
66/66 ordering result of v0.3.1. It adds a rigorous regularity certificate for
the production Krawczyk preconditioners, an independent high-precision
reconstruction of all twelve finite-error means and their complete ordering, and
mutation-tested analytic unit tests for the Krawczyk operator.

- Added `tests/audit_closure/` with three separable checks:
  - **P0** (`p0_preconditioner_nonsingularity.py`): rigorous 256-bit Arb
    non-singularity certificate for each frozen Krawczyk preconditioner `B` (the
    `Y` actually used by `krawczyk_path`), via `||I - R B||_inf < 1`, plus a
    verified inverse enclosure. Emits
    `results/audit_closure/p0_preconditioner_certificate.json`. Closes the
    Krawczyk regularity precondition.
  - **P2** (`p2_krawczyk_unit_tests.py`): analytic unit tests for the Krawczyk
    interval operator (matrix direction, sign, strict-inclusion logic) on
    linear, no-root, multi-root, and edge-touching families.
  - **P1** (`p1_independent_model.py`): independent reconstruction of the
    Hamiltonian, 24-segment propagation, and six-point mean infidelity
    (operators rebuilt from scratch, eigendecomposition propagation, 60-digit
    mpmath cross-check); reproduces all twelve means inside the certificate
    enclosures, the complete ordering, and the six closest certified pairs.
- Added `tests/audit_closure/run_mutation_tests.py` and
  `MUTATION_TEST_REPORT.md`: mutation testing confirms the P2 suite fails when
  the operator's defect direction/sign or correction sign is perturbed.
- Added CI workflows `audit_closure_fast.yml` (P0 + P2 + mutation, every push)
  and `audit_closure_independent.yml` (P1, manual / weekly).
- No changes to the existing frozen v0.3.1 scientific artifacts or `paper/`;
  `SHA256SUMS.txt` is refreshed only to include the v0.3.2 audit-closure files.

## [Unreleased]

- Reframed the manuscript around the theorem-first exact-root ordering result
  and renamed it to use the more precise term “finite-error ordering.”
- Corrected the projective phase-alignment factor by conjugating the
  reference-to-path overlap.
- Synchronized the manuscript PDF, README, citation metadata, CI text gates,
  and manuscript-artifact consistency tests.
- Corrected manuscript quartic-only coverage to 34/66 (51.52%); later
  release hygiene qualifies the prospective $G_4$ result at threshold level
  rather than as a cross-platform exact Spearman value.
- Tightened manuscript boundary wording for declared global error coordinates,
  exact-root interval ordering, pre-outcome formal-cohort ordering freeze, and
  the minimal two-atom interacting setting claim.
- Added ORCID and preferred manuscript/software citation separation to
  `CITATION.cff`.
- Added a locked formal dependency file and a manual full exact-root
  certificate reproduction workflow.
- Replaced the editable manuscript source with the split submission tree
  rooted at `paper/main.tex` while retaining `paper/manuscript.pdf` as the
  public PDF version of record.
- Sharpened the submission manuscript into the theorem-first 21-page text and
  refreshed the public PDF hash.
- Removed the duplicate standalone manuscript workflow; the main CI workflow
  remains the manuscript compile and text-gate authority.
- Clarified that code is MIT licensed and manuscript materials are CC BY 4.0.
- Froze the theorem-first exact-root finite-error ordering submission.
- Separated the 66/66 direct theorem from the 52/66 order-thirty
  mechanism certificate, the 34/66 quartic boundary, and the independent
  prospective ranking result.
- Updated the manuscript narrative, submission PDF, integrity metadata,
  and manuscript consistency gates.

## [0.3.1] - 2026-07-29

### Added

- Single-file reproducible-certificate audit v1.3.
- Frozen phase centres, transverse bases, and point preconditioners for the
  declared twelve-path cohort.
- Complete deterministic Krawczyk and exact-root ordering certificates.
- Canonical-hash verification and rejection of runtime fields inside hashed
  proof objects.
- Two-run byte-identity regression gate.
- Standalone exact response-fibre Krawczyk audit v1.2 Colab script.
- Exact-root direct finite-error ordering audit v1.1, with direct Arb
  propagation as the primary theorem gate and order-30 as a separately
  reported mechanism certificate.
- Representative summaries for the 12/12 Krawczyk inclusions and the direct
  66/66 exact-root ordering closure.

### Scientific closure

- Certified one locally unique root exactly matched in projective output state
  and first projective response inside every declared transverse Krawczyk box.
- Certified all 66 frozen finite-error pair orderings by direct
  outward-rounded propagation of the exact-root phase boxes.
- Improved the exact-root order-30 phase-box mechanism result to 52/66
  certified pairs, all correct, with 14 unresolved through interval widening.
- Reconfirmed the primary direct exact-root ordering theorem at 66/66.

## [0.2.0] - 2026-07-29

### Scientific corrections

- Replaced the placeholder path-moment `ResponseTensor` with the actual
  Hamiltonian response audits used for the reported L3/L4 results.
- Removed the circular example that copied the predicted ranking into the
  “actual” ranking before reporting success.
- Corrected the distinction between quartic-only partial certification and
  complete order-30 certification.
- Updated the claim boundary from generic “100% certified predictions” to a
  formal certificate conditional on the serialized finite-dimensional model.
- Removed the unsupported structural-isomorphism claim involving the K=1
  framework.

### Added

- Standalone Colab/Jupyter scripts for G4, L3, floating L4, and formal Arb L4.
- Readable core audit scripts.
- Frozen representative JSON protocols, certificates, and reports.
- Manuscript source and compiled PDF.
- Reference-artifact verification utility and standard-library tests.

## [0.1.0]

- Initial placeholder package.
