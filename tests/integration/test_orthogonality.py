"""Integration tests for orthogonality: normalized, is_vec_orthogonal,
is_mat_orthogonal, orthogonal_complement, orthogonal_decomposition,
proj_comp, norm_comp, gram_schmidt, QRdecomposition, solve_least_squares,
create_vander, apply_vander."""

import pytest
import sympy as sym

from ma1522 import Matrix, ScalarFactor, VecDecomp
from ma1522.custom_types import QR


# ---------------------------------------------------------------------------
# TestNormalized
# ---------------------------------------------------------------------------

class TestNormalized:
    """Tests for Matrix.normalized()."""

    def test_unit_norm_after_normalizing(self, mat_2x2):
        result = mat_2x2.normalized()
        for j in range(result.cols):
            col = result.select_cols(j)
            norm_sq = sym.simplify(col.dot(col))
            assert norm_sq == 1

    def test_3_4_vector(self):
        mat = Matrix([[3], [4]])
        result = mat.normalized()
        assert result == Matrix([[sym.Rational(3, 5)], [sym.Rational(4, 5)]])

    def test_factor_true_returns_scalar_factor(self, mat_2x2):
        result = mat_2x2.normalized(factor=True)
        assert isinstance(result, ScalarFactor)

    def test_symbolic_normalization(self, a, b):
        import warnings
        mat = Matrix([[a], [b]])
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            result = mat.normalized()
        assert isinstance(result, Matrix)
        assert result.rows == 2
        assert result.cols == 1


# ---------------------------------------------------------------------------
# TestIsVecOrthogonal
# ---------------------------------------------------------------------------

class TestIsVecOrthogonal:
    """Tests for Matrix.is_vec_orthogonal()."""

    def test_standard_basis_orthogonal(self, identity_2):
        assert identity_2.is_vec_orthogonal() is True

    def test_scaled_standard_basis_orthogonal(self):
        mat = Matrix([[2, 0], [0, 3]])
        assert mat.is_vec_orthogonal() is True

    def test_non_orthogonal_pair(self):
        mat = Matrix([[1, 1], [1, 1]])
        assert mat.is_vec_orthogonal() is False

    def test_3x2_orthog_cols_fixture(self, orthog_cols):
        assert orthog_cols.is_vec_orthogonal() is True


# ---------------------------------------------------------------------------
# TestIsMatOrthogonal
# ---------------------------------------------------------------------------

class TestIsMatOrthogonal:
    """Tests for Matrix.is_mat_orthogonal()."""

    def test_identity_is_orthogonal(self, identity_2):
        assert identity_2.is_mat_orthogonal() is True

    def test_rotation_90_is_orthogonal(self):
        rot = Matrix([[0, -1], [1, 0]])
        assert rot.is_mat_orthogonal() is True

    def test_scaled_identity_not_orthogonal(self):
        mat = Matrix([[2, 0], [0, 2]])
        assert mat.is_mat_orthogonal() is False


# ---------------------------------------------------------------------------
# TestOrthogonalComplement
# ---------------------------------------------------------------------------

class TestOrthogonalComplement:
    """Tests for Matrix.orthogonal_complement()."""

    def test_3x2_complement_is_1d(self, orthog_cols):
        comp = orthog_cols.orthogonal_complement()
        assert comp.cols == 1

    def test_complement_is_orthogonal(self, orthog_cols):
        comp = orthog_cols.orthogonal_complement()
        assert (orthog_cols.T @ comp).is_zero_matrix

    def test_full_rank_square_complement_empty(self, identity_2):
        comp = identity_2.orthogonal_complement()
        assert comp == Matrix([])

    def test_complement_expected_direction(self):
        # Column space of [[1,0],[0,1],[0,0]] is xy-plane; complement is z-axis
        mat = Matrix([[1, 0], [0, 1], [0, 0]])
        comp = mat.orthogonal_complement()
        assert comp.rows == 3
        # Should be proportional to [0,0,1]
        assert comp[0, 0] == 0
        assert comp[1, 0] == 0
        assert comp[2, 0] != 0


