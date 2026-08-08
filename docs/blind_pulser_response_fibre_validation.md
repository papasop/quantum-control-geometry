# Blind Pulser Validation of Response-Fibre Prediction

## Question

Can a response-fibre geometric score frozen before Pulser outcomes predict
finite-error performance for unseen two-atom control schedules?

## Protocol

The executable reads the pre-outcome prospective certificate from immutable
tag `v0.3.2`. The certificate records `outcomes_unlocked=false`, twenty
candidate 24-segment phase schedules, and a best-to-worst G4 prediction.

Pulser 1.9 then evaluates each schedule at six predeclared finite-error points:
two amplitude, two detuning, and two interaction perturbations. This produces
120 propagated losses. Only after those calculations does the script compare
the frozen prediction with the Pulser ordering.

## Predeclared gates

- all 120 propagations produce finite values;
- Spearman correlation is at least 0.80;
- one-sided 20,000-permutation p-value is below 0.05;
- the predicted-best five schedules outperform the predicted-worst five with
  a 20,000-bootstrap 95% confidence interval whose lower endpoint is positive.

## Recorded result

- Spearman rho: 0.998496;
- permutation p: 4.99975e-05;
- best-versus-worst mean-loss advantage: 0.01131757;
- bootstrap 95% interval: [0.007947237, 0.01522103];
- simple phase-total-variation baseline rho: -0.263158.

The predicted and observed orders differ only by the adjacent `pv18`/`pv04`
swap.

## Claim boundary

This supports prospective geometric prediction in the local Pulser two-atom
model. It is not a second Arb/Krawczyk proof, not PASQAL Cloud execution, and
not QPU or hardware evidence. The exact-root certificate and this prospective
G4 test are distinct evidence layers.

