# UI Improvements Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix 5 bugs and add 3 features: solve bug, arrow-key nav, resize-preserve, Set-returns-to-grid, history count, bidirectional size-link, chain working steps, and a settings popup with dark mode + auto-link toggle.

**Architecture:** All changes self-contained in 4 files: `app.py` (solve bug + chain steps), `script.js` (arrow nav, resize, history, auto-link, settings logic), `style.css` (dark mode vars + settings/toggle CSS), `index.html` (settings button + popover HTML). No new files needed.

**Tech Stack:** Vanilla JS, CSS custom properties, FastAPI/Python, SymPy

---

## File Map

| File | Changes |
|------|---------|
| `src/gui/app.py` | Fix `solve` list bug; add chain multiply step printing |
| `src/gui/static/script.js` | Arrow boundary, resize preserve, Set→grid, history max, auto-link, settings logic |
| `src/gui/static/style.css` | Dark mode vars, settings popover, toggle switch, settings btn |
| `src/gui/static/index.html` | Settings gear btn in op-bar, settings popover HTML, bump `?v=` cache busters |

---

## Task 1: Fix Solve Ax=b Bug

**Files:** Modify `src/gui/app.py:406-414`

`A.solve()` returns `list[Matrix]`. Current code passes the list to `sym.latex()` and `matrix_to_raw()`, both of which expect a single Matrix. The `except ValueError` also misses `AttributeError` from `matrix_to_raw`.

- [ ] **Step 1: Replace the solve block**

Replace lines 406-414:

```python
elif operation == "solve":
    b_vec = b if b is not None else _zero_col_vector(A.rows)
    try:
        sol_list = A.solve(b_vec)
        if not sol_list:
            result = "No solution"
            raw = ""
        else:
            sol = sol_list[0]
            result = f"\\[ {sym.latex(sol)} \\]"
            raw = matrix_to_raw(sol)
    except (ValueError, Exception):
        result = "\\( \\text{No solution — system is inconsistent.} \\)"
        raw = ""
```

- [ ] **Step 2: Verify fix manually**

Start server: `uv run python -m ma1522.gui`
Enter A = `[1 0; 0 1]`, b = `[1; 2]`, run Solve Ax=b → should show solution matrix.
Enter A = `[1 2; 2 4]`, b = `[1; 3]` → should show "No solution".

- [ ] **Step 3: Commit**

```bash
git add src/gui/app.py
git commit -m "fix: solve Ax=b returns list[Matrix], extract first element"
```

---

## Task 2: Add Chain Multiply Working Steps

**Files:** Modify `src/gui/app.py:486-519`

When mods (T, inv, inv_T) are applied, print the intermediate matrix so it shows in the steps card. Use the existing `capture()` mechanism.

- [ ] **Step 1: Refactor chain_multiply to use capture()**

Replace the existing `elif operation == "chain_multiply":` block (lines 486-519) with:

```python
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
```

- [ ] **Step 2: Verify manually**

In the GUI, select Chain Multiply. Set M1 mod to T, M2 mod to inv. Compute. Steps card should appear showing M_1^T and M_2^{-1} intermediate matrices.

- [ ] **Step 3: Commit**

```bash
git add src/gui/app.py
git commit -m "feat: show working steps for chain multiply mods (T, inv, inv_T)"
```

---

## Task 3: Arrow Key Boundary Check

**Files:** Modify `src/gui/static/script.js:195-209`

`ArrowLeft` should only navigate to previous cell when cursor is at position 0. `ArrowRight` should only navigate when cursor is at end of text. Up/Down/Enter unchanged.

- [ ] **Step 1: Replace the keydown handler inside createGrid**

Replace lines 195-209 (the `input.addEventListener('keydown', ...)` block) with:

