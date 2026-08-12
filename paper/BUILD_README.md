# Build README — exact_root v1.2.1 (freeze candidate)

Text-and-proof-object alignment revision of *Exact-Root Certification of Finite-Error
Ordering in Quantum Control*, prepared on top of repository commit
`ca888e7e5585668910ee5c6379038057c5e36bfc` (v1.1 release-metadata commit).

## Scope of this package

This is a **textual revision only**. No formal certificate, protocol, report, JSON,
numerical gate, interval endpoint, or theorem-bearing hash was modified; no
Arb/Krawczyk computation was rerun. Changes are confined to wording, definitions,
cross-references, citations, and typesetting, plus a layout-only repositioning of the
Figure 2 inset (same frozen certificate data, same generator script logic).

**v1.2.1 supersedes the v1.2 freeze candidate.** v1.2.1 differs from v1.2 by exactly two
spot corrections: (i) the §4.2.2 sentence now reports the maximum *relative* fit residual
as a direction-safe upward rendering (`2.37×10⁻¹⁰`) of the frozen field
`maximum_relative_fit_residual = 2.3662077377223515e-10` in
`results/g4_prospective/report.json`, replacing a stale `1.48×10⁻¹⁰` value from a
superseded artifact; (ii) the repository provenance status field
`legacy_manuscript_sample_status` in `results/g4_prospective/provenance.json` is closed
as "corrected in v1.2.1 textual revision" (with the matching verifier expectation and
root manifest entries synchronized). Nothing else changed: theorems, certificates, JSON
results, figures, and all numerical gates are byte-identical to v1.2. The v1.2 candidate
remains on record and is not overwritten by this package.

## Contents

| Path | Role |
|---|---|
| `main.tex` | Top-level LaTeX source (unchanged from pinned commit) |
| `sec_front.tex` | Front matter, model, fibre, chart lemma (revised); contains the Figure 1 TikZ source (typesetting-only label fixes) |
| `sec_mid.tex` | Prospective prediction, covariance, certification (revised) |
| `sec_back.tex` | Ordering theorem, summary, discussion, appendices (revised) |
| `fig2_exact_root.png` | Figure 2, regenerated from the frozen certificate (inset repositioned; endpoints parsed outward) |
| `scripts/generate_fig2_exact_root.py` | Figure 2 generator (layout edit + outward endpoint parsing; data source unchanged) |
| `data/exact_root_ordering_certificate.json` | Frozen exact-root ordering certificate (byte-identical to pinned commit) |
| `exact_root_v1_2_1_freeze_candidate.pdf` | Compiled 25-page candidate PDF |
| `REVISION_LOG_v1.2.md` | Item-by-item closure log of all BR/A/B/D/E review findings |
| `SOURCE_MANIFEST.md` | Package manifest with per-file change status vs v1.2 |
| `SHA256SUMS.txt` | Checksum manifest for this package only |

## Build

Canonical build:

```
xelatex main.tex
xelatex main.tex
xelatex main.tex
```

Expected output: 25 A4 pages (spot-fix revision of 2026-08-12; the immediately
preceding candidate was 24 pages).

pdfLaTeX may produce a typographically equivalent layout with one fewer page and
is not the canonical freeze build. Tectonic (XeTeX/xdvipdfmx-based) follows the
canonical route and is what produced the frozen PDF in this package.

The build was verified to produce zero undefined references, zero undefined
citations, zero rerun warnings, and zero overfull/underfull box warnings. The PDF
inside this package is byte-identical to the separately distributed
`exact_root_v1_2_1_freeze_candidate.pdf`.

## Integrity

```
sha256sum -c SHA256SUMS.txt
```

All entries must report OK. The frozen JSON under `data/` matches the pinned commit
byte-for-byte; the figure was regenerated with

```
python3 scripts/generate_fig2_exact_root.py \
  --certificate data/exact_root_ordering_certificate.json \
  --output fig2_exact_root.png
```

## Status

Freeze candidate for author review. No commit, tag, Release, or Zenodo action has been
taken for v1.2.1.
