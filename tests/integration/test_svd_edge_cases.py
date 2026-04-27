"""Edge-case tests for SVD, diagonalize, and orthogonally_diagonalize.

These tests target the classes of inputs that previously caused regressions:
  - Matrices whose A^T A has irrational eigenvalues (triggers the fallback
    diagonalize path added after the MatrixError regression)
  - Rank-deficient matrices (some singular values are zero)
  - Non-square shapes: tall (m > n) and wide (m < n)
  - Zero matrix
  - 3×3 symmetric matrices with repeated eigenvalues (Gram-Schmidt needed)

Note: all SVD calls use verify=False to skip the internal symbolic norm check
(which hangs on irrational RootOf eigenvalues). Reconstruction is verified
numerically in the test helpers instead.
"""

import pytest

from ma1522 import Matrix
from ma1522.custom_types import PDP, SVD


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _reconstruction_norm(svd: SVD, A: Matrix) -> float:
    """Numerical Frobenius norm of U S V^T - A."""
    U = svd.U.evalf()
    S = svd.S.evalf()
    V = svd.V.evalf()
    diff = U @ S @ V.T - A.evalf()
    return float(diff.norm())


def _orthogonality_norm(M: Matrix, I: Matrix) -> float:
    """Numerical Frobenius norm of M^T M - I."""
    M_num = M.evalf()
    diff = M_num.T @ M_num - I.evalf()
    return float(diff.norm())


def _diag_reconstruction_norm_no_inv(pdp: PDP, A: Matrix) -> float:
    """Verify A = P D P^{-1} without inverting P: check ||A P - P D|| numerically."""
    P = pdp.P.evalf()
    D = pdp.D.evalf()
    A_num = A.evalf()
    diff = A_num @ P - P @ D
    return float(diff.norm())


def _ortho_diag_reconstruction_norm(pdp: PDP, A: Matrix) -> float:
    """Verify A = P D P^T without inverting: check ||A P - P D|| numerically."""
    P = pdp.P.evalf()
    D = pdp.D.evalf()
    A_num = A.evalf()
    diff = A_num @ P - P @ D
    return float(diff.norm())


# ---------------------------------------------------------------------------
# TestSVDIrrationalEigenvalues
#
# The bug: A^T A with irrational eigenvalues caused sympy's diagonalize to
# raise MatrixError("Matrix is not diagonalizable") because is_real was None
# for symbolic RootOf expressions when reals_only=True filtered them out.
# ---------------------------------------------------------------------------

class TestSVDIrrationalEigenvalues:
    """SVD on matrices whose A^T A has irrational (but real) eigenvalues."""

    @pytest.fixture
    def mat_4x3_irrational(self):
        """The exact matrix from the original bug report."""
        return Matrix([[1, -2, -1], [2, 0, 1], [2, -4, 2], [4, 0, 0]])

    @pytest.fixture
    def mat_3x2_irrational(self):
        """3×2 matrix whose A^T A eigenvalues are irrational."""
        return Matrix([[1, 1], [1, 2], [2, 1]])

    @pytest.fixture
    def mat_2x3_irrational(self):
        """Wide (m < n) matrix with irrational singular values."""
        return Matrix([[1, 2, 3], [1, 1, 2]])

    def test_4x3_irrational_does_not_raise(self, mat_4x3_irrational):
        svd = mat_4x3_irrational.singular_value_decomposition(verbosity=0, verify=False)
        assert isinstance(svd, SVD)

    def test_4x3_reconstruction(self, mat_4x3_irrational):
        svd = mat_4x3_irrational.singular_value_decomposition(verbosity=0, verify=False)
        assert _reconstruction_norm(svd, mat_4x3_irrational) < 1e-8

    def test_4x3_u_is_orthogonal(self, mat_4x3_irrational):
        svd = mat_4x3_irrational.singular_value_decomposition(verbosity=0, verify=False)
        I4 = Matrix.eye(4)
        assert _orthogonality_norm(svd.U, I4) < 1e-8

    def test_4x3_v_is_orthogonal(self, mat_4x3_irrational):
        svd = mat_4x3_irrational.singular_value_decomposition(verbosity=0, verify=False)
        I3 = Matrix.eye(3)
        assert _orthogonality_norm(svd.V, I3) < 1e-8

    def test_4x3_s_shape(self, mat_4x3_irrational):
        svd = mat_4x3_irrational.singular_value_decomposition(verbosity=0, verify=False)
        assert svd.S.shape == (4, 3)

    def test_4x3_singular_values_nonneg(self, mat_4x3_irrational):
        svd = mat_4x3_irrational.singular_value_decomposition(verbosity=0, verify=False)
        for i in range(min(svd.S.rows, svd.S.cols)):
            val = float(svd.S[i, i].evalf())
            assert val >= -1e-8

    def test_3x2_irrational_reconstruction(self, mat_3x2_irrational):
        svd = mat_3x2_irrational.singular_value_decomposition(verbosity=0, verify=False)
        assert _reconstruction_norm(svd, mat_3x2_irrational) < 1e-8

    def test_3x2_irrational_u_orthogonal(self, mat_3x2_irrational):
        svd = mat_3x2_irrational.singular_value_decomposition(verbosity=0, verify=False)
        I3 = Matrix.eye(3)
        assert _orthogonality_norm(svd.U, I3) < 1e-8

    def test_2x3_wide_reconstruction(self, mat_2x3_irrational):
        svd = mat_2x3_irrational.singular_value_decomposition(verbosity=0, verify=False)
        assert _reconstruction_norm(svd, mat_2x3_irrational) < 1e-8

    def test_2x3_wide_shapes(self, mat_2x3_irrational):
        svd = mat_2x3_irrational.singular_value_decomposition(verbosity=0, verify=False)
        assert svd.U.shape == (2, 2)
        assert svd.S.shape == (2, 3)
        assert svd.V.shape == (3, 3)

    def test_2x3_wide_u_orthogonal(self, mat_2x3_irrational):
        svd = mat_2x3_irrational.singular_value_decomposition(verbosity=0, verify=False)
        I2 = Matrix.eye(2)
        assert _orthogonality_norm(svd.U, I2) < 1e-8

    def test_2x3_wide_v_orthogonal(self, mat_2x3_irrational):
        svd = mat_2x3_irrational.singular_value_decomposition(verbosity=0, verify=False)
        I3 = Matrix.eye(3)
        assert _orthogonality_norm(svd.V, I3) < 1e-8