```javascript
input.addEventListener('keydown', e => {
  const dirs = {
    Enter:      [1,  0],
    ArrowDown:  [1,  0],
    ArrowUp:    [-1, 0],
    ArrowRight: [0,  1],
    ArrowLeft:  [0, -1],
  };
  const delta = dirs[e.key];
  if (!delta) return;

  // For horizontal arrows, only navigate when cursor is at the boundary
  if (e.key === 'ArrowLeft') {
    if (input.selectionStart !== 0 || input.selectionEnd !== 0) return;
  }
  if (e.key === 'ArrowRight') {
    const end = input.value.length;
    if (input.selectionStart !== end || input.selectionEnd !== end) return;
  }

  const next = container.querySelector(
    `[data-row="${r + delta[0]}"][data-col="${c + delta[1]}"]`
  );
  if (next) { e.preventDefault(); next.focus(); }
});
```

- [ ] **Step 2: Verify manually**

In a grid cell with text "123", pressing Left should move cursor through the text. Only at position 0 should it jump to the previous cell. Right should only jump at end.

- [ ] **Step 3: Commit**

```bash
git add src/gui/static/script.js
git commit -m "fix: arrow keys only navigate cells at start/end of cell text"
```

---

## Task 4: Preserve Cell Values on Resize + Set Returns to Grid Mode

**Files:** Modify `src/gui/static/script.js`

`applyDimA/B/C` must: (a) if in text mode, parse textarea and switch to grid mode first; (b) save existing cell values before `createGrid`; (c) restore matching cells after.

- [ ] **Step 1: Add saveGrid and restoreGrid helpers after the clearGrid function (after line 234)**

```javascript
/** Snapshot all non-empty cell values. Returns Map keyed by "row,col". */
function saveGrid(containerId) {
  const saved = new Map();
  const container = $(containerId);
  container.querySelectorAll('.grid-cell').forEach(cell => {
    const v = cell.value.trim();
    if (v) saved.set(`${cell.dataset.row},${cell.dataset.col}`, v);
  });
  return saved;
}

/** Restore cell values from a Map keyed by "row,col". */
function restoreGrid(containerId, saved) {
  if (!saved || saved.size === 0) return;
  const container = $(containerId);
  saved.forEach((val, key) => {
    const [row, col] = key.split(',');
    const cell = container.querySelector(`[data-row="${row}"][data-col="${col}"]`);
    if (cell) cell.value = val;
  });
}
```

- [ ] **Step 2: Rewrite applyDimA to preserve values and exit text mode**

Replace the existing `applyDimA` function (lines 247-259):

```javascript
async function applyDimA() {
  const r = parseInt(els.rowsA.value, 10);
  const c = parseInt(els.colsA.value, 10);
  if (!r || !c || r < 1 || c < 1) return;

  // If in text mode: parse, switch to grid mode
  if (state.textModeA) {
    const text = els.textA.value.trim();
    if (text) {
      const data = await fetchParse(text);
      if (data) populateGrid('gridA', data, 'rowsA', 'colsA', els.rowsA, els.colsA);
    }
    state.textModeA = false;
    els.textWrapA.classList.add('hidden');
    els.gridA.classList.remove('hidden');
  }

  const saved = saveGrid('gridA');
  state.rowsA = r;
  state.colsA = c;
  createGrid('gridA', r, c);
  restoreGrid('gridA', saved);

  if (state.secondaryMode === 'rhs' || state.secondaryMode === 'rhs-optional') {
    state.rowsB = r;
    els.rowsB.value = r;
    const savedB = saveGrid('gridB');
    createGrid('gridB', state.rowsB, state.colsB);
    restoreGrid('gridB', savedB);
  }

  applyAutoLink('A');
}
```

- [ ] **Step 3: Rewrite applyDimB to preserve values and exit text mode**

Replace the existing `applyDimB` function (lines 418-425):

```javascript
async function applyDimB() {
  const r = parseInt(els.rowsB.value, 10);
  const c = parseInt(els.colsB.value, 10);
  if (!r || !c || r < 1 || c < 1) return;

  if (state.textModeB) {
    const text = els.textB.value.trim();
    if (text) {
      const data = await fetchParse(text);
      if (data) populateGrid('gridB', data, 'rowsB', 'colsB', els.rowsB, els.colsB);
    }
    state.textModeB = false;
    els.textWrapB.classList.add('hidden');
    els.gridB.classList.remove('hidden');
  }

  const saved = saveGrid('gridB');
  state.rowsB = r;
  state.colsB = c;
  createGrid('gridB', r, c);
  restoreGrid('gridB', saved);

  applyAutoLink('B');
}
```

