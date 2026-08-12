# Reviewer guide

This repository accompanies the manuscript **Exact-Root Certification of
Finite-Error Ordering in Quantum Control**.

Historical manuscript DOI: [10.5281/zenodo.21831180](https://doi.org/10.5281/zenodo.21831180).
The version-independent concept DOI is
[10.5281/zenodo.20713301](https://doi.org/10.5281/zenodo.20713301).
The current reviewer-facing manuscript on `main` is a
`paper-exact-root-v1.2.1` archive candidate pending tag, GitHub Release, and
DOI creation. The historical DOI above refers to an older PDF, not to v1.2.1.

## What is proved

For the declared serialized two-atom model and six-axis finite-error
functional, twelve strict 192-bit Krawczyk inclusions certify locally unique
projectively matched roots. Direct outward-rounded Arb propagation over the
certified root boxes proves the frozen ordering of all 66 unordered path
pairs.

The evidence layers have different logical roles:

| Result | Role |
|---|---|
| 66/66 direct exact-root Arb ordering | Main theorem |
| 52/66 exact-root order-30 comparisons | Independent mechanism certificate |
| 34/66 quartic-only comparisons | Lowest-order mechanism boundary |
| Spearman rho >= 0.95 on the frozen 20-path prospective cohort; exact correlation, complete ranking, and named top path are platform-dependent diagnostics | Separate prospective evidence |

The prospective result is not a premise of the theorem.

## Evidence layers

| Layer | What to run | Logical status |
|---|---|---|
| Strict Arb proof | `tools/verify_reference_results.py`; full v1.3 standalone reproduction | Model-conditional interval certificate |
| Pulser translation robustness | `Pulser translation diagnostic` workflow or `tests/external/recompute_pulser_translation.py` | Independent numerical translation cross-check |
| Blind prospective Pulser validation | `Blind Pulser response-fibre prospective test` workflow or `tests/external/pasqal_blind_response_fibre_v1_0.py` | Prospective numerical validation through an independent code path |
| Open-system QuTiP stress audit | `Open-system ordering-survival stress audit` workflow or `tools/verify_open_system_ordering_survival_v1_0.py` | Empirical open-system sensitivity stress test within a declared Lindblad extension |
| Prospective dissipative-susceptibility reveal | `Dissipative susceptibility reveal` workflow or `tools/verify_dissipative_susceptibility_reveal_summary.py` | Frozen prospective QuTiP Lindblad validation |
| PASQAL QPU test | Not available in this repository | No hardware claim |

The JSON validators check committed reports. They are not the same as rerunning
the Pulser propagation workflows. Pulser is not Arb. Pulser is not PASQAL Cloud
or a physical QPU. The open-system stress audit is not an interval proof,
Pulser run, PASQAL Cloud run, or QPU result.

## Three-minute verification

No PASQAL account is required.

```bash
python tools/verify_reference_results.py
python -m unittest discover -s tests -v
sha256sum -c SHA256SUMS.txt
```

On macOS, replace the final command with:

```bash
shasum -a 256 -c SHA256SUMS.txt
```

## v0.3.2 audit closure

- P0: rigorous regularity certificate for the production preconditioners.
- P1: independent high-precision point reconstruction.
- P2: analytic and mutation-tested Krawczyk operator checks.

These checks strengthen but do not replace the frozen v0.3.1 Arb certificate.

```bash
python -m pip install -r requirements-lock.txt
python tests/audit_closure/p0_preconditioner_nonsingularity.py
python tests/audit_closure/p2_krawczyk_unit_tests.py
python tests/audit_closure/run_mutation_tests.py
python tests/audit_closure/p1_independent_model.py
```

## Full formal reproduction

Install the frozen formal environment and run the single complete entry point:

```bash
python -m pip install -r requirements-lock.txt
python scripts/standalone/pasqal_L4_reproducible_certificate_v1_3_colab.py
```

The complete run recomputes the Krawczyk and direct exact-root certificates
twice and requires byte-identical proof artifacts.

## External numerical validation

The external Pulser workflows are reviewer-facing numerical checks around the
formal theorem. They do not change or replace the Arb/Krawczyk certificate.

Translation robustness:

```bash
python -m pip install -r requirements-pulser.txt
python tests/external/recompute_pulser_translation.py \
  --output /tmp/pulser_recomputed_report.json
python tools/validate_pulser_translation_report.py \
  --report /tmp/pulser_recomputed_report.json
python tools/compare_pulser_translation_reports.py \
  --reference results/external/pulser_translation_report.json \
  --candidate /tmp/pulser_recomputed_report.json
```

Manual workflow:
[`Pulser translation diagnostic`](https://github.com/papasop/quantum-control-geometry/actions/workflows/pulser_translation_diagnostic.yml).

Blind prospective validation:

```bash
python -m pip install -r requirements-pulser-blind.txt
python tests/external/pasqal_blind_response_fibre_v1_0.py \
  --report /tmp/pasqal_blind_response_fibre_v1_0_report.json
python tools/verify_blind_pulser_summary.py
```

Manual workflow:
[`Blind Pulser response-fibre prospective test`](https://github.com/papasop/quantum-control-geometry/actions/workflows/blind_pulser_response_fibre.yml).

Open-system ordering-survival stress audit:

```bash
python tools/verify_open_system_ordering_survival_v1_0.py
```

The manual workflow reruns 2088 propagations across 29 declared decay/dephasing
stress conditions and uploads the full machine report:
[`Open-system ordering-survival stress audit`](https://github.com/papasop/quantum-control-geometry/actions/workflows/open_system_ordering_survival.yml).

Dissipative-susceptibility reveal summary:

```bash
python tools/verify_dissipative_susceptibility_reveal_summary.py
```

The committed compact summary records the successful manual v1.1.2
prospective reveal: 1715/1716 held-out pair-condition directions, pooled
Harrell C-index 1.000, and 19/20 eligible first-flip scales within a factor
of two. The full machine report is a workflow artifact, not a tracked proof
object. Status and provenance are recorded in
`docs/dissipative_susceptibility_reveal_status.md`.

Manual workflow:
[`Dissipative susceptibility reveal`](https://github.com/papasop/quantum-control-geometry/actions/workflows/dissipative_susceptibility_reveal.yml).

For all manual workflows, use **Actions -> Run workflow -> main -> Run workflow**.

Recommended reviewer route:

1. Fast integrity check:
   `python tools/verify_reference_results.py`,
   `python -m unittest discover -s tests -v`, and
   `sha256sum -c SHA256SUMS.txt`.
2. Formal theorem reproduction:
   install `requirements-lock.txt` and run
   `scripts/standalone/pasqal_L4_reproducible_certificate_v1_3_colab.py`.
3. External Pulser validation:
   run the 72-propagation translation workflow and the 120-propagation blind
   workflow.
4. Open-system stress audit:
   run `tools/verify_open_system_ordering_survival_v1_0.py` for committed
   summary integrity, then run the manual 2088-propagation workflow if the
   empirical stress layer is under review.
5. Prospective dissipative-susceptibility reveal:
   run `tools/verify_dissipative_susceptibility_reveal_summary.py` for the
   committed compact summary and inspect the manual reveal workflow artifact
   only if the v1.1.2 holdout layer is under review.

## Where to look

- `paper/manuscript.pdf`: submitted manuscript.
- `paper/main.tex`: canonical LaTeX entry point.
- `results/exact_fibre_krawczyk/`: locally unique root certificates.
- `results/exact_root_ordering/`: direct 66/66 ordering certificate.
- `results/audit_closure/`: v0.3.2 production-preconditioner regularity
  certificate.
- `tests/audit_closure/`: P0, P1, P2, and mutation-test scripts.
- `results/external/pulser_translation_report.json`: committed 72-cell Pulser
  translation summary.
- `results/external/pasqal_blind_response_fibre_v1_0_summary.json`: committed
  120-propagation blind prospective summary.
- `results/external/open_system/`: committed open-system protocol and
  scientific summary for the 2088-propagation stress audit, plus the compact
  v1.1.2 dissipative-susceptibility reveal summary.
- `docs/dissipative_susceptibility_reveal_status.md`: technical-abort history,
  successful reveal provenance, and claim boundary for v1.1.2.
- `tools/verify_dissipative_susceptibility_reveal_summary.py`: compact summary
  verifier for the v1.1.2 reveal.
- `tests/test_dissipative_susceptibility_reveal_summary.py`: dependency-light
  regression test for the reveal summary.
- `docs/pulser_translation_scope.md`: translation robustness scope.
- `docs/blind_pulser_response_fibre_scope.md`: blind prospective validation
  scope.
- `docs/open_system_ordering_survival_scope.md`: open-system stress-audit
  scope.
- `.github/workflows/pulser_translation_diagnostic.yml`: manual 72-propagation
  Pulser workflow.
- `.github/workflows/blind_pulser_response_fibre.yml`: manual 120-propagation
  blind workflow.
- `.github/workflows/open_system_ordering_survival.yml`: manual
  2088-propagation open-system stress workflow.
- `.github/workflows/dissipative_susceptibility_reveal.yml`: manual v1.1.2
  holdout reveal workflow.
- `results/reproducibility_summary.json`: two-run identity record.
- `docs/claim_scope.md`: exact claim boundary.
- `tools/verify_reference_results.py`: fast artifact verifier.

## Scope boundary

The theorem is conditional on the declared finite-dimensional model and error
functional. It is not PASQAL hardware, QPU, model-discrepancy, global-fibre,
open-system, worst-case-error, or many-body certification.

## Frozen versions

- `v0.3.1` freezes the scientific certificate artifacts.
- `v0.3.2` freezes the audit-closure supplement after P1 has a successful
  GitHub Actions run.
- `paper-exact-root-v1.0` and `paper-exact-root-v1.1` freeze earlier
  synchronized manuscript/source packages without moving `v0.3.1`.
- `v0.4.1` marks the external Pulser-model validation layer as a tag.
- The current reviewer-facing manuscript is a `paper-exact-root-v1.2.1`
  archive candidate until its tag, GitHub Release, and DOI are created.
- The v1.2.1 candidate is a text and presentation-layer revision only; it does
  not rerun Arb, alter theorem-bearing JSON, change certified thresholds, or
  add hardware/QPU claims.