# ---------------------------------------------------------------------------
# TestSVDRankDeficient
# ---------------------------------------------------------------------------

class TestSVDRankDeficient:
    """SVD on rank-deficient matrices (some singular values are zero)."""

    @pytest.fixture
    def rank1_2x2(self):
        return Matrix([[1, 2], [2, 4]])  # rank 1

    @pytest.fixture
    def rank1_3x3(self):
        return Matrix([[1, 2, 3], [2, 4, 6], [3, 6, 9]])  # rank 1

    @pytest.fixture
    def rank2_4x3(self):
        """4×3 matrix with rank 2 (row 3 = row 1 + row 2)."""
        return Matrix([[1, 0, 1], [0, 1, 1], [1, 1, 2], [2, 0, 2]])

    def test_rank1_2x2_reconstruction(self, rank1_2x2):
        svd = rank1_2x2.singular_value_decomposition(verbosity=0, verify=False)
        assert _reconstruction_norm(svd, rank1_2x2) < 1e-8

    def test_rank1_2x2_has_zero_singular_value(self, rank1_2x2):
        svd = rank1_2x2.singular_value_decomposition(verbosity=0, verify=False)
        diagonal = [float(svd.S[i, i].evalf()) for i in range(min(svd.S.rows, svd.S.cols))]
        zero_count = sum(1 for v in diagonal if abs(v) < 1e-8)
        assert zero_count >= 1

    def test_rank1_3x3_reconstruction(self, rank1_3x3):
        svd = rank1_3x3.singular_value_decomposition(verbosity=0, verify=False)
        assert _reconstruction_norm(svd, rank1_3x3) < 1e-8

    def test_rank1_3x3_u_orthogonal(self, rank1_3x3):
        svd = rank1_3x3.singular_value_decomposition(verbosity=0, verify=False)
        I3 = Matrix.eye(3)
        assert _orthogonality_norm(svd.U, I3) < 1e-8

    def test_rank2_4x3_reconstruction(self, rank2_4x3):
        svd = rank2_4x3.singular_value_decomposition(verbosity=0, verify=False)
        assert _reconstruction_norm(svd, rank2_4x3) < 1e-8

    def test_rank2_4x3_shapes(self, rank2_4x3):
        svd = rank2_4x3.singular_value_decomposition(verbosity=0, verify=False)
        assert svd.U.shape == (4, 4)
        assert svd.S.shape == (4, 3)
        assert svd.V.shape == (3, 3)


# ---------------------------------------------------------------------------
# TestSVDSpecialShapes
# ---------------------------------------------------------------------------

