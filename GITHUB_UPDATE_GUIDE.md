# GitHub update guide — v0.3.1

Target repository:
`https://github.com/papasop/quantum-control-geometry`

This archive is a complete repository snapshot without `.git` metadata.

## Recommended update

1. Clone the current repository.
2. Copy the contents of this archive over the clone, preserving the clone's
   `.git` directory.
3. From the clone, run:

```bash
python tools/verify_reference_results.py
python -m unittest discover -s tests -v
```

4. Confirm that all seven artifact groups and all tests pass.
5. Review and publish:

```bash
git add -A
git commit -m "Add reproducible v1.3 exact-root certificates"
git push origin main
git tag -a v0.3.1 -m "Reproducible exact-root certificate v1.3"
git push origin v0.3.1
```

## Expected v1.3 result

- frozen cohort SHA-256:
  `9942af610c1e9499a10e989e4ae069e3912d58eec4fd3ad1d3d39947c232c356`
- Krawczyk inclusions: `12/12`
- direct exact-root ordering: `66/66`
- order-30 exact-root mechanism: `52/66`
- reversed order-30 certified pairs: `0`
- two-run proof-file identity: `PASS`

## Claim boundary

The formal certificates apply to the serialized finite-dimensional two-atom
model. They do not certify PASQAL hardware, cloud execution, calibration,
model discrepancy, global fibre topology, or many-body scaling.
