# Theory Background

## Introduction

Quantum Control Geometry provides a rigorous mathematical framework for quantum control based on covariant tensor theory and ordering theorems. This document provides the theoretical background.

## Mathematical Foundation

### Covariant Tensor Theory

The framework is based on **covariant tensors**, which are geometric objects that transform correctly under coordinate changes. This ensures that physical predictions are independent of the choice of coordinates.

### Ordering Theorem

The **ordering theorem** (L4) provides a strict mathematical guarantee that the G4 coefficient can predict finite-error performance rankings with certified accuracy.

## Key Concepts

### 1. Covariant Response Tensor

The covariant response tensor $T_{\mu\nu\rho\sigma}$ encodes the fourth-order response of a control path:

$$T_{\mu\nu\rho\sigma} = \frac{\partial^4 J}{\partial \xi^\mu \partial \xi^\nu \partial \xi^\rho \partial \xi^\sigma}\bigg|_{\xi=0}$$

### 2. G4 Coefficient

The G4 coefficient is the primary invariant:

$$G4 = \text{mean\_axis}(a4_{\text{axis}})$$

Smaller G4 predicts better finite-error performance.

### 3. Ordering Theorem

The theorem states:

$$|J(\gamma, \sigma) - (J_0 + G4(\gamma) \cdot \sigma^4)| \leq R(\sigma)$$

where $R(\sigma) = 1.23 \times 10^{-11}$ is the analytic tail bound.

## Relation to K=1 Framework

The L3-L4 framework is structurally isomorphic to the K=1 framework:

| K=1 Framework | Quantum Control (L3-L4) |
|---------------|-------------------------|
| Path cost functional $E[\gamma]$ | G4 coefficient |
| Principle R | Ordering theorem |
| Covariant geometry | Covariant response tensor |
| Inverse gap scaling | Remainder bound |

## References

1. Li, Y. Y. N. (2026). "Prospective Noise-Robust Control within a Fixed-Unitary Fibre"
2. Li, Y. Y. N. (2026). "Realization Time from a Timeless Constraint"