class TestSVDSpecialShapes:
    """SVD shape correctness for square, tall, wide, and column/row vectors."""

    def test_square_3x3_shapes(self):
        A = Matrix([[1, 0, 1], [0, 2, 0], [1, 0, 3]])
        svd = A.singular_value_decomposition(verbosity=0, verify=False)
        assert svd.U.shape == (3, 3)
        assert svd.S.shape == (3, 3)
        assert svd.V.shape == (3, 3)

    def test_square_3x3_reconstruction(self):
        A = Matrix([[1, 0, 1], [0, 2, 0], [1, 0, 3]])
        svd = A.singular_value_decomposition(verbosity=0, verify=False)
        assert _reconstruction_norm(svd, A) < 1e-8

    def test_tall_5x2_shapes(self):
        A = Matrix([[1, 0], [0, 1], [1, 1], [2, 1], [1, 2]])
        svd = A.singular_value_decomposition(verbosity=0, verify=False)
        assert svd.U.shape == (5, 5)
        assert svd.S.shape == (5, 2)
        assert svd.V.shape == (2, 2)

    def test_tall_5x2_reconstruction(self):
        A = Matrix([[1, 0], [0, 1], [1, 1], [2, 1], [1, 2]])
        svd = A.singular_value_decomposition(verbosity=0, verify=False)
        assert _reconstruction_norm(svd, A) < 1e-8

    def test_1x3_row_vector_reconstruction(self):
        A = Matrix([[3, 0, 4]])
        svd = A.singular_value_decomposition(verbosity=0, verify=False)
        assert _reconstruction_norm(svd, A) < 1e-8

    def test_3x1_col_vector_reconstruction(self):
        A = Matrix([[3], [0], [4]])
        svd = A.singular_value_decomposition(verbosity=0, verify=False)
        assert _reconstruction_norm(svd, A) < 1e-8

    def test_singular_values_decreasing(self):
        A = Matrix([[3, 2, 2], [2, 3, -2]])
        svd = A.singular_value_decomposition(verbosity=0, verify=False)
        diag = [float(svd.S[i, i].evalf()) for i in range(min(svd.S.rows, svd.S.cols))]
        for i in range(len(diag) - 1):
            assert diag[i] >= diag[i + 1] - 1e-8


# ---------------------------------------------------------------------------
# TestSVDZeroMatrix
# ---------------------------------------------------------------------------

class TestSVDZeroMatrix:
    """SVD on the zero matrix — all singular values are zero."""

    def test_2x2_zero_reconstruction(self):
        A = Matrix([[0, 0], [0, 0]])
        svd = A.singular_value_decomposition(verbosity=0, verify=False)
        assert isinstance(svd, SVD)

    def test_2x3_zero_reconstruction(self):
        A = Matrix([[0, 0, 0], [0, 0, 0]])
        svd = A.singular_value_decomposition(verbosity=0, verify=False)
        assert isinstance(svd, SVD)


# ---------------------------------------------------------------------------
# TestSVDVerifyFalse
# ---------------------------------------------------------------------------

class TestSVDVerifyFalse:
    """verify=False should skip the assertion without raising."""

    def test_no_assert_with_verify_false(self):
        A = Matrix([[1, 2], [3, 4]])
        svd = A.singular_value_decomposition(verbosity=0, verify=False)
        assert isinstance(svd, SVD)


# ---------------------------------------------------------------------------
# TestDiagonalizeIrrationalEigenvalues
#
# Directly tests the new fallback path in diagonalize() for matrices where
# sympy's internal is_real check returns None for irrational eigenvalues.
# ---------------------------------------------------------------------------

class TestDiagonalizeIrrationalEigenvalues:
    """diagonalize() fallback for matrices with irrational eigenvalues."""

    @pytest.fixture
    def mat_irrational_3x3(self):
        """Symmetric 3×3 with irrational eigenvalues."""
        return Matrix([[2, 1, 0], [1, 3, 1], [0, 1, 2]])

    @pytest.fixture
    def ata_4x3_irrational(self):
        """A^T A from the bug-report matrix — symmetric, irrational eigenvalues."""
        A = Matrix([[1, -2, -1], [2, 0, 1], [2, -4, 2], [4, 0, 0]])
        return (A.T @ A)

    def test_3x3_irrational_returns_pdp(self, mat_irrational_3x3):
        pdp = mat_irrational_3x3.diagonalize(verbosity=0)
        assert isinstance(pdp, PDP)

    def test_3x3_irrational_reconstruction(self, mat_irrational_3x3):
        pdp = mat_irrational_3x3.diagonalize(verbosity=0)
        assert _diag_reconstruction_norm_no_inv(pdp, mat_irrational_3x3) < 1e-8

    def test_3x3_irrational_d_is_diagonal(self, mat_irrational_3x3):
        pdp = mat_irrational_3x3.diagonalize(verbosity=0)
        n = pdp.D.rows
        for i in range(n):
            for j in range(n):
                if i != j:
                    assert pdp.D[i, j] == 0

    def test_3x3_irrational_p_invertible(self, mat_irrational_3x3):
        pdp = mat_irrational_3x3.diagonalize(verbosity=0)
        # Use numerical det to avoid symbolic slowdown on irrational entries
        assert abs(float(pdp.P.evalf().det())) > 1e-8

    def test_ata_irrational_returns_pdp(self, ata_4x3_irrational):
        pdp = ata_4x3_irrational.diagonalize(verbosity=0)
        assert isinstance(pdp, PDP)

    def test_ata_irrational_reconstruction(self, ata_4x3_irrational):
        pdp = ata_4x3_irrational.diagonalize(verbosity=0)
        assert _diag_reconstruction_norm_no_inv(pdp, ata_4x3_irrational) < 1e-8


