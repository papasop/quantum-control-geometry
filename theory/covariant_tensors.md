# Covariant Tensor Theory for Quantum Control

## Overview

This document describes the covariant tensor framework for quantum control, which provides a coordinate-invariant geometric description of control path properties.

## Motivation

Traditional quantum control methods rely on specific coordinate representations, making it difficult to:
- Compare control paths across different parameterizations
- Establish general theoretical results
- Develop coordinate-invariant optimization algorithms

The covariant tensor framework addresses these limitations by encoding control path properties in geometric objects that are independent of coordinate choice.

## Mathematical Foundation

### Minisupermetric

The configuration space of quantum control is equipped with a **minisupermetric** $G_{AB}$:

$$G_{AB} = \begin{pmatrix} g_{11} & g_{12} \\ g_{21} & g_{22} \end{pmatrix}$$

This metric defines the geometry of the control space and is used to raise/lower indices.

### Covariant Response Tensor

The **covariant response tensor** $T_{\mu\nu\rho\sigma}$ is defined as:

$$T_{\mu\nu\rho\sigma} = \frac{\partial^4 J}{\partial \xi^\mu \partial \xi^\nu \partial \xi^\rho \partial \xi^\sigma}\bigg|_{\xi=0}$$

where:
- $J$ is the task loss (infidelity)
- $\xi^\mu$ are error parameters
- The derivative is evaluated at the zero-error point

### Coordinate Transformation

Under a coordinate transformation $\xi^\mu \to \xi'^\mu$, the tensor transforms as:

$$T'_{\mu'\nu'\rho'\sigma'} = \frac{\partial \xi^\mu}{\partial \xi'^{\mu'}} \frac{\partial \xi^\nu}{\partial \xi'^{\nu'}} \frac{\partial \xi^\rho}{\partial \xi'^{\rho'}} \frac{\partial \xi^\sigma}{\partial \xi'^{\sigma'}} T_{\mu\nu\rho\sigma}$$

This ensures that physical predictions are independent of coordinate choice.

## Key Invariants

### G4 Coefficient

The **G4 coefficient** is the primary invariant:

$$G4 = \text{mean\_axis}(a4_{\text{axis}})$$

where $a4_{\text{axis}}$ are the fourth-order coefficients along each principal axis.

**Interpretation**: Smaller G4 predicts better finite-error performance.

### Tensor Contractions

The tensor can be contracted with noise moments to produce coordinate-invariant scalars:

$$\mathcal{C} = T_{\mu\nu\rho\sigma} M^{\mu\nu\rho\sigma}$$

where $M^{\mu\nu\rho\sigma}$ is the noise moment tensor.

## Properties

### Symmetry

The response tensor is fully symmetric in its indices:

$$T_{\mu\nu\rho\sigma} = T_{(\mu\nu\rho\sigma)}$$

This follows from the equality of mixed partial derivatives.

### Coordinate Invariance

All physical predictions derived from the tensor are coordinate-invariant:
- G4 coefficient
- Tensor contractions
- Performance rankings

## Applications

### Performance Prediction

The G4 coefficient can be used to predict control performance:

1. Compute G4 for multiple control paths
2. Rank paths by G4 (smaller is better)
3. Predicted ranking matches actual finite-error ranking

### Optimization

The covariant framework enables coordinate-invariant optimization:

1. Define objective function in terms of invariants
2. Optimize in any convenient coordinate system
3. Results are independent of coordinate choice

## Relation to K=1 Framework

The covariant tensor framework is structurally isomorphic to the K=1 framework:

| K=1 Framework | Quantum Control (L3) |
|---------------|----------------------|
| Path cost functional $E[\gamma]$ | Covariant response tensor $T_{\mu\nu\rho\sigma}$ |
| Principle R | Ordering theorem |
| Covariant geometry | Covariant tensor |
| Null cone structure | Response tensor symmetries |

## References

- Li, Y. Y. N. (2026). "Prospective Noise-Robust Control within a Fixed-Unitary Fibre"
- Li, Y. Y. N. (2026). "Realization Time from a Timeless Constraint: A Semiclassical Test of the K=1 Framework"
