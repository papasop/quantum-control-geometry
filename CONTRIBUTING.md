# Contributing

Contributions that improve reproducibility, validated numerics, or the
declared physical model are welcome.

## Scientific requirements

Any pull request changing a scientific claim must:

1. identify the exact model, error law, cohort, and prediction target;
2. separate discovery data from held-out evaluation;
3. state whether arithmetic is ordinary floating point or outward-rounded
   interval arithmetic;
4. include the emitted protocol and report;
5. preserve negative or inconclusive outcomes;
6. distinguish correlation, pairwise certification, and complete bounded
   reconstruction.

Do not describe numerical optimizer residuals as an exact manifold theorem.
Do not describe local emulation as PASQAL Cloud or QPU evidence.

## Development

```bash
python -m pip install -r requirements.txt
python tools/verify_reference_results.py
python -m unittest discover -s tests -v
```

For a scientific script change, rerun the affected standalone audit and
include the new JSON artifacts and hashes in the pull request description.
