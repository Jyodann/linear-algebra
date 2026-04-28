"""Tests for miscellaneous Matrix methods with no existing coverage.

Covers:
- sep_unk
- H property (Hermitian transpose)
- adjoint() deprecation warning / adj()
- inverse(matrices=2)
- solve_least_squares(matrices=2)
- get_linearly_independent_vectors
- is_linearly_independent(colspace=False)
- cramer_solve
- is_same_subspace(other=None)
- find_all_cases
"""

import pytest
import sympy as sym

from ma1522 import Matrix, PartGen


# ---------------------------------------------------------------------------
# sep_unk
# ---------------------------------------------------------------------------

class TestSepUnk:
    def test_single_symbol(self):
        a = sym.Symbol("a", real=True)
        mat = Matrix([[a, 2 * a]])
        result = mat.sep_unk()
        assert a in result
        assert result[a] == Matrix([[1, 2]])

    def test_two_symbols(self):
        a, b = sym.symbols("a b", real=True)
        mat = Matrix([[a + b], [a - b]])
        result = mat.sep_unk()
        assert a in result
        assert b in result
        assert result[a] == Matrix([[1], [1]])
        assert result[b] == Matrix([[1], [-1]])

    def test_reconstruction(self, a, b):
        mat = Matrix([[2 * a + 3 * b], [a]])
        result = mat.sep_unk()
        items = list(result.items())
        reconstructed = items[0][0] * items[0][1]
        for k, v in items[1:]:
            reconstructed = reconstructed + k * v
        diff = sym.simplify((reconstructed - mat).norm())
        assert diff == 0

    def test_no_free_symbols_returns_empty(self, mat_2x2):
        result = mat_2x2.sep_unk()
        assert len(result) == 0


# ---------------------------------------------------------------------------
# H property (Hermitian / conjugate transpose)
# ---------------------------------------------------------------------------

class TestHermitianTranspose:
    def test_real_matrix_h_equals_t(self, mat_2x2):
        assert mat_2x2.H == mat_2x2.T

    def test_complex_matrix_conjugate(self):
        i = sym.I
        mat = Matrix([[1 + i, 2], [3, 4 - i]])
        H = mat.H
        assert H[0, 0] == 1 - i
        assert H[1, 1] == 4 + i

    def test_h_returns_matrix_instance(self, mat_2x2):
        assert isinstance(mat_2x2.H, Matrix)

    def test_h_shape(self):
        mat = Matrix([[1, 2, 3], [4, 5, 6]])  # 2x3
        assert mat.H.shape == (3, 2)


# ---------------------------------------------------------------------------
# adj() and adjoint() deprecation
# ---------------------------------------------------------------------------

class TestAdjAndAdjoint:
    def test_adj_2x2(self, mat_2x2):
        result = mat_2x2.adj()
        assert result == Matrix([[4, -2], [-3, 1]])

    def test_adj_property(self, mat_2x2, identity_2):
        adj = mat_2x2.adj()
        det = mat_2x2.det()
        assert (mat_2x2 @ adj - det * identity_2).norm() == 0

    def test_adjoint_raises_deprecation(self, mat_2x2):
        with pytest.warns(DeprecationWarning):
            result = mat_2x2.adjoint()
        assert result == mat_2x2.adj()

    def test_adj_3x3(self, identity_3):
        mat = Matrix([[1, 2, 3], [0, 1, 4], [5, 6, 0]])
        adj = mat.adj()
        det = mat.det()
        assert sym.simplify((mat @ adj - det * identity_3).norm()) == 0


# ---------------------------------------------------------------------------
# inverse(matrices=2)
# ---------------------------------------------------------------------------

class TestInverseMatrices2:
    def test_square_returns_partgen(self, mat_2x2):
        result = mat_2x2.inverse(matrices=2, verbosity=0)
        assert isinstance(result, PartGen)

    def test_square_partgen_eval_is_inverse(self, mat_2x2, identity_2):
        pg = mat_2x2.inverse(matrices=2, verbosity=0)
        inv = pg.eval()
        diff = sym.simplify((mat_2x2 @ inv - identity_2).norm())
        assert diff == 0

    def test_left_inverse_matrices_2(self):
        A = Matrix([[1, 0], [0, 1], [1, 1]])
        result = A.inverse(option="left", matrices=2, verbosity=0)
        assert isinstance(result, PartGen)


# ---------------------------------------------------------------------------
# solve_least_squares(matrices=2)
# ---------------------------------------------------------------------------

class TestSolveLeastSquaresMatrices2:
    def test_returns_partgen_rank_deficient(self):
        # ATA singular → sympy's solve_least_squares raises → falls to custom path
        A = Matrix([[1, 0], [0, 0]])
        b = Matrix([[1], [2]])
        result = A.solve_least_squares(b, verbosity=0, matrices=2)
        assert isinstance(result, PartGen)

    def test_partgen_particular_satisfies_normal_equations(self):
        # ATA singular → custom path → matrices=2 returns PartGen
        A = Matrix([[1, 0], [0, 0]])
        b = Matrix([[1], [2]])
        pg = A.solve_least_squares(b, verbosity=0, matrices=2)
        x_part = pg.part_sol
        # Particular solution satisfies the normal equations: A^T A x = A^T b
        residual = A.T @ A @ x_part - A.T @ b
        assert sym.simplify(residual.norm()) == 0


