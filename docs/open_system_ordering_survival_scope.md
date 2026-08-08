# Open-system ordering-survival audit v1.0

## Purpose

This audit stress-tests the twelve frozen exact-root controls from
`quantum-control-geometry` v0.3.2 under declared two-atom Lindblad decay and
dephasing channels. It asks how much of the unitary-model ordering survives a
specific open-system model discrepancy.

It does not modify or extend the Arb/Krawczyk certificate of record.

## Frozen inputs

- Twelve 24-segment phase schedules from the v0.3.2 Krawczyk certificate.
- The six signed amplitude, detuning, and interaction error points.
- The direct 66-pair exact-root ordering and its Arb interval margins.
- The serialized two-atom Hamiltonian with `Omega=2*pi`, `V=4*Omega`, and
  24 segments of `0.1 us`.

## Added open-system model

The density matrix satisfies a GKSL/Lindblad master equation. Each atom has
the declared channels

```math
L_{r,i}=\sqrt{\Gamma_r}\,|g\rangle_i\langle r|,
```

and

```math
L_{\phi,i}=\sqrt{2\Gamma_\phi}\,|r\rangle_i\langle r|.
```

With this convention, an isolated single-atom `g-r` coherence decays at rate
`Gamma_phi`. The scan coordinate is the integrated dimensionless severity
`Gamma*T`. It is a declared stress coordinate, not a hardware calibration.

## Declared grid and metrics

The audit covers 29 conditions and 2,088 density-matrix propagations. It
records rank correlation to the frozen order, preserved certified-pair
directions, top/bottom stability, first observed pair reversals, and an
exploratory association between certificate margin and observed flip
threshold.

At integrated severity `0.01`, the prespecified empirical gates require:

- Spearman rank correlation at least `0.90`;
- at least `60/66` certified pair directions preserved;
- the frozen best path remains in the observed top two;
- the frozen worst path remains in the observed bottom two.

The stronger `66/66` condition is recorded separately and is not required for
the stress-audit completion status.

## Result of record

The original run completed `2088/2088` propagations with finite values and
reconstructed the unitary ordering at `rho=1` and `66/66` pairs. All three
evaluation-point gate groups passed. Across the full declared grid, 55 pairs
never flipped and 11 flipped at least once.

The minimum-margin pair, `pv08 > pv11`, did not flip anywhere on the grid.
The first observed reversal was `pv01 > pv10`. Therefore the interval margin
alone does not determine open-system survival; path-specific differential
dissipative susceptibility is a post-hoc follow-up hypothesis.

The original full report is intentionally not committed because it contains
2,088 cell rows. Its SHA-256 is recorded in the committed summary. The GitHub
Actions workflow regenerates a full report and uploads it as an artifact.

## Provenance

The original run has
`prospective_freeze_verified_by_expected_hash=false`. It is therefore
classified as a prespecified-in-code stress audit, not an independently frozen
blind prospective test. In particular, the original run was not independently
hash-frozen before outcome reveal. The protocol, summary, and full-report hash
preserve that limitation explicitly.

## Non-claims

This layer is not:

- an Arb or interval certificate;
- a second proof of the exact-root theorem;
- a Pulser translation run;
- PASQAL Cloud, FRESNEL, or QPU evidence;
- a calibrated claim about decay or dephasing rates;
- a model of SPAM, atom loss, leakage, Doppler effects, waveform filtering,
  or many-body dynamics.

## Reproduction

Install the repository's locked Pulser/QuTiP dependencies, then run

```bash
python tests/external/pasqal_open_system_ordering_survival_v1_0.py \
  --expected-protocol-sha \
  0ba13647e72a9215072ca70577d3e4d9f0ddf5c95f5796bee5b671e9a08ad888 \
  --output /tmp/pasqal_open_system_ordering_survival_v1_0_report.json \
  --protocol-output /tmp/pasqal_open_system_ordering_survival_v1_0_protocol.json
```

Then verify the generated scientific content against the committed summary:

```bash
python tools/verify_open_system_ordering_survival_v1_0.py \
  --report /tmp/pasqal_open_system_ordering_survival_v1_0_report.json
```
