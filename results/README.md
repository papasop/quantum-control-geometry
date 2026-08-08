# Frozen reference artifacts

Each directory contains the protocol, pre-outcome ranking/certificate where
applicable, and final report emitted by one representative audit.

- `g4_prospective/`: frozen 20-path quartic ranking.
- `l3_covariance/`: fourth-order tensor and coordinate-covariance audit.
- `l4_order30/`: floating-point order-30 reconstruction and tail audit.
- `l4_formal/`: 192-bit Arb ball certificate.
- `exact_fibre_krawczyk/`: frozen cohort, deterministic protocol, complete
  Krawczyk certificate, and report for the 12/12 exact matched-root audit.
- `exact_root_ordering/`: deterministic protocol, complete certificate, and
  report for direct 66/66 exact-root box propagation and the secondary 52/66
  order-30 mechanism audit.
- `audit_closure/`: v0.3.2 production-preconditioner regularity certificate.
  This is an audit supplement, not a replacement for the frozen v0.3.1
  exact-root certificates.
- `external/open_system/pasqal_open_system_ordering_survival_v1_0_summary.json`:
  compact summary for the 2088-propagation QuTiP Lindblad ordering-survival
  stress audit.
- `external/open_system/dissipative_susceptibility_reveal_v1_1_2_summary.json`:
  compact summary for the successful frozen v1.1.2 prospective
  dissipative-susceptibility reveal. This is numerical QuTiP Lindblad evidence,
  not an Arb interval proof, calibrated PASQAL hardware-noise result, PASQAL
  Cloud run, FRESNEL run, or QPU experiment.
- `reproducibility_summary.json`: hashes and byte-identity gates from two
  complete v1.3 formal executions.

The `protocol_sha256` and certificate hashes are hashes of canonical payloads
defined by the scripts; they are not necessarily bytewise hashes of the
pretty-printed JSON files. Runtime diagnostics are excluded from the v1.3
hashed proof objects.

The two exact-root directories contain the complete deterministic v1.3 proof
objects. Reproduce them with
`pasqal_L4_reproducible_certificate_v1_3_colab.py`.
