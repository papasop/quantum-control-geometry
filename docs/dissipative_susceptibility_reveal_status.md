# Dissipative susceptibility reveal status

## First manual workflow run

The first attempted v1.1.2 reveal workflow is recorded as:

```text
TECHNICAL_ABORT_BEFORE_PROPAGATION_NO_OUTCOMES_COMPUTED
```

The abort occurred before holdout propagation began. No JSON report was
produced, no classification, C-index, or factor-of-two result exists, and no
scientific interpretation can be drawn from that run.

The v1.1.2 frozen protocol remains bound to:

- merged protocol commit:
  `03055196b5b58d022a5cfcea46b007cb752cea44`
- canonical protocol SHA-256:
  `0c220213ba9485fd06268c56b726848c33b684da10c9d715c96690e9e7ae8476`

After this technical fix is merged and CI is green, the reveal workflow must
be rerun manually. Only a subsequent workflow run that produces the complete
JSON report artifact may be interpreted.
