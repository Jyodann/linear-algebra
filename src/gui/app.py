import io
import asyncio
import contextlib
import traceback
import warnings
import ast
from concurrent.futures import ThreadPoolExecutor

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
import sympy as sym
from ma1522.symbolic import Matrix

app = FastAPI()

app.mount("/static", StaticFiles(directory="src/gui/static"), name="static")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_bracket_format(s: str) -> Matrix:
    """Parse [v11 v12; v21 v22] or [v11, v12; v21, v22] format.

    Cells may be any sympy expression.  When rows contain commas they are used
    as the cell delimiter (allowing spaces inside expressions); otherwise cells
    are split on whitespace.
    """
    inner = s.strip()[1:-1]   # strip outer [ ]
    rows = []
    for row_str in inner.split(';'):
        row_str = row_str.strip()
        if not row_str:
            continue
        if ',' in row_str:
            cells = [sym.sympify(c.strip()) for c in row_str.split(',')]
        else:
            cells = [sym.sympify(c) for c in row_str.split()]
        rows.append(cells)
    if not rows:
        raise ValueError("Empty matrix")
    ncols = len(rows[0])
    for r in rows:
        if len(r) != ncols:
            raise ValueError(
                f"Row length mismatch: expected {ncols} cells, got {len(r)}. "
                "Use commas to separate cells when expressions contain spaces, "
                "e.g. [30, -1 + sqrt(5); 1, 2]"
            )
    return Matrix(rows)


def parse_matrix(s: str) -> Matrix:
    """Parse matrix from LaTeX, Python list, or bracket notation.

    Supported formats:
    - LaTeX:       \\begin{pmatrix} 1 & 2 \\\\ 3 & 4 \\end{pmatrix}
    - Python list: [[1, 2], [3, 4]]  or  [[1, sqrt(5)], [3, 4]]
    - Bracket:     [1 2; 3 4]  (space-separated, no spaces within cells)
    - Bracket+CSV: [1, -1+sqrt(5); 3, 4]  (comma-separated, spaces OK in cells)

    All float entries are converted to exact rationals.
    """
    s = s.strip()

    if "begin" in s or ("\\" in s and any(c in s for c in "{}[]")):
        M = Matrix.from_latex(s, verbosity=0)
    else:
        M = None
        # Try Python list literal first: [[1, sqrt(5)], [3, 4]]
        try:
            list_data = ast.literal_eval(s)
            if isinstance(list_data, list):
                rows = []
                for row in list_data:
                    if isinstance(row, list):
                        rows.append([sym.sympify(v) for v in row])
                    else:
                        rows.append([sym.sympify(row)])
                M = Matrix(rows)
        except Exception:
            pass
        # Try bracket format: [v1, v2; v3, v4] or [v1 v2; v3 v4]
        if M is None and s.startswith('[') and s.endswith(']'):
            bracket_err = None
            try:
                M = _parse_bracket_format(s)
            except Exception as e:
                bracket_err = e
            # Fallback to from_str (handles augmented matrices etc.)
            if M is None:
                try:
                    M = Matrix.from_str(s)
                except Exception:
                    # Both failed — give a useful message
                    hint = (
                        "When cell expressions contain spaces (e.g. '-1 + sqrt(5)'), "
                        "use commas to separate cells: [30, -1 + sqrt(5); 22, 1]"
                    )
                    raise ValueError(f"{bracket_err}. {hint}") from None
        # Final fallback for non-bracket formats
        elif M is None:
            M = Matrix.from_str(s)

    return M.applyfunc(lambda x: sym.nsimplify(x, rational=True))


def capture(fn):
    """Redirect stdout + suppress warnings, return (result, raw_str)."""
    buf = io.StringIO()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        with contextlib.redirect_stdout(buf):
            result = fn()
    return result, buf.getvalue()

