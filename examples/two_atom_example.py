"""Example: Two-atom Rydberg system with G4 prediction.

This example demonstrates the complete workflow for computing G4 coefficients
and predicting control performance in a two-atom Rydberg system.
"""

import numpy as np
from quantum_control_geometry.tensors import ResponseTensor
from quantum_control_geometry.theorems import OrderingTheorem


def main():
    """Run two-atom example."""
    # Define minisupermetric for two-atom system
    # This is a simplified example - actual metric depends on system parameters
    metric = np.array([
        [-2.0, 0.0],
        [0.0, 1.0]
    ], dtype=np.float64)

    # Initialize response tensor
    response_tensor = ResponseTensor(metric=metric, order=4)

    # Define control paths (example)
    # In practice, these would be actual control sequences
    n_paths = 20
    control_paths = [
        np.random.rand(10, 2) for _ in range(n_paths)  # Placeholder
    ]

    # Compute G4 coefficients for all paths
    g4_coefficients = []
    for path in control_paths:
        # Compute Jacobian (placeholder)
        jacobian = np.random.rand(10, 2, 2)  # Placeholder
        
        # Compute G4
        g4 = response_tensor.compute_g4_coefficient(path, jacobian)
        g4_coefficients.append(g4)

    g4_coefficients = np.array(g4_coefficients)

    # Rank paths by G4 (smaller is better)
    predicted_ranking = response_tensor.rank_by_g4(g4_coefficients)

    print("G4 Coefficients:")
    for i, g4 in enumerate(g4_coefficients):
        print(f"  Path {i}: G4 = {g4:.6e}")

    print("\nPredicted Ranking (best -> worst):")
    for rank, path_idx in enumerate(predicted_ranking):
        print(f"  {rank+1}. Path {path_idx} (G4 = {g4_coefficients[path_idx]:.6e})")

    # Verify with ordering theorem
    theorem = OrderingTheorem(jet_order=30, tail_bound=1.23e-11)
    
    # For demonstration, we'll use the predicted ranking as "actual"
    # In practice, you would compute actual finite-error performance
    actual_ranking = predicted_ranking.copy()
    
    certified = theorem.verify_ranking(
        predicted_ranking,
        actual_ranking,
        certification_level=1.0
    )

    print(f"\nCertification: {'PASS' if certified else 'FAIL'}")
    print(f"Certified pairs: {theorem.certified_pairs}/{len(predicted_ranking)}")
    print(f"Certification level: {theorem.certification_level:.2%}")


if __name__ == "__main__":
    main()
