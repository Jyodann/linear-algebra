"""Regression tests for bugs found during code review.

Each test is tied to a specific fix so regressions are caught immediately.
"""

import pytest
import sympy as sym
import warnings

from ma1522 import Matrix
from ma1522.custom_types import QR, SVD, NumSVD


# ---------------------------------------------------------------------------
# from_list must not mutate the caller's list
# ---------------------------------------------------------------------------

class TestFromListNoMutation:
    def test_does_not_pop_from_input(self):
        vecs = [Matrix([[1], [0]]), Matrix([[0], [1]])]
        original_len = len(vecs)
        Matrix.from_list(vecs, row_join=True)
        assert len(vecs) == original_len, "from_list must not mutate the input list"

    def test_result_correct_after_non_mutation(self):
        vecs = [Matrix([[1], [2]]), Matrix([[3], [4]])]
        result = Matrix.from_list(vecs, row_join=True)
        assert result == Matrix([[1, 3], [2, 4]])
        assert len(vecs) == 2


# ---------------------------------------------------------------------------
# is_mat_orthogonal: is_diagonal() must be called as a method
# ---------------------------------------------------------------------------

class TestIsMatOrthogonal:
    def test_identity_is_orthogonal(self, identity_2):
        assert identity_2.is_mat_orthogonal(verbosity=0) is True

    def test_identity_3x3_is_orthogonal(self, identity_3):
        assert identity_3.is_mat_orthogonal(verbosity=0) is True

    def test_rotation_90_is_orthogonal(self):
        mat = Matrix([[0, -1], [1, 0]])
        assert mat.is_mat_orthogonal(verbosity=0) is True

    def test_scaled_identity_is_not_orthogonal(self):
        mat = Matrix([[2, 0], [0, 2]])
        assert mat.is_mat_orthogonal(verbosity=0) is False

    def test_upper_triangular_is_not_orthogonal(self):
        # [[1,1],[0,1]] — was incorrectly passing before the is_diagonal() fix
        mat = Matrix([[1, 1], [0, 1]])
        assert mat.is_mat_orthogonal(verbosity=0) is False

    def test_non_diagonal_symmetric_is_not_orthogonal(self):
        mat = Matrix([[1, 1], [1, 1]])
        assert mat.is_mat_orthogonal(verbosity=0) is False


# ---------------------------------------------------------------------------
# is_subspace_of: empty pivots must not crash
# ---------------------------------------------------------------------------

class TestIsSubspaceOfEdgeCases:
    def test_zero_matrix_is_subspace_of_identity(self):
        zero = Matrix([[0], [0]])
        span = Matrix.eye(2)
        assert zero.is_subspace_of(span, verbosity=0) is True

    def test_column_subspace(self):
        sub = Matrix([[1], [0]])
        full = Matrix.eye(2)
        assert sub.is_subspace_of(full, verbosity=0) is True

    def test_not_subspace(self):
        A = Matrix([[1, 0], [0, 1]])
        B = Matrix([[1, 0], [0, 0]])
        # span of A is all of R^2; span of B is only x-axis
        assert not A.is_subspace_of(B, verbosity=0)


# ---------------------------------------------------------------------------
# apply_vander: next(iter()) is deterministic, does not mutate free_symbols
# ---------------------------------------------------------------------------

class TestApplyVander:
    def test_basic_substitution(self):
        # create_vander(3, 3) gives a 3×3 Vandermonde with symbols x_1, x_2, x_3
        V = Matrix.create_vander(3, 3)
        x_vec = Matrix([[2], [3], [5]])
        result = V.apply_vander(x_vec)
        assert result.free_symbols == set()

    def test_correct_values(self):
        V = Matrix.create_vander(2, 3)
        x_vec = Matrix([[2], [3]])
        result = V.apply_vander(x_vec)
        # Row i of Vandermonde: [1, x_i, x_i^2]
        assert result[0, 1] == 2
        assert result[1, 1] == 3
        assert result[0, 2] == 4
        assert result[1, 2] == 9

    def test_free_symbols_not_mutated(self):
        V = Matrix.create_vander(3, 3)
        syms_before = frozenset(V.free_symbols)
        x_vec = Matrix([[2], [3], [5]])
        V.apply_vander(x_vec)
        assert frozenset(V.free_symbols) == syms_before


# ---------------------------------------------------------------------------
# fast_svd: tol=None must not raise TypeError
# ---------------------------------------------------------------------------

