"""
P1 -- Independent reconstruction of the Hamiltonian, 24-segment propagation, and
six-point mean infidelity, to rule out a shared model-translation error.

Nothing is imported from the repo's engine. Operators are rebuilt from scratch,
propagation is done by Hermitian eigendecomposition (a different numerical path
from the repo's formal acb_mat.exp()), and three paths are cross-checked at 60-digit
mpmath precision. The 12 candidate phase vectors are read from the frozen
Krawczyk certificate. Each independently computed per-path mean infidelity must
land inside the certificate's rigorous direct_mean_interval ball.

Documented model (from paper / base module):
  H_seg = 0.5*Omega*(1+eps_amp)*(cos phi * Gx + sin phi * Gy)
          - Omega*eps_det * Ntot
          + V*(1+eps_int) * n1 n2
  Omega = 2*pi rad/us,  V = 4*Omega,  dt = 0.1 us,  24 segments.
  target = zero-error endpoint of the reference phase vector.
  infidelity(eps) = 1 - |<target|U(eps)|gg>|^2 ; mean over the six held-out points.
"""
import json, math, sys
from decimal import Decimal
from pathlib import Path
import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
CERT = str(REPO_ROOT / "results/exact_fibre_krawczyk/krawczyk_certificate.json")
ORDER = str(REPO_ROOT /
            "results/exact_root_ordering/exact_root_ordering_certificate.json")

# --- constants (independent literals, not imported) ---
PI = math.pi
OMEGA = 2.0 * PI            # rad/us
V = 4.0 * OMEGA            # nominal Rydberg interaction, rad/us
DT = 0.1                   # us
NSEG = 24

REFERENCE_PHASES = [
    5.395938949660, 4.364190556336, 4.065716153363, 4.362035605699,
    5.384474017704, 1.275621345422, 1.330584917556, 4.407856703296,
    4.811419315138, 4.022090674744, 0.414000889690, 1.067187010905,
    1.401546960667, 3.017636778929, 2.942592144415, 3.205438748314,
    0.757976217375, 5.846203422983, 3.626398737602, 5.777000471280,
    3.048480766333, 4.247669043136, 2.313878941042, 3.714910179805,
]

# six held-out error points: (amp, det, int)
HELD_OUT = [
    (-0.06, 0.0, 0.0), (+0.06, 0.0, 0.0),
    (0.0, -0.04, 0.0), (0.0, +0.04, 0.0),
    (0.0, 0.0, -0.05), (0.0, 0.0, +0.05),
]


# --- operators built from scratch (single-qubit -> two-qubit by hand) ---
def kron(a, b):
    return np.kron(a, b)

sx = np.array([[0, 1], [1, 0]], dtype=complex)
sy = np.array([[0, -1j], [1j, 0]], dtype=complex)
num = np.array([[0, 0], [0, 1]], dtype=complex)   # |r><r|
i2 = np.eye(2, dtype=complex)

Gx = kron(sx, i2) + kron(i2, sx)
Gy = kron(sy, i2) + kron(i2, sy)
Ntot = kron(num, i2) + kron(i2, num)
nn = kron(num, num)
GG = np.array([1, 0, 0, 0], dtype=complex)

# sanity: all Hermitian
for name, M in [("Gx", Gx), ("Gy", Gy), ("Ntot", Ntot), ("nn", nn)]:
    assert np.allclose(M, M.conj().T), name


def seg_H(phi, amp, det, itn):
    drive = 0.5 * OMEGA * (1.0 + amp) * (math.cos(phi) * Gx + math.sin(phi) * Gy)
    detune = -OMEGA * det * Ntot
    inter = V * (1.0 + itn) * nn
    return drive + detune + inter


def seg_U_eig(H):
    """Segment propagator via Hermitian eigendecomposition (independent path)."""
    w, Vv = np.linalg.eigh(H)               # H = V diag(w) V^H
    return (Vv * np.exp(-1j * DT * w)) @ Vv.conj().T