def matrix_to_raw(M) -> str:
    """Convert a Matrix to '[r0c0 r0c1; r1c0 r1c1]' format (from_str-compatible)."""
    rows = []
    for r in range(M.rows):
        rows.append(' '.join(str(M[r, c]) for c in range(M.cols)))
    return '[' + '; '.join(rows) + ']'

def steps_html(raw: str) -> str:
    """Convert captured stdout (LaTeX-based) to HTML step cards."""
    lines = raw.splitlines()
    html_parts = []
    i = 0
    while i < len(lines):
        line = lines[i]

        if not line.strip():
            i += 1
            continue

        # Display-math block  \[ ... \]  (possibly multi-line)
        if line.strip().startswith("\\["):
            block = []
            while i < len(lines):
                block.append(lines[i])
                if lines[i].strip().endswith("\\]"):
                    i += 1
                    break
                i += 1
            content = "\n".join(block)
            html_parts.append(f'<div class="step-matrix">\n{content}\n</div>')
            continue

        # Inline-math  \( ... \)  — ERO label
        if line.strip().startswith("\\("):
            html_parts.append(f'<div class="step-ero">{line.strip()}</div>')
            i += 1
            continue

        stripped = line.strip()
        if (
            stripped.startswith("Case ")
            or stripped == "Unique solution"
            or stripped == "No solution"
            or stripped.startswith("Solution with")
        ):
            html_parts.append(f'<div class="step-case">{stripped}</div>')
            i += 1
            continue

        if stripped:
            html_parts.append(f'<div class="step-text">{stripped}</div>')
        i += 1

    return "\n".join(html_parts)


# Shared thread pool for blocking computations
_executor = ThreadPoolExecutor(max_workers=4)
COMPUTE_TIMEOUT = 30  # seconds


def _zero_col_vector(rows: int) -> Matrix:
    return Matrix([[0]] * rows)



# ---------------------------------------------------------------------------
# Process endpoint
# ---------------------------------------------------------------------------

