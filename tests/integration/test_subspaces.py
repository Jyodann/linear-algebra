"""Integration tests for subspaces: nullspace, nullity, simplify_basis,
extend_basis, intersect_subspace, is_subspace_of, is_same_subspace,
coords_relative, transition_matrix, is_linearly_independent,
get_linearly_independent_vectors."""

import pytest
import sympy as sym

from ma1522 import Matrix


# ---------------------------------------------------------------------------
# TestNullspace
# ---------------------------------------------------------------------------

class TestNullspace:
    """Tests for Matrix.nullspace() — returns list[Matrix]."""

    def test_full_rank_empty_nullspace(self, identity_2):
        ns = identity_2.nullspace()
        assert ns == []

    def test_singular_2x2_one_null_vector(self, singular_2x2):
        ns = singular_2x2.nullspace()
        assert len(ns) == 1
        v = ns[0]
        residual = singular_2x2 @ v
        assert residual.norm() == 0

    def test_rank1_matrix_two_null_vectors(self):
        # Rank-1 3x3: all rows are multiples of [1,2,3]
        A = Matrix([[1, 2, 3], [2, 4, 6], [3, 6, 9]])
        ns = A.nullspace()
        assert len(ns) == 2
        for v in ns:
            assert (A @ v).norm() == 0

    def test_symbolic_nullspace(self, a):
        import warnings
        mat = Matrix([[a, 2 * a]])
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            ns = mat.nullspace()
        assert len(ns) >= 1
        # The null vector should satisfy mat @ v == 0
        for v in ns:
            product = mat @ v
            for i in range(product.rows):
                assert sym.simplify(product[i, 0]) == 0


# ---------------------------------------------------------------------------
# TestNullity
# ---------------------------------------------------------------------------

class TestNullity:
    """Tests for Matrix.nullity()."""

    def test_identity_nullity_zero(self, identity_2):
        assert identity_2.nullity() == 0

    def test_singular_2x2_nullity_one(self, singular_2x2):
        assert singular_2x2.nullity() == 1

    def test_zero_matrix_nullity_equals_cols(self):
        mat = Matrix.zeros(2, 3)
        assert mat.nullity() == 3

    @pytest.mark.parametrize("rows,cols,expected_nullity", [
        (2, 2, 0),   # identity_2
        (3, 3, 0),   # identity_3
        (2, 3, 1),   # 2x3 full row rank
    ])
    def test_parametrized_nullity(self, rows, cols, expected_nullity):
        mat = Matrix.eye(rows, cols)
        assert mat.nullity() == expected_nullity


# ---------------------------------------------------------------------------
# TestSimplifyBasis
# ---------------------------------------------------------------------------

class TestSimplifyBasis:
    """Tests for Matrix.simplify_basis()."""

    def test_column_basis_two_independent_cols(self):
        import warnings
        mat = Matrix([[1, 2, 2, 5], [3, 4, 6, 13], [0, 0, 0, 0]])
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            basis = mat.simplify_basis(colspace=True, verbosity=0)
        assert isinstance(basis, Matrix)
        assert basis.cols == 2

    def test_row_basis_two_independent_rows(self):
        import warnings
        mat = Matrix([[1, 2, 2, 5], [3, 4, 6, 13], [0, 0, 0, 0]])
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            basis = mat.simplify_basis(colspace=False, verbosity=0)
        assert isinstance(basis, Matrix)
        # Two non-zero rows
        assert basis.rows == 2

    def test_already_independent_identity(self, identity_2):
        basis = identity_2.simplify_basis(colspace=True, verbosity=0)
        assert basis.cols == 2


# ---------------------------------------------------------------------------
# TestExtendBasis
# ---------------------------------------------------------------------------

class TestExtendBasis:
    """Tests for Matrix.extend_basis()."""

    def test_extend_to_full_rank(self):
        # Single column of standard e1 in R^2
        mat = Matrix([[1], [0]])
        extended = mat.extend_basis(verbosity=0)
        assert extended.rank() == 2

    def test_extended_has_enough_cols(self):
        mat = Matrix([[1], [0]])
        extended = mat.extend_basis(verbosity=0)
        assert extended.cols >= 2


# ---------------------------------------------------------------------------
# TestIntersectSubspace
# ---------------------------------------------------------------------------

class TestIntersectSubspace:
    """Tests for Matrix.intersect_subspace()."""

    def test_full_plane_and_rank1(self):
        # eye(2) spans all of R^2; [[1,1],[1,1]] spans the line [1,1]
        A = Matrix.eye(2)
        B = Matrix([[1, 1], [1, 1]])
        inter = A.intersect_subspace(B, verbosity=0)
        # Intersection should be 1-dimensional
        assert inter.cols == 1

    def test_docstring_example(self):
        # From docstring: eye(2) ∩ span([[1,1],[0,0]]) = span([[1],[0]])
        mat1 = Matrix([[1, 0], [0, 1]])
        mat2 = Matrix([[1, 1], [0, 0]])
        inter = mat1.intersect_subspace(mat2, verbosity=0)
        assert inter.cols == 1
        assert inter[1, 0] == 0  # second component is 0


