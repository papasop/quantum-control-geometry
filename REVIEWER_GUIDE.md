# Reviewer guide

This repository accompanies the manuscript **Exact-Root Certification of
Finite-Error Ordering in Quantum Control**.

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
| Spearman rho = 0.996992 on 20 held-out paths | Separate prospective evidence |

The prospective result is not a premise of the theorem.

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

## Full formal reproduction

Install the frozen formal environment and run the single complete entry point:

```bash
python -m pip install -r requirements-lock.txt
python scripts/standalone/pasqal_L4_reproducible_certificate_v1_3_colab.py
```

The complete run recomputes the Krawczyk and direct exact-root certificates
twice and requires byte-identical proof artifacts.

## Where to look

- `paper/manuscript.pdf`: submitted manuscript.
- `paper/main.tex`: canonical LaTeX entry point.
- `results/exact_fibre_krawczyk/`: locally unique root certificates.
- `results/exact_root_ordering/`: direct 66/66 ordering certificate.
- `results/reproducibility_summary.json`: two-run identity record.
- `docs/claim_scope.md`: exact claim boundary.
- `tools/verify_reference_results.py`: fast artifact verifier.

## Scope boundary

The theorem is conditional on the declared finite-dimensional model and error
functional. It is not PASQAL hardware, QPU, model-discrepancy, global-fibre,
open-system, worst-case-error, or many-body certification.

## Frozen versions

- `v0.3.1` freezes the scientific certificate artifacts.
- `paper-exact-root-v1.0` freezes the synchronized submission manuscript and
  reviewer-facing repository state after CI passes.
