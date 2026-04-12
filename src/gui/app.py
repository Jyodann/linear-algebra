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

def parse_matrix(s: str) -> Matrix:
    """Try LaTeX → nested-list literal → from_str ([v v; v v] format)."""
    s = s.strip()
    # LaTeX
    if "begin" in s or ("\\" in s and any(c in s for c in "{}[]")):
        return Matrix.from_latex(s, verbosity=0)
    # Pure numeric nested list  e.g. [[1, 2], [3, 4]]
    try:
        list_data = ast.literal_eval(s)
        if isinstance(list_data, list):
            # Flatten inner lists to sym expressions
            parsed = []
            for row in list_data:
                if isinstance(row, list):
                    parsed.append([sym.sympify(v) for v in row])
                else:
                    parsed.append([sym.sympify(row)])
            return Matrix(parsed)
    except Exception:
        pass
    # from_str: "[v00 v01; v10 v11]" or text-mode variants
    return Matrix.from_str(s)


def capture(fn):
    """Redirect stdout + suppress warnings, return (result, raw_str)."""
    buf = io.StringIO()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        with contextlib.redirect_stdout(buf):
            result = fn()
    return result, buf.getvalue()

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

        loop = asyncio.get_event_loop()

        def compute():
            """All heavy CPU work runs here — in the thread pool, so the event loop is free."""
            result = ""
            steps_raw = ""

            # ------------------------------------------------------------------
            # Row Reduction
            # ------------------------------------------------------------------
            if operation == "rref":
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", UserWarning)
                    res = A.rref()
                result = f"\\[ {sym.latex(res[0])} \\]"

            elif operation == "ref":
                res, steps_raw = capture(lambda: A.ref(verbosity=2))
                result = f"\\[ {sym.latex(res.U)} \\]"

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

            elif operation == "qr":
                _, steps_raw = capture(lambda: A.gram_schmidt(verbosity=1))
                Q, R = A.QRdecomposition()
                result = (
                    f"\\( Q = {sym.latex(Q)}, \\quad R = {sym.latex(R)} \\)"
                )

            elif operation == "gram_schmidt":
                gs_result, steps_raw = capture(lambda: A.gram_schmidt(verbosity=1))
                result = f"\\[ {sym.latex(gs_result)} \\]"

            elif operation == "svd":
                res = A.singular_value_decomposition(verbosity=0)
                result = (
                    f"\\( U = {sym.latex(res.U)}, \\quad "
                    f"\\Sigma = {sym.latex(res.S)}, \\quad "
                    f"V^T = {sym.latex(res.V)} \\)"
                )

            # ------------------------------------------------------------------
            # Properties
            # ------------------------------------------------------------------
            elif operation == "det":
                d = A.det()
                result = f"\\( \\det(A) = {sym.latex(d)} \\)"

            elif operation == "inv":
                res, steps_raw = capture(lambda: A.inverse(option="right", verbosity=1))
                result = f"\\( A^{{-1}} = {sym.latex(res)} \\)"

            elif operation == "rank":
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    r = A.rank()
                nullity = A.cols - r
                result = f"\\( \\mathrm{{rank}}(A) = {r}, \\quad \\mathrm{{nullity}}(A) = {nullity} \\)"

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

            elif operation == "diagonalize":
                res, steps_raw = capture(lambda: A.diagonalize(verbosity=1))
                result = (
                    f"\\( P = {sym.latex(res.P)}, \\quad D = {sym.latex(res.D)} \\)"
                )

            elif operation == "orth_diagonalize":
                res, steps_raw = capture(lambda: A.orthogonally_diagonalize(verbosity=1))
                result = (
                    f"\\( P = {sym.latex(res.P)}, \\quad D = {sym.latex(res.D)} \\)"
                )

            # ------------------------------------------------------------------
            # Vector Spaces
            # ------------------------------------------------------------------
            elif operation == "nullspace":
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    ns = A.nullspace()
                if not ns:
                    result = f"\\( \\mathrm{{Null}}(A) = \\{{0\\}} \\)"
                else:
                    vecs = ", ".join(sym.latex(v) for v in ns)
                    result = (
                        f"\\( \\mathrm{{Null}}(A) = \\operatorname{{span}}\\{{ {vecs} \\}} \\)"
                    )

            elif operation == "colspace":
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    cs = A.columnspace()
                vecs = ", ".join(sym.latex(v) for v in cs)
                result = (
                    f"\\( \\mathrm{{Col}}(A) = \\operatorname{{span}}\\{{ {vecs} \\}} \\)"
                )

            elif operation == "orth_complement":
                res, steps_raw = capture(lambda: A.orthogonal_complement(verbosity=1))
                result = (
                    f"\\( (\\mathrm{{Col}}(A))^\\perp = {sym.latex(res)} \\)"
                )

            elif operation == "col_constraints":
                res, steps_raw = capture(lambda: A.column_constraints(verbosity=1))
                result = f"\\[ {sym.latex(res)} \\]"

            elif operation == "extend_basis":
                res, steps_raw = capture(lambda: A.extend_basis(verbosity=2))
                result = f"\\[ {sym.latex(res)} \\]"

            # ------------------------------------------------------------------
            # Linear Systems
            # ------------------------------------------------------------------
            elif operation == "solve":
                b_vec = b if b is not None else _zero_col_vector(A.rows)
                try:
                    sol = A.solve(b_vec)
                    result = f"\\[ {sym.latex(sol)} \\]"
                except ValueError:
                    result = "No solution"

            elif operation == "least_squares":
                b_vec = b if b is not None else _zero_col_vector(A.rows)
                res, steps_raw = capture(lambda: A.solve_least_squares(b_vec, verbosity=1))
                result = f"\\( \\hat{{x}} = {sym.latex(res)} \\)"

            elif operation == "projection":
                if A.cols < 2:
                    return None, None, "Matrix must have at least 2 columns (augmented [A|b])"
                Acols = A.select_cols(*range(A.cols - 1))
                b_col = A.select_cols(A.cols - 1)
                res, steps_raw = capture(
                    lambda: Acols.solve_least_squares(b_col, verbosity=1)
                )
                x_hat = res
                p = Acols @ x_hat
                result = (
                    f"\\( \\hat{{x}} = {sym.latex(x_hat)}, \\quad "
                    f"p = A\\hat{{x}} = {sym.latex(p)} \\)"
                )

            # ------------------------------------------------------------------
            # Subspaces
            # ------------------------------------------------------------------
            elif operation == "intersect":
                if B is None:
                    return None, None, "This operation requires a second matrix (matrix2)."
                res, steps_raw = capture(lambda: A.intersect_subspace(B, verbosity=2))
                result = f"\\[ {sym.latex(res)} \\]"

            elif operation == "transition":
                if B is None:
                    return None, None, "This operation requires a second matrix (matrix2)."
                res, steps_raw = capture(lambda: A.transition_matrix(B, verbosity=2))
                result = (
                    f"\\( P_{{B \\leftarrow A}} = {sym.latex(res)} \\)"
                )

            # ------------------------------------------------------------------
            # Symbolic / Parametric
            # ------------------------------------------------------------------
            elif operation == "eval_cases":
                b_vec = b if b is not None else _zero_col_vector(A.rows)
                _, steps_raw = capture(lambda: A.evaluate_cases(b_vec))
                result = "See steps below."

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

            else:
                return None, None, f"Unknown operation: {operation}"

            return result, steps_raw, None  # (result, steps, error)

        try:
            result, steps_raw, err = await asyncio.wait_for(
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
        return JSONResponse(content={"result": result, "steps": steps})

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
# Serve frontend
# ---------------------------------------------------------------------------

@app.get("/")
async def read_index():
    return FileResponse("src/gui/static/index.html")
