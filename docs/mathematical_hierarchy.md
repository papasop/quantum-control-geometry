# Mathematical hierarchy

Let \(\gamma\) denote a phase schedule and let
\(\epsilon=(\epsilon_\Omega,\epsilon_\Delta,\epsilon_V)\) denote the declared
implementation errors.

## Matched response

The numerical construction matches the nominal output state and the three
horizontal first-order state responses:

\[
P_\perp\partial_{\epsilon_a}\psi_\gamma(0),
\qquad a\in\{\Omega,\Delta,V\}.
\]

Consequently, the leading quadratic loss is nearly common across paths.

## Fourth-order response

For a normalized error direction \(v\), the symmetric response is

\[
S_\gamma(t,v)=
\frac{\mathcal I_\gamma(tDv)+\mathcal I_\gamma(-tDv)}{2}
=q_{2,\gamma}(v)t^2+q_{4,\gamma}(v)t^4+\cdots.
\]

The quartic form is represented by a symmetric tensor:

\[
q_{4,\gamma}(v)
=A^{(4)}_{\gamma,ijkl}v_iv_jv_kv_l.
\]

For a fourth noise moment \(M^{(4)}\),

\[
G_4(\gamma;M^{(4)})
=A^{(4)}_{\gamma,ijkl}M^{(4)}_{ijkl}.
\]

Under \(z=Ry\), the response tensor and noise moment transform oppositely, so
their contraction is invariant.

## Finite-error closure

For the signed-axis mean at full normalized error scale:

\[
\overline{\mathcal I}_\gamma(1)
=C_{0,\gamma}+C_{2,\gamma}+G_{4,\gamma}
+\sum_{m=3}^{15}G_{2m,\gamma}+R_{32,\gamma}.
\]

The computed order-30 centre contains every displayed coefficient. The
formal radius contains outward-rounding error, the Cauchy-alias enclosure,
and the analytic tail \(R_{32}\). Disjoint intervals certify pairwise order.

## Exact-root closure

Write the 24 phase variables near path \(\gamma_k\) as

\[
\gamma=\widehat\gamma_k+N_k u,\qquad u\in\mathbb R^{16},
\]

where \(N_k\) is the frozen transverse chart. A strict Krawczyk inclusion

\[
K_k(X_k)\subset\operatorname{int}(X_k)
\]

certifies one locally unique exact
projective-state-and-first-projective-response-matched root in each declared
box. Direct outward-rounded evaluation of the six-error mean over the
corresponding phase enclosure then yields intervals
\(\mathcal B_k\). For every frozen ordered pair \(a\prec b\),

\[
\sup\mathcal B_a<\inf\mathcal B_b.
\]

All \(66\) comparisons pass. The order-30 jet propagated over the same boxes
separates \(52/66\) pairs, all in the frozen direction. Thus direct box
propagation supplies the primary finite-radius theorem, while the local jet
supplies a correct but partial mechanism certificate on the exact-root
boxes.

Version v0.3.2 records the regularity condition for the production
preconditioners used in those Krawczyk inclusions. For each frozen
preconditioner \(Y\), an approximate inverse \(R\) is chosen and 256-bit
outward-rounded Arb arithmetic verifies

\[
\rho=\lVert I-RY\rVert_\infty < 1.
\]

By the Neumann-series argument, \(RY\) and therefore \(Y\) are nonsingular.
This closes the regularity premise for the production Krawczyk operator; it
does not replace the v0.3.1 exact-root Arb certificate.

The v1.3 proof freezes the phase centres, transverse bases, and point
preconditioners as decimal inputs and fixes a common box radius of
\(3\times10^{-12}\). Runtime metadata is stored outside the hashed proof
objects. Two complete executions produce byte-identical protocols,
certificates, and reports.