# ---------------------------------------------------------------------------
# TestIsSubspaceOf
# ---------------------------------------------------------------------------

class TestIsSubspaceOf:
    """Tests for Matrix.is_subspace_of()."""

    def test_e1_is_subspace_of_eye2(self):
        e1 = Matrix([[1], [0]])
        assert e1.is_subspace_of(Matrix.eye(2), verbosity=0) is True

    def test_non_subspace(self):
        v = Matrix([[1], [1]])
        basis = Matrix([[1], [0]])
        assert v.is_subspace_of(basis, verbosity=0) is False

    def test_whole_space_is_subspace_of_itself(self, identity_2):
        assert identity_2.is_subspace_of(identity_2, verbosity=0) is True


# ---------------------------------------------------------------------------
# TestIsSameSubspace
# ---------------------------------------------------------------------------

class TestIsSameSubspace:
    """Tests for Matrix.is_same_subspace()."""

    def test_same_matrix(self, mat_2x2):
        assert mat_2x2.is_same_subspace(mat_2x2, verbosity=0) is True

    def test_scaled_version(self, mat_2x2):
        # Scaling columns does not change the column space
        scaled = mat_2x2 * 2
        assert mat_2x2.is_same_subspace(scaled, verbosity=0) is True

    def test_different_subspace(self):
        A = Matrix([[1, 0], [0, 1]])
        B = Matrix([[1, 0], [0, 2]])
        # Both span R^2, so same subspace
        assert A.is_same_subspace(B, verbosity=0) is True

    def test_actually_different_subspace(self):
        # span([1,0]) vs span([0,1]) — different 1-d subspaces
        A = Matrix([[1], [0]])
        B = Matrix([[0], [1]])
        assert A.is_same_subspace(B, verbosity=0) is False


# ---------------------------------------------------------------------------
# TestCoordsRelative
# ---------------------------------------------------------------------------

class TestCoordsRelative:
    """Tests for Matrix.coords_relative(basis)."""

    def test_standard_basis_coords(self):
        v = Matrix([[3], [4]])
        coords = v.coords_relative(Matrix.eye(2), verbosity=0)
        assert coords == Matrix([[3], [4]])

    def test_non_standard_basis(self):
        v = Matrix([[1], [1]])
        basis = Matrix([[1, 0], [0, 1]])
        coords = v.coords_relative(basis, verbosity=0)
        assert coords == Matrix([[1], [1]])

    def test_reconstruction_from_coords(self):
        basis = Matrix([[1, 1], [1, -1]])
        v = Matrix([[3], [1]])
        coords = v.coords_relative(basis, verbosity=0)
        reconstructed = basis @ coords
        diff = sym.simplify((reconstructed - v).norm())
        assert diff == 0


# ---------------------------------------------------------------------------
# TestTransitionMatrix
# ---------------------------------------------------------------------------

class TestTransitionMatrix:
    """Tests for Matrix.transition_matrix(to).

    Implementation returns P = to^{-1} @ self, so the relation is: to @ P = self.
    (Docstring says P @ to = self, but that only commutes for diagonal 'to'.)
    """

    def test_transition_satisfies_equation(self):
        A = Matrix([[1, 1], [0, 1]])
        B = Matrix([[1, 0], [1, 1]])
        P = A.transition_matrix(to=B, verbosity=0)
        # Actual relation: B @ P = A
        diff = sym.simplify((A - B @ P).norm())
        assert diff == 0

    def test_identity_to_scaled(self):
        I = Matrix.eye(2)
        S = 2 * Matrix.eye(2)
        P = I.transition_matrix(to=S, verbosity=0)
        # S @ P = I  →  P = S^{-1} = (1/2)I (diagonal so P @ S = I too)
        expected = sym.Rational(1, 2) * Matrix.eye(2)
        diff = sym.simplify((P - expected).norm())
        assert diff == 0

    def test_round_trip(self, mat_2x2):
        # self.transition_matrix(to=B) gives P with to @ P = self
        B = Matrix([[1, 0], [0, 2]])
        P = mat_2x2.transition_matrix(to=B, verbosity=0)
        diff = sym.simplify((mat_2x2 - B @ P).norm())
        assert diff == 0


# ---------------------------------------------------------------------------
# TestIsLinearlyIndependent
# ---------------------------------------------------------------------------

class TestIsLinearlyIndependent:
    """Tests for Matrix.is_linearly_independent()."""

    def test_invertible_is_independent(self, mat_2x2):
        assert mat_2x2.is_linearly_independent() is True

    def test_singular_is_dependent(self, singular_2x2):
        assert singular_2x2.is_linearly_independent() is False

    def test_single_nonzero_vector_independent(self):
        v = Matrix([[1], [0], [0]])
        assert v.is_linearly_independent() is True

    @pytest.mark.parametrize("data,expected", [
        ([[1, 0], [0, 1]], True),
        ([[1, 2], [2, 4]], False),
        ([[1, 0, 0], [0, 1, 0], [0, 0, 1]], True),
    ])
    def test_parametrized(self, data, expected):
        mat = Matrix(data)
        assert mat.is_linearly_independent() is expected
