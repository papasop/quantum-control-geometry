"""Tests for tensor modules."""

import numpy as np
import pytest

from quantum_control_geometry.tensors import CovariantTensor, ResponseTensor


class TestCovariantTensor:
    """Tests for CovariantTensor class."""

    def test_initialization(self):
        """Test tensor initialization."""
        metric = np.eye(2)
        tensor = CovariantTensor(metric=metric, order=4)
        assert tensor.order == 4
        assert tensor.dim == 2
        assert tensor.components is None

    def test_invalid_metric(self):
        """Test initialization with invalid metric."""
        with pytest.raises(ValueError):
            CovariantTensor(metric=np.array([1, 2]), order=4)

    def test_invalid_order(self):
        """Test initialization with invalid order."""
        metric = np.eye(2)
        with pytest.raises(ValueError):
            CovariantTensor(metric=metric, order=1)


class TestResponseTensor:
    """Tests for ResponseTensor class."""

    def test_initialization(self):
        """Test response tensor initialization."""
        metric = np.eye(2)
        tensor = ResponseTensor(metric=metric, order=4)
        assert tensor.covariant_tensor is not None
        assert tensor.g4_coefficient is None

    def test_rank_by_g4(self):
        """Test ranking by G4 coefficient."""
        metric = np.eye(2)
        tensor = ResponseTensor(metric=metric, order=4)
        
        g4_coeffs = np.array([0.5, 0.1, 0.3, 0.2])
        ranking = tensor.rank_by_g4(g4_coeffs)
        
        # Should rank in ascending order: [1, 3, 2, 0]
        assert ranking[0] == 1  # Smallest G4
        assert ranking[-1] == 0  # Largest G4
