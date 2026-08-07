"""
P0 -- Rigorous Arb non-singularity certificate for every frozen preconditioner B.

Goal: close the Krawczyk uniqueness precondition. The Krawczyk map used in
scripts/core/pasqal_L4_exact_fibre_krawczyk_audit_v1_3.py is

    K(X) - x = -B f(x) + (I - B J(X)) (X - x),

where B = chart.inverse = point_preconditioner_decimal (16x16) is used as the
preconditioner Y. The existence+uniqueness conclusion of the Krawczyk theorem
requires Y = B to be REGULAR (non-singular). The frozen certificate records the
inclusion pass but never emits a standalone, machine-checkable regularity
certificate for B. This script supplies one.

Method (Rump verified non-singularity, the standard "interval inverse
certificate"): pick a floating approximate inverse R ~ B^{-1}, then bound

    rho := ||I - R B||_inf

rigorously with outward-rounded Arb. If rho < 1 then (I - (I - RB)) = RB is
non-singular by the Neumann series, hence B is non-singular. The verified
enclosure of the true inverse follows:

    ||B^{-1} - R||_inf <= rho * ||R||_inf / (1 - rho).

Every arithmetic operation below is an Arb ball op, so every reported bound is
an outward-rounded rigorous enclosure, not a float estimate.
"""
import json
import hashlib
import sys
from pathlib import Path
from flint import arb, arb_mat, ctx
import numpy as np

ctx.prec = 256  # 256-bit working precision

REPO_ROOT = Path(__file__).resolve().parents[2]
COHORT = str(REPO_ROOT / "results/exact_fibre_krawczyk/cohort.json")


def arb_from_decimal(s: str) -> arb:
    # arb(str) parses the decimal string to a ball that provably contains it.
    return arb(s)


def load_B_matrices():
    d = json.load(open(COHORT))
    out = []
    for entry in d["paths"]:
        rows = entry["point_preconditioner_decimal"]
        n = len(rows)
        # Match the Y ACTUALLY used in krawczyk_path: ar(repr(float(decimal))),
        # i.e. the frozen decimal rounded to double, then taken as an exact ball.
        Bf = np.array([[float(rows[i][j]) for j in range(n)] for i in range(n)])
        Bmat = arb_mat([[arb(repr(float(Bf[i, j]))) for j in range(n)]
                        for i in range(n)])
        out.append((entry["path"], Bmat, Bf, n))
    return out


def inf_norm_ball(M: arb_mat, n: int) -> arb:
    """Rigorous upper enclosure of the infinity norm of a ball matrix."""
    best = arb(0)
    for i in range(n):
        row = arb(0)
        for j in range(n):
            row = row + abs(M[i, j])   # abs of a ball -> ball; sum outward-rounded
        # keep the max as a ball whose upper bound dominates every row sum
        if row.upper() > best.upper():
            best = row
    return best


def certify(path, Bmat, Bf, n):
    # Floating approximate inverse (non-rigorous; only a preconditioner choice).
    R = np.linalg.inv(Bf)
    Rmat = arb_mat([[arb(repr(float(R[i, j]))) for j in range(n)]
                    for i in range(n)])
    Imat = arb_mat(n, n)
    for i in range(n):
        Imat[i, i] = arb(1)

    # Rigorous residual  M = I - R B   (all Arb ball ops)
    RB = Rmat * Bmat
    M = Imat - RB
    rho = inf_norm_ball(M, n)          # >= ||I - RB||_inf , rigorous upper bound
    Rnorm_up = float(inf_norm_ball(Rmat, n).upper())

    rho_up = float(rho.upper())
    nonsingular = rho_up < 1

    if nonsingular:
        # rigorous:  ||B^-1 - R||_inf <= rho*||R||/(1-rho), enclose with Arb balls
        inv_err = rho * inf_norm_ball(Rmat, n) / (arb(1) - rho)
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


def main():
    print(f"P0  frozen preconditioner non-singularity  (Arb prec={ctx.prec} bits)")
    print(f"{'path':6} {'||I-RB||_inf <=':>22}  {'nonsingular':>11}  "
          f"{'||B^-1 - R||_inf <=':>20}")
    print("-" * 70)
    results = []
    all_pass = True
    for path, Bmat, Bf, n in load_B_matrices():
        r = certify(path, Bmat, Bf, n)
        results.append(r)
        all_pass = all_pass and r["nonsingular"]
        rho = r["rho_upper"]
        err = (f"{r['inverse_error_bound_upper']:.3e}"
               if r["inverse_error_bound_upper"] is not None else "  --")
        print(f"{r['path']:6} {rho:22.3e}  {str(r['nonsingular']):>11}  {err:>20}")
    print("-" * 70)
    print(f"P0 RESULT: {'PASS' if all_pass else 'FAIL'}  "
          f"({sum(x['nonsingular'] for x in results)}/{len(results)} "
          f"preconditioners rigorously non-singular)")
    out = REPO_ROOT / "results/audit_closure"
    out.mkdir(parents=True, exist_ok=True)
    cohort_sha256 = hashlib.sha256(Path(COHORT).read_bytes()).hexdigest()
    json.dump({
               "method": "Rump-Neumann regularity certificate",
               "production_preconditioner_conversion": "arb(repr(float(decimal)))",
               "source_cohort_sha256": cohort_sha256,
               "prec_bits": ctx.prec,
               "results": results,
               "all_nonsingular": all_pass},
              open(out / "p0_preconditioner_certificate.json", "w"), indent=1)
    return all_pass


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
