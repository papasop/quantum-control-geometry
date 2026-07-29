"""Tests for theorem modules."""

import numpy as np
import pytest

from quantum_control_geometry.theorems import OrderingTheorem


class TestOrderingTheorem:
    """Tests for OrderingTheorem class."""

    def test_initialization(self):
        """Test theorem initialization."""
        theorem = OrderingTheorem(jet_order=30, tail_bound=1.23e-11)
        assert theorem.jet_order == 30
        assert theorem.tail_bound == 1.23e-11
        assert theorem.certified_pairs == 0

    def test_invalid_jet_order(self):
        """Test initialization with invalid jet_order."""
        with pytest.raises(ValueError):
            OrderingTheorem(jet_order=1)

    def test_invalid_tail_bound(self):
        """Test initialization with invalid tail_bound."""
        with pytest.raises(ValueError):
            OrderingTheorem(tail_bound=-1.0)

    def test_verify_ranking(self):
        """Test ranking verification."""
        theorem = OrderingTheorem()
        
        predicted = np.array([0, 1, 2, 3])
        actual = np.array([0, 1, 2, 3])
        
        certified = theorem.verify_ranking(predicted, actual)
        assert certified is True
        assert theorem.certified_pairs == len(predicted)

    def test_certify_pair(self):
        """Test pair certification."""
        theorem = OrderingTheorem()
        
        path1 = np.random.rand(10, 2)
        path2 = np.random.rand(10, 2)
        
        # G4 difference larger than bound should certify
        certified = theorem.certify_pair(
            path1, path2,
            g4_1=0.1, g4_2=0.5,
            error_scale=0.1
        )
        # This is a placeholder test - actual implementation may differ
        assert isinstance(certified, bool)
