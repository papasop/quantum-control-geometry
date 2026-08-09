# Release notes -- v0.4.2 release candidate (G4 manuscript qualification)

The v0.4.2 release candidate is a release-hygiene update for the submitted
manuscript and CI text gates. It does not modify the frozen physical model,
exact-root boxes, Arb/Krawczyk proof engines, result artifacts,
audit-closure artifacts, Pulser reports, open-system reports, or the certified
12/12 and 66/66 conclusions.

## What changed

- The manuscript reports the prospective G4 result at the stable
  threshold level:
  `rho_Spearman >= 0.95`.
- The legacy platform-specific value `0.996992` is removed from
  `paper/*.tex` and `paper/manuscript.pdf`.
- Exact G4 correlations and named top paths are explicitly treated as
  platform-dependent float64 diagnostics.
- Figure 2 now uses the exact-root-only interval panel
  `paper/fig2_exact_root.png`.
- The reproducibility statement confines byte-identical claims to the formal
  Arb/Krawczyk proof artifacts.
- The `Artifact checks` workflow forbids `0.996992`, checks the new threshold
  wording, and includes `workflow_dispatch` for manual release checks.

## Manuscript PDF

Final manuscript PDF:

```text
paper/manuscript.pdf
SHA-256: ad5862e1bd79006586e397f10d3cb08d12eb5b43082c8bc2e330aa5fb578cf9b
```

## Verification

```bash
python tools/verify_reference_results.py
python -m unittest discover -s tests -v
sha256sum -c SHA256SUMS.txt
git diff --check
```

Do not move earlier immutable tags. Create `v0.4.2` only after the final
release-hygiene branch is merged to `main` and the GitHub Artifact checks are
green on that commit.