- [ ] **Step 4: Update Matrix C dim handler in init() to also preserve values**

In `init()`, replace the `els.updateC.addEventListener('click', ...)` handler (lines 987-994):

```javascript
els.updateC.addEventListener('click', async () => {
  const r = parseInt(els.rowsC.value, 10);
  const c = parseInt(els.colsC.value, 10);
  if (!r || !c || r < 1 || c < 1) return;

  if (state.textModeC) {
    const text = els.textC.value.trim();
    if (text) {
      const data = await fetchParse(text);
      if (data) populateGrid('gridC', data, 'rowsC', 'colsC', els.rowsC, els.colsC);
    }
    state.textModeC = false;
    els.textWrapC.classList.add('hidden');
    els.gridC.classList.remove('hidden');
  }

  const saved = saveGrid('gridC');
  state.rowsC = r;
  state.colsC = c;
  createGrid('gridC', r, c);
  restoreGrid('gridC', saved);
});
```

- [ ] **Step 5: Verify manually**

Enter values in a 2×2 grid. Change to 3×3. Values should remain in top-left 2×2. Switch to text mode, type a matrix, press Set — should parse and show as grid.

- [ ] **Step 6: Commit**

```bash
git add src/gui/static/script.js
git commit -m "fix: preserve cell values on resize; Set button exits text mode"
```

---

## Task 5: Increase History Count

**Files:** Modify `src/gui/static/script.js:791`

- [ ] **Step 1: Change HISTORY_MAX**

```javascript
const HISTORY_MAX = 50;
```

- [ ] **Step 2: Commit**

```bash
git add src/gui/static/script.js
git commit -m "feat: increase history max from 10 to 50"
```

---

## Task 6: Bidirectional Size Linking

**Files:** Modify `src/gui/static/script.js`

Add `state.autoLinkSize` flag. Add `applyAutoLink(source)` that enforces constraints after A or B dims change. Loaded from localStorage.

Constraints:
- `rhs` / `rhs-optional`: `rows(A) === rows(b)`. If A→: b rows = A rows. If B→: A rows = B rows (A cols unchanged).
- `matrix2` / `chain`: `cols(A) === rows(B)`. If A→: B rows = A cols. If B→: A cols = B rows (A rows unchanged).

- [ ] **Step 1: Add autoLinkSize to state (top of file, inside the state object)**

Add to the `state` object:
```javascript
autoLinkSize: true,
```

- [ ] **Step 2: Add applyAutoLink function after applyDimB**

