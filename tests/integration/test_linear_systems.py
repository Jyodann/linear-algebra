"""Integration tests for linear systems: ref, rref, solve, inverse, adj, elem,
column_constraints, evaluate_cases."""

import pytest
import sympy as sym

from ma1522 import Matrix, PartGen
from ma1522.custom_types import PLU, RREF


# ---------------------------------------------------------------------------
# TestRef
# ---------------------------------------------------------------------------

class TestRef:
    """Tests for Matrix.ref() — returns PLU dataclass."""

    def test_2x2_numeric_upper_triangular(self, mat_2x2):
        plu = mat_2x2.ref(verbosity=0)
        assert isinstance(plu, PLU)
        U = plu.U
        # Entry below the diagonal must be zero
        assert U[1, 0] == 0

    def test_2x2_numeric_exact_values(self, mat_2x2):
        plu = mat_2x2.ref(verbosity=0)
        U = plu.U
        assert U[0, 0] == 1
        assert U[0, 1] == 2

    def test_3x3_row_echelon(self, mat_3x3):
        plu = mat_3x3.ref(verbosity=0)
        U = plu.U
        # All entries strictly below the diagonal must be zero
        for i in range(U.rows):
            for j in range(i):
                assert U[i, j] == 0, f"U[{i},{j}] should be 0 in REF"

    def test_3x3_det_sign_preserved(self, mat_3x3):
        plu = mat_3x3.ref(verbosity=0)
        # det(A) == det(P) * det(L) * det(U); det(L)=1 always
        # Just confirm reconstruction is correct
        reconstructed = plu.P @ plu.L @ plu.U
        assert (reconstructed - mat_3x3).norm() == 0

    def test_singular_ref_has_zero_row(self, singular_2x2):
        plu = singular_2x2.ref(verbosity=0)
        U = plu.U
        # Last row should be all zeros for singular matrix
        assert all(U[U.rows - 1, j] == 0 for j in range(U.cols))

    def test_singular_ref_reconstruction(self, singular_2x2):
        plu = singular_2x2.ref(verbosity=0)
        reconstructed = plu.P @ plu.L @ plu.U
        assert (reconstructed - singular_2x2).norm() == 0

    def test_symbolic_entries_with_numeric_pivot(self, a, b):
        # Concrete numeric first row ensures elimination can proceed
        mat = Matrix([[1, a], [2, b]])
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            plu = mat.ref(verbosity=0)
        assert sym.simplify(plu.U[1, 0]) == 0


# ---------------------------------------------------------------------------
# TestRref
# ---------------------------------------------------------------------------

class TestRref:
    """Tests for Matrix.rref() — returns RREF dataclass or plain Matrix."""

    def test_invertible_rref_is_identity(self, mat_2x2):
        result = mat_2x2.rref()
        assert isinstance(result, RREF)
        assert result.rref == Matrix.eye(2)

    def test_invertible_pivot_count(self, mat_2x2):
        result = mat_2x2.rref()
        assert len(result.pivots) == 2
        assert result.pivots == (0, 1)

    def test_underdetermined_fewer_pivots(self, underdetermined):
        # 2x3 matrix — at most 2 pivots, fewer than 3 columns
        result = underdetermined.rref()
        assert isinstance(result, RREF)
        assert len(result.pivots) < underdetermined.cols

    def test_singular_pivot_count_less_than_rows(self, singular_2x2):
        result = singular_2x2.rref()
        assert isinstance(result, RREF)
        assert len(result.pivots) < singular_2x2.rows

    def test_pivots_false_returns_plain_matrix(self, mat_2x2):
        result = mat_2x2.rref(pivots=False)
        assert isinstance(result, Matrix)

    def test_symbolic_upper_triangular_form(self, a, c):
        import warnings
        mat = Matrix([[a, 2], [0, c]])
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            result = mat.rref(pivots=False)
        assert isinstance(result, Matrix)
        # Row 1, col 0 must be zero
        assert result[1, 0] == 0


# ---------------------------------------------------------------------------
# TestSolve
# ---------------------------------------------------------------------------

class TestSolve:
    """Tests for Matrix.solve(rhs) — returns list[Matrix]."""

    def test_unique_solution(self):
        A = Matrix([[2, 1], [1, 3]])
        b = Matrix([[5], [10]])
        sols = A.solve(b, verbosity=0)
        assert len(sols) == 1
        x = sols[0]
        residual = A @ x - b
        assert residual.norm() == 0

    def test_no_solution_raises(self, singular_2x2):
        b = Matrix([[1], [3]])  # inconsistent with singular matrix
        with pytest.raises(ValueError):
            singular_2x2.solve(b, verbosity=0)

    def test_infinite_solutions_has_free_symbols(self):
        # Under-determined: x + y = 1
        A = Matrix([[1, 1]])
        b = Matrix([[1]])
        sols = A.solve(b, verbosity=0)
        assert len(sols) >= 1
        # At least one entry should be symbolic (free variable)
        has_free = any(bool(sol.free_symbols) for sol in sols)
        assert has_free

    def test_symbolic_rhs(self, a, b):
        A = Matrix([[1, 1], [1, -1]])
        rhs = Matrix([[a], [b]])
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            sols = A.solve(rhs, verbosity=0)
        assert len(sols) >= 1
        x = sols[0]
        # x should contain a and b
        assert a in x.free_symbols or b in x.free_symbols

    def test_tutorial_case(self):
        mat = Matrix([[3, 2, -4], [2, 3, 3], [5, -3, 1]])
        rhs = Matrix([[3], [15], [14]])
        sols = mat.solve(rhs, verbosity=0)
        assert len(sols) == 1
        x = sols[0]
        assert x[0, 0] == 3
        assert x[1, 0] == 1
        assert x[2, 0] == 2


