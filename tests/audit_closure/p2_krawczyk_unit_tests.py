"""
P2 -- Analytic unit tests for the Krawczyk map logic.

The repo's krawczyk_path() (scripts/core/pasqal_L4_exact_fibre_krawczyk_audit_v1_3.py,
lines ~785-867) builds, in the box-centered frame:

    correction_i = -sum_j  Y_ij * residual_j          # -Y f(x_center)
    defect_ij    = I_ij - sum_k Y_ik * J(X)_kj         # I - Y J(X)
    x_interval   = ball(0, r)                          # [-r, r]
    K_i          = correction_i + sum_j defect_ij * x_interval
    strict_i     = (K_i.lower > -r) and (K_i.upper < r)
    pass         = all(strict_i)

`krawczyk_operator` below reproduces that operator EXACTLY (same matrix
direction Y*J, same sign on -Y f, same strict '<' interior test), decoupled from
the 16-dim physics chart so it can be exercised on analytic problems with known
answers. The four cases probe matrix direction, sign, and the strict-inclusion
logic.
"""
import sys
from flint import arb, ctx

ctx.prec = 200


def krawczyk_operator(center, f, jac_interval, Y, r):
    """Faithful re-expression of krawczyk_path's interval operator.

    center : list[float]        box center (approx root)
    f      : callable(list[arb])->list[arb]    residual, evaluated at exact center
    jac_interval : callable(box:list[arb])->list[list[arb]]  Jacobian enclosure
    Y      : list[list[float]]  preconditioner (approx inverse of J at center)
    r      : float              box radius (per-coordinate)
    returns (pass:bool, K:list[arb], strict:list[bool])
    """
    n = len(center)
    R = arb(repr(r))
    center_ball = [arb(repr(c)) for c in center]
    residual = f(center_ball)                                   # f(x_center)

    # box = center +/- r  as balls, for the Jacobian enclosure J(X)
    box = [arb(c, r) for c in center]                           # arb(mid, rad)
    J = jac_interval(box)                                       # n x n ball matrix

    Yb = [[arb(repr(Y[i][j])) for j in range(n)] for i in range(n)]

    # correction_i = -sum_j Y_ij residual_j
    correction = []
    for i in range(n):
        v = arb(0)
        for j in range(n):
            v -= Yb[i][j] * residual[j]
        correction.append(v)

    # defect_ij = I_ij - sum_k Y_ik J_kj      (matrix direction: Y * J)
    defect = [[arb(0)] * n for _ in range(n)]
    for i in range(n):
        row = []
        for j in range(n):
            v = arb(1 if i == j else 0)
            for k in range(n):
                v -= Yb[i][k] * J[k][j]
            row.append(v)
        defect[i] = row

    x_interval = arb(0, r)                                      # [-r, r]
    K, strict = [], []
    for i in range(n):
        v = correction[i]
        for j in range(n):
            v += defect[i][j] * x_interval
        K.append(v)
        strict.append(bool(v.lower() > (-R)) and bool(v.upper() < R))
    return all(strict), K, strict


# ---------- analytic problems ----------
# 1-D linear: f(x) = a (x - xstar)
def make_linear(a, xstar):
    f = lambda xb: [arb(repr(a)) * (xb[0] - arb(repr(xstar)))]
    jac = lambda box: [[arb(repr(a))]]          # constant derivative a
    return f, jac


# quadratic: f(x) = (x - r1)(x - r2)  -> f'(x) = 2x - (r1+r2)
def make_quadratic(r1, r2):
    R1, R2 = arb(repr(r1)), arb(repr(r2))
    f = lambda xb: [(xb[0] - R1) * (xb[0] - R2)]
    jac = lambda box: [[arb(2) * box[0] - (R1 + R2)]]
    return f, jac


# double root: f(x) = (x - xstar)^2 -> f'(x) = 2(x - xstar)
def make_double(xstar):
    XS = arb(repr(xstar))
    f = lambda xb: [(xb[0] - XS) ** 2]
    jac = lambda box: [[arb(2) * (box[0] - XS)]]
    return f, jac


PASS = "\033[0m"
def check(name, got, want):
    ok = (got == want)
    print(f"  [{'ok' if ok else 'XX'}] {name:52} got={got!s:5} want={want!s:5}")
    return ok