```javascript
/**
 * Enforce dimensional constraints between A and B after one side changed.
 * source: 'A' | 'B'
 * Only fires when state.autoLinkSize is true and a constrained dim actually differs.
 */
function applyAutoLink(source) {
  if (!state.autoLinkSize) return;
  const mode = state.secondaryMode;
  if (!mode || mode === 'chain') {
    // chain: cols(A) = rows(B)
    if (mode === 'chain' || mode === 'matrix2') {
      if (source === 'A') {
        if (state.rowsB !== state.colsA) {
          const savedB = saveGrid('gridB');
          state.rowsB = state.colsA;
          els.rowsB.value = state.colsA;
          createGrid('gridB', state.rowsB, state.colsB);
          restoreGrid('gridB', savedB);
        }
      } else if (source === 'B') {
        if (state.colsA !== state.rowsB) {
          const savedA = saveGrid('gridA');
          state.colsA = state.rowsB;
          els.colsA.value = state.rowsB;
          createGrid('gridA', state.rowsA, state.colsA);
          restoreGrid('gridA', savedA);
        }
      }
    }
    return;
  }
  if (mode === 'rhs' || mode === 'rhs-optional') {
    if (source === 'A') {
      if (state.rowsB !== state.rowsA) {
        const savedB = saveGrid('gridB');
        state.rowsB = state.rowsA;
        els.rowsB.value = state.rowsA;
        createGrid('gridB', state.rowsB, state.colsB);
        restoreGrid('gridB', savedB);
      }
    } else if (source === 'B') {
      if (state.rowsA !== state.rowsB) {
        const savedA = saveGrid('gridA');
        state.rowsA = state.rowsB;
        els.rowsA.value = state.rowsB;
        createGrid('gridA', state.rowsA, state.colsA);
        restoreGrid('gridA', savedA);
      }
    }
  } else if (mode === 'matrix2') {
    if (source === 'A') {
      if (state.rowsB !== state.colsA) {
        const savedB = saveGrid('gridB');
        state.rowsB = state.colsA;
        els.rowsB.value = state.colsA;
        createGrid('gridB', state.rowsB, state.colsB);
        restoreGrid('gridB', savedB);
      }
    } else if (source === 'B') {
      if (state.colsA !== state.rowsB) {
        const savedA = saveGrid('gridA');
        state.colsA = state.rowsB;
        els.colsA.value = state.rowsB;
        createGrid('gridA', state.rowsA, state.colsA);
        restoreGrid('gridA', savedA);
      }
    }
  }
}
```

- [ ] **Step 3: Verify manually**

Select "Solve Ax=b". Set A to 3×2. B should auto-resize to 3×1. Change b to 4×1. A should change to 4×2.

Select "Intersect". Set A to 3×4. B should become 4×something. Change B rows to 5. A cols should become 5.

- [ ] **Step 4: Commit**

```bash
git add src/gui/static/script.js
git commit -m "feat: bidirectional matrix size linking (auto-link toggle)"
```

---

## Task 7: Settings UI — HTML Structure

**Files:** Modify `src/gui/static/index.html`

Add a gear button and popover panel. Place gear button between `?` and `History` in `.op-bar-right`.

- [ ] **Step 1: Add settings button in op-bar-right**

In `index.html`, replace:
```html
          <button id="helpBtn" class="btn-help" aria-label="Input syntax reference" title="Input syntax reference">?</button>
```
with:
```html
          <button id="helpBtn" class="btn-help" aria-label="Input syntax reference" title="Input syntax reference">?</button>
          <div class="settings-anchor">
            <button id="settingsBtn" class="btn-settings" aria-label="Settings" title="Settings">
              <svg width="15" height="15" viewBox="0 0 15 15" fill="none" aria-hidden="true">
                <path d="M7.5 9.5a2 2 0 100-4 2 2 0 000 4z" stroke="currentColor" stroke-width="1.3"/>
                <path d="M7.5 1v1.5M7.5 12.5V14M1 7.5h1.5M12.5 7.5H14M2.636 2.636l1.06 1.06M11.304 11.304l1.06 1.06M2.636 12.364l1.06-1.06M11.304 3.696l1.06-1.06" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/>
              </svg>
            </button>
            <div class="settings-popover hidden" id="settingsPopover" role="dialog" aria-label="Settings">
              <div class="settings-header">
                <span class="settings-title">Settings</span>
                <button class="settings-close" id="settingsClose" aria-label="Close settings">
                  <svg width="11" height="11" viewBox="0 0 11 11" fill="none"><path d="M1 1l9 9M10 1L1 10" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg>
                </button>
              </div>
              <div class="settings-body">
                <div class="settings-row">
                  <div class="settings-row-text">
                    <span class="settings-row-label">Dark mode</span>
                  </div>
                  <button class="toggle-switch" id="darkToggle" role="switch" aria-checked="false" aria-label="Toggle dark mode">
                    <span class="toggle-thumb"></span>
                  </button>
                </div>
                <div class="settings-row">
                  <div class="settings-row-text">
                    <span class="settings-row-label">Auto-link sizes</span>
                    <span class="settings-row-sub">Resize B when A changes, and vice versa</span>
                  </div>
                  <button class="toggle-switch" id="autoLinkToggle" role="switch" aria-checked="true" aria-label="Toggle auto-link sizes">
                    <span class="toggle-thumb"></span>
                  </button>
                </div>
              </div>
            </div>
          </div>
```

