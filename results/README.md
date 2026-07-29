# Frozen reference artifacts

Each directory contains the protocol, pre-outcome ranking/certificate where
applicable, and final report emitted by one representative audit.

- `g4_prospective/`: frozen 20-path quartic ranking.
- `l3_covariance/`: fourth-order tensor and coordinate-covariance audit.
- `l4_order30/`: floating-point order-30 reconstruction and tail audit.
- `l4_formal/`: 192-bit Arb ball certificate.

The `protocol_sha256` and certificate hashes are hashes of canonical payloads
defined by the scripts; they are not necessarily bytewise hashes of the JSON
files because output files may include additional metadata or formatting.
Certificate hashes may also be run-specific when creation times or accepted
path realizations are included.

These artifacts document representative runs. Use the standalone scripts to
generate a fresh cohort and fresh hashes.
