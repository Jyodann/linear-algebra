# GUI Enhancements Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix decimal support, add chain matrix multiplication with modifiers, copy-to-clipboard, calculation history drawer, and scrolling for long results.

**Architecture:** Backend changes in `app.py` (nsimplify, raw field, chain_multiply op). Frontend changes across `index.html`/`script.js`/`style.css` (new UI elements, JS state, CSS fixes). Tests in `tests/test_gui_api.py`.

**Tech Stack:** FastAPI + SymPy backend; vanilla JS + CSS frontend; pytest + `uv run pytest` for tests.

---

## File Map

| File | Changes |
|---|---|
| `src/gui/app.py` | `parse_matrix` nsimplify; `matrix_to_raw` helper; `raw` field on all ops; `matrix3`/`mod1-3` params; `chain_multiply` op; return 4-tuple |
| `tests/test_gui_api.py` | Tests for decimal fix, raw field, chain_multiply |
| `src/gui/static/style.css` | Scroll fixes; mod-btn; copy-btn; history drawer |
| `src/gui/static/index.html` | Arithmetic group; modifier buttons; cardC; addM3Btn; answerToolbar/copyBtn; historyBtn; history drawer HTML |
| `src/gui/static/script.js` | chain state; getModStr; wireModBtn; configureForChain; updated showSecondary/runOperation; copy button logic; history array + drawer |

---

## Task 1: CSS Scrolling Fix

**Files:** Modify `src/gui/static/style.css`

- [ ] **Step 1: Apply three CSS rule changes**

In `style.css`, make exactly these three changes:

Change 1 — `.answer-card` (line ~458): `overflow: hidden` → `overflow: visible`
```css
.answer-card {
  background: var(--surface);
  border-radius: 12px;
  box-shadow: var(--shadow-md);
  overflow: visible;
  min-height: 140px;
}
```

Change 2 — `.result-body` (line ~489): `align-items: center` → `align-items: flex-start`
```css
.result-body {
  display: flex;
  align-items: flex-start;
  justify-content: center;
  min-height: 140px;
  padding: 2rem 2.5rem;
  text-align: center;
  font-size: 1.1rem;
  overflow-x: auto;
}
```

Change 3 — `mjx-container` (line ~705): `overflow-y: hidden` → `overflow-y: visible`
```css
mjx-container { overflow-x: auto; overflow-y: visible; max-width: 100%; }
```

- [ ] **Step 2: Commit**
```bash
git add src/gui/static/style.css
git commit -m "fix: remove overflow clipping on answer card and mjx-container"
```

---

## Task 2: Backend Decimal Fix

**Files:** Modify `src/gui/app.py`, `tests/test_gui_api.py`

- [ ] **Step 1: Write the failing test**

Add to `tests/test_gui_api.py`:
```python
def test_diagonalize_with_decimals():
    response = client.post(
        "/api/process",
        json={"matrix": "[[2.0, 0.0], [0.0, 3.0]]", "operation": "diagonalize"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "error" not in data
    assert "result" in data
    assert "P" in data["result"]

def test_eigenvals_with_decimals():
    response = client.post(
        "/api/process",
        json={"matrix": "[[1.5, 0.0], [0.0, 2.5]]", "operation": "eigenvals"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "error" not in data
    assert "3/2" in data["result"] or "1.5" in data["result"]
```

- [ ] **Step 2: Run tests to verify they fail**
```bash
uv run pytest tests/test_gui_api.py::test_diagonalize_with_decimals tests/test_gui_api.py::test_eigenvals_with_decimals -v
```
Expected: FAIL (SymPy raises on float matrix)

- [ ] **Step 3: Refactor `parse_matrix` to single-return with nsimplify**

Replace the entire `parse_matrix` function in `src/gui/app.py`:
```python
def parse_matrix(s: str) -> Matrix:
    """Try LaTeX → nested-list literal → from_str ([v v; v v] format).

    All float entries are converted to exact rationals so that symbolic
    operations (eigenvals, diagonalize, nullspace, etc.) work correctly.
    """
    s = s.strip()

    if "begin" in s or ("\\" in s and any(c in s for c in "{}[]")):
        M = Matrix.from_latex(s, verbosity=0)
    else:
        M = None
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
        if M is None:
            M = Matrix.from_str(s)

    return M.applyfunc(lambda x: sym.nsimplify(x, rational=True))
```

- [ ] **Step 4: Run tests to verify they pass**
```bash
uv run pytest tests/test_gui_api.py::test_diagonalize_with_decimals tests/test_gui_api.py::test_eigenvals_with_decimals -v
```
Expected: PASS

- [ ] **Step 5: Run full test suite to confirm no regressions**
```bash
uv run pytest tests/test_gui_api.py -v
```
Expected: all 5 tests PASS

- [ ] **Step 6: Commit**
```bash
git add src/gui/app.py tests/test_gui_api.py
git commit -m "fix: convert float matrix entries to rationals before symbolic operations"
```

---

## Task 3: Backend `raw` Field

**Files:** Modify `src/gui/app.py`, `tests/test_gui_api.py`

- [ ] **Step 1: Write failing tests**

