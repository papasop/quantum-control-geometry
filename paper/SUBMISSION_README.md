LaTeX source for
"Exact-Root Certification of Finite-Error Ordering in Quantum Control"
 (Y.Y.N. Li)
Version of record: paper-exact-root-v1.0 (2026-08-07)

All files in this directory constitute the complete submission source.
The compiled PDF is manuscript.pdf in THIS SAME directory.

Files:
  main.tex        - preamble, macros, theorem environments, entry point
  sec_front.tex   - abstract, Sections 1-3
  sec_mid.tex     - Sections 4-6
  sec_back.tex    - Sections 7-11, Appendices A-C, declarations, references
  fig1.png        - Figure 1 (schematic)
  fig2.png        - Figure 2 (prospective ranking / certified intervals)
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

Frozen build record (this copy):
  Engine    : Tectonic (XeTeX-based), package bundle current as of 2026-08-07
  Command   : tectonic main.tex  (single command; equivalent to the
              three pdflatex runs above)
  Output    : manuscript.pdf, 20 pages
  SHA-256   : 413bf864968586201daa2ea4a1e5464a14a1a142606c52d853b61eb9637f9040
Note: The bundled Tectonic-generated manuscript.pdf is the frozen
version of record. Other TeX engines may produce typographically
equivalent output with a different byte hash; page breaks may also
differ by +/- 1 page across TeX engines/versions. Freeze the bundled
PDF (with its SHA-256) as the version of record, or pin a TeX Live
version and regenerate from this source.

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
