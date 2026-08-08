"""
P0 -- deterministic Arb non-singularity certificate for frozen preconditioners.

The Krawczyk map used in
scripts/core/pasqal_L4_exact_fibre_krawczyk_audit_v1_3.py is

    K(X) - x = -B f(x) + (I - B J(X)) (X - x),

where B = chart.inverse = point_preconditioner_decimal (16x16) is used as the
preconditioner Y. The Krawczyk theorem requires Y = B to be regular.

This audit proves regularity by the Rump-Neumann criterion. For a frozen
binary64 approximate inverse R, Arb outward-rounded arithmetic verifies

    rho := ||I - R B||_inf < 1.

Then RB is non-singular by the Neumann series, hence B is non-singular, and

    ||B^-1 - R||_inf <= rho * ||R||_inf / (1 - rho).

The approximate inverses R are committed as exact binary64 hexadecimal strings
in tests/audit_closure/data/p0_frozen_inverse_hex.json and reconstructed only
with float.fromhex(...). The default command is read-only: it verifies that the
committed certificate is byte-identical to the regenerated deterministic
payload. Maintainers may pass --write-certificate to refresh the tracked JSON.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from flint import arb, arb_mat, ctx


ctx.prec = 256  # 256-bit working precision

REPO_ROOT = Path(__file__).resolve().parents[2]
COHORT = REPO_ROOT / "results/exact_fibre_krawczyk/cohort.json"
FROZEN_INVERSE_DATA = (
    REPO_ROOT / "tests/audit_closure/data/p0_frozen_inverse_hex.json"
)
P0_CERTIFICATE = (
    REPO_ROOT / "results/audit_closure/p0_preconditioner_certificate.json"
)
EXPECTED_PATHS = tuple(f"pv{index:02d}" for index in range(1, 13))
EXPECTED_MATRIX_SHAPE = (16, 16)


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def canonical_json(value: object) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def sha256_bytes(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_json(value: object) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def preconditioner_payload(cohort: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "path": entry["path"],
            "point_preconditioner_decimal": entry[
                "point_preconditioner_decimal"
            ],
        }
        for entry in cohort["paths"]
    ]


def arb_from_production_decimal(s: str) -> arb:
    # Match krawczyk_path: decimal -> binary64 -> exact decimal spelling -> Arb.
    return arb(repr(float(s)))


def arb_from_frozen_hex(s: str) -> arb:
    # The persisted representation is exact binary64 hex, not display decimal.
    return arb(repr(float.fromhex(s)))


def load_B_matrices(cohort_path: Path = COHORT) -> list[tuple[str, arb_mat, int]]:
    cohort = load_json(cohort_path)
    out: list[tuple[str, arb_mat, int]] = []
    for entry in cohort["paths"]:
        rows = entry["point_preconditioner_decimal"]
        n = len(rows)
        Bmat = arb_mat(
            [[arb_from_production_decimal(rows[i][j]) for j in range(n)]
             for i in range(n)]
        )
        out.append((entry["path"], Bmat, n))
    return out


def inf_norm_ball(M: arb_mat, n: int) -> arb:
    """Rigorous upper enclosure of the infinity norm of a ball matrix."""
    best = arb(0)
    for i in range(n):
        row = arb(0)
        for j in range(n):
            row = row + abs(M[i, j])
        if row.upper() > best.upper():
            best = row
    return best


def validate_frozen_inverse_data(
    cohort_path: Path = COHORT,
    inverse_data_path: Path = FROZEN_INVERSE_DATA,
) -> dict[str, Any]:
    cohort = load_json(cohort_path)
    frozen = load_json(inverse_data_path)
    payload = preconditioner_payload(cohort)
    paths = [entry["path"] for entry in cohort["paths"]]

    if frozen["schema"] != "p0_frozen_inverse_hex":
        raise ValueError("unexpected frozen inverse schema")
    if int(frozen["schema_version"]) != 1:
        raise ValueError("unexpected frozen inverse schema version")
    if tuple(frozen["matrix_shape"]) != EXPECTED_MATRIX_SHAPE:
        raise ValueError("unexpected frozen inverse matrix shape")
    if tuple(frozen["paths"]) != EXPECTED_PATHS:
        raise ValueError("unexpected frozen inverse path list")
    if tuple(paths) != EXPECTED_PATHS:
        raise ValueError("unexpected cohort path list")
    if frozen["source_cohort_sha256"] != sha256_bytes(cohort_path):
        raise ValueError("frozen inverse data does not match cohort SHA-256")
    if frozen["production_preconditioner_payload_sha256"] != sha256_json(
        payload
    ):
        raise ValueError(
            "frozen inverse data does not match preconditioner payload"
        )
    if frozen["production_preconditioner_conversion"] != (
        "arb(repr(float(decimal)))"
    ):
        raise ValueError("unexpected production preconditioner conversion")

    matrices = frozen["matrices"]
    if set(matrices) != set(EXPECTED_PATHS):
        raise ValueError("frozen inverse matrix paths do not match cohort")
    rows_expected, cols_expected = EXPECTED_MATRIX_SHAPE
    for path in EXPECTED_PATHS:
        rows = matrices[path]
        if len(rows) != rows_expected:
            raise ValueError(f"{path}: wrong frozen inverse row count")
        for row in rows:
            if len(row) != cols_expected:
                raise ValueError(f"{path}: wrong frozen inverse column count")
            for value in row:
                if float.fromhex(value).hex() != value:
                    raise ValueError(f"{path}: non-canonical float hex entry")

    return frozen


def frozen_R_matrix(frozen: dict[str, Any], path: str, n: int) -> arb_mat:
    rows = frozen["matrices"][path]
    return arb_mat(
        [[arb_from_frozen_hex(rows[i][j]) for j in range(n)] for i in range(n)]
    )


def certify(path: str, Bmat: arb_mat, Rmat: arb_mat, n: int) -> dict[str, Any]:
    Imat = arb_mat(n, n)
    for i in range(n):
        Imat[i, i] = arb(1)

    RB = Rmat * Bmat
    residual = Imat - RB
    rho = inf_norm_ball(residual, n)
    Rnorm = inf_norm_ball(Rmat, n)

    rho_up = float(rho.upper())
    Rnorm_up = float(Rnorm.upper())
    nonsingular = rho_up < 1

    if nonsingular:
        inv_err = rho * Rnorm / (arb(1) - rho)
        inv_err_up = float(inv_err.upper())
    else:
        inv_err_up = None

    return {
        "path": path,
        "rho_upper": rho_up,
        "R_norm_upper": Rnorm_up,
        "nonsingular": bool(nonsingular),
        "inverse_error_bound_upper": inv_err_up,
    }


def build_certificate(
    cohort_path: Path = COHORT,
    inverse_data_path: Path = FROZEN_INVERSE_DATA,
) -> dict[str, Any]:
    cohort = load_json(cohort_path)
    frozen = validate_frozen_inverse_data(cohort_path, inverse_data_path)
    payload = preconditioner_payload(cohort)

    results = []
    all_pass = True
    for path, Bmat, n in load_B_matrices(cohort_path):
        Rmat = frozen_R_matrix(frozen, path, n)
        row = certify(path, Bmat, Rmat, n)
        results.append(row)
        all_pass = all_pass and row["nonsingular"]

    return {
        "schema": "p0_preconditioner_certificate",
        "schema_version": 2,
        "method": "Rump-Neumann regularity certificate",
        "production_preconditioner_conversion": "arb(repr(float(decimal)))",
        "source_cohort_sha256": sha256_bytes(cohort_path),
        "production_preconditioner_payload_sha256": sha256_json(payload),
        "frozen_inverse_data_sha256": sha256_bytes(inverse_data_path),
        "frozen_inverse_schema": "p0_frozen_inverse_hex@1",
        "matrix_shape": list(EXPECTED_MATRIX_SHAPE),
        "paths": list(EXPECTED_PATHS),
        "prec_bits": ctx.prec,
        "results": results,
        "all_nonsingular": all_pass,
    }


def certificate_bytes(certificate: dict[str, Any]) -> bytes:
    return (json.dumps(certificate, indent=1, sort_keys=False) + "\n").encode(
        "utf-8"
    )


def print_summary(certificate: dict[str, Any]) -> None:
    print(f"P0  frozen preconditioner non-singularity  (Arb prec={ctx.prec} bits)")
    print(f"{'path':6} {'||I-RB||_inf <=':>22}  {'nonsingular':>11}  "
          f"{'||B^-1 - R||_inf <=':>20}")
    print("-" * 70)
    for row in certificate["results"]:
        err = (f"{row['inverse_error_bound_upper']:.3e}"
               if row["inverse_error_bound_upper"] is not None else "  --")
        print(f"{row['path']:6} {row['rho_upper']:22.3e}  "
              f"{str(row['nonsingular']):>11}  {err:>20}")
    print("-" * 70)
    passed = sum(bool(row["nonsingular"]) for row in certificate["results"])
    total = len(certificate["results"])
    result = "PASS" if certificate["all_nonsingular"] else "FAIL"
    print(f"P0 RESULT: {result}  "
          f"({passed}/{total} preconditioners rigorously non-singular)")


def main(argv: list[str] | None = None) -> bool:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--write-certificate",
        action="store_true",
        help="maintainer-only: overwrite the tracked P0 certificate",
    )
    args = parser.parse_args(argv)

    certificate = build_certificate()
    print_summary(certificate)
    generated = certificate_bytes(certificate)

    if args.write_certificate:
        P0_CERTIFICATE.parent.mkdir(parents=True, exist_ok=True)
        P0_CERTIFICATE.write_bytes(generated)
        print(f"P0 certificate written: {P0_CERTIFICATE.relative_to(REPO_ROOT)}")
    else:
        committed = P0_CERTIFICATE.read_bytes()
        if generated != committed:
            print("P0 certificate byte-identical: False")
            print("Run with --write-certificate only after maintainer review.")
            return False
        print("P0 certificate byte-identical: True")

    return bool(certificate["all_nonsingular"])


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