Add to `tests/test_gui_api.py`:
```python
def test_raw_field_single_matrix():
    response = client.post(
        "/api/process",
        json={"matrix": "[[1, 2], [3, 4]]", "operation": "rref"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "raw" in data
    assert data["raw"].startswith("[")

def test_raw_field_decomposition():
    response = client.post(
        "/api/process",
        json={"matrix": "[[1, 2], [3, 4]]", "operation": "lu"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "raw" in data
    assert "P=" in data["raw"]
    assert "L=" in data["raw"]
    assert "U=" in data["raw"]
```

- [ ] **Step 2: Run tests to verify they fail**
```bash
uv run pytest tests/test_gui_api.py::test_raw_field_single_matrix tests/test_gui_api.py::test_raw_field_decomposition -v
```
Expected: FAIL (`KeyError: 'raw'`)

- [ ] **Step 3: Add `matrix_to_raw` helper**

Add after the `capture` function in `src/gui/app.py`:
```python
def matrix_to_raw(M) -> str:
    """Convert a Matrix to '[r0c0 r0c1; r1c0 r1c1]' format (from_str-compatible)."""
    rows = []
    for r in range(M.rows):
        rows.append(' '.join(str(M[r, c]) for c in range(M.cols)))
    return '[' + '; '.join(rows) + ']'
```

- [ ] **Step 4: Change `compute()` return from 3-tuple to 4-tuple**

Inside `compute()`, update the success return at the very end from:
```python
return result, steps_raw, None  # (result, steps, error)
```
to:
```python
return result, steps_raw, raw, None  # (result, steps, raw, error)
```

Update the three error-return paths inside `compute()`:
```python
# projection check
return None, None, None, "Matrix must have at least 2 columns (augmented [A|b])"

# intersect / transition B check
return None, None, None, "This operation requires a second matrix (matrix2)."

# unknown op
return None, None, None, f"Unknown operation: {operation}"
```

Update the unpacking in `process_matrix`:
```python
result, steps_raw, raw, err = await asyncio.wait_for(
    loop.run_in_executor(_executor, compute),
    timeout=COMPUTE_TIMEOUT,
)
```

Update the success response:
```python
steps = steps_html(steps_raw) if steps_raw and steps_raw.strip() else ""
return JSONResponse(content={"result": result, "steps": steps, "raw": raw or ""})
```

- [ ] **Step 5: Add `raw` variable to every operation branch inside `compute()`**

Add the following `raw = ...` line to each operation. This is mechanical — add it immediately after `result = ...` in each branch:

```python
# rref
result = f"\\[ {sym.latex(res[0])} \\]"
raw = matrix_to_raw(res[0])

# ref
result = f"\\[ {sym.latex(res.U)} \\]"
raw = matrix_to_raw(res.U)

# lu
result = (f"\\( P = {sym.latex(res.P)}, \\quad "
          f"L = {sym.latex(res.L)}, \\quad "
          f"U = {sym.latex(res.U)} \\)")
raw = f"P={matrix_to_raw(res.P)}\nL={matrix_to_raw(res.L)}\nU={matrix_to_raw(res.U)}"

# qr  (Q and R are separate variables — Q, R = A.QRdecomposition())
result = (f"\\( Q = {sym.latex(Q)}, \\quad R = {sym.latex(R)} \\)")
raw = f"Q={matrix_to_raw(Q)}\nR={matrix_to_raw(R)}"

# gram_schmidt
result = f"\\[ {sym.latex(gs_result)} \\]"
raw = matrix_to_raw(gs_result)

# svd
result = (f"\\( U = {sym.latex(res.U)}, \\quad "
          f"\\Sigma = {sym.latex(res.S)}, \\quad "
          f"V^T = {sym.latex(res.V)} \\)")
raw = f"U={matrix_to_raw(res.U)}\nS={matrix_to_raw(res.S)}\nV={matrix_to_raw(res.V)}"

# det
result = f"\\( \\det(A) = {sym.latex(d)} \\)"
raw = str(d)

# inv
result = f"\\( A^{{-1}} = {sym.latex(res)} \\)"
raw = matrix_to_raw(res)

# rank
result = f"\\( \\mathrm{{rank}}(A) = {r}, \\quad \\mathrm{{nullity}}(A) = {nullity} \\)"
raw = f"rank={r}\nnullity={nullity}"

# eigenvals
result = "\\[ " + ", \\quad ".join(parts) + " \\]"
raw = ', '.join(str(v) for v in evals.keys())

# eigenvects
result = "\\[ " + " \\\\[6pt] ".join(parts) + " \\]"
raw = ""

# diagonalize
result = (f"\\( P = {sym.latex(res.P)}, \\quad D = {sym.latex(res.D)} \\)")
raw = f"P={matrix_to_raw(res.P)}\nD={matrix_to_raw(res.D)}"

# orth_diagonalize
result = (f"\\( P = {sym.latex(res.P)}, \\quad D = {sym.latex(res.D)} \\)")
raw = f"P={matrix_to_raw(res.P)}\nD={matrix_to_raw(res.D)}"

# nullspace
if not ns:
    result = f"\\( \\mathrm{{Null}}(A) = \\{{0\\}} \\)"
    raw = ""
else:
    vecs = ", ".join(sym.latex(v) for v in ns)
    result = (f"\\( \\mathrm{{Null}}(A) = \\operatorname{{span}}\\{{ {vecs} \\}} \\)")
    raw = '\n'.join(matrix_to_raw(v) for v in ns)

# colspace
vecs = ", ".join(sym.latex(v) for v in cs)
result = (f"\\( \\mathrm{{Col}}(A) = \\operatorname{{span}}\\{{ {vecs} \\}} \\)")
raw = '\n'.join(matrix_to_raw(v) for v in cs)

# orth_complement
result = (f"\\( (\\mathrm{{Col}}(A))^\\perp = {sym.latex(res)} \\)")
raw = matrix_to_raw(res)

# col_constraints
result = f"\\[ {sym.latex(res)} \\]"
raw = matrix_to_raw(res)

# extend_basis
result = f"\\[ {sym.latex(res)} \\]"
raw = matrix_to_raw(res)

# solve — update the try/except block:
try:
    sol = A.solve(b_vec)
    result = f"\\[ {sym.latex(sol)} \\]"
    raw = matrix_to_raw(sol)
except ValueError:
    result = "No solution"
    raw = ""

# least_squares
result = f"\\( \\hat{{x}} = {sym.latex(res)} \\)"
raw = matrix_to_raw(res)

# projection
x_hat = res
p = Acols @ x_hat
result = (f"\\( \\hat{{x}} = {sym.latex(x_hat)}, \\quad "
          f"p = A\\hat{{x}} = {sym.latex(p)} \\)")
raw = f"x_hat={matrix_to_raw(x_hat)}\np={matrix_to_raw(p)}"

# intersect
result = f"\\[ {sym.latex(res)} \\]"
raw = matrix_to_raw(res)

# transition
result = (f"\\( P_{{B \\leftarrow A}} = {sym.latex(res)} \\)")
raw = matrix_to_raw(res)

# eval_cases
result = "See steps below."
raw = ""

# find_cases
# (after building result string)
raw = ""
```

