"""Covariant tensor objects for quantum control geometry."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


@dataclass
class CovariantTensor:
    """Finite-dimensional covariant tensor with a metric.

    The implementation is intentionally conservative: it provides deterministic
    numerical tensor components and contractions suitable for examples, tests,
    and later replacement by domain-specific response calculations.
    """

    metric: np.ndarray
    order: int = 4
    components: np.ndarray | None = field(default=None, init=False)

    def __post_init__(self) -> None:
        self.metric = np.asarray(self.metric, dtype=float)
        if self.metric.ndim != 2 or self.metric.shape[0] != self.metric.shape[1]:
            raise ValueError("metric must be a square matrix")
        if self.order < 2:
            raise ValueError("order must be at least 2")
        self.dim = self.metric.shape[0]

    def compute_components(
        self,
        control_path: np.ndarray,
        jacobian: np.ndarray | None = None,
    ) -> np.ndarray:
        """Compute symmetric tensor components for a control path.

        Parameters
        ----------
        control_path:
            Array of shape ``(steps, dim)``.
        jacobian:
            Optional Jacobian samples. When provided, its average magnitude is
            used to scale the path moments.
        """

        path = np.asarray(control_path, dtype=float)
        if path.ndim != 2 or path.shape[1] != self.dim:
            raise ValueError(f"control_path must have shape (n, {self.dim})")

        centered = path - path.mean(axis=0, keepdims=True)
        shape = (self.dim,) * self.order
        components = np.zeros(shape, dtype=float)
        for point in centered:
            term = point
            for _ in range(self.order - 1):
                term = np.multiply.outer(term, point)
            components += term.reshape(shape)

        components /= max(len(centered), 1)
        if jacobian is not None:
            components *= float(np.mean(np.abs(jacobian)))

        self.components = components
        return components

    def compute_invariants(self) -> np.ndarray:
        """Return scalar invariants derived from current components."""

        if self.components is None:
            raise ValueError("components have not been computed")
        return np.array(
            [
                float(np.linalg.norm(self.components)),
                float(np.mean(self.components)),
                float(np.max(np.abs(self.components))),
            ]
        )

    def contract_with_noise(self, noise_moments: np.ndarray) -> float:
        """Contract tensor components with a noise moment tensor."""

        if self.components is None:
            raise ValueError("components have not been computed")
        noise = np.asarray(noise_moments, dtype=float)
        if noise.shape != self.components.shape:
            raise ValueError(f"noise_moments must have shape {self.components.shape}")
        return float(np.tensordot(self.components, noise, axes=self.order))
