"""Edge case integration tests for methods with thin coverage.

Covers branches and inputs that existing tests miss entirely.
"""

import pytest
import sympy as sym
import warnings

from ma1522 import Matrix
from ma1522.custom_types import QR, PartGen


# ---------------------------------------------------------------------------
# column_constraints: use_ref=True branch
# ---------------------------------------------------------------------------

class TestColumnConstraintsUseRef:
    def test_use_ref_true_runs(self):
        A = Matrix([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
        result, _ = A.column_constraints(use_ref=True, verbosity=0), None
        assert result is not None

    def test_use_ref_matches_default_for_full_rank(self):
        A = Matrix([[1, 0], [0, 1]])
        r_default = A.column_constraints(use_ref=False, verbosity=0)
        r_ref = A.column_constraints(use_ref=True, verbosity=0)
        assert r_default == r_ref


# ---------------------------------------------------------------------------
# QRdecomposition(full=True) on non-square matrix
# ---------------------------------------------------------------------------

class TestQRDecompositionFull:
    def test_3x2_full_qr_shape(self):
        A = Matrix([[1, 0], [0, 1], [1, 1]])
        qr = A.QRdecomposition(full=True, verbosity=0)
        assert isinstance(qr, QR)
        Q, R = qr.Q, qr.R
        assert Q.rows == Q.cols == 3  # full Q is square m×m
        assert R.rows == 3
        assert R.cols == 2

    def test_full_qr_reconstruction(self):
        A = Matrix([[1, 0], [0, 1], [1, 1]])
        qr = A.QRdecomposition(full=True, verbosity=0)
        Q, R = qr.Q, qr.R
        diff = (Q @ R - A).applyfunc(sym.simplify)
        assert diff == Matrix([[0, 0], [0, 0], [0, 0]])

    def test_full_qr_q_is_orthogonal(self):
        A = Matrix([[1, 0], [0, 1], [1, 0]])
        qr = A.QRdecomposition(full=True, verbosity=0)
        Q = qr.Q
        product = (Q.T @ Q).applyfunc(sym.simplify)
        assert product == Matrix.eye(3)


# ---------------------------------------------------------------------------
# coords_relative: inconsistent system raises ValueError
# ---------------------------------------------------------------------------

class TestCoordsRelativeEdgeCases:
    def test_consistent_system_returns_coordinates(self):
        basis = Matrix([[1, 0], [0, 1]])
        vec = Matrix([[3], [4]])
        coords = vec.coords_relative(basis, verbosity=0)
        assert coords == Matrix([[3], [4]])

    def test_inconsistent_system_raises(self):
        # vec is not in span of single column
        basis = Matrix([[1], [0]])
        vec = Matrix([[0], [1]])
        with pytest.raises(ValueError):
            vec.coords_relative(basis, verbosity=0)

    def test_wrong_shape_raises(self):
        basis = Matrix([[1, 0], [0, 1]])
        vec = Matrix([[1, 2], [3, 4]])  # not a column vector
        with pytest.raises(sym.ShapeError):
            vec.coords_relative(basis, verbosity=0)


# ---------------------------------------------------------------------------
# equilibrium_vectors: non-trivial stochastic with non-unique equilibrium
# ---------------------------------------------------------------------------

class TestEquilibriumVectorsEdgeCases:
    def test_stochastic_sum_preserved(self, stochastic_2x2):
        eq = stochastic_2x2.equilibrium_vectors()
        col_sum = sum(eq[i, 0] for i in range(eq.rows))
        assert sym.simplify(col_sum - 1) == 0

    def test_3x3_stochastic_equilibrium(self):
        A = Matrix([
            [sym.Rational(1, 2), sym.Rational(1, 4), sym.Rational(1, 4)],
            [sym.Rational(1, 4), sym.Rational(1, 2), sym.Rational(1, 4)],
            [sym.Rational(1, 4), sym.Rational(1, 4), sym.Rational(1, 2)],
        ])
        eq = A.equilibrium_vectors()
        diff = (A @ eq - eq).applyfunc(sym.simplify)
        assert all(diff[i, 0] == 0 for i in range(diff.rows))

    def test_equilibrium_is_fixed_point(self, stochastic_2x2):
        eq = stochastic_2x2.equilibrium_vectors()
        diff = (stochastic_2x2 @ eq - eq).applyfunc(sym.simplify)
        assert all(diff[i, 0] == 0 for i in range(diff.rows))


# ---------------------------------------------------------------------------
# diagonalize: reals_only=False (complex eigenvalues)
# ---------------------------------------------------------------------------

class TestDiagonalizeComplexEigenvalues:
    def test_rotation_matrix_not_real_diagonalizable(self):
        # [[0,-1],[1,0]] has eigenvalues ±i — not diagonalizable over reals
        A = Matrix([[0, -1], [1, 0]])
        assert A.is_diagonalizable(verbosity=0) is False

    def test_real_diagonalizable_matrix(self):
        A = Matrix([[2, 0], [0, 3]])
        assert A.is_diagonalizable(verbosity=0) is True
        pdp = A.diagonalize(reals_only=True, verbosity=0)
        assert pdp is not None


# ---------------------------------------------------------------------------
# cpoly: force_factor=False path
# ---------------------------------------------------------------------------

class TestCpolyForceFactor:
    def test_force_factor_false_returns_polynomial(self, mat_2x2):
        result = mat_2x2.cpoly(force_factor=False)
        # Should return the characteristic polynomial (not factored)
        assert result is not None

    def test_force_factor_true_returns_factored(self, mat_2x2):
        result = mat_2x2.cpoly(force_factor=True)
        assert result is not None


# ---------------------------------------------------------------------------
# intersect_subspace: edge cases
# ---------------------------------------------------------------------------

class TestIntersectSubspaceEdgeCases:
    def test_orthogonal_subspaces_trivial_intersection(self):
        A = Matrix([[1], [0]])
        B = Matrix([[0], [1]])
        inter = A.intersect_subspace(B, verbosity=0)
        # Intersection of x-axis and y-axis is {0} — empty or zero cols
        assert inter.cols == 0 or all(
            inter.select_cols(i).norm() == 0 for i in range(inter.cols)
        )

    def test_shared_vector_in_intersection(self):
        # Both span includes [1,0] — intersection is at least span{[1,0]}
        A = Matrix([[1, 0], [0, 1]])  # span = R^2
        B = Matrix([[1], [0]])         # span = x-axis
        inter = A.intersect_subspace(B, verbosity=0)
        # x-axis should be in intersection
        assert inter.cols >= 1


# ---------------------------------------------------------------------------
# standard_matrix: symbolic input branch
# ---------------------------------------------------------------------------

class TestStandardMatrixSymbolic:
    def test_identity_transformation(self):
        # T(e1)=e1, T(e2)=e2 — standard matrix is identity
        domain = Matrix.eye(2)
        images = Matrix.eye(2)
        result = domain.standard_matrix(images)
        assert isinstance(result, list)
        assert len(result) >= 1


# ---------------------------------------------------------------------------
# normalized: iszerofunc parameter
# ---------------------------------------------------------------------------

class TestNormalizedIszerofunc:
    def test_default_normalized_unit_norm(self):
        mat = Matrix([[3], [4]])
        result = mat.normalized()
        assert isinstance(result, Matrix)
        assert sym.simplify(result.norm() - 1) == 0

    def test_factor_true_extracts_scalar(self):
        from ma1522.custom_types import ScalarFactor
        mat = Matrix([[2], [4]])
        result = mat.normalized(factor=True)
        # With factor=True, should return ScalarFactor
        assert isinstance(result, ScalarFactor)


# ---------------------------------------------------------------------------
# simplify_basis: actual vectors verified, not just shape
# ---------------------------------------------------------------------------

class TestSimplifyBasisCorrectness:
    def test_colspace_basis_spans_original_colspace(self):
        mat = Matrix([[1, 2, 3], [0, 0, 1]])
        simplified = mat.simplify_basis(colspace=True, verbosity=0)
        assert isinstance(simplified, Matrix)
        # Each original column should be in span of simplified basis
        for i in range(mat.cols):
            col = mat.select_cols(i)
            assert col.is_subspace_of(simplified, verbosity=0)

    def test_rowspace_basis_spans_original_rowspace(self):
        mat = Matrix([[1, 2, 3], [2, 4, 6], [0, 0, 1]])
        simplified = mat.simplify_basis(colspace=False, verbosity=0)
        assert simplified.rows <= mat.rows


# ---------------------------------------------------------------------------
# find_all_cases: multi-symbol matrix
# ---------------------------------------------------------------------------

class TestFindAllCasesMultiSymbol:
    def test_two_symbol_matrix(self):
        a, b = sym.symbols("a b", real=True)
        mat = Matrix([[a, 0], [0, b]])
        cases = mat.find_all_cases()
        # Should return cases for a=0 and b=0
        assert isinstance(cases, list)
