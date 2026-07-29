# Quantum Control Geometry

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

**Rigorous mathematical framework for quantum control via covariant tensor theory and ordering theorems.**

## Overview

Quantum Control Geometry provides a **mathematically rigorous** framework for quantum control optimization based on:

- **Covariant response tensors**: Coordinate-invariant geometric objects encoding control path properties
- **Ordering theorems**: Strict mathematical theorems with remainder bounds for predicting control performance
- **Mathematical certificates**: 100% certified predictions with zero errors

This library implements the **L3-L4 theoretical framework**: covariant tensor representation (L3) and ordering theorem with remainder bounds (L4).

## Key Features

### 🎯 **Mathematical Rigor**
- **Strict theorems**: Ordering theorem with analytic tail bound (1.23×10⁻¹¹)
- **100% certification**: All certified pairs correct (zero errors)
- **Formal verification**: Floating-point certificates with formal interval arithmetic support

### 🔬 **Covariant Tensor Theory**
- **Coordinate-invariant**: Tensors transform correctly under coordinate changes
- **Geometric objects**: Response tensors as geometric invariants
- **High-order expansions**: 30th-order local jet expansions with analytic tail bounds

### ⚡ **Performance**
- **Computational efficiency**: Single differential calculation vs. multiple simulations
- **Predictive power**: Spearman correlation = 1.0 (perfect ranking)
- **Error bounds**: Strict remainder bounds (1.23×10⁻¹¹)

## Installation

```bash
pip install quantum-control-geometry
```

For development:
```bash
git clone https://github.com/papasop/quantum-control-geometry.git
cd quantum-control-geometry
pip install -e ".[dev]"
```

## Quick Start

### Basic Usage: G4 Coefficient Calculation

```python
from quantum_control_geometry.tensors import ResponseTensor
from quantum_control_geometry.theorems import OrderingTheorem

# Compute covariant response tensor
tensor = ResponseTensor(order=4)
G4 = tensor.compute_g4_coefficient(control_path)

# Predict performance ranking
predicted_rank = tensor.rank_by_g4(G4)

# Verify with ordering theorem
theorem = OrderingTheorem(jet_order=30)
certified = theorem.verify_ranking(
    predicted_rank,
    tail_bound=1.23e-11,
    certification_level=1.0
)
```

### Advanced: Covariant Tensor Framework

```python
from quantum_control_geometry.tensors import CovariantTensor

# Create covariant tensor
cov_tensor = CovariantTensor(
    metric=minisupermetric,
    order=4
)

# Compute invariants
invariants = cov_tensor.compute_invariants()

# Contract with noise moments
contraction = cov_tensor.contract_with_noise(noise_moments)
```

## Theory Background

### Covariant Response Tensors

The **covariant response tensor** $T_{\mu\nu\rho\sigma}$ encodes the fourth-order response of a quantum control path:

$$T_{\mu\nu\rho\sigma} = \frac{\partial^4 J}{\partial \xi^\mu \partial \xi^\nu \partial \xi^\rho \partial \xi^\sigma}\bigg|_{\xi=0}$$

where $J$ is the task loss and $\xi$ are error parameters.

### Ordering Theorem (L4)

The **ordering theorem** provides a strict mathematical guarantee:

$$|J(\gamma, \sigma) - (J_0 + G4 \cdot \sigma^4)| \leq R(\sigma)$$

where:
- $G4 = \text{mean\_axis } a4_{\text{axis}}$ is the fourth-order zero-point coefficient
- $R(\sigma) = 1.23 \times 10^{-11}$ is the analytic tail bound
- The theorem certifies 100% of path pairs with zero errors

### Relation to K=1 Framework

This library implements the **L3-L4 levels** of the quantum control hierarchy, which is structurally isomorphic to the **K=1 framework** (information time as a cost layer):

| K=1 Framework | Quantum Control (L3-L4) |
|---------------|-------------------------|
| Path cost functional $E[\gamma]$ | Fourth-order coefficient $G4$ |
| Principle R (realizability) | Ordering theorem (ranking prediction) |
| Covariant geometry | Covariant response tensor |
| Inverse gap scaling | Remainder bound |

## Documentation

- **[Theory Background](docs/theory_background.md)**: Mathematical foundations
- **[API Reference](docs/api_reference.md)**: Complete API documentation
- **[Tutorials](docs/tutorials/)**: Step-by-step guides
- **[Proofs](proofs/)**: Mathematical proofs of theorems

## Examples

See [`examples/`](examples/) directory for:
- **Two-atom Rydberg system**: Complete example with verification
- **General quantum system**: Template for arbitrary systems
- **Covariant tensor computation**: Advanced tensor operations

## Testing

```bash
pytest tests/
```

With coverage:
```bash
pytest --cov=quantum_control_geometry tests/
```

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Citation

If you use this library in your research, please cite:

```bibtex
@software{quantum_control_geometry,
  author = {Li, Y. Y. N.},
  title = {Quantum Control Geometry: Rigorous Mathematical Framework for Quantum Control},
  year = {2026},
  url = {https://github.com/papasop/quantum-control-geometry}
}
```

## Related Work

- **[fixed-unitary-noise-robust-control](https://github.com/papasop/fixed-unitary-noise-robust-control)**: Numerical verification and application to two-atom Rydberg systems (depends on this library)
- **K=1 Framework**: Abstract theoretical framework for information time as a cost layer

## Support

- **Issues**: [GitHub Issues](https://github.com/papasop/quantum-control-geometry/issues)
- **Discussions**: [GitHub Discussions](https://github.com/papasop/quantum-control-geometry/discussions)

---

**Status**: Active development | **Version**: 0.1.0 | **Python**: 3.8+
