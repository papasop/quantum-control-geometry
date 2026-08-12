# SOURCE MANIFEST — exact_root v1.2.1 (freeze candidate)

Version: v1.2.1 (supersedes the v1.2 freeze candidate; see BUILD_README.md and
REVISION_LOG_v1.2.md §第四轮定点修复 for the exact two-item delta).

Baseline repository commit: `ca888e7e5585668910ee5c6379038057c5e36bfc`
(v1.1 release-metadata commit). Provenance status closure recorded in the repository
working copy: `results/g4_prospective/provenance.json` status field, the matching
expectation in `tools/verify_reference_results.py`, and the two affected root
`SHA256SUMS.txt` entries (old→new hashes logged in REVISION_LOG_v1.2.md).

## File manifest

All package files except `SHA256SUMS.txt` itself are covered by that manifest
(SHA-256, paths relative to the package root). Verify with:

```
sha256sum -c SHA256SUMS.txt
```

Expected result: every entry OK, 0 failures (100% coverage).

| Path | Role | Changed vs v1.2 |
|---|---|---|
| `main.tex` | Top-level LaTeX source | no (byte-identical) |
| `sec_front.tex` | Front matter, model, fibre, chart lemma; Figure 1 TikZ source | no (byte-identical) |
| `sec_mid.tex` | Prospective prediction, covariance, certification | yes (one sentence, §4.2.2) |
| `sec_back.tex` | Ordering theorem, summary, discussion, appendices | no (byte-identical) |
| `fig2_exact_root.png` | Figure 2 (frozen-certificate rendering) | no (byte-identical) |
| `scripts/generate_fig2_exact_root.py` | Figure 2 generator (outward endpoint parsing) | no (byte-identical) |
| `data/exact_root_ordering_certificate.json` | Frozen exact-root ordering certificate | no (byte-identical) |
| `exact_root_v1_2_1_freeze_candidate.pdf` | Compiled 25-page candidate PDF (XeTeX route) | yes (recompiled) |
| `BUILD_README.md` | Build instructions and version notes | yes (v1.2.1 naming/notes) |
| `REVISION_LOG_v1.2.md` | Item-by-item closure log (all four rounds) | yes (round-4 section) |
| `SOURCE_MANIFEST.md` | This manifest | new |
| `SHA256SUMS.txt` | Package checksum manifest | regenerated |

## Hygiene

- No build artifacts (`.aux`, `.log`, `.out`, caches) are included.
- No local absolute paths or credentials are included; the figure script resolves the
  certificate via package-relative paths.
- The package builds standalone from a fresh temporary directory via the canonical
  route documented in BUILD_README.md (XeLaTeX ×3; Tectonic/XeTeX engine equivalent).

## Theorem-bearing assets

The Figure 2 asset is byte-identical to the v1.2 source package. Relative to
the earlier pinned manuscript baseline, it was regenerated under the
outward-endpoint parser and inset-layout correction; its frozen certificate
data source is unchanged. The theorem-bearing certificate data object remains
byte-identical to the pinned baseline and to v1.2:
`data/exact_root_ordering_certificate.json`
(SHA-256 `1e0bb221bbe88cd091699a3d0eb77c2327efc18a11b2ae3685749c3905da7d42`).
The frozen Figure 2 display asset in this package has SHA-256
`fig2_exact_root.png`
`743ee77415281cc7710d082b1e046878608aad039b5ca8294781f8fe3866c6a6`.
No certificate, protocol, numerical gate, interval endpoint, or theorem-bearing hash
was modified; no Arb/Krawczyk computation was rerun.