- [ ] **Step 6: Run tests**
```bash
uv run pytest tests/test_gui_api.py -v
```
Expected: all 7 tests PASS

- [ ] **Step 7: Commit**
```bash
git add src/gui/app.py tests/test_gui_api.py
git commit -m "feat: add raw field to all operation responses for clipboard copy"
```

---

## Task 4: Backend Chain Multiply

**Files:** Modify `src/gui/app.py`, `tests/test_gui_api.py`

- [ ] **Step 1: Write failing tests**

Add to `tests/test_gui_api.py`:
```python
def test_chain_multiply_two_matrices():
    response = client.post(
        "/api/process",
        json={
            "operation": "chain_multiply",
            "matrix":  "[[1, 0], [0, 1]]",
            "matrix2": "[[2, 0], [0, 3]]",
            "mod1": "none",
            "mod2": "none",
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "error" not in data
    assert "2" in data["result"]
    assert "3" in data["result"]

def test_chain_multiply_three_matrices():
    response = client.post(
        "/api/process",
        json={
            "operation": "chain_multiply",
            "matrix":  "[[1, 0], [0, 1]]",
            "matrix2": "[[2, 0], [0, 2]]",
            "matrix3": "[[3, 0], [0, 3]]",
            "mod1": "none",
            "mod2": "none",
            "mod3": "none",
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "error" not in data
    assert "6" in data["result"]

def test_chain_multiply_transpose():
    # A^T @ A for [[1,2],[3,4]] should give [[10,14],[14,20]]
    response = client.post(
        "/api/process",
        json={
            "operation": "chain_multiply",
            "matrix":  "[[1, 2], [3, 4]]",
            "matrix2": "[[1, 2], [3, 4]]",
            "mod1": "T",
            "mod2": "none",
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "error" not in data
    assert "10" in data["result"]

def test_chain_multiply_inverse():
    # A^{-1} @ A = I
    response = client.post(
        "/api/process",
        json={
            "operation": "chain_multiply",
            "matrix":  "[[1, 2], [3, 4]]",
            "matrix2": "[[1, 2], [3, 4]]",
            "mod1": "inv",
            "mod2": "none",
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "error" not in data
    assert "1" in data["result"]
```

- [ ] **Step 2: Run tests to verify they fail**
```bash
uv run pytest tests/test_gui_api.py::test_chain_multiply_two_matrices tests/test_gui_api.py::test_chain_multiply_three_matrices -v
```
Expected: FAIL (`Unknown operation: chain_multiply`)

- [ ] **Step 3: Add matrix3, mod1/2/3 extraction to `process_matrix`**

In `process_matrix`, after the existing `matrix2_str = data.get("matrix2", "")` line, add:
```python
matrix3_str = data.get("matrix3", "")
mod1 = data.get("mod1", "none")
mod2 = data.get("mod2", "none")
mod3 = data.get("mod3", "none")
```

After the existing `B = None` block, add:
```python
C = None
if matrix3_str and matrix3_str.strip():
    try:
        C = parse_matrix(matrix3_str)
    except Exception as e:
        return JSONResponse(content={"error": f"Failed to parse matrix3: {e}"}, status_code=400)
```

- [ ] **Step 4: Add `chain_multiply` operation inside `compute()`**

Add after the `find_cases` block, before `else: return None, None, None, f"Unknown operation..."`:

