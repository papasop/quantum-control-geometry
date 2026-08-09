LaTeX source for
"Exact-Root Certification of Finite-Error Ordering in Quantum Control"
 (Y.Y.N. Li)
Version of record: paper-exact-root-v1.0 (2026-08-07)
Zenodo DOI: 10.5281/zenodo.21831180
Zenodo concept DOI: 10.5281/zenodo.20713301

All files in this directory constitute the complete submission source.
The compiled PDF is manuscript.pdf in THIS SAME directory.

Files:
  main.tex        - preamble, macros, theorem environments, entry point
  sec_front.tex   - abstract, Sections 1-3
  sec_mid.tex     - Sections 4-6
  sec_back.tex    - Sections 7-11, Appendices A-C, declarations, references
  fig1.png        - Figure 1 (schematic)
  fig2_exact_root.png
                  - Figure 2 (exact-root-only certified interval panel)
  manuscript.pdf  - compiled output (20 pages)
  SHA256SUMS.txt  - frozen SHA-256 of manuscript.pdf

Build:
  pdflatex main.tex
  pdflatex main.tex
  pdflatex main.tex
(three runs resolve all cross-references; no bibtex/biber needed -
references are in a manual thebibliography environment)

Requirements: pdflatex with amsmath, amssymb, amsthm, graphicx,
booktabs, enumitem, microtype, hyperref (any recent TeX Live).

Current bundled PDF record:
  Output    : manuscript.pdf, 20 pages
  SHA-256   : ad5862e1bd79006586e397f10d3cb08d12eb5b43082c8bc2e330aa5fb578cf9b
Note: The bundled manuscript.pdf is the reviewer-facing PDF synchronized with
the current main branch and CI manuscript build. Other TeX engines may produce
typographically equivalent output with a different byte hash; page breaks may
also differ by +/- 1 page across TeX engines/versions. For release freezing,
use the bundled PDF and SHA-256 above, or pin a TeX Live version and
regenerate from this source.

Version management (single final source):
  The split-file tree above is the ONLY final manuscript source.
  Sync it to https://github.com/papasop/quantum-control-geometry
  as paper/ via a pull request - do NOT push to main directly. After
  the PR is merged and CI is green, tag the merge commit as
  paper-exact-root-v1.0:
    git fetch origin main && git checkout main && git pull
    git tag -a paper-exact-root-v1.0 -m "Submission manuscript v1.0"
    git push origin paper-exact-root-v1.0
  Do NOT move the frozen v0.3.1 scientific-certificate tag.