@app.post("/api/process")
async def process_matrix(request: Request):
    try:
        data = await request.json()
        matrix_str = data.get("matrix", "")
        matrix2_str = data.get("matrix2", "")
        matrix3_str = data.get("matrix3", "")
        mod1 = data.get("mod1", "none")
        mod2 = data.get("mod2", "none")
        mod3 = data.get("mod3", "none")
        rhs_str = data.get("rhs", "")
        operation = data.get("operation", "")

        # Parse primary matrix
        try:
            A = parse_matrix(matrix_str)
        except Exception as e:
            return JSONResponse(content={"error": f"Failed to parse matrix: {e}"}, status_code=400)

        # Parse rhs (default: zero column vector)
        b = None
        if rhs_str and rhs_str.strip():
            try:
                b = parse_matrix(rhs_str)
            except Exception as e:
                return JSONResponse(content={"error": f"Failed to parse rhs: {e}"}, status_code=400)

        # Parse matrix2 if needed
        B = None
        if matrix2_str and matrix2_str.strip():
            try:
                B = parse_matrix(matrix2_str)
            except Exception as e:
                return JSONResponse(content={"error": f"Failed to parse matrix2: {e}"}, status_code=400)

        C = None
        if matrix3_str and matrix3_str.strip():
            try:
                C = parse_matrix(matrix3_str)
            except Exception as e:
                return JSONResponse(content={"error": f"Failed to parse matrix3: {e}"}, status_code=400)

        # Build input LaTeX summary
        is_chain = operation == "chain_multiply"
        a_label = "M_1" if is_chain else "A"
        input_parts = [f"{a_label} = {sym.latex(A)}"]
        if b is not None:
            input_parts.append(f"b = {sym.latex(b)}")
        if B is not None:
            b_label = "M_2" if is_chain else "B"
            input_parts.append(f"{b_label} = {sym.latex(B)}")
        if C is not None:
            input_parts.append(f"M_3 = {sym.latex(C)}")
        input_latex = "\\[" + " \\quad ".join(input_parts) + "\\]"

        loop = asyncio.get_event_loop()

        def compute():
            """All heavy CPU work runs here — in the thread pool, so the event loop is free."""
            result = ""
            steps_raw = ""
            raw = ""

            # ------------------------------------------------------------------
            # Row Reduction
            # ------------------------------------------------------------------
            if operation == "rref":
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", UserWarning)
                    res = A.rref()
                result = f"\\[ {sym.latex(res[0])} \\]"
                raw = matrix_to_raw(res[0])

            elif operation == "ref":
                res, steps_raw = capture(lambda: A.ref(verbosity=2))
                result = f"\\[ {sym.latex(res.U)} \\]"
                raw = matrix_to_raw(res.U)

            # ------------------------------------------------------------------
            # Factorizations
            # ------------------------------------------------------------------
            elif operation == "lu":
                res, steps_raw = capture(lambda: A.ref(verbosity=2))
                result = (
                    f"\\( P = {sym.latex(res.P)}, \\quad "
                    f"L = {sym.latex(res.L)}, \\quad "
                    f"U = {sym.latex(res.U)} \\)"
                )
                raw = f"P={matrix_to_raw(res.P)}\nL={matrix_to_raw(res.L)}\nU={matrix_to_raw(res.U)}"

            elif operation == "qr":
                _, steps_raw = capture(lambda: A.gram_schmidt(verbosity=1))
                Q, R = A.QRdecomposition()
                result = (
                    f"\\( Q = {sym.latex(Q)}, \\quad R = {sym.latex(R)} \\)"
                )
                raw = f"Q={matrix_to_raw(Q)}\nR={matrix_to_raw(R)}"

            elif operation == "gram_schmidt":
                gs_result, steps_raw = capture(lambda: A.gram_schmidt(verbosity=1))
                result = f"\\[ {sym.latex(gs_result)} \\]"
                raw = matrix_to_raw(gs_result)

            elif operation == "svd":
                res = A.singular_value_decomposition(verbosity=0)
                result = (
                    f"\\( U = {sym.latex(res.U)}, \\quad "
                    f"\\Sigma = {sym.latex(res.S)}, \\quad "
                    f"V^T = {sym.latex(res.V)} \\)"
                )
                raw = f"U={matrix_to_raw(res.U)}\nS={matrix_to_raw(res.S)}\nV={matrix_to_raw(res.V)}"

            # ------------------------------------------------------------------
            # Properties
            # ------------------------------------------------------------------
            elif operation == "det":
                d = A.det()
                result = f"\\( \\det(A) = {sym.latex(d)} \\)"
                raw = str(d)

            elif operation == "inv":
                res, steps_raw = capture(lambda: A.inverse(option="right", verbosity=1))
                result = f"\\( A^{{-1}} = {sym.latex(res)} \\)"
                raw = matrix_to_raw(res)

            elif operation == "rank":
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    r = A.rank()
                nullity = A.cols - r
                result = f"\\( \\mathrm{{rank}}(A) = {r}, \\quad \\mathrm{{nullity}}(A) = {nullity} \\)"
                raw = f"rank={r}\nnullity={nullity}"

            # ------------------------------------------------------------------
            # Eigen Analysis
            # ------------------------------------------------------------------
            elif operation == "eigenvals":
                evals = A.eigenvals()
                parts = [
                    f"\\lambda = {sym.latex(val)} \\text{{ (mult. {mult})}}"
                    for val, mult in evals.items()
                ]
                result = "\\[ " + ", \\quad ".join(parts) + " \\]"
                raw = ', '.join(str(v) for v in evals.keys())

            elif operation == "eigenvects":
                evects = A.eigenvects()
                parts = []
                for val, mult, vecs in evects:
                    vec_strs = ", ".join(sym.latex(v) for v in vecs)
                    parts.append(
                        f"\\lambda = {sym.latex(val)} \\text{{ (mult. {mult})}}: "
                        f"\\left[ {vec_strs} \\right]"
                    )
                result = "\\[ " + " \\\\[6pt] ".join(parts) + " \\]"
                raw = ""

            elif operation == "diagonalize":
                res, steps_raw = capture(lambda: A.diagonalize(verbosity=1))
                result = (
                    f"\\( P = {sym.latex(res.P)}, \\quad D = {sym.latex(res.D)} \\)"
                )
                raw = f"P={matrix_to_raw(res.P)}\nD={matrix_to_raw(res.D)}"

            elif operation == "orth_diagonalize":
                res, steps_raw = capture(lambda: A.orthogonally_diagonalize(verbosity=1))
                result = (
                    f"\\( P = {sym.latex(res.P)}, \\quad D = {sym.latex(res.D)} \\)"
                )
                raw = f"P={matrix_to_raw(res.P)}\nD={matrix_to_raw(res.D)}"

            # ------------------------------------------------------------------
            # Vector Spaces
            # ------------------------------------------------------------------
            elif operation == "nullspace":
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    ns = A.nullspace()
                if not ns:
                    result = f"\\( \\mathrm{{Null}}(A) = \\{{0\\}} \\)"
                    raw = ""
                else:
                    vecs = ", ".join(sym.latex(v) for v in ns)
                    result = (
                        f"\\( \\mathrm{{Null}}(A) = \\operatorname{{span}}\\{{ {vecs} \\}} \\)"
                    )
                    raw = '\n'.join(matrix_to_raw(v) for v in ns)

            elif operation == "colspace":
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    cs = A.columnspace()
                vecs = ", ".join(sym.latex(v) for v in cs)
                result = (
                    f"\\( \\mathrm{{Col}}(A) = \\operatorname{{span}}\\{{ {vecs} \\}} \\)"
                )
                raw = '\n'.join(matrix_to_raw(v) for v in cs)

            elif operation == "orth_complement":
                res, steps_raw = capture(lambda: A.orthogonal_complement(verbosity=1))
                result = (
                    f"\\( (\\mathrm{{Col}}(A))^\\perp = {sym.latex(res)} \\)"
                )
                raw = matrix_to_raw(res)

            elif operation == "col_constraints":
                res, steps_raw = capture(lambda: A.column_constraints(verbosity=1))
                result = f"\\[ {sym.latex(res)} \\]"
                raw = matrix_to_raw(res)

            elif operation == "extend_basis":
                res, steps_raw = capture(lambda: A.extend_basis(verbosity=2))
                result = f"\\[ {sym.latex(res)} \\]"
                raw = matrix_to_raw(res)

            # ------------------------------------------------------------------
            # Linear Systems
            # ------------------------------------------------------------------
            elif operation == "solve":
                b_vec = b if b is not None else _zero_col_vector(A.rows)
                try:
                    sol_list = A.solve(b_vec)
                    if not sol_list:
                        result = "\\( \\text{No solution — system is inconsistent.} \\)"
                        raw = ""
                    else:
                        sol = sol_list[0]
                        result = f"\\[ {sym.latex(sol)} \\]"
                        raw = matrix_to_raw(sol)
                except Exception:
                    result = "\\( \\text{No solution — system is inconsistent.} \\)"
                    raw = ""

            elif operation == "least_squares":
                b_vec = b if b is not None else _zero_col_vector(A.rows)
                try:
                    res, steps_raw = capture(lambda: A.solve_least_squares(b_vec, verbosity=1))
                except (IndexError, KeyError):
                    # sym.solve returned empty list (AᵀA singular, underdetermined normal eqs)
                    # Fall back to pseudoinverse minimum-norm solution
                    res = A.pinv() @ b_vec
                    steps_raw = ""
                result = f"\\( \\hat{{x}} = {sym.latex(res)} \\)"
                raw = matrix_to_raw(res)

            elif operation == "projection":
                b_vec = b if b is not None else _zero_col_vector(A.rows)
                try:
                    res, steps_raw = capture(lambda: A.solve_least_squares(b_vec, verbosity=1))
                except (IndexError, KeyError):
                    res = A.pinv() @ b_vec
                    steps_raw = ""
                x_hat = res
                p = A @ x_hat
                result = (
                    f"\\( \\hat{{x}} = {sym.latex(x_hat)}, \\quad "
                    f"p = A\\hat{{x}} = {sym.latex(p)} \\)"
                )
                raw = f"x_hat={matrix_to_raw(x_hat)}\np={matrix_to_raw(p)}"

            # ------------------------------------------------------------------
            # Subspaces
            # ------------------------------------------------------------------
            elif operation == "intersect":
                if B is None:
                    return None, None, None, "This operation requires a second matrix (matrix2)."
                res, steps_raw = capture(lambda: A.intersect_subspace(B, verbosity=2))
                result = f"\\[ {sym.latex(res)} \\]"
                raw = matrix_to_raw(res)

            elif operation == "transition":
                if B is None:
                    return None, None, None, "This operation requires a second matrix (matrix2)."
                res, steps_raw = capture(lambda: A.transition_matrix(B, verbosity=2))
                result = (
                    f"\\( P_{{B \\leftarrow A}} = {sym.latex(res)} \\)"
                )
                raw = matrix_to_raw(res)

            # ------------------------------------------------------------------
            # Symbolic / Parametric
            # ------------------------------------------------------------------
            elif operation == "eval_cases":
                b_vec = b if b is not None else _zero_col_vector(A.rows)
                _, steps_raw = capture(lambda: A.evaluate_cases(b_vec))
                result = "See steps below."
                raw = ""

            elif operation == "find_cases":
                cases = A.find_all_cases()
                if not cases:
                    result = "No parametric cases"
                else:
                    parts = []
                    for case in cases:
                        parts.append(
                            "\\{" +
                            ", ".join(f"{sym.latex(k)} = {sym.latex(v)}" for k, v in case.items()) +
                            "\\}"
                        )
                    result = "\\[ " + ", \\quad ".join(parts) + " \\]"
                raw = ""

            elif operation == "chain_multiply":
                def _apply_mod(M, mod):
                    if mod == "T":
                        return M.T
                    elif mod == "inv":
                        return M.inv()
                    elif mod == "inv_T":
                        return M.inv().T
                    elif mod == "none":
                        return M
                    else:
                        raise ValueError(f"Unknown modifier '{mod}'. Must be one of: none, T, inv, inv_T")

                operands = [(A, mod1)]
                if B is not None:
                    operands.append((B, mod2))
                if C is not None:
                    operands.append((C, mod3))

                if len(operands) < 2:
                    return None, None, None, "chain_multiply requires at least two matrices."

                _labels = ["M_1", "M_2", "M_3"]
                _mod_superscripts = {"T": "T", "inv": "{-1}", "inv_T": "{T,-1}"}

                def _compute_chain():
                    modified = []
                    for i, (M, mod) in enumerate(operands):
                        mod_mat = _apply_mod(M, mod)
                        if mod != "none":
                            sup = _mod_superscripts[mod]
                            print(f"\\( {_labels[i]}^{sup} = \\)")
                            print(f"\\[ {sym.latex(mod_mat)} \\]")
                        modified.append(mod_mat)

                    acc = modified[0]
                    for j, M in enumerate(modified[1:], start=1):
                        acc = acc @ M
                        partial = acc.doit()
                        if j < len(modified) - 1:
                            print(f"\\( {_labels[0]} \\cdots {_labels[j]} = \\)")
                            print(f"\\[ {sym.latex(partial)} \\]")
                    return acc.doit()

                try:
                    result_mat, steps_raw = capture(_compute_chain)
                except Exception as e:
                    return None, None, None, f"Could not apply matrix modifier: {e}"

                result = f"\\[ {sym.latex(result_mat)} \\]"
                raw = matrix_to_raw(result_mat)

            else:
                return None, None, None, f"Unknown operation: {operation}"

            return result, steps_raw, raw, None  # (result, steps, raw, error)

        try:
            result, steps_raw, raw, err = await asyncio.wait_for(
                loop.run_in_executor(_executor, compute),
                timeout=COMPUTE_TIMEOUT,
            )
        except asyncio.TimeoutError:
            return JSONResponse(
                content={"error": f"Computation timed out after {COMPUTE_TIMEOUT}s. Try a smaller or simpler matrix."},
                status_code=504,
            )

        if err:
            return JSONResponse(content={"error": err}, status_code=400)

        steps = steps_html(steps_raw) if steps_raw and steps_raw.strip() else ""
        return JSONResponse(content={"result": result, "steps": steps, "raw": raw or "", "input_latex": input_latex})

    except Exception as e:
        traceback.print_exc()
        return JSONResponse(content={"error": str(e)}, status_code=500)


