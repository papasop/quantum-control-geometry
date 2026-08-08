# Integration Instructions

Apply these files to a fresh branch created from the latest `main` after PR
#22 is resolved. Do not overwrite frozen tags or formal certificates.

Suggested branch:

```text
codex/blind-pulser-response-fibre-v041
```

Suggested pull request title:

```text
Add blind Pulser validation of response-fibre prediction
```

Before committing:

```bash
python tools/verify_blind_pulser_summary.py
python -m unittest discover -s tests -v
python tools/verify_reference_results.py
sha256sum -c SHA256SUMS.txt
git diff --check
```

Regenerate `SHA256SUMS.txt` from the combined latest repository state. Do not
copy a manifest from this ZIP. Manually run the new workflow and retain the
complete generated machine report before marking the pull request ready.

Do not describe this result as PASQAL Cloud, Fresnel, QPU, or hardware
validation.