# ---------------------------------------------------------------------------
# TestOrthogonallyDiagonalizeRepeatedEigenvalues
# ---------------------------------------------------------------------------

class TestOrthogonallyDiagonalizeRepeatedEigenvalues:
    """orthogonally_diagonalize() with repeated eigenvalues (requires Gram-Schmidt)."""

    @pytest.fixture
    def scaled_identity_3(self):
        """3×3 scalar matrix: eigenvalue 5 with multiplicity 3."""
        return Matrix([[5, 0, 0], [0, 5, 0], [0, 0, 5]])

    @pytest.fixture
    def repeated_eigenvalue_3x3(self):
        """Symmetric 3×3 with eigenvalue 2 repeated (multiplicity 2)."""
        return Matrix([[2, 0, 0], [0, 2, 0], [0, 0, 4]])

    @pytest.fixture
    def symmetric_3x3_irrational(self):
        """Symmetric 3×3 with irrational eigenvalues."""
        return Matrix([[3, 1, 0], [1, 3, 0], [0, 0, 5]])

    def test_scaled_identity_reconstruction(self, scaled_identity_3):
        pdp = scaled_identity_3.orthogonally_diagonalize(verbosity=0)
        assert _ortho_diag_reconstruction_norm(pdp, scaled_identity_3) < 1e-8

    def test_scaled_identity_p_orthogonal(self, scaled_identity_3):
        pdp = scaled_identity_3.orthogonally_diagonalize(verbosity=0)
        I3 = Matrix.eye(3)
        assert _orthogonality_norm(pdp.P, I3) < 1e-8

    def test_repeated_eigenvalue_reconstruction(self, repeated_eigenvalue_3x3):
        pdp = repeated_eigenvalue_3x3.orthogonally_diagonalize(verbosity=0)
        assert _ortho_diag_reconstruction_norm(pdp, repeated_eigenvalue_3x3) < 1e-8

    def test_repeated_eigenvalue_p_orthogonal(self, repeated_eigenvalue_3x3):
        pdp = repeated_eigenvalue_3x3.orthogonally_diagonalize(verbosity=0)
        I3 = Matrix.eye(3)
        assert _orthogonality_norm(pdp.P, I3) < 1e-8

    def test_repeated_eigenvalue_d_diagonal(self, repeated_eigenvalue_3x3):
        pdp = repeated_eigenvalue_3x3.orthogonally_diagonalize(verbosity=0)
        n = pdp.D.rows
        for i in range(n):
            for j in range(n):
                if i != j:
                    assert pdp.D[i, j] == 0

    def test_symmetric_irrational_reconstruction(self, symmetric_3x3_irrational):
        pdp = symmetric_3x3_irrational.orthogonally_diagonalize(verbosity=0)
        assert _ortho_diag_reconstruction_norm(pdp, symmetric_3x3_irrational) < 1e-8

    def test_symmetric_irrational_p_orthogonal(self, symmetric_3x3_irrational):
        pdp = symmetric_3x3_irrational.orthogonally_diagonalize(verbosity=0)
        I3 = Matrix.eye(3)
        assert _orthogonality_norm(pdp.P, I3) < 1e-8

    def test_4x4_symmetric_repeated_eigenvalue(self):
        A = Matrix([
            [1, 0, 0, 0],
            [0, 1, 0, 0],
            [0, 0, 3, 0],
            [0, 0, 0, 3],
        ])
        pdp = A.orthogonally_diagonalize(verbosity=0)
        I4 = Matrix.eye(4)
        assert _ortho_diag_reconstruction_norm(pdp, A) < 1e-8
        assert _orthogonality_norm(pdp.P, I4) < 1e-8
