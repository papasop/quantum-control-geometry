# Quantum Control Geometry

Reproducible research code for **covariant local response jets on
response-matched neutral-atom controls**.

This repository accompanies the manuscript:

> **Covariant Local Jets of Response-Matched Neutral-Atom Controls:
> From Quartic Prediction to Formal Finite-Error Certification**

The study asks a deliberately narrow question: when control schedules have
the same nominal output state and the same first-order output-state response
to amplitude, detuning, and interaction errors, what local information
determines their finite-error performance ordering?

## What is supported

For the declared two-atom, finite-dimensional, piecewise-constant Hamiltonian
model:

- a 24-parameter phase control has a numerical constraint-Jacobian rank of
  16, leaving an eight-dimensional numerical implementation fibre;
- the matched quadratic response has relative spread of order \(10^{-7}\);
- a symmetric fourth-order response tensor has 15 independent components in
  the three-dimensional error space;
- its coordinate transformation and invariant noise-moment contraction were
  verified to approximately \(10^{-14}\) and \(2\times10^{-15}\);
- a frozen 20-path prospective cohort gave quartic-ranking Spearman
  correlation \(0.998496\) and the correct top path;
- the quartic term alone formally separates only a subset of the 66 path
  pairs;
- the zero-point jet through order 30, together with a Cauchy-alias enclosure
  and an analytic order-32 tail enclosure, separates all 66 pairs in a
  192-bit Arb calculation;
- a square 16-dimensional transverse chart and outward-rounded Krawczyk
  calculation certify a unique exact state-and-first-response-matched root
  inside each of 12 declared phase boxes;
- direct 192-bit Arb propagation of those exact-root boxes certifies the
  frozen finite-error order for all 66 pairs;
- the order-30 phase-box mechanism audit separately certifies 42/66 pairs,
  with zero reversed certified pairs.

The strongest result is a **formal, model-conditional exact-root
finite-error ordering certificate** for the declared 12-path cohort. It
proves local existence and uniqueness inside each supplied Krawczyk box, not
global uniqueness of the implementation fibre. It is not PASQAL Cloud or QPU
evidence.

## Repository layout

```text
paper/
  manuscript.tex
  manuscript.pdf
scripts/
  standalone/       # one-file Colab/Jupyter entry points
  core/             # readable audit engines and shared model code
results/
  g4_prospective/
  l3_covariance/
  l4_order30/
  l4_formal/
  exact_fibre_krawczyk/
  exact_root_ordering/
tools/
  verify_reference_results.py
tests/
  test_reference_artifacts.py
```

The former placeholder `quantum_control_geometry` package has been removed.
It computed path-coordinate moments rather than the Hamiltonian response
tensor defined in the manuscript, so it was not a valid implementation of
the reported science.

## Quick reproduction

No PASQAL password is required. In Colab, upload and run one of the files in
`scripts/standalone/`:

```python
%run /content/pasqal_two_atom_G4_standalone_colab.py
%run /content/pasqal_L3_L4_standalone_colab.py
%run /content/pasqal_L4_order30_standalone_colab.py
%run /content/pasqal_L4_formal_arb_standalone_colab.py
%run /content/pasqal_L4_exact_fibre_krawczyk_standalone_colab_v1_2.py
%run /content/pasqal_L4_exact_root_ordering_standalone_colab.py
```

Locally:

```bash
python -m pip install -r requirements.txt
python scripts/standalone/pasqal_two_atom_G4_standalone_colab.py
python scripts/standalone/pasqal_L3_L4_standalone_colab.py
python scripts/standalone/pasqal_L4_order30_standalone_colab.py
python scripts/standalone/pasqal_L4_formal_arb_standalone_colab.py
python scripts/standalone/pasqal_L4_exact_fibre_krawczyk_standalone_colab_v1_2.py
python scripts/standalone/pasqal_L4_exact_root_ordering_standalone_colab.py
```

Run the last two commands in the same working directory: the exact-root
ordering audit consumes the Krawczyk certificate and the earlier frozen
formal-order certificate. The formal audits pin `python-flint==0.8.0`.

## Verify the bundled reference artifacts

```bash
python tools/verify_reference_results.py
python -m unittest discover -s tests -v
```

These checks validate the declared gates in the bundled JSON artifacts. They
do not replace rerunning the scientific audits.

## Result hierarchy

| Stage | Object | Supported conclusion |
|---|---|---|
| Prospective G4 | Scalar fourth-order contraction | Strong mean-performance predictor on the frozen 20-path cohort |
| L3 | Symmetric fourth-order response tensor | Coordinate-covariant tensor and invariant noise-moment contraction |
| L4 quartic | G4 plus all known higher terms placed in the radius | Partial pairwise certification |
| L4 order 30 | Zero-point jet through order 30 plus tail | Complete 66/66 ordering for the frozen serialized cohort |
| Exact-fibre step | Interval Newton/Krawczyk | Unique local exact matched root in each of 12 declared boxes |
| Exact-root direct L4 | Direct Arb propagation of certified root boxes | Complete 66/66 frozen finite-error ordering |
| Exact-root order-30 mechanism | Jet propagation over certified root boxes | Correct partial order, 42/66 with zero reversals |

The quartic result and the order-30 result must not be conflated. The analytic
tail after order 30 is not a remainder bound for truncation after order four.
Likewise, direct exact-root propagation is the primary finite-radius theorem;
the order-30 phase-box calculation is a secondary mechanism certificate.

## Citation

See [`CITATION.cff`](CITATION.cff). Until an archival paper or software
release is available, cite the repository and the exact commit used.

## License

MIT License. See [`LICENSE`](LICENSE).
