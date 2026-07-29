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