def propagate(phases, amp, det, itn):
    psi = GG.copy()
    for phi in phases:
        psi = seg_U_eig(seg_H(phi, amp, det, itn)) @ psi
    return psi


def infidelity(target, psi):
    ov = np.vdot(target, psi)
    return float(1.0 - (ov.real ** 2 + ov.imag ** 2))


def mean_infidelity(phases, target):
    vals = [infidelity(target, propagate(phases, *e)) for e in HELD_OUT]
    return float(np.mean(vals)), vals


# --- high-precision cross-check (mpmath, 60 digits) for one path ---
def mpmath_mean(phases, target_ph):
    import mpmath as mp
    mp.mp.dps = 60
    o = mp.mpf(2) * mp.pi
    v = mp.mpf(4) * o
    dt = mp.mpf(1) / 10
    Sx = mp.matrix([[0, 1], [1, 0]])
    Sy = mp.matrix([[0, -1j], [1j, 0]])
    Nm = mp.matrix([[0, 0], [0, 1]])
    I = mp.eye(2)

    def mkron(a, b):
        r = mp.zeros(4, 4)
        for i in range(2):
            for j in range(2):
                for k in range(2):
                    for l in range(2):
                        r[i * 2 + k, j * 2 + l] = a[i, j] * b[k, l]
        return r
    gX = mkron(Sx, I) + mkron(I, Sx)
    gY = mkron(Sy, I) + mkron(I, Sy)
    nt = mkron(Nm, I) + mkron(I, Nm)
    NN = mkron(Nm, Nm)

    def H(phi, amp, det, itn):
        return (mp.mpf('0.5') * o * (1 + amp) * (mp.cos(phi) * gX + mp.sin(phi) * gY)
                - o * det * nt + v * (1 + itn) * NN)

    def U(phi, amp, det, itn):
        return mp.expm(-1j * dt * H(phi, amp, det, itn))

    def prop(phases, amp, det, itn):
        psi = mp.matrix([1, 0, 0, 0])
        for phi in phases:
            psi = U(mp.mpf(str(phi)), amp, det, itn) * psi
        return psi
    tgt = prop([mp.mpf(str(p)) for p in target_ph], 0, 0, 0)
    tb = tgt.conjugate().T
    errs = [(-mp.mpf('0.06'), 0, 0), (mp.mpf('0.06'), 0, 0),
            (0, -mp.mpf('0.04'), 0), (0, mp.mpf('0.04'), 0),
            (0, 0, -mp.mpf('0.05')), (0, 0, mp.mpf('0.05'))]
    losses = []
    for e in errs:
        st = prop([mp.mpf(str(p)) for p in phases], *e)
        ov = (tb * st)[0, 0]
        losses.append(1 - (ov.conjugate() * ov).real)
    return sum(losses) / 6


def parse_ball(ball_str):
    """Parse an Arb display ball without first rounding it to binary64."""
    s = ball_str.strip().lstrip("[").rstrip("]")
    if "+/-" in s:
        mid, rad = s.split("+/-")
        return Decimal(mid.strip()), Decimal(rad.strip())
    return Decimal(s.strip()), Decimal(0)


def certificate_enclosure(dm):
    """Read the certificate's outward-rounded endpoint balls as Decimals.

    direct_mean_interval stores 'lower' and 'upper' as arb balls; the rigorous
    outer bound is [inf(lower_ball), sup(upper_ball)].
    """
    lo_mid, lo_rad = parse_ball(dm["lower"])
    hi_mid, hi_rad = parse_ball(dm["upper"])
    return lo_mid - lo_rad, hi_mid + hi_rad