# ---------------------------------------------------------------------------
# TestInverse
# ---------------------------------------------------------------------------

class TestInverse:
    """Tests for Matrix.inverse()."""

    def test_square_invertible_left(self, mat_2x2, identity_2):
        inv = mat_2x2.inverse(verbosity=0)
        assert (inv @ mat_2x2 - identity_2).norm() == 0

    def test_square_invertible_right(self, mat_2x2, identity_2):
        inv = mat_2x2.inverse(verbosity=0)
        assert (mat_2x2 @ inv - identity_2).norm() == 0

    def test_singular_raises(self, singular_2x2):
        with pytest.raises((ValueError, Exception)):
            singular_2x2.inverse(verbosity=0)

    def test_left_inverse_tall_matrix(self, identity_2):
        # 3x2 tall matrix, full column rank → left inverse exists
        A = Matrix([[1, 0], [0, 1], [1, 1]])
        inv = A.inverse(option="left", verbosity=0)
        result = inv @ A
        assert (result - identity_2).norm() == 0

    def test_right_inverse_wide_matrix(self):
        # 2x3 wide matrix, full row rank → right inverse exists
        A = Matrix([[1, 0, 1], [0, 1, 1]])
        inv = A.inverse(option="right", verbosity=0)
        I2 = Matrix.eye(2)
        assert (A @ inv - I2).norm() == 0

    def test_1x1_matrix(self):
        mat = Matrix([[5]])
        inv = mat.inverse(verbosity=0)
        assert inv == Matrix([[sym.Rational(1, 5)]])

    def test_symbolic_2x2_identity(self, b):
        # A = [[1, b],[0, 1]] is always invertible
        A = Matrix([[1, b], [0, 1]])
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            inv = A.inverse(verbosity=0)
        product = sym.simplify((A @ inv - Matrix.eye(2)).norm())
        assert product == 0


# ---------------------------------------------------------------------------
# TestAdj
# ---------------------------------------------------------------------------

class TestAdj:
    """Tests for Matrix.adj() — classical adjugate."""

    def test_2x2_adj_values(self, mat_2x2):
        # mat_2x2 = [[1,2],[3,4]], adj should be [[4,-2],[-3,1]]
        adj = mat_2x2.adj()
        assert adj == Matrix([[4, -2], [-3, 1]])

    def test_2x2_adj_property(self, mat_2x2):
        adj = mat_2x2.adj()
        det = mat_2x2.det()
        I = Matrix.eye(2)
        assert (mat_2x2 @ adj - det * I).norm() == 0

    def test_3x3_adj_property(self, mat_3x3):
        adj = mat_3x3.adj()
        det = mat_3x3.det()
        I = Matrix.eye(3)
        assert sym.simplify((mat_3x3 @ adj - det * I).norm()) == 0


# ---------------------------------------------------------------------------
# TestElem
# ---------------------------------------------------------------------------

class TestElem:
    """Tests for Matrix.elem() — identity matrix with same row count."""

    @pytest.mark.parametrize("rows,cols", [(2, 2), (2, 3), (3, 2), (3, 3)])
    def test_elem_is_identity_of_correct_size(self, rows, cols):
        mat = Matrix.zeros(rows, cols)
        e = mat.elem()
        assert e == Matrix.eye(rows)
        assert e.rows == rows
        assert e.cols == rows


# ---------------------------------------------------------------------------
# TestColumnConstraints
# ---------------------------------------------------------------------------

class TestColumnConstraints:
    """Tests for Matrix.column_constraints()."""

    def test_singular_returns_augmented_matrix(self, singular_2x2):
        result = singular_2x2.column_constraints(verbosity=0)
        assert isinstance(result, Matrix)
        # Should have the same number of rows as the original
        assert result.rows == singular_2x2.rows

    def test_singular_constraint_row_has_zero_coefficients(self, singular_2x2):
        result = singular_2x2.column_constraints(verbosity=0)
        # For a singular 2x2, the last row of the coefficient part (first 2 cols) is zero
        coeff_part = result[result.rows - 1, : singular_2x2.cols]
        assert all(coeff_part[0, j] == 0 for j in range(singular_2x2.cols))

    def test_full_rank_no_constraint_row(self, mat_2x2):
        result = mat_2x2.column_constraints(verbosity=0)
        # For full-rank matrix, no zero constraint rows in coefficient part
        zero_rows = 0
        for i in range(result.rows):
            if all(result[i, j] == 0 for j in range(mat_2x2.cols)):
                zero_rows += 1
        assert zero_rows == 0


# ---------------------------------------------------------------------------
# TestEvaluateCases
# ---------------------------------------------------------------------------

class TestEvaluateCases:
    """Smoke tests for Matrix.evaluate_cases()."""

    def test_runs_without_error(self):
        mat = Matrix([[1, 2], [3, 4]])
        rhs = Matrix([[1], [2]])
        # Should not raise; output is printed
        mat.evaluate_cases(rhs)