# ---------------------------------------------------------------------------
# TestOrthogonalDecomposition
# ---------------------------------------------------------------------------

class TestOrthogonalDecomposition:
    """Tests for Matrix.orthogonal_decomposition(to)."""

    def test_sum_equals_original(self):
        A = Matrix([[1, 0], [1, 1]])
        b = Matrix([[-1], [2]])
        decomp = b.orthogonal_decomposition(A)
        assert isinstance(decomp, VecDecomp)
        assert decomp.proj + decomp.norm == b

    def test_norm_orthogonal_to_column_space(self):
        A = Matrix([[1, 0], [1, 1]])
        b = Matrix([[-1], [2]])
        decomp = b.orthogonal_decomposition(A)
        result = A.T @ decomp.norm
        assert result.norm() == 0

    def test_projection_onto_full_space_equals_b(self):
        A = Matrix.eye(2)
        b = Matrix([[3], [4]])
        decomp = b.orthogonal_decomposition(A)
        assert decomp.proj == b
        assert decomp.norm == Matrix([[0], [0]])


# ---------------------------------------------------------------------------
# TestProjComp
# ---------------------------------------------------------------------------

class TestProjComp:
    """Tests for Matrix.proj_comp(to)."""

    def test_project_onto_e1(self):
        e1 = Matrix([[1], [0]])
        v = Matrix([[3], [7]])
        proj = v.proj_comp(e1)
        assert proj == Matrix([[3], [0]])

    def test_project_onto_full_space(self, identity_2):
        v = Matrix([[5], [6]])
        proj = v.proj_comp(identity_2)
        assert proj == v

    def test_symbolic_projection(self):
        e1 = Matrix([[1], [0]])
        a = sym.Symbol("a", real=True)
        b = sym.Symbol("b", real=True)
        v = Matrix([[a], [b]])
        proj = v.proj_comp(e1)
        assert proj == Matrix([[a], [0]])


# ---------------------------------------------------------------------------
# TestNormComp
# ---------------------------------------------------------------------------

class TestNormComp:
    """Tests for Matrix.norm_comp(to)."""

    def test_sum_is_original(self):
        A = Matrix([[1, 0], [1, 1]])
        b = Matrix([[-1], [2]])
        proj = b.proj_comp(A)
        norm = b.norm_comp(A)
        assert proj + norm == b

    def test_project_onto_full_space_gives_zero_norm(self, identity_2):
        v = Matrix([[1], [2]])
        norm = v.norm_comp(identity_2)
        assert norm == Matrix([[0], [0]])


# ---------------------------------------------------------------------------
# TestGramSchmidt
# ---------------------------------------------------------------------------

class TestGramSchmidt:
    """Tests for Matrix.gram_schmidt()."""

    def test_factor_true_returns_scalar_factor(self, mat_2x2):
        result = mat_2x2.gram_schmidt(factor=True, verbosity=0)
        assert isinstance(result, ScalarFactor)

    def test_factor_true_columns_are_orthogonal(self, mat_2x2):
        result = mat_2x2.gram_schmidt(factor=True, verbosity=0)
        assert isinstance(result, ScalarFactor)
        assert result.full.is_vec_orthogonal() is True

    def test_factor_false_returns_matrix(self, mat_2x2):
        result = mat_2x2.gram_schmidt(factor=False, verbosity=0)
        assert isinstance(result, Matrix)

    def test_factor_false_columns_orthonormal(self, mat_2x2):
        result = mat_2x2.gram_schmidt(factor=False, verbosity=0)
        assert isinstance(result, Matrix)
        for j in range(result.cols):
            col = result.select_cols(j)
            norm_sq = sym.simplify(col.dot(col))
            assert norm_sq == 1

    def test_3_vector_pairwise_orthogonal(self):
        mat = Matrix([[1, 0, 1], [1, 1, 0], [0, 1, 1]])
        result = mat.gram_schmidt(factor=True, verbosity=0)
        assert isinstance(result, ScalarFactor)
        full = result.full
        for i in range(full.cols):
            for j in range(i + 1, full.cols):
                dot = sym.simplify(full.select_cols(i).dot(full.select_cols(j)))
                assert dot == 0

    def test_linearly_dependent_warns(self):
        import warnings
        mat = Matrix([[1, 2], [1, 2]])
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            mat.gram_schmidt(factor=True, verbosity=1)
        types = [w.category for w in caught]
        assert UserWarning in types

    def test_symbolic_gram_schmidt_runs(self, a, b):
        import warnings
        mat = Matrix([[a, b], [b, a]])
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            result = mat.gram_schmidt(factor=True, verbosity=0)
        assert isinstance(result, ScalarFactor)


