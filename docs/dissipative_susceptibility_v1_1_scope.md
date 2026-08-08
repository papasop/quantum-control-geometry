# Differential dissipative-susceptibility protocol v1.1.2

## Purpose

This document freezes a protocol-only clarification of the prospective test of
the post-hoc open-system pattern observed in `v0.5.0`. Version `1.1.2`
supersedes v1.1.1 before any holdout results are run, read, generated, or
used. The goal is still to turn the differential dissipative-susceptibility
interpretation into a falsifiable holdout prediction, while correcting an
internal algebraic sign inconsistency found before outcome reveal.

This PR must not run the holdout grid, inspect holdout outcomes, generate a
result file, or adjust thresholds after seeing results.

## Source

The protocol is based on release `v0.5.0` at commit
`2fb0c4a3e339bfb899ef3963bc92ea1fc6a74d45`.

The v0.5.0 release asset SHA-256 is
`cb5c5b6e0634f98c306c8d13d39e94da263d7f1808d67cd13ab7113603691453`.

The v1.0 canonical protocol SHA-256 is
`0ba13647e72a9215072ca70577d3e4d9f0ddf5c95f5796bee5b671e9a08ad888`.

The superseded v1.1 protocol SHA-256 is
`d749b48c9153a32c4a7baec79400d092dcba71b459acacccaa300b7e40afe7a5`.

The superseded v1.1.1 protocol SHA-256 is
`d10c5e8a5b152994d7e60d1d7fb4322068734d6b082c72d404365930010b3c60`.

The frozen v1.1.2 protocol SHA-256 is
`0c220213ba9485fd06268c56b726848c33b684da10c9d715c96690e9e7ae8476`.

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

For a single channel, the point prediction is

```math
\hat D_{ij}(\lambda)=\Delta_{ij}+\chi_{ij}\lambda.
```

The pair is predicted preserved when `D_hat_ij(lambda) > 0` and predicted
flipped when `D_hat_ij(lambda) <= 0`. A positive-axis crossing is predicted
only when `chi_ij < 0` and `lambda_pred_ij > 0`; otherwise the pair is labeled
`no-crossing-on-positive-axis`.

For the joint diagonal grid, v1.1.2 freezes the algebraically consistent
additive first-order rule

```math
\hat D_{ij}(\lambda_r,\lambda_\phi)
=\Delta_{ij}+\chi_{\mathrm{decay},ij}\lambda_r
+\chi_{\mathrm{dephasing},ij}\lambda_\phi.
```

Substituting `lambda_r = lambda_phi = lambda` gives
`D_hat = Delta + (chi_decay + chi_dephasing) * lambda`, so the diagonal
crossing scale is

The joint diagonal crossing scale is

```math
\lambda_{\mathrm{pred,joint},ij}
=\frac{\Delta_{ij}}{-(\chi_{\mathrm{decay},ij}
+\chi_{\mathrm{dephasing},ij})}.
```

It is valid only when the denominator gives a positive finite crossing.
Equivalently, the validity condition is
`chi_decay_ij + chi_dephasing_ij < 0` and finite positive
`lambda_pred_joint`.

## Frozen Holdout Grid

The single-channel holdout grid is
`[0.0005, 0.00075, 0.0015, 0.002, 0.004, 0.006, 0.008, 0.015, 0.020, 0.025]`,
run separately for decay only and dephasing only.

The joint holdout grid is the new diagonal grid
`[(0.0005,0.0005), (0.0015,0.0015), (0.002,0.002), (0.006,0.006),
(0.015,0.015), (0.025,0.025)]`.

None of these holdout points are the v1.0 training points.

Actual first flip means the first flip on this frozen discrete grid. It is not
a continuous crossing estimate and must not be interpolated.

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

The classification accuracy denominator is frozen as all `66` certified pairs
across all `26` holdout conditions, for a total denominator of `1716`. No
pair, channel family, or condition may be removed.

The Harrell C-index is computed separately for decay, dephasing, and joint
families. Within a family, comparable examples are unordered pairs of
certified path pairs. Two observed flips are comparable only if their discrete
first-flip lambdas differ. One observed flip and one observed right-censored
pair are comparable, with the observed flip earlier. Two right-censored items
or equal observed first-flip lambdas are not comparable. Equal predicted risk
scores receive `0.5` concordance credit. A family with zero comparable
examples contributes zero weight. The primary C-index is the comparable-count
weighted pooled value across the three families; if the pooled denominator is
zero, the C-index gate fails.

The factor-of-two denominator includes only pair-family items that actually
flip on the frozen discrete grid and have a positive finite predicted scale.
The success condition is
`0.5 * actual_first_flip_lambda <= lambda_pred <= 2.0 * actual_first_flip_lambda`.
A family with zero eligible items contributes zero weight. The primary
factor-of-two value is the eligible-count weighted pooled value across decay,
dephasing, and joint; if the pooled eligible denominator is zero, the gate
fails.

## Boundaries

This is a protocol-only correction. It does not modify the Arb/Krawczyk proof
engines, serialized unitary model, exact-root boxes, v0.5.0 release, existing
certificates, Pulser results, manuscript theorem, training points, holdout
grids, C-index rules, factor-of-two rules, thresholds, or solver settings.

The differential dissipative-susceptibility mechanism remains a post-hoc v1.1
hypothesis until this frozen holdout protocol is executed. This protocol is
not an Arb interval proof, not calibrated PASQAL hardware noise, and not
PASQAL Cloud, FRESNEL, or QPU evidence.
