# Differential dissipative-susceptibility protocol v1.1

## Purpose

This document freezes a protocol-only prospective test of the post-hoc
open-system pattern observed in `v0.5.0`. The goal is to turn the
differential dissipative-susceptibility interpretation into a falsifiable
holdout prediction.

This PR must not run the holdout grid, inspect holdout outcomes, generate a
result file, or adjust thresholds after seeing results.

## Source

The protocol is based on release `v0.5.0` at commit
`2fb0c4a3e339bfb899ef3963bc92ea1fc6a74d45`.

The v0.5.0 release asset SHA-256 is
`cb5c5b6e0634f98c306c8d13d39e94da263d7f1808d67cd13ab7113603691453`.

The v1.0 canonical protocol SHA-256 is
`0ba13647e72a9215072ca70577d3e4d9f0ddf5c95f5796bee5b671e9a08ad888`.

The frozen v1.1 protocol SHA-256 is
`d749b48c9153a32c4a7baec79400d092dcba71b459acacccaa300b7e40afe7a5`.

## Prediction Rule

For every certified ordered path pair `i>j`, define

```math
D_{ij}(\lambda)=L_j(\lambda)-L_i(\lambda)
```

and

```math
\Delta_{ij}=D_{ij}(0).
```

For decay and dephasing separately, fit the local slope

```math
\chi_{ij}=\left.\frac{dD_{ij}}{d\lambda}\right|_{\lambda=0}
```

using only the already public v1.0 training points
`\lambda in {0, 1e-4, 3e-4}`. The predicted crossing scale is

```math
\lambda_{\mathrm{pred},ij}=\frac{\Delta_{ij}}{-\chi_{ij}}.
```

A positive-axis crossing is predicted only when `chi_ij < 0` and
`lambda_pred_ij > 0`; otherwise the pair is labeled
`no-crossing-on-positive-axis`.

## Frozen Holdout Grid

The single-channel holdout grid is
`[0.0005, 0.00075, 0.0015, 0.002, 0.004, 0.006, 0.008, 0.015, 0.020, 0.025]`,
run separately for decay only and dephasing only.

The joint holdout grid is the new diagonal grid
`[(0.0005,0.0005), (0.0015,0.0015), (0.002,0.002), (0.006,0.006),
(0.015,0.015), (0.025,0.025)]`.

None of these holdout points are the v1.0 training points.

## Primary Gates

The frozen gates are:

- all propagation values are finite;
- `lambda=0` reconstructs `66/66` certified pair directions;
- holdout pair-direction classification accuracy is at least `0.90`;
- Harrell concordance index between predicted flip-risk order and actual
  first-flip order is at least `0.75`;
- for pairs that actually flip and have positive predicted scales, at least
  `70%` of predictions fall within a factor of two of the actual first-flip
  scale;
- all failures are reported;
- successful pairs are not selectively reported;
- `pv01/pv10` and `pv08/pv11` are diagnostic named pairs only and do not
  determine pass/fail.

## Boundaries

This is a protocol-only freeze. It does not modify the Arb/Krawczyk proof
engines, serialized unitary model, exact-root boxes, v0.5.0 release, existing
certificates, Pulser results, or manuscript theorem.

The differential dissipative-susceptibility mechanism remains a post-hoc v1.1
hypothesis until this frozen holdout protocol is executed. This protocol is
not an Arb interval proof, not calibrated PASQAL hardware noise, and not
PASQAL Cloud, FRESNEL, or QPU evidence.