# ---------------------------------------------------------------------------
# TestQRDecomposition
# ---------------------------------------------------------------------------

class TestQRDecomposition:
    """Tests for Matrix.QRdecomposition()."""

    def test_q_has_orthonormal_columns(self, mat_2x2, identity_2):
        qr = mat_2x2.QRdecomposition()
        assert isinstance(qr, QR)
        Q, R = qr.Q, qr.R
        diff = sym.simplify((Q.T @ Q - identity_2).norm())
        assert diff == 0

    def test_reconstruction(self, mat_2x2):
        qr = mat_2x2.QRdecomposition()
        Q, R = qr.Q, qr.R
        diff = sym.simplify((Q @ R - mat_2x2).norm())
        assert diff == 0

    def test_r_is_upper_triangular(self, mat_2x2):
        qr = mat_2x2.QRdecomposition()
        assert qr.R[1, 0] == 0

    def test_full_qr_q_is_square(self):
        A = Matrix([[1, 0], [0, 1], [1, 0]])
        qr = A.QRdecomposition(full=True)
        Q = qr.Q
        assert Q.rows == Q.cols == 3

    def test_3x2_reduced_q_shape(self, orthog_cols):
        qr = orthog_cols.QRdecomposition(full=False)
        Q = qr.Q
        assert Q.rows == 3
        assert Q.cols == 2

    def test_unpack_syntax(self, mat_2x2):
        Q, R = mat_2x2.QRdecomposition()
        assert isinstance(Q, Matrix)
        assert isinstance(R, Matrix)


# ---------------------------------------------------------------------------
# TestSolveLeastSquares
# ---------------------------------------------------------------------------

class TestSolveLeastSquares:
    """Tests for Matrix.solve_least_squares()."""

    def test_overdetermined_minimizes_error(self, overdetermined):
        A, b = overdetermined
        x = A.solve_least_squares(b, verbosity=0)
        assert hasattr(x, 'rows')  # matrix-like (may be base sympy type)
        # Known minimum residual norm for this system is sqrt(6)
        residual = (A @ x - b).norm()
        assert sym.simplify(residual - sym.sqrt(6)) == 0

    def test_exact_solution_zero_residual(self, mat_2x2):
        b = Matrix([[1], [2]])
        x = mat_2x2.solve_least_squares(b, verbosity=0)
        residual = (mat_2x2 @ x - b).norm()
        assert sym.simplify(residual) == 0


# ---------------------------------------------------------------------------
# TestVandermonde
# ---------------------------------------------------------------------------

class TestVandermonde:
    """Tests for Matrix.create_vander() and Matrix.apply_vander()."""

    def test_create_vander_shape(self):
        V = Matrix.create_vander(2, 3)
        assert V.rows == 2
        assert V.cols == 3

    def test_create_vander_first_col_ones(self):
        V = Matrix.create_vander(3, 4)
        for i in range(V.rows):
            assert V[i, 0] == 1

    def test_apply_vander_numeric(self):
        V = Matrix.create_vander(2, 2)
        x = Matrix([[1], [2]])
        result = V.apply_vander(x)
        assert result == Matrix([[1, 1], [1, 2]])

    def test_apply_vander_shape_mismatch_raises(self):
        V = Matrix.create_vander(2, 2)
        x = Matrix([[1], [2], [3]])
        with pytest.raises(Exception):
            V.apply_vander(x)
