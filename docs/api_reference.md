# API Reference

Complete API documentation for quantum-control-geometry.

## Tensors

### `CovariantTensor`

Covariant tensor for quantum control geometry.

```python
from quantum_control_geometry.tensors import CovariantTensor

tensor = CovariantTensor(metric=metric, order=4)
```

#### Methods

##### `compute_components(control_path, jacobian)`

Compute tensor components for a control path.

**Parameters:**
- `control_path` (ndarray): Control path in configuration space
- `jacobian` (ndarray): Jacobian matrix

**Returns:**
- `ndarray`: Tensor components

##### `compute_invariants()`

Compute coordinate invariants.

**Returns:**
- `ndarray`: Array of invariant scalars

##### `contract_with_noise(noise_moments)`

Contract tensor with noise moments.

**Parameters:**
- `noise_moments` (ndarray): Noise moment tensor

**Returns:**
- `float`: Contracted scalar value

### `ResponseTensor`

Response tensor for performance prediction.

```python
from quantum_control_geometry.tensors import ResponseTensor

tensor = ResponseTensor(metric=metric, order=4)
```

#### Methods

##### `compute_g4_coefficient(control_path, jacobian)`

Compute G4 coefficient.

**Parameters:**
- `control_path` (ndarray): Control path
- `jacobian` (ndarray): Jacobian matrix

**Returns:**
- `float`: G4 coefficient (smaller predicts better)

##### `rank_by_g4(g4_coefficients)`

Rank paths by G4 coefficient.

**Parameters:**
- `g4_coefficients` (ndarray): Array of G4 coefficients

**Returns:**
- `ndarray`: Ranking indices

## Theorems

### `OrderingTheorem`

L4 ordering theorem with remainder bounds.

```python
from quantum_control_geometry.theorems import OrderingTheorem

theorem = OrderingTheorem(jet_order=30, tail_bound=1.23e-11)
```

#### Methods

##### `compute_jet_expansion(control_path, derivatives)`

Compute local jet expansion.

**Parameters:**
- `control_path` (ndarray): Control path
- `derivatives` (ndarray): Derivatives up to jet_order

**Returns:**
- `ndarray`: Jet expansion coefficients

##### `compute_remainder_bound(control_path, error_scale)`

Compute analytic remainder bound.

**Parameters:**
- `control_path` (ndarray): Control path
- `error_scale` (float): Error scale σ

**Returns:**
- `float`: Remainder bound R(σ)

##### `verify_ranking(predicted_rank, actual_rank, certification_level)`

Verify ranking with certification.

**Parameters:**
- `predicted_rank` (ndarray): Predicted ranking
- `actual_rank` (ndarray, optional): Actual ranking
- `certification_level` (float): Required certification level

**Returns:**
- `bool`: True if certified

##### `certify_pair(path1, path2, g4_1, g4_2, error_scale)`

Certify ordering of a pair of paths.

**Parameters:**
- `path1` (ndarray): First control path
- `path2` (ndarray): Second control path
- `g4_1` (float): G4 coefficient of first path
- `g4_2` (float): G4 coefficient of second path
- `error_scale` (float): Error scale σ

**Returns:**
- `bool`: True if certified
