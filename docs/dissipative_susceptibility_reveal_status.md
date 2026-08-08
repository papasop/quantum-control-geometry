# Dissipative susceptibility reveal status

## First manual workflow attempt

The first attempted v1.1.2 reveal terminated before any propagation and is
recorded as:

```text
TECHNICAL_ABORT_BEFORE_PROPAGATION_NO_OUTCOMES_COMPUTED
```

No result from that technical abort is interpreted scientifically.

## Frozen prospective reveal

The corrected manual workflow was executed once from `main`:

- workflow run: [31243388596](https://github.com/papasop/quantum-control-geometry/actions/runs/31243388596)
- executed commit: `134b6ff747b7941d68bd645bec091b6dafbaf8b7`
- merged protocol commit: `03055196b5b58d022a5cfcea46b007cb752cea44`
- canonical protocol SHA-256:
  `0c220213ba9485fd06268c56b726848c33b684da10c9d715c96690e9e7ae8476`
- complete report SHA-256:
  `73ca097b726e152035f20097c4e98acff01de26772abeb22370fd4bba863a65b`

The run completed all 2,232 declared density-matrix propagations and produced
the complete report artifact.

## Frozen results

| Gate | Frozen threshold | Result | Status |
|---|---:|---:|---|
| Finite propagation values | all | 2232/2232 | PASS |
| Zero-noise reconstruction | 66/66 | 66/66 | PASS |
| Pair-condition classification | at least 0.90 | 1715/1716 = 0.999417 | PASS |
| Pooled Harrell C-index | at least 0.75 | 1.000 (1217 comparable) | PASS |
| Factor-of-two first-flip scale | at least 0.70 | 19/20 = 0.95 | PASS |

The prospective scientific status is:

```text
PROSPECTIVE_DISSIPATIVE_SUSCEPTIBILITY_SUPPORTED
```

All declared gates passed. No condition, family, pair, or failure was removed
from the frozen denominators.

## Disclosed exceptions

The sole classification error is `pv07>pv10` under the joint condition
`(Gamma_r T, Gamma_phi T)=(0.015,0.015)`. The linear model predicts a small
negative difference (`-7.1191e-5`), while the observed difference remains
small and positive (`+6.9657e-5`).

The sole eligible crossing outside the factor-of-two window is the joint
`pv01>pv10` crossing. Its predicted scale is `0.0006994233`, its first observed
flip on the frozen grid is `0.0015`, and their ratio is `0.4662822`.

## Claim boundary

This result prospectively supports local differential dissipative
susceptibility as a predictor of finite-noise pair ordering and first-flip
risk within the frozen two-atom QuTiP Lindblad model. It is not an Arb interval
proof, calibrated PASQAL hardware-noise evidence, PASQAL Cloud execution,
FRESNEL execution, or a QPU experiment.

The compact result of record is
`results/external/open_system/dissipative_susceptibility_reveal_v1_1_2_summary.json`.
The complete report remains the immutable workflow artifact identified by the
run URL and SHA-256 above.
