from fastapi import FastAPI, Request, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import sympy as sym
from ma1522.symbolic import Matrix
from ma1522.utils import display
import traceback

app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="src/gui/static"), name="static")

class MatrixRequest(BaseModel):
    matrix: str
    operation: str

@app.post("/api/process")
async def process_matrix(request: Request):
    try:
        data = await request.json()
        matrix_str = data.get("matrix")
        operation = data.get("operation")

        print(f"Received matrix: {matrix_str}, operation: {operation}")

        # Parse matrix
        # Try LaTeX first, then string, then python list
        try:
            if "begin" in matrix_str or "\\" in matrix_str:
                 mat = Matrix.from_latex(matrix_str, verbosity=0)
            else:
                # Try to parse as python list first
                import ast
                try:
                    list_data = ast.literal_eval(matrix_str)
                    if isinstance(list_data, list):
                        mat = Matrix(list_data)
                    else:
                        mat = Matrix.from_str(matrix_str)
                except:
                     mat = Matrix.from_str(matrix_str)
        except Exception as e:
            return JSONResponse(content={"error": f"Failed to parse matrix: {str(e)}"}, status_code=400)

        result = ""
        steps = []

        # Helper to capture display output (mocking display for now or just using return values)
        # Since the library prints a lot, we might want to capture stdout or just use the return values.
        # For this MVP, we will use the return values and format them as LaTeX.

        if operation == "rref":
            res = mat.rref()
            result = f"$$ {sym.latex(res[0])} $$"
        elif operation == "det":
            res = mat.det()
            result = f"$$ {sym.latex(res)} $$"
        elif operation == "inv":
            res = mat.inv()
            result = f"$$ {sym.latex(res)} $$"
        elif operation == "eigenvals":
            res = mat.eigenvals()
            # Format eigenvalues nicely
            latex_res = ", ".join([f"{sym.latex(k)}: {v}" for k, v in res.items()])
            result = f"$$ {latex_res} $$"
        elif operation == "eigenvects":
            res = mat.eigenvects()
            # res is a list of tuples (eigenval, multiplicity, [eigenvectors])
            latex_parts = []
            for val, mult, vecs in res:
                vec_strs = ", ".join([sym.latex(v) for v in vecs])
                latex_parts.append(f"\\lambda = {sym.latex(val)} (mult: {mult}): \\left[ {vec_strs} \\right]")
            result = "$$ " + " \\\\ ".join(latex_parts) + " $$"
        elif operation == "diagonalize":
            P, D = mat.diagonalize()
            result = f"$$ P = {sym.latex(P)}, \\quad D = {sym.latex(D)} $$"
        elif operation == "lu":
            L, U, _ = mat.LUdecomposition()
            result = f"$$ L = {sym.latex(L)}, \\quad U = {sym.latex(U)} $$"
        elif operation == "qr":
            Q, R = mat.QRdecomposition()
            result = f"$$ Q = {sym.latex(Q)}, \\quad R = {sym.latex(R)} $$"
        elif operation == "svd":
            U, S, V_T = mat.singular_value_decomposition()
            result = f"$$ U = {sym.latex(U)}, \\quad S = {sym.latex(S)}, \\quad V^T = {sym.latex(V_T)} $$"
        else:
            return JSONResponse(content={"error": "Unknown operation"}, status_code=400)

        return JSONResponse(content={"result": result})

    except Exception as e:
        traceback.print_exc()
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.post("/api/equivalent")
async def equivalent_statements(request: Request):
    try:
        data = await request.json()
        matrix_str = data.get("matrix")
        
        # Parse matrix (reuse logic)
        try:
            if "begin" in matrix_str or "\\" in matrix_str:
                 mat = Matrix.from_latex(matrix_str, verbosity=0)
            else:
                import ast
                try:
                    list_data = ast.literal_eval(matrix_str)
                    if isinstance(list_data, list):
                        mat = Matrix(list_data)
                    else:
                        mat = Matrix.from_str(matrix_str)
                except:
                     mat = Matrix.from_str(matrix_str)
        except Exception as e:
            return JSONResponse(content={"error": f"Failed to parse matrix: {str(e)}"}, status_code=400)

        rows, cols = mat.rows, mat.cols
        rank = mat.rank()
        nullity = cols - rank
        
        statements = []
        category = ""
        
        if rows == cols:
            det = mat.det()
            is_invertible = det != 0
            
            if is_invertible:
                category = f"Square Matrix ({rows}x{rows}) - Invertible (Non-Singular)"
                statements = [
                    "det(A) ≠ 0",
                    "AB = BA = I (Inverse exists)",
                    "A has both a left and a right inverse",
                    "A^T is invertible",
                    "A is row equivalent to I (RREF is I)",
                    "A can be expressed as a product of elementary matrices",
                    "Eigenvalues: 0 is not an eigenvalue of A",
                    "Ax = 0 has only the trivial solution (x = 0)",
                    "Ax = b has a unique solution for all b",
                    "T(x) = Ax is Bijective (Injective & Surjective)",
                    "Null(A) = {0} and nullity(A) = 0",
                    "Columns are linearly independent",
                    "Rows are linearly independent",
                    "Columns span R^n (Col(A) = R^n)",
                    "Rows span R^n (Row(A) = R^n)",
                    f"rank(A) = {rows} (Full Rank)"
                ]
            else:
                category = f"Square Matrix ({rows}x{rows}) - Singular (Non-Invertible)"
                statements = [
                    "det(A) = 0",
                    "A has no left inverse and no right inverse",
                    "A^T is singular",
                    "A is not row equivalent to I",
                    "RREF of A contains at least one zero row",
                    "RREF of A contains non-pivot columns",
                    "Eigenvalues: 0 is an eigenvalue of A",
                    "Ax = 0 has non-trivial solutions",
                    "For some b, Ax = b is inconsistent",
                    "T(x) = Ax is neither injective nor surjective",
                    "Null(A) ≠ {0} and nullity(A) > 0",
                    "Columns are linearly dependent",
                    "Rows are linearly dependent",
                    "Columns do not span R^n",
                    "Rows do not span R^n",
                    f"rank(A) < {rows}"
                ]
        else:
            # Rectangular
            if rank == cols: # Full Column Rank (Tall usually)
                category = f"Rectangular Matrix ({rows}x{cols}) - Full Column Rank"
                statements = [
                    f"rank(A) = {cols} (Max possible rank)",
                    "Columns of A are linearly independent",
                    "Ax = 0 has only the trivial solution",
                    "A^T A is invertible",
                    "A has a Left Inverse",
                    "T(x) = Ax is Injective (One-to-One)",
                    "If Ax = v is consistent, the solution is unique",
                    "Least Squares: Unique solution for Ax = b"
                ]
            elif rank == rows: # Full Row Rank (Wide usually)
                category = f"Rectangular Matrix ({rows}x{cols}) - Full Row Rank"
                statements = [
                    f"rank(A) = {rows} (Max possible rank)",
                    "Rows of A are linearly independent",
                    "Columns of A span R^m",
                    "Ax = b is consistent for every b",
                    "A A^T is invertible",
                    "A has a Right Inverse",
                    "T(x) = Ax is Surjective (Onto)",
                    f"nullity(A) = {cols} - {rows} = {cols - rows}"
                ]
            else:
                category = f"Rectangular Matrix ({rows}x{cols}) - Rank Deficient"
                statements = [
                    "Both A^T A and A A^T are singular",
                    "A has neither a left nor a right inverse",
                    "Columns are dependent AND Rows are dependent",
                    "Col(A) ≠ R^m AND Row(A) ≠ R^n",
                    "Ax = 0 has non-trivial solutions",
                    "Ax = b is inconsistent for some b",
                    "RREF contains non-pivot columns AND zero rows",
                    f"nullity(A) > {max(0, cols - rows)}"
                ]

        return JSONResponse(content={
            "category": category,
            "statements": statements,
            "properties": {
                "rows": rows,
                "cols": cols,
                "rank": int(rank),
                "nullity": int(nullity)
            }
        })

    except Exception as e:
        traceback.print_exc()
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.get("/")
async def read_index():
    from fastapi.responses import FileResponse
    return FileResponse("src/gui/static/index.html")