# ---------------------------------------------------------------------------
# Equivalent Statements endpoint
# ---------------------------------------------------------------------------

@app.post("/api/equivalent")
async def equivalent_statements(request: Request):
    try:
        data = await request.json()
        matrix_str = data.get("matrix", "")

        try:
            mat = parse_matrix(matrix_str)
        except Exception as e:
            return JSONResponse(
                content={"error": f"Failed to parse matrix: {e}"}, status_code=400
            )

        rows, cols = mat.rows, mat.cols
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            rank = mat.rank()
        nullity = cols - rank

        statements = []
        category = ""

        if rows == cols:
            det = mat.det()
            is_invertible = det != 0

            if is_invertible:
                category = f"Square Matrix ({rows}×{rows}) — Invertible (Non-Singular)"
                statements = [
                    "\\(\\det(A) \\neq 0\\)",
                    "\\(AB = BA = I\\) (inverse exists)",
                    "\\(A\\) has both a left and a right inverse",
                    "\\(A^T\\) is invertible",
                    "\\(A\\) is row equivalent to \\(I\\) (RREF is \\(I\\))",
                    "\\(A\\) can be expressed as a product of elementary matrices",
                    "\\(0\\) is not an eigenvalue of \\(A\\)",
                    "\\(Ax = 0\\) has only the trivial solution \\(x = 0\\)",
                    "\\(Ax = b\\) has a unique solution for all \\(b\\)",
                    "\\(T(x) = Ax\\) is bijective (injective & surjective)",
                    "\\(\\mathrm{Null}(A) = \\{0\\}\\) and \\(\\mathrm{nullity}(A) = 0\\)",
                    "Columns of \\(A\\) are linearly independent",
                    "Rows of \\(A\\) are linearly independent",
                    "\\(\\mathrm{Col}(A) = \\mathbb{R}^n\\)",
                    "\\(\\mathrm{Row}(A) = \\mathbb{R}^n\\)",
                    f"\\(\\mathrm{{rank}}(A) = {rows}\\) (full rank)",
                ]
            else:
                category = f"Square Matrix ({rows}×{rows}) — Singular (Non-Invertible)"
                statements = [
                    "\\(\\det(A) = 0\\)",
                    "\\(A\\) has no left inverse and no right inverse",
                    "\\(A^T\\) is singular",
                    "\\(A\\) is not row equivalent to \\(I\\)",
                    "RREF of \\(A\\) contains at least one zero row",
                    "RREF of \\(A\\) contains non-pivot columns",
                    "\\(0\\) is an eigenvalue of \\(A\\)",
                    "\\(Ax = 0\\) has non-trivial solutions",
                    "For some \\(b\\), \\(Ax = b\\) is inconsistent",
                    "\\(T(x) = Ax\\) is neither injective nor surjective",
                    "\\(\\mathrm{Null}(A) \\neq \\{0\\}\\) and \\(\\mathrm{nullity}(A) > 0\\)",
                    "Columns of \\(A\\) are linearly dependent",
                    "Rows of \\(A\\) are linearly dependent",
                    "\\(\\mathrm{Col}(A) \\neq \\mathbb{R}^n\\)",
                    "\\(\\mathrm{Row}(A) \\neq \\mathbb{R}^n\\)",
                    f"\\(\\mathrm{{rank}}(A) < {rows}\\)",
                ]
        else:
            if rank == cols:
                category = f"Rectangular Matrix ({rows}×{cols}) — Full Column Rank"
                statements = [
                    f"\\(\\mathrm{{rank}}(A) = {cols}\\) (maximum possible rank)",
                    "Columns of \\(A\\) are linearly independent",
                    "\\(Ax = 0\\) has only the trivial solution",
                    "\\(A^T A\\) is invertible",
                    "\\(A\\) has a left inverse",
                    "\\(T(x) = Ax\\) is injective (one-to-one)",
                    "If \\(Ax = v\\) is consistent, the solution is unique",
                    "Least squares: unique solution for \\(Ax = b\\)",
                ]
            elif rank == rows:
                category = f"Rectangular Matrix ({rows}×{cols}) — Full Row Rank"
                statements = [
                    f"\\(\\mathrm{{rank}}(A) = {rows}\\) (maximum possible rank)",
                    "Rows of \\(A\\) are linearly independent",
                    "Columns of \\(A\\) span \\(\\mathbb{R}^m\\)",
                    "\\(Ax = b\\) is consistent for every \\(b\\)",
                    "\\(AA^T\\) is invertible",
                    "\\(A\\) has a right inverse",
                    "\\(T(x) = Ax\\) is surjective (onto)",
                    f"\\(\\mathrm{{nullity}}(A) = {cols} - {rows} = {cols - rows}\\)",
                ]
            else:
                category = f"Rectangular Matrix ({rows}×{cols}) — Rank Deficient"
                statements = [
                    "Both \\(A^T A\\) and \\(AA^T\\) are singular",
                    "\\(A\\) has neither a left nor a right inverse",
                    "Columns are linearly dependent AND rows are linearly dependent",
                    "\\(\\mathrm{Col}(A) \\neq \\mathbb{R}^m\\) AND \\(\\mathrm{Row}(A) \\neq \\mathbb{R}^n\\)",
                    "\\(Ax = 0\\) has non-trivial solutions",
                    "\\(Ax = b\\) is inconsistent for some \\(b\\)",
                    "RREF contains non-pivot columns AND zero rows",
                    f"\\(\\mathrm{{nullity}}(A) > {max(0, cols - rows)}\\)",
                ]

        return JSONResponse(content={
            "category": category,
            "statements": statements,
            "properties": {
                "rows": rows,
                "cols": cols,
                "rank": int(rank),
                "nullity": int(nullity),
            },
        })

    except Exception as e:
        traceback.print_exc()
        return JSONResponse(content={"error": str(e)}, status_code=500)


# ---------------------------------------------------------------------------
# Parse endpoint (used by frontend blur-autosave and text→grid toggle)
# ---------------------------------------------------------------------------

@app.post("/api/parse")
async def parse_matrix_endpoint(request: Request):
    try:
        data = await request.json()
        s = data.get("matrix", "").strip()
        if not s:
            return JSONResponse(content={"error": "Empty input"}, status_code=400)
        M = parse_matrix(s)
        cells = [[str(M[r, c]) for c in range(M.cols)] for r in range(M.rows)]
        return JSONResponse(content={"rows": M.rows, "cols": M.cols, "cells": cells})
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=400)


# ---------------------------------------------------------------------------
# Serve frontend
# ---------------------------------------------------------------------------

@app.get("/")
async def read_index():
    return FileResponse("src/gui/static/index.html")