# ---------------------------------------------------------------------------
# get_linearly_independent_vectors
# ---------------------------------------------------------------------------

class TestGetLinearlyIndependentVectors:
    def test_colspace_full_rank(self, identity_2):
        result = identity_2.get_linearly_independent_vectors(colspace=True, verbosity=0)
        assert result.cols == 2

    def test_colspace_rank_deficient(self, singular_2x2):
        result = singular_2x2.get_linearly_independent_vectors(colspace=True, verbosity=0)
        assert result.cols == 1

    def test_rowspace(self):
        mat = Matrix([[1, 2, 3], [2, 4, 6], [0, 0, 1]])
        result = mat.get_linearly_independent_vectors(colspace=False, verbosity=0)
        assert result.rows == 2

    def test_colspace_returns_columns_from_original(self):
        mat = Matrix([[1, 2, 1], [0, 0, 1]])
        result = mat.get_linearly_independent_vectors(colspace=True, verbosity=0)
        assert result.cols >= 1


# ---------------------------------------------------------------------------
# is_linearly_independent(colspace=False)
# ---------------------------------------------------------------------------

class TestIsLinearlyIndependentRowspace:
    def test_identity_rows_independent(self, identity_2):
        assert identity_2.is_linearly_independent(colspace=False) is True

    def test_dependent_rows(self, singular_2x2):
        assert singular_2x2.is_linearly_independent(colspace=False) is False

    def test_3_independent_rows(self, identity_3):
        assert identity_3.is_linearly_independent(colspace=False) is True


# ---------------------------------------------------------------------------
# cramer_solve
# ---------------------------------------------------------------------------

class TestCramerSolve:
    def test_2x2_unique_solution(self):
        A = Matrix([[2, 1], [1, 3]])
        b = Matrix([[5], [10]])
        x = A.cramer_solve(b, verbosity=0)
        residual = A @ x - b
        assert residual.norm() == 0

    def test_known_values(self, mat_2x2):
        b = Matrix([[5], [11]])
        x = mat_2x2.cramer_solve(b, verbosity=0)
        assert x[0, 0] == 1
        assert x[1, 0] == 2

    def test_3x3(self):
        A = Matrix([[3, 2, -4], [2, 3, 3], [5, -3, 1]])
        b = Matrix([[3], [15], [14]])
        x = A.cramer_solve(b, verbosity=0)
        assert x[0, 0] == 3
        assert x[1, 0] == 1
        assert x[2, 0] == 2

    def test_singular_raises(self, singular_2x2):
        b = Matrix([[1], [2]])
        with pytest.raises(ValueError):
            singular_2x2.cramer_solve(b, verbosity=0)

    def test_non_square_raises(self):
        A = Matrix([[1, 2, 3], [4, 5, 6]])
        b = Matrix([[1], [2]])
        with pytest.raises(sym.NonSquareMatrixError):
            A.cramer_solve(b, verbosity=0)

    def test_rhs_wrong_rows_raises(self, mat_2x2):
        b = Matrix([[1], [2], [3]])
        with pytest.raises(sym.ShapeError):
            mat_2x2.cramer_solve(b, verbosity=0)

    def test_rhs_not_column_vector_raises(self, mat_2x2):
        b = Matrix([[1, 2], [3, 4]])
        with pytest.raises(sym.ShapeError):
            mat_2x2.cramer_solve(b, verbosity=0)


# ---------------------------------------------------------------------------
# is_same_subspace(other=None)
# ---------------------------------------------------------------------------

class TestIsSameSubspaceNone:
    def test_full_rank_spans_space(self, identity_2):
        assert identity_2.is_same_subspace(other=None, verbosity=0) is True

    def test_single_vector_does_not_span_R2(self):
        mat = Matrix([[1], [0]])
        assert mat.is_same_subspace(other=None, verbosity=0) is False

    def test_square_with_zero_row_does_not_span(self):
        mat = Matrix([[1, 0], [0, 0]])
        assert mat.is_same_subspace(other=None, verbosity=0) is False


# ---------------------------------------------------------------------------
# find_all_cases
# ---------------------------------------------------------------------------

class TestFindAllCases:
    def test_numeric_matrix_returns_empty(self, mat_2x2):
        cases = mat_2x2.find_all_cases()
        assert cases == []

    def test_symbolic_matrix_returns_cases(self):
        x = sym.Symbol("x", real=True)
        mat = Matrix([[x, 1], [0, 1]])
        cases = mat.find_all_cases()
        assert len(cases) >= 1
        has_zero_case = any(c.get(x) == 0 for c in cases)
        assert has_zero_case

    def test_identity_returns_empty(self, identity_2):
        cases = identity_2.find_all_cases()
        assert cases == []