```python
elif operation == "chain_multiply":
    def _apply_mod(M, mod):
        if mod == "T":
            return M.T
        elif mod == "inv":
            return M.inv()
        elif mod == "inv_T":
            return M.inv().T
        return M

    operands = [(A, mod1)]
    if B is not None:
        operands.append((B, mod2))
    if C is not None:
        operands.append((C, mod3))

    modified = [_apply_mod(M, m) for M, m in operands]
    result_mat = modified[0]
    for M in modified[1:]:
        result_mat = result_mat @ M
    result_mat = result_mat.doit()

    result = f"\\[ {sym.latex(result_mat)} \\]"
    raw = matrix_to_raw(result_mat)
```

- [ ] **Step 5: Run all tests**
```bash
uv run pytest tests/test_gui_api.py -v
```
Expected: all 11 tests PASS

- [ ] **Step 6: Commit**
```bash
git add src/gui/app.py tests/test_gui_api.py
git commit -m "feat: add chain matrix multiplication with transpose and inverse modifiers"
```

---

## Task 5: Frontend Chain Multiply UI

**Files:** Modify `src/gui/static/index.html`, `src/gui/static/script.js`, `src/gui/static/style.css`

- [ ] **Step 1: Add HTML — Arithmetic group + modifier buttons + cardC + addM3Btn**

In `index.html`, insert the **Arithmetic op-group** as the first child of `.ops-panel` (before Row Reduction):
```html
<!-- Arithmetic -->
<div class="op-group" data-color="var(--accent-light)">
  <button class="group-header" type="button" aria-expanded="false">
    <span class="group-label">Arithmetic</span>
    <svg class="chevron" width="12" height="12" viewBox="0 0 12 12" fill="none" aria-hidden="true"><path d="M2 4l4 4 4-4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
  </button>
  <div class="group-body">
    <div class="group-btns">
      <button class="op-btn" data-op="chain_multiply" data-needs="chain">Chain Multiply</button>
    </div>
  </div>
</div>
```

In `index.html`, add modifier buttons to **cardA's** `.card-header` (after the `<span class="card-label">Matrix A</span>` line):
```html
<div class="chain-mods hidden" id="modsA">
  <button class="mod-btn" id="modAT">T</button>
  <button class="mod-btn" id="modAInv">⁻¹</button>
</div>
```

In `index.html`, add modifier buttons to **cardB's** `.card-header` (after `<span class="card-label" id="labelB">Vector b</span>`):
```html
<div class="chain-mods hidden" id="modsB">
  <button class="mod-btn" id="modBT">T</button>
  <button class="mod-btn" id="modBInv">⁻¹</button>
</div>
```

In `index.html`, add the **Add M3 button** and **cardC** between `cardB` and `.ops-panel` (after the closing `</div>` of `cardB`):
```html
<!-- Add M3 button (chain multiply only) -->
<button class="btn-sm hidden" id="addM3Btn">+ Add M3</button>

<!-- Matrix M3 (chain multiply optional third matrix) -->
<div class="input-card secondary-card hidden" id="cardC">
  <div class="card-header">
    <span class="card-label">Matrix M3</span>
    <div class="chain-mods" id="modsC">
      <button class="mod-btn" id="modCT">T</button>
      <button class="mod-btn" id="modCInv">⁻¹</button>
    </div>
    <div class="dim-controls" id="dimCtrlC">
      <input type="number" id="rowsC" value="2" min="1" max="10" aria-label="Rows C">
      <span class="dim-sep">×</span>
      <input type="number" id="colsC" value="2" min="1" max="10" aria-label="Cols C">
      <button class="btn-sm" id="updateC">Set</button>
    </div>
  </div>
  <div id="gridC" class="matrix-grid"></div>
</div>
```

- [ ] **Step 2: Add CSS for modifier buttons**

Add to `style.css` (after `.btn-sm-ghost` rules):
```css
/* ── Chain multiply modifier buttons ────────────────────────────────────── */
.chain-mods { display: flex; align-items: center; gap: 0.25rem; }

.mod-btn {
  height: 22px;
  min-width: 28px;
  padding: 0 0.4rem;
  background: var(--surface-2);
  border: 1px solid var(--border);
  border-radius: 4px;
  color: var(--text-sub);
  font-family: var(--mono);
  font-size: 0.72rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.12s, border-color 0.12s, color 0.12s;
  line-height: 1;
}
.mod-btn:hover { background: var(--accent-dim); border-color: var(--accent); color: var(--accent); }
.mod-btn.active { background: var(--accent); border-color: var(--accent); color: #fff; }
```

- [ ] **Step 3: Wire chain multiply JS**

In `script.js`, extend the `state` object with chain state:
```js
const state = {
  rowsA: 2,
  colsA: 2,
  rowsB: 2,
  colsB: 1,
  rowsC: 2,
  colsC: 2,
  textModeA: false,
  secondaryMode: null,
  stepsCollapsed: false,
  activeOp: null,
  currentAbort: null,
  lastRaw: null,
  chain: {
    modA: { T: false, inv: false },
    modB: { T: false, inv: false },
    modC: { T: false, inv: false },
    showM3: false,
  },
};
```

Add new elements to the `els` object:
```js
modsA:        $('modsA'),
modAT:        $('modAT'),
modAInv:      $('modAInv'),
modsB:        $('modsB'),
modBT:        $('modBT'),
modBInv:      $('modBInv'),
cardC:        $('cardC'),
gridC:        $('gridC'),
rowsC:        $('rowsC'),
colsC:        $('colsC'),
updateC:      $('updateC'),
modsC:        $('modsC'),
modCT:        $('modCT'),
modCInv:      $('modCInv'),
addM3Btn:     $('addM3Btn'),
```