class TestFastSvdTolNone:
    def test_sym_identify_tol_none_does_not_crash(self):
        A = Matrix([[1, 0], [0, 2]])
        # tol defaults to None; identify=True triggers the comparison — must not raise
        result = A.fast_svd(option="sym", identify=True, tol=None)
        assert isinstance(result, SVD)

    def test_sym_no_identify_returns_svd(self):
        A = Matrix([[3, 0], [0, 4]])
        result = A.fast_svd(option="sym", identify=False)
        assert isinstance(result, SVD)

    def test_invalid_option_returns_numsvd_with_warning(self):
        A = Matrix([[1, 0], [0, 1]])
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = A.fast_svd(option="bad_option")
        assert isinstance(result, NumSVD)
        assert any(issubclass(warning.category, SyntaxWarning) for warning in w)


# ---------------------------------------------------------------------------
# transition_matrix: must use to.cols, not self.cols, for slice boundary
# ---------------------------------------------------------------------------

class TestTransitionMatrix:
    def test_square_same_size(self):
        B1 = Matrix([[1, 0], [0, 1]])
        B2 = Matrix([[1, 1], [0, 1]])
        P = B1.transition_matrix(B2, verbosity=0)
        # B1 * P should equal B2 (up to simplification)
        assert P.shape == (2, 2)

    def test_transition_reconstructs_basis(self):
        B_from = Matrix([[1, 1], [0, 1]])
        B_to = Matrix([[1, 0], [0, 1]])
        P = B_from.transition_matrix(B_to, verbosity=0)
        # Verify: to @ P == from
        diff = (B_to @ P - B_from).applyfunc(sym.simplify)
        assert diff == Matrix([[0, 0], [0, 0]])


# ---------------------------------------------------------------------------
# solve_least_squares: IndexError guard on empty solve result
# ---------------------------------------------------------------------------

class TestSolveLeastSquaresConsistency:
    def test_overdetermined_invertible_ata(self):
        A = Matrix([[1, 0], [0, 1], [1, 1]])
        b = Matrix([[1], [2], [3]])
        x = A.solve_least_squares(b, verbosity=0)
        # Normal equations: A^T A x = A^T b
        residual = A.T @ A @ x - A.T @ b
        assert sym.simplify(residual.norm()) == 0

    def test_verbosity1_invertible_ata_returns_solution(self):
        A = Matrix([[2, 1], [0, 1], [1, 0]])
        b = Matrix([[1], [2], [3]])
        x = A.solve_least_squares(b, verbosity=1)
        assert isinstance(x, Matrix)
        residual = A.T @ A @ x - A.T @ b
        assert sym.simplify(residual.norm()) == 0


# ---------------------------------------------------------------------------
# gram_schmidt: LaTeX coefficients use original vector (classical GS)
# ---------------------------------------------------------------------------

class TestGramSchmidtEdgeCases:
    def test_empty_matrix_returns_empty(self):
        mat = Matrix([]).reshape(3, 0)
        result = mat.gram_schmidt(verbosity=0)
        assert isinstance(result, Matrix)
        assert result.cols == 0

    def test_orthogonal_input_unchanged(self):
        mat = Matrix([[1, 0], [0, 1], [0, 0]])
        # factor=False ensures Matrix return, not ScalarFactor
        result = mat.gram_schmidt(factor=False, verbosity=0)
        assert isinstance(result, Matrix)
        assert result.cols == 2
        assert sym.simplify(result.select_cols(0).dot(result.select_cols(1))) == 0

    def test_produces_orthogonal_set(self):
        mat = Matrix([[1, 1], [1, 0], [0, 1]])
        result = mat.gram_schmidt(factor=False, verbosity=0)
        assert isinstance(result, Matrix)
        c0 = result.select_cols(0)
        c1 = result.select_cols(1)
        assert sym.simplify(c0.dot(c1)) == 0

    def test_linearly_dependent_vectors_warns(self):
        mat = Matrix([[1, 2], [1, 2]])
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            mat.gram_schmidt(verbosity=1)
        assert any(issubclass(warning.category, UserWarning) for warning in w)


# ---------------------------------------------------------------------------
# scale_row: zero scalar triggers UserWarning
# ---------------------------------------------------------------------------

class TestScaleRowWarning:
    def test_zero_scalar_warns(self, mat_2x2):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            mat_2x2.scale_row(0, 0)
        assert any(issubclass(warning.category, UserWarning) for warning in w)


# ---------------------------------------------------------------------------
# normalized: zero-norm column is left unchanged (no division by zero)
# ---------------------------------------------------------------------------

class TestNormalizedZeroColumn:
    def test_zero_column_not_divided(self):
        mat = Matrix([[0, 1], [0, 0]])
        result = mat.normalized()
        assert isinstance(result, Matrix)
        # Zero column stays zero (no division by zero)
        assert result[0, 0] == 0
        assert result[1, 0] == 0
