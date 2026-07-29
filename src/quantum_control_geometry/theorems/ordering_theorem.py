"""Ordering theorem utilities with analytic remainder bounds."""

from __future__ import annotations

import math

import numpy as np


class OrderingTheorem:
    """L4 ordering theorem helper.

    The class tracks certification statistics and exposes deterministic checks
    for ranking and pairwise ordering based on G4 gaps and remainder bounds.
    """

    def __init__(self, jet_order: int = 30, tail_bound: float = 1.23e-11) -> None:
        if jet_order < 2:
            raise ValueError("jet_order must be at least 2")
        if tail_bound < 0:
            raise ValueError("tail_bound must be non-negative")
        self.jet_order = jet_order
        self.tail_bound = float(tail_bound)
        self.certified_pairs = 0
        self.certification_level = 0.0

    def compute_jet_expansion(
        self,
        control_path: np.ndarray,
        derivatives: np.ndarray,
    ) -> np.ndarray:
        """Compute a truncated local jet expansion."""

        path = np.asarray(control_path, dtype=float)
        derivs = np.asarray(derivatives, dtype=float)
        scale = float(np.linalg.norm(path) / max(path.size, 1))
        coeffs = []
        for index, derivative in enumerate(derivs[: self.jet_order], start=1):
            coeffs.append(float(np.mean(derivative) * scale**index / math.factorial(index)))
        return np.asarray(coeffs, dtype=float)

    def compute_remainder_bound(self, control_path: np.ndarray, error_scale: float) -> float:
        """Compute an analytic remainder bound for an error scale."""

        if error_scale < 0:
            raise ValueError("error_scale must be non-negative")
        path_norm = float(np.linalg.norm(control_path))
        return self.tail_bound * (1.0 + path_norm) * (1.0 + error_scale ** self.jet_order)

    def verify_ranking(
        self,
        predicted_rank: np.ndarray,
        actual_rank: np.ndarray | None = None,
        certification_level: float = 1.0,
    ) -> bool:
        """Verify that a predicted ranking matches the actual ranking."""

        predicted = np.asarray(predicted_rank)
        actual = predicted if actual_rank is None else np.asarray(actual_rank)
        if predicted.shape != actual.shape:
            self.certification_level = 0.0
            return False

        matches = predicted == actual
        self.certified_pairs = int(np.count_nonzero(matches))
        self.certification_level = float(np.mean(matches)) if matches.size else 1.0
        return self.certification_level >= certification_level

    def certify_pair(
        self,
        path1: np.ndarray,
        path2: np.ndarray,
        g4_1: float,
        g4_2: float,
        error_scale: float = 1.0,
    ) -> bool:
        """Certify a pairwise ordering when the G4 gap exceeds both bounds."""

        bound = self.compute_remainder_bound(path1, error_scale)
        bound += self.compute_remainder_bound(path2, error_scale)
        certified = abs(float(g4_1) - float(g4_2)) > bound
        if certified:
            self.certified_pairs += 1
        return bool(certified)