Add these helper functions (before `runOperation`):
```js
function getModStr(mod) {
  if (mod.T && mod.inv) return 'inv_T';
  if (mod.T) return 'T';
  if (mod.inv) return 'inv';
  return 'none';
}

function wireModBtn(btnEl, modObj, key) {
  btnEl.addEventListener('click', () => {
    modObj[key] = !modObj[key];
    btnEl.classList.toggle('active', modObj[key]);
  });
}

function resetChainMods() {
  ['modAT','modAInv','modBT','modBInv','modCT','modCInv'].forEach(id => {
    const el = $(id);
    if (el) el.classList.remove('active');
  });
  state.chain.modA = { T: false, inv: false };
  state.chain.modB = { T: false, inv: false };
  state.chain.modC = { T: false, inv: false };
}

function configureForChain(active) {
  if (active) {
    els.modsA.classList.remove('hidden');
    els.modsB.classList.remove('hidden');
    els.addM3Btn.classList.remove('hidden');
  } else {
    els.modsA.classList.add('hidden');
    els.modsB.classList.add('hidden');
    els.addM3Btn.classList.add('hidden');
    els.addM3Btn.textContent = '+ Add M3';
    els.cardC.classList.add('hidden');
    state.chain.showM3 = false;
    resetChainMods();
  }
}
```

Update `showSecondary` to add a `'chain'` branch and deactivate chain when switching away. Replace the function:
```js
function showSecondary(mode) {
  // Deactivate chain UI when switching to non-chain mode
  if (state.secondaryMode === 'chain' && mode !== 'chain') {
    configureForChain(false);
  }

  if (state.secondaryMode === mode) {
    if (mode === 'rhs' || mode === 'rhs-optional') {
      if (state.rowsB !== state.rowsA) {
        state.rowsB = state.rowsA;
        createGrid('gridB', state.rowsB, state.colsB);
      }
    }
    return;
  }

  state.secondaryMode = mode;

  if (!mode) {
    els.cardB.classList.add('hidden');
    return;
  }

  els.cardB.classList.remove('hidden');

  if (mode === 'rhs') {
    els.labelB.textContent = 'Vector b';
    els.hintB.textContent = '';
    els.dimCtrlB.classList.add('hidden');
    state.rowsB = state.rowsA;
    state.colsB = 1;
    createGrid('gridB', state.rowsB, state.colsB);
  } else if (mode === 'rhs-optional') {
    els.labelB.textContent = 'Vector b (optional)';
    els.hintB.textContent = 'Leave empty to use the zero vector.';
    els.dimCtrlB.classList.add('hidden');
    state.rowsB = state.rowsA;
    state.colsB = 1;
    createGrid('gridB', state.rowsB, state.colsB);
  } else if (mode === 'matrix2') {
    els.labelB.textContent = 'Matrix B';
    els.hintB.textContent = '';
    els.dimCtrlB.classList.remove('hidden');
    els.rowsB.value = state.rowsB;
    els.colsB.value = state.colsB;
    createGrid('gridB', state.rowsB, state.colsB);
  } else if (mode === 'chain') {
    els.labelB.textContent = 'Matrix M2';
    els.hintB.textContent = '';
    els.dimCtrlB.classList.remove('hidden');
    els.rowsB.value = state.rowsB;
    els.colsB.value = state.colsB;
    createGrid('gridB', state.rowsB, state.colsB);
    configureForChain(true);
  }
}
```

Update `runOperation` — replace the existing secondary-input body-building block:
```js
if (needs === 'rhs' || needs === 'rhs-optional') {
  const rhsVal = getSecondaryValue();
  if (rhsVal) body.rhs = rhsVal;
} else if (needs === 'matrix2') {
  body.matrix2 = readGrid('gridB', state.rowsB, state.colsB);
} else if (needs === 'chain') {
  body.matrix2 = readGrid('gridB', state.rowsB, state.colsB);
  if (state.chain.showM3) {
    body.matrix3 = readGrid('gridC', state.rowsC, state.colsC);
  }
  body.mod1 = getModStr(state.chain.modA);
  body.mod2 = getModStr(state.chain.modB);
  body.mod3 = getModStr(state.chain.modC);
}
```

In the `init` function, add event listeners (after the Matrix B dim controls section):
```js
// Chain multiply: modifier buttons
wireModBtn(els.modAT,   state.chain.modA, 'T');
wireModBtn(els.modAInv, state.chain.modA, 'inv');
wireModBtn(els.modBT,   state.chain.modB, 'T');
wireModBtn(els.modBInv, state.chain.modB, 'inv');
wireModBtn(els.modCT,   state.chain.modC, 'T');
wireModBtn(els.modCInv, state.chain.modC, 'inv');

// Chain multiply: M3 toggle
els.addM3Btn.addEventListener('click', () => {
  state.chain.showM3 = !state.chain.showM3;
  if (state.chain.showM3) {
    createGrid('gridC', state.rowsC, state.colsC);
    els.cardC.classList.remove('hidden');
    els.addM3Btn.textContent = '× Remove M3';
  } else {
    els.cardC.classList.add('hidden');
    els.addM3Btn.textContent = '+ Add M3';
    els.modCT.classList.remove('active');
    els.modCInv.classList.remove('active');
    state.chain.modC = { T: false, inv: false };
  }
});

// Chain multiply: Matrix C dim controls
els.updateC.addEventListener('click', () => {
  const r = parseInt(els.rowsC.value, 10);
  const c = parseInt(els.colsC.value, 10);
  if (!r || !c || r < 1 || c < 1) return;
  state.rowsC = r;
  state.colsC = c;
  createGrid('gridC', r, c);
});
els.rowsC.addEventListener('keydown', e => e.key === 'Enter' && els.updateC.click());
els.colsC.addEventListener('keydown', e => e.key === 'Enter' && els.updateC.click());
```