def main():
    print("P2  Krawczyk operator unit tests (analytic; logic-level)\n")
    results = []

    # ---- Case 1: analytic linear -------------------------------------------
    print("Case 1  analytic linear  f(x)=a(x-x*)")
    a, xstar = 3.7, 1.234
    f, jac = make_linear(a, xstar)
    r = 1e-6
    Y_good = [[1.0 / a]]
    ok, K, _ = krawczyk_operator([xstar], f, jac, Y_good, r)
    results.append(check("centered, correct Y=1/a -> certifies unique root", ok, True))
    # wrong SIGN of preconditioner must break the contraction
    Y_bad = [[-1.0 / a]]
    ok, _, _ = krawczyk_operator([xstar], f, jac, Y_bad, r)
    results.append(check("wrong-sign Y=-1/a -> refuses (sign test)", ok, False))
    # approximate Y (10% off): defect = 1 - 1.1 = -0.1 (nonzero, <1 in magnitude)
    # exercises the defect*x_interval contraction term, must still certify.
    Y_approx = [[1.1 / a]]
    ok, K, _ = krawczyk_operator([xstar], f, jac, Y_approx, r)
    results.append(check("approx Y (defect=-0.1, nonzero<1) -> certifies", ok, True))
    # slack Y (defect = 1 - 1.9 = -0.9, still <1): certifies at the margin
    ok, _, _ = krawczyk_operator([xstar], f, jac, [[1.9 / a]], r)
    results.append(check("approx Y (defect=-0.9, near margin) -> certifies", ok, True))
    # Y giving |defect|>=1 (defect = 1 - 2.0 = -1.0) -> loses contraction
    ok, _, _ = krawczyk_operator([xstar], f, jac, [[2.0 / a]], r)
    results.append(check("Y with |defect|=1 -> refuses (margin lost)", ok, False))
    # off-center but root still inside box (shift < r)
    shift = 0.4e-6
    ok, Koff, _ = krawczyk_operator([xstar + shift], f, jac, Y_good, r)
    results.append(check("off-center, root still in box -> certifies", ok, True))
    # correction DIRECTION: with center = x*+shift (shift>0), -Y f(center) must
    # point back toward the root, i.e. K midpoint < 0. A correction-sign error
    # (+Y f) flips this even though |K|<r keeps the pass/fail verdict unchanged.
    k_mid = float(Koff[0].mid())
    results.append(check("off-center K points back to root (K_mid<0)",
                         k_mid < 0, True))

    # ---- Case 2: no root in box --------------------------------------------
    print("\nCase 2  no root in box  (root outside)")
    r = 1e-6
    # center displaced far beyond the box from the true root
    ok, K, _ = krawczyk_operator([xstar + 10 * r], f, jac, Y_good, r)
    results.append(check("root far outside box -> refuses (no false cert)", ok, False))

    # ---- Case 3: multiple roots --------------------------------------------
    print("\nCase 3  multi-root  f(x)=(x-r1)(x-r2)")
    r1, r2 = -0.5, 0.5
    fq, jacq = make_quadratic(r1, r2)
    r = 1e-5
    # (a) tight box around ONE simple root: J does not contain 0
    fprime_r1 = 2 * r1 - (r1 + r2)     # = -1.0
    Yq = [[1.0 / fprime_r1]]
    ok, _, _ = krawczyk_operator([r1], fq, jacq, Yq, r)
    results.append(check("box around one simple root -> certifies it", ok, True))
    # (b) box straddling BOTH roots (contains turning point, J spans 0).
    # General reason: if J(X) contains 0 then Y*J(X) contains 0, so the defect
    # I - Y*J(X) contains 1 for EVERY Y; hence defect*[-r,r] contains [-r,r] and
    # strict inclusion is impossible. The Y sweep below just illustrates this.
    mid = 0.5 * (r1 + r2)              # = 0.0, where f'=0
    big_r = 0.6                        # box [-0.6,0.6] covers both roots
    any_certified = False
    for Ytry in ([[1.0]], [[10.0]], [[-10.0]], [[0.5]], [[-0.5]]):
        ok, _, _ = krawczyk_operator([mid], fq, jacq, Ytry, big_r)
        any_certified = any_certified or ok
    results.append(check("box straddling both roots -> refuses (any Y)",
                         any_certified, False))

    # ---- Case 4: edge-touching / tangency ----------------------------------
    print("\nCase 4  edge-touching")
    # (a) double root: f=(x-x*)^2, J(X) contains 0 -> not certifiable
    fd, jacd = make_double(0.0)
    r = 1e-4
    ok, _, _ = krawczyk_operator([0.0], fd, jacd, [[1.0]], r)
    results.append(check("double root (tangent to axis) -> refuses", ok, False))
    # (b) strict-vs-nonstrict: craft K that TOUCHES the box edge exactly.
    #     Use linear f with Y s.t. defect makes K reach exactly +r at the wall.
    #     center offset chosen so correction = -r exactly, defect=0 -> K=[-r,-r]
    #     which touches the lower wall; strict '>' must reject it.
    a2, xs2 = 1.0, 0.0
    fl, jacl = make_linear(a2, xs2)
    r = 1e-6
    # residual = a*(center - x*) = center; correction = -Y*residual = -center (Y=1)
    # choose center = r  -> correction = -r, K = [-r] touching lower wall
    ok, K, strict = krawczyk_operator([r], fl, jacl, [[1.0 / a2]], r)
    # K is the thin ball [-r,-r] sitting on the lower wall; strict '>' must reject.
    on_wall = float(K[0].lower()) <= -r      # sanity: really touches the wall
    results.append(check("K exactly on box wall -> strict '<' rejects", ok, False))
    results.append(check("  (sanity) K.lower() sits at/below -r", on_wall, True))

    print("\n" + "-" * 66)
    npass = sum(results)
    ok = (npass == len(results))
    print(f"P2 RESULT: {'PASS' if ok else 'FAIL'}  "
          f"({npass}/{len(results)} logic assertions)")
    return ok


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