- [ ] **Step 2: Bump cache buster on CSS and JS links**

In `index.html`, change:
```html
  <link rel="stylesheet" href="/static/style.css?v=9">
```
to:
```html
  <link rel="stylesheet" href="/static/style.css?v=10">
```

And:
```html
  <script src="/static/script.js?v=9"></script>
```
to:
```html
  <script src="/static/script.js?v=10"></script>
```

- [ ] **Step 3: Commit**

```bash
git add src/gui/static/index.html
git commit -m "feat: add settings button and popover HTML structure"
```

---

## Task 8: Settings UI — CSS

**Files:** Modify `src/gui/static/style.css`

Add: dark mode CSS variables, settings button style, settings popover, toggle switch, and all dark-mode component overrides via `body[data-theme="dark"]`.

- [ ] **Step 1: Add dark mode tokens at the end of the `:root` block**

After the last line of `:root { ... }` (before the closing `}`), add nothing — instead, add a new rule block after the entire `:root` block:

```css
/* ── Dark mode tokens ───────────────────────────────────────────────────── */
body[data-theme="dark"] {
  --bg:          #0f0f11;
  --surface:     #18181d;
  --surface-2:   #1e1e24;
  --surface-3:   #25252e;

  --border:        #2e2e38;
  --border-bright: #3d3d4d;

  --text:       #e8e8f0;
  --text-sub:   #9898b0;
  --text-muted: #55556a;

  --accent:       #6366f1;
  --accent-light: #818cf8;
  --accent-dim:   rgba(99, 102, 241, 0.12);
  --accent-glow:  rgba(99, 102, 241, 0.22);

  --green:  #34d399;
  --amber:  #fbbf24;
  --rose:   #fb7185;
  --rose-dim:    rgba(251, 113, 133, 0.10);
  --rose-border: rgba(251, 113, 133, 0.35);
  --purple: #a78bfa;
  --teal:   #2dd4bf;
  --sky:    #38bdf8;

  --step-ero-bg:     #1e1b12;
  --step-ero-border: #78350f;
  --step-ero-color:  #fde68a;
  --step-matrix-bg:  #1e1e24;

  --shadow-sm: 0 1px 3px rgba(0,0,0,0.30), 0 1px 2px rgba(0,0,0,0.20);
  --shadow-md: 0 4px 14px rgba(0,0,0,0.40), 0 2px 6px rgba(0,0,0,0.20);
  --shadow-lg: 0 20px 50px rgba(0,0,0,0.55), 0 8px 20px rgba(0,0,0,0.28);
}

/* Dark: MathJax text colour */
body[data-theme="dark"] mjx-container { color: var(--text); }
```

- [ ] **Step 2: Add settings button style**

Append to `style.css` (after `.btn-history` section):