Also add `chain_multiply` to `OP_LABELS`:
```js
chain_multiply: 'Chain Multiply',
```

- [ ] **Step 4: Manual smoke test**

Start server: `uv run uvicorn src.gui.app:app --reload --app-dir .`

1. Open `http://localhost:8000`
2. Click "Chain Multiply" — cardB should appear labeled "Matrix M2" with T/⁻¹ buttons; A card should show T/⁻¹ buttons; "+ Add M3" should appear
3. Enter `[[1,2],[3,4]]` in A, `[[1,0],[0,1]]` in M2, click Chain Multiply → result should show `[[1,2],[3,4]]`
4. Toggle T on M1, click again → result should be `[[1,3],[2,4]]` (transpose of A times I)
5. Click "+ Add M3", enter `[[2,0],[0,2]]` in M3, click Chain Multiply → result should be `2 * A^T`
6. Click any other operation → modifier buttons and M3 card should disappear

- [ ] **Step 5: Commit**
```bash
git add src/gui/static/index.html src/gui/static/script.js src/gui/static/style.css
git commit -m "feat: add chain matrix multiplication UI with transpose and inverse modifiers"
```

---

## Task 6: Frontend Copy Button

**Files:** Modify `src/gui/static/index.html`, `src/gui/static/script.js`, `src/gui/static/style.css`

- [ ] **Step 1: Add HTML — toolbar + copy button inside answer-card**

In `index.html`, replace the `<div class="answer-card">` block:
```html
<div class="answer-card">
  <div class="answer-toolbar hidden" id="answerToolbar">
    <button class="btn-copy" id="copyBtn">Copy</button>
  </div>
  <div class="answer-shimmer hidden" id="answerShimmer">
    <div class="shimmer-block"></div>
  </div>
  <div id="resultDisplay" class="result-body">
    <p class="placeholder">Select an operation from the left panel</p>
  </div>
</div>
```

- [ ] **Step 2: Add CSS for toolbar and copy button**

Add to `style.css` (after `.answer-card` rules):
```css
/* ── Answer toolbar ─────────────────────────────────────────────────────── */
.answer-toolbar {
  display: flex;
  justify-content: flex-end;
  padding: 0.4rem 0.75rem;
  border-bottom: 1px solid var(--border);
  background: var(--surface-2);
  border-radius: 12px 12px 0 0;
}

.btn-copy {
  height: 24px;
  padding: 0 0.65rem;
  background: var(--surface);
  border: 1px solid var(--border-bright);
  border-radius: 5px;
  color: var(--text-sub);
  font-family: var(--font);
  font-size: 0.72rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.12s, border-color 0.12s, color 0.12s;
}
.btn-copy:hover { background: var(--accent-dim); border-color: var(--accent); color: var(--accent); }
```

- [ ] **Step 3: Wire copy button JS**

Add to `els`:
```js
answerToolbar: $('answerToolbar'),
copyBtn:       $('copyBtn'),
```

In `showShimmer`, hide the toolbar:
```js
function showShimmer() {
  els.answerShimmer.classList.remove('hidden');
  els.resultDisplay.classList.add('hidden');
  els.resultDisplay.innerHTML = '';
  els.answerToolbar.classList.add('hidden');
  state.lastRaw = null;
}
```

Update `runOperation` success path — after `setStatus('done')` and before `await renderResult(...)`, store raw:
```js
state.lastRaw = data.raw || null;
await renderResult(data.result || '<span class="placeholder">No result returned.</span>');

if (state.lastRaw) {
  els.answerToolbar.classList.remove('hidden');
} else {
  els.answerToolbar.classList.add('hidden');
}
```

In the `init` function, add copy button listener:
```js
els.copyBtn.addEventListener('click', () => {
  if (!state.lastRaw) return;
  navigator.clipboard.writeText(state.lastRaw).then(() => {
    els.copyBtn.textContent = '✓ Copied';
    setTimeout(() => { els.copyBtn.textContent = 'Copy'; }, 500);
  }).catch(() => {
    els.copyBtn.textContent = 'Failed';
    setTimeout(() => { els.copyBtn.textContent = 'Copy'; }, 1000);
  });
});
```

- [ ] **Step 4: Manual smoke test**

1. Run any operation (e.g. RREF on `[[1,2],[3,4]]`)
2. A "Copy" button should appear in the top-right of the answer card
3. Click Copy → button shows "✓ Copied" briefly
4. Paste into Matrix A text mode → should show parseable matrix string
5. Run an operation that produces a scalar (Determinant) → "Copy" still appears, paste gives the number

