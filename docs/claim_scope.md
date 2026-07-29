# Claim scope

## Certified statement

For the twelve serialized phase schedules in the formal artifact, the
declared finite-dimensional two-atom Hamiltonian, the common reference
target, and the six signed axial errors, 192-bit outward-rounded Arb balls
certify the order of all 66 unordered path pairs.

The certificate includes:

- outward-rounded complex-ball propagation;
- 64-point Cauchy coefficient extraction;
- a verified enclosure of Fourier aliases;
- coefficients through order 30;
- an analytic enclosure of the even tail beginning at order 32;
- direct checks that ordinary held-out values lie inside the formal balls.

## Not certified

The repository does not certify:

- PASQAL hardware, FRESNEL, or PASQAL Cloud behavior;
- model discrepancy, calibration drift, sampling noise, decoherence, Doppler
  effects, leakage, waveform filtering, or position fluctuations;
- exact equality of the optimizer constraints;
- exact existence or dimension of the matched implementation fibre;
- worst-case-error ranking;
- a universal fourth-order robustness law;
- many-body scaling.

## Quartic versus order-30 certification

The quartic predictor is

\[
G_4=A^{(4)}_{ijkl}M^{(4)}_{ijkl}.
\]

It strongly organizes mean finite-error performance, but it does not certify
every close comparison. A quartic-only interval places the known sixth-
through-thirtieth-order correction inside its radius, in addition to the
analytic tail.

The complete formal ranking instead uses all known terms through order 30.
Therefore:

\[
\text{strong G4 correlation}
\ne
\text{partial quartic certification}
\ne
\text{complete order-30 certification}.
\]

## Remaining theorem

The missing closure step is a square transverse formulation of the matching
constraints followed by an interval-Newton or Krawczyk inclusion proof.
Propagating the resulting phase balls through the Arb calculation would
connect exact response matching to the formal finite-error ordering.