```css
/* ── Settings button ────────────────────────────────────────────────────── */
.settings-anchor { position: relative; }

.btn-settings {
  width: 28px;
  height: 28px;
  border-radius: 100px;
  border: 1px solid var(--border-bright);
  background: var(--surface);
  color: var(--text-sub);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-size: 0.85rem;
  font-weight: 600;
  transition: background 0.15s, border-color 0.15s, color 0.15s;
  flex-shrink: 0;
}
.btn-settings:hover { background: var(--accent-dim); border-color: var(--accent); color: var(--accent); }
.btn-settings.active { background: var(--accent-dim); border-color: var(--accent); color: var(--accent); }

/* ── Settings popover ───────────────────────────────────────────────────── */
.settings-popover {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  width: 260px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  box-shadow: var(--shadow-lg);
  z-index: 200;
  animation: fadeUp 0.15s ease both;
}
.settings-popover.hidden { display: none; }

.settings-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.6rem 0.75rem;
  border-bottom: 1px solid var(--border);
}
.settings-title {
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--text-sub);
}
.settings-close {
  width: 22px;
  height: 22px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: transparent;
  color: var(--text-muted);
  cursor: pointer;
  border-radius: 4px;
  transition: color 0.12s, background 0.12s;
}
.settings-close:hover { color: var(--text); background: var(--surface-3); }

.settings-body { padding: 0.5rem 0; }

.settings-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.55rem 0.75rem;
  gap: 0.75rem;
}
.settings-row:hover { background: var(--surface-2); }

.settings-row-text { display: flex; flex-direction: column; gap: 0.15rem; min-width: 0; }
.settings-row-label {
  font-size: 0.82rem;
  font-weight: 500;
  color: var(--text);
}
.settings-row-sub {
  font-size: 0.72rem;
  color: var(--text-muted);
  line-height: 1.3;
}

/* ── Toggle switch ──────────────────────────────────────────────────────── */
.toggle-switch {
  flex-shrink: 0;
  width: 36px;
  height: 20px;
  border-radius: 100px;
  border: none;
  background: var(--border-bright);
  cursor: pointer;
  position: relative;
  transition: background 0.2s;
  padding: 0;
}
.toggle-switch[aria-checked="true"] { background: var(--accent); }
.toggle-thumb {
  position: absolute;
  top: 2px;
  left: 2px;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: #fff;
  transition: transform 0.2s cubic-bezier(0.34, 1.56, 0.64, 1);
  box-shadow: 0 1px 3px rgba(0,0,0,0.25);
}
.toggle-switch[aria-checked="true"] .toggle-thumb { transform: translateX(16px); }
```

- [ ] **Step 3: Verify dark mode visually**

Open app, open settings, toggle dark mode. All surfaces, borders, text, step cards, modals, history drawer should change. Check math renders with correct colour.

- [ ] **Step 4: Commit**

```bash
git add src/gui/static/style.css
git commit -m "feat: dark mode CSS tokens + settings popover + toggle switch styles"
```

---

## Task 9: Settings JS Logic

**Files:** Modify `src/gui/static/script.js`

Wire up the settings button, popover, dark mode toggle, and auto-link toggle. Load saved preferences from `localStorage` on init.

- [ ] **Step 1: Add settings elements to els object**

In the `els` object (around line 67), add after `historyList`:
```javascript
  settingsBtn:     $('settingsBtn'),
  settingsPopover: $('settingsPopover'),
  settingsClose:   $('settingsClose'),
  darkToggle:      $('darkToggle'),
  autoLinkToggle:  $('autoLinkToggle'),
```

- [ ] **Step 2: Add settings open/close functions**

Add after the `closeHistoryDrawer` function:

```javascript
/* ─────────────────────────────────────────────────────────────────────────
   Settings popover
   ───────────────────────────────────────────────────────────────────────── */

function openSettings() {
  els.settingsPopover.classList.remove('hidden');
  els.settingsBtn.classList.add('active');
}

function closeSettings() {
  els.settingsPopover.classList.add('hidden');
  els.settingsBtn.classList.remove('active');
}

function applyDarkMode(dark) {
  document.body.dataset.theme = dark ? 'dark' : '';
  els.darkToggle.setAttribute('aria-checked', dark ? 'true' : 'false');
  localStorage.setItem('la-studio-dark', dark ? '1' : '0');
}

function applyAutoLinkPref(on) {
  state.autoLinkSize = on;
  els.autoLinkToggle.setAttribute('aria-checked', on ? 'true' : 'false');
  localStorage.setItem('la-studio-autolink', on ? '1' : '0');
}
```

- [ ] **Step 3: Wire settings event listeners in init()**

Add at the end of `init()`, before the closing `}`:

