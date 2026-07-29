"""Response tensor helpers for ranking quantum control paths."""

from __future__ import annotations

import numpy as np

from quantum_control_geometry.tensors.covariant_tensor import CovariantTensor


class ResponseTensor:
    """Compute response coefficients used by ordering theorems."""

    def __init__(self, metric: np.ndarray | None = None, order: int = 4) -> None:
        if metric is None:
            metric = np.eye(2)
        self.covariant_tensor = CovariantTensor(metric=metric, order=order)
        self.g4_coefficient: float | None = None

    def compute_g4_coefficient(
        self,
        control_path: np.ndarray,
        jacobian: np.ndarray | None = None,
    ) -> float:
        """Compute a fourth-order response coefficient.

        Smaller values are interpreted as better predicted robustness.
        """

        components = self.covariant_tensor.compute_components(control_path, jacobian)
        metric_weight = float(np.linalg.norm(self.covariant_tensor.metric, ord="fro"))
        coefficient = float(np.mean(np.square(components)) * metric_weight)
        self.g4_coefficient = coefficient
        return coefficient

    @staticmethod
    def rank_by_g4(g4_coefficients: np.ndarray) -> np.ndarray:
        """Rank path indices by ascending G4 coefficient."""

        coeffs = np.asarray(g4_coefficients, dtype=float)
        if coeffs.ndim != 1:
            raise ValueError("g4_coefficients must be one-dimensional")
        return np.argsort(coeffs)