- [ ] **Step 5: Commit**
```bash
git add src/gui/static/index.html src/gui/static/script.js src/gui/static/style.css
git commit -m "feat: add copy-to-clipboard button for operation results"
```

---

## Task 7: Frontend History Drawer

**Files:** Modify `src/gui/static/index.html`, `src/gui/static/script.js`, `src/gui/static/style.css`

- [ ] **Step 1: Add HTML — history button in op-bar + drawer**

In `index.html`, update the `<div class="op-bar-right">` block:
```html
<div class="op-bar-right">
  <button id="historyBtn" class="btn-history" aria-label="Show calculation history">
    History<span id="historyCount" class="history-count hidden">0</span>
  </button>
  <button id="cancelBtn" class="btn-cancel hidden" aria-label="Cancel computation">✕ Cancel</button>
  <span id="statusBadge" class="status-badge status-ready">Ready</span>
</div>
```

Before `</body>`, add the drawer (after the existing modal):
```html
<!-- ═══════════════ HISTORY DRAWER ═══════════════ -->
<div class="history-backdrop hidden" id="historyBackdrop"></div>
<aside class="history-drawer" id="historyDrawer" aria-label="Calculation history">
  <div class="history-drawer-header">
    <span class="history-drawer-title">History</span>
    <div style="display:flex;gap:0.5rem;align-items:center">
      <button class="btn-sm btn-sm-ghost" id="clearHistoryBtn">Clear</button>
      <button class="btn-sm" id="closeHistoryBtn">×</button>
    </div>
  </div>
  <div class="history-drawer-body" id="historyList"></div>
</aside>
```

- [ ] **Step 2: Add CSS for history drawer**

Add to `style.css` (after modal rules, before `/* ── Utilities */`):
```css
/* ── History button ─────────────────────────────────────────────────────── */
.btn-history {
  height: 26px;
  padding: 0 0.65rem;
  background: var(--surface-2);
  border: 1px solid var(--border-bright);
  border-radius: 5px;
  color: var(--text-sub);
  font-family: var(--font);
  font-size: 0.73rem;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.35rem;
  transition: background 0.12s, border-color 0.12s, color 0.12s;
  white-space: nowrap;
}
.btn-history:hover { background: var(--accent-dim); border-color: var(--accent); color: var(--accent); }

.history-count {
  background: var(--accent);
  color: #fff;
  border-radius: 100px;
  font-size: 0.62rem;
  font-weight: 700;
  padding: 0.05rem 0.38rem;
  line-height: 1.5;
}

/* ── History drawer ─────────────────────────────────────────────────────── */
.history-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(24, 24, 27, 0.28);
  z-index: 50;
  backdrop-filter: blur(2px);
}

.history-drawer {
  position: fixed;
  top: 0;
  right: 0;
  width: 320px;
  height: 100vh;
  background: var(--surface);
  border-left: 1px solid var(--border-bright);
  z-index: 51;
  display: flex;
  flex-direction: column;
  box-shadow: var(--shadow-lg);
  transform: translateX(100%);
  transition: transform 0.25s ease;
}
.history-drawer.drawer-open { transform: translateX(0); }

.history-drawer-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.875rem 1rem;
  border-bottom: 1px solid var(--border);
  flex-shrink: 0;
  background: var(--surface-2);
}
.history-drawer-title {
  font-size: 0.88rem;
  font-weight: 700;
  color: var(--text);
}

.history-drawer-body {
  flex: 1;
  overflow-y: auto;
  padding: 0.625rem;
  scrollbar-width: thin;
  scrollbar-color: var(--border-bright) transparent;
}
.history-drawer-body::-webkit-scrollbar { width: 4px; }
.history-drawer-body::-webkit-scrollbar-thumb { background: var(--border-bright); border-radius: 2px; }

.history-entry {
  padding: 0.625rem 0.75rem;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  margin-bottom: 0.4rem;
  cursor: pointer;
  transition: background 0.12s, border-color 0.12s;
}
.history-entry:hover { background: var(--accent-dim); border-color: var(--accent); }

.history-entry-header {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 0.3rem;
}
.history-entry-op {
  font-size: 0.8rem;
  font-weight: 700;
  color: var(--text);
}
.history-entry-time {
  font-size: 0.68rem;
  color: var(--text-muted);
  font-family: var(--mono);
}
.history-entry-matrices {
  font-size: 0.7rem;
  color: var(--text-sub);
  font-family: var(--mono);
  line-height: 1.55;
}
```

- [ ] **Step 3: Wire history drawer JS**

Add to `els`:
```js
historyBtn:      $('historyBtn'),
historyCount:    $('historyCount'),
historyDrawer:   $('historyDrawer'),
historyBackdrop: $('historyBackdrop'),
clearHistoryBtn: $('clearHistoryBtn'),
closeHistoryBtn: $('closeHistoryBtn'),
historyList:     $('historyList'),
```