def main():
    cert = json.load(open(CERT))
    order = json.load(open(ORDER))
    cand = cert["candidate_phases_decimal"]                 # 12 x 24
    balls = {r["path"]: parse_ball(r["direct_mean_interval"]["ball"])
             for r in order["path_rows"]}
    # Exact decimal parsing of the certificate's outward-rounded endpoints.
    encl = {r["path"]: certificate_enclosure(r["direct_mean_interval"])
            for r in order["path_rows"]}

    target = propagate([float(p) for p in REFERENCE_PHASES], 0, 0, 0)
    tgt_gg = float(1.0 - abs(target[0]) ** 2)
    print(f"target zero-error endpoint infidelity vs |gg> = {tgt_gg:.2e} "
          f"(should be ~0: reference returns to gg)\n")

    print(f"{'path':6} {'independent mean':>18} {'cert enclosure [lo, hi]':>40} "
          f"{'inside?':>8}")
    print("-" * 78)
    my_means = {}
    margins = {}
    all_inside = True
    for p in cert.get("candidate_phases_decimal", {}):
        phases = [float(x) for x in cand[p]]
        m, _ = mean_infidelity(phases, target)
        my_means[p] = m
        lo, hi = encl[p]
        # Decimal.from_float preserves the independently computed binary64
        # value exactly. This is a point cross-check against a rigorous
        # certificate enclosure, not a second interval proof.
        md = Decimal.from_float(m)
        inside = (lo <= md <= hi)
        margins[p] = min(md - lo, hi - md)
        all_inside = all_inside and inside
        print(f"{p:6} {m:18.12f}   [{float(lo):.9f}, {float(hi):.9f}] {str(inside):>8}")
    print("-" * 78)

    # ordering + closest pairs
    order_by_mean = sorted(my_means, key=lambda k: my_means[k])
    cert_order = sorted(balls, key=lambda k: balls[k][0])
    print("\nIndependent ordering (best->worst):", " ".join(order_by_mean))
    print("Certificate  ordering (best->worst):", " ".join(cert_order))
    print("Ordering identical:", order_by_mean == cert_order)

    # closest ordering pairs, using the certificate's CERTIFIED order as truth
    # (full-precision disjoint intervals, not the display-rounded midpoints).
    certified = {(p["better"], p["worse"]) for p in order["direct_certified_pairs"]}

    def certified_better(x, y):
        if (x, y) in certified:
            return x
        if (y, x) in certified:
            return y
        return None
    ms = sorted(balls.items(), key=lambda kv: kv[1][0])
    gaps = []
    for a in range(len(ms)):
        for b in range(a + 1, len(ms)):
            gaps.append((abs(ms[a][1][0] - ms[b][1][0]), ms[a][0], ms[b][0]))
    gaps.sort()
    print("\nClosest ordering pairs (hardest to certify) -- independent check")
    print("(order truth = certificate's certified disjoint intervals):")
    print(f"{'pair':16} {'cert better':>12} {'indep better':>13} {'match?':>8}")
    closest_ok = True
    for gap, x, y in gaps[:6]:
        cb = certified_better(x, y)
        ib = x if my_means[x] < my_means[y] else y
        same = (cb == ib)
        closest_ok = closest_ok and same
        print(f"{x}/{y:11} {str(cb):>12} {ib:>13} {str(same):>8}")

    # high-precision cross-check on the best and a close pair member
    print("\nmpmath 60-digit cross-check (rules out float artefacts):")
    for p in ["pv07", "pv08", "pv11"]:
        m_hp = float(mpmath_mean([float(x) for x in cand[p]], REFERENCE_PHASES))
        print(f"  {p}: float={my_means[p]:.10f}  mpmath60={m_hp:.10f}  "
              f"|diff|={abs(m_hp-my_means[p]):.2e}")

    verdict = all_inside and (order_by_mean == cert_order) and closest_ok
    print("\nP1 RESULT:", "PASS" if verdict else "FAIL")
    print(f"  - 12/12 means inside certificate balls: {all_inside}")
    print(f"  - full 12-path ordering reproduced: {order_by_mean == cert_order}")
    print(f"  - closest pairs order reproduced: {closest_ok}")
    print(f"  - minimum point-to-certificate-boundary margin: "
          f"{float(min(margins.values())):.3e}")
    return verdict


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
