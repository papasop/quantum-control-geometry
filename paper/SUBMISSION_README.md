# Submission manuscript

Title: **Geometric Prediction and Exact-Root Certification of Finite-Error
Ordering in Quantum Control**

Version of record: `paper-exact-root-v1.0`

## Files

- `main.tex`: canonical LaTeX entry point.
- `sec_front.tex`: abstract and Sections 1-3.
- `sec_mid.tex`: Sections 4-6.
- `sec_back.tex`: Sections 7-11, appendices, declarations, and references.
- `fig1.png`: local matching and quartic-separation schematic.
- `fig2.png`: prospective ranking and certified-interval evidence.
- `manuscript.pdf`: frozen 20-page submission PDF.

## Build

```bash
pdflatex main.tex
pdflatex main.tex
pdflatex main.tex
```

No BibTeX or Biber step is required. References use a manual
`thebibliography` environment.

The bundled PDF was produced with Tectonic. Different TeX engines may produce
typographically equivalent output with a different byte hash or a one-page
layout difference.

Frozen PDF SHA-256:

```text
378c0c5d92fc18e49d409ddfcc3dba649eb9e78098fdf27dc3c99c0480875a76
```