Add history state and functions before `init`:
```js
const _history = [];
const HISTORY_MAX = 10;

function _timestamp() {
  return new Date().toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' });
}

function updateHistoryCount() {
  const n = _history.length;
  els.historyCount.textContent = n;
  els.historyCount.classList.toggle('hidden', n === 0);
}

function addToHistory(op, label, matrices, result, steps, raw) {
  _history.unshift({ op, label, matrices, result, steps, raw, timestamp: _timestamp() });
  if (_history.length > HISTORY_MAX) _history.pop();
  updateHistoryCount();
}

function renderHistoryList() {
  if (_history.length === 0) {
    els.historyList.innerHTML = '<p class="placeholder" style="padding:1rem;text-align:center;font-size:0.8rem">No history yet</p>';
    return;
  }
  els.historyList.innerHTML = _history.map((entry, i) => {
    const matPreview = entry.matrices.map(m => {
      const val = m.value.length > 22 ? m.value.slice(0, 22) + '\u2026' : m.value;
      return `<div>${escapeHtml(m.label)} = ${escapeHtml(val)}</div>`;
    }).join('');
    return `<div class="history-entry" data-idx="${i}">
      <div class="history-entry-header">
        <span class="history-entry-op">${escapeHtml(entry.label)}</span>
        <span class="history-entry-time">${entry.timestamp}</span>
      </div>
      <div class="history-entry-matrices">${matPreview}</div>
    </div>`;
  }).join('');

  els.historyList.querySelectorAll('.history-entry').forEach(el => {
    el.addEventListener('click', () => restoreHistory(_history[parseInt(el.dataset.idx, 10)]));
  });
}

function openHistoryDrawer() {
  renderHistoryList();
  els.historyBackdrop.classList.remove('hidden');
  requestAnimationFrame(() => els.historyDrawer.classList.add('drawer-open'));
}

function closeHistoryDrawer() {
  els.historyDrawer.classList.remove('drawer-open');
  setTimeout(() => els.historyBackdrop.classList.add('hidden'), 250);
}

function restoreHistory(entry) {
  if (!state.textModeA) toggleTextModeA();
  els.textA.value = entry.matrices[0].value;

  els.resultDisplay.innerHTML = entry.result || '';
  typesetMath(els.resultDisplay);
  hideShimmer();

  if (entry.steps && entry.steps.trim()) {
    renderSteps(entry.steps);
  } else {
    clearSteps();
  }

  state.lastRaw = entry.raw || null;
  if (state.lastRaw) {
    els.answerToolbar.classList.remove('hidden');
  } else {
    els.answerToolbar.classList.add('hidden');
  }

  els.opLabel.textContent = entry.label;
  setStatus('done');
  closeHistoryDrawer();
}
```

In `runOperation`, after `setStatus('done')` and after showing/hiding the copy toolbar, add history recording:
```js
const histMatrices = [{ label: 'A', value: getMatrixA() }];
if (needs === 'rhs' || needs === 'rhs-optional') {
  const rhsVal = getSecondaryValue();
  if (rhsVal) histMatrices.push({ label: 'b', value: rhsVal });
} else if (needs === 'matrix2') {
  histMatrices.push({ label: 'B', value: readGrid('gridB', state.rowsB, state.colsB) });
} else if (needs === 'chain') {
  histMatrices.push({ label: 'M2', value: readGrid('gridB', state.rowsB, state.colsB) });
  if (state.chain.showM3) {
    histMatrices.push({ label: 'M3', value: readGrid('gridC', state.rowsC, state.colsC) });
  }
}
addToHistory(op, OP_LABELS[op] || op, histMatrices, data.result || '', data.steps || '', data.raw || '');
```

In the `init` function, add event listeners:
```js
els.historyBtn.addEventListener('click', openHistoryDrawer);
els.closeHistoryBtn.addEventListener('click', closeHistoryDrawer);
els.historyBackdrop.addEventListener('click', closeHistoryDrawer);
els.clearHistoryBtn.addEventListener('click', () => {
  _history.length = 0;
  updateHistoryCount();
  renderHistoryList();
});

// Close history drawer on Escape
document.addEventListener('keydown', e => {
  if (e.key === 'Escape' && !els.historyBackdrop.classList.contains('hidden')) {
    closeHistoryDrawer();
  }
});
```

- [ ] **Step 4: Manual smoke test**

1. Run 3+ different operations
2. Click "History" button — drawer should slide in from right with entries listed
3. Each entry shows operation name, timestamp, matrix used
4. Click an entry — drawer closes, Matrix A switches to text mode with that matrix, result re-renders
5. Click backdrop — drawer closes
6. Click "Clear" — list empties, count badge disappears
7. Run 11 operations — only the 10 most recent should appear

- [ ] **Step 5: Commit**
```bash
git add src/gui/static/index.html src/gui/static/script.js src/gui/static/style.css
git commit -m "feat: add calculation history sidebar drawer"
```

---

## Self-Review

**Spec coverage:**
- ✅ Decimal fix — Task 2 (nsimplify in parse_matrix)
- ✅ Chain multiply (3 matrices, T/⁻¹ modifiers) — Tasks 4 + 5
- ✅ Copy result in parseable format — Tasks 3 + 6
- ✅ History drawer (10 entries, all matrices, scrollable) — Task 7
- ✅ Scrolling fix — Task 1

**Placeholder scan:** No TBD/TODO/placeholder text found.

**Type consistency:** `matrix_to_raw` defined in Task 3 and used in Tasks 3 + 4. `state.chain`/`getModStr` defined in Task 5, used in Task 5 only. `addToHistory`/`_history` defined in Task 7, called in `runOperation` in Task 7. `state.lastRaw` defined in Task 5 state extension, used in Tasks 6 + 7.