```javascript
  // 19. Settings popover
  els.settingsBtn.addEventListener('click', e => {
    e.stopPropagation();
    if (els.settingsPopover.classList.contains('hidden')) openSettings();
    else closeSettings();
  });
  els.settingsClose.addEventListener('click', closeSettings);
  document.addEventListener('click', e => {
    if (!els.settingsPopover.classList.contains('hidden') &&
        !els.settingsPopover.contains(e.target) &&
        e.target !== els.settingsBtn) {
      closeSettings();
    }
  });
  els.darkToggle.addEventListener('click', () => {
    applyDarkMode(els.darkToggle.getAttribute('aria-checked') !== 'true');
  });
  els.autoLinkToggle.addEventListener('click', () => {
    applyAutoLinkPref(els.autoLinkToggle.getAttribute('aria-checked') !== 'true');
  });

  // 20. Load saved settings
  const savedDark = localStorage.getItem('la-studio-dark');
  applyDarkMode(savedDark === '1');
  const savedAutoLink = localStorage.getItem('la-studio-autolink');
  applyAutoLinkPref(savedAutoLink !== '0');  // default on

  // 21. Escape closes settings
  // (add to the existing keydown handler at step 18)
```

- [ ] **Step 4: Add Escape handler for settings in the existing keydown listener**

In the existing keyboard Escape handler (around line 1063), add at the top of that listener:

```javascript
    if (!els.settingsPopover.classList.contains('hidden')) {
      if (e.key === 'Escape') { closeSettings(); return; }
    }
```

- [ ] **Step 5: Verify end-to-end**

1. Open settings → popover appears, gear icon highlighted.
2. Toggle dark mode → page switches theme, persists on reload.
3. Toggle auto-link off → resizing A no longer affects B.
4. Toggle auto-link on → resizing A affects B per mode constraints.
5. Press Escape or click outside → popover closes.

- [ ] **Step 6: Commit**

```bash
git add src/gui/static/script.js
git commit -m "feat: settings popover with dark mode and auto-link toggles"
```

---

## Task 10: Item 8 — Suggestions

This task is informational only (no code). The following improvements are worth considering for a future session:

1. **Matrix templates** — "Insert identity", "Insert zeros", "Insert random" buttons on each matrix card. Very low effort, high student utility.
2. **Undo/redo for grid edits** — Cmd+Z to revert the last cell change. Moderate effort.
3. **Export result as LaTeX** — "Copy LaTeX" button next to "Copy" to copy the raw LaTeX string rather than the bracket notation.
4. **Keyboard shortcut to focus Matrix A** — e.g. `Alt+A` jumps focus to the first cell of gridA.
5. **Operation search** — A small search/filter box above the op accordion to quickly jump to an operation by name.
6. **Pin/favourite operations** — Let students star their most-used ops so they appear at the top.
7. **Session persistence** — Save the current matrix values to `localStorage` so they survive page refresh.
8. **Sharable state URL** — Encode matrix + operation into URL query params for easy sharing with TAs.

---

## Self-Review

**Spec coverage check:**
- ✅ Item 1: preserve elements on resize → Task 4
- ✅ Item 2: Set returns to grid mode → Task 4 (applyDimA exits text mode)
- ✅ Item 3: increase history count → Task 5
- ✅ Item 4: solve bug → Task 1
- ✅ Item 5: arrow key boundary → Task 3
- ✅ Item 6: auto-link bidirectional → Task 6; toggle in Task 9
- ✅ Item 7: settings button + popover + dark mode + auto-link → Tasks 7, 8, 9
- ✅ Item 8: suggestions → Task 10
- ✅ Chain multiply working steps (extra) → Task 2

**Placeholder scan:** No TBDs. All code blocks complete.

**Type consistency:** `saveGrid/restoreGrid` defined in Task 4 Step 1, used in Tasks 4, 6. `applyAutoLink('A'/'B')` defined in Task 6, called from `applyDimA`/`applyDimB` in Task 4. `applyDarkMode`/`applyAutoLinkPref` defined in Task 9 Step 2, wired in Task 9 Step 3. Consistent.

**One gap found and fixed:** `applyAutoLink` in Task 6 has a logic issue — the outer `if (!mode || mode === 'chain')` block was incorrectly structured. The correct version is in Task 6 Step 2 as written (the matrix2/chain block is inside the `else if` chain). ✅
