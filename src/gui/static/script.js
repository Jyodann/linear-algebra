/* ─────────────────────────────────────────────────────────────────────────
   Linear Algebra Studio — Frontend Controller
   ───────────────────────────────────────────────────────────────────────── */

'use strict';

/* ── Operation metadata ─────────────────────────────────────────────────── */
const OP_LABELS = {
  rref:             'RREF',
  ref:              'REF (with steps)',
  lu:               'LU Decomposition',
  qr:               'QR Decomposition',
  svd:              'SVD',
  gram_schmidt:     'Gram-Schmidt Orthogonalization',
  det:              'Determinant',
  inv:              'Inverse',
  rank:             'Rank & Nullity',
  eigenvals:        'Eigenvalues',
  eigenvects:       'Eigenvectors',
  diagonalize:      'Diagonalization',
  orth_diagonalize: 'Orthogonal Diagonalization',
  nullspace:        'Nullspace',
  colspace:         'Column Space',
  orth_complement:  'Orthogonal Complement',
  col_constraints:  'Column Constraints',
  extend_basis:     'Extend Basis',
  solve:            'Solve Ax = b',
  least_squares:    'Least Squares',
  projection:       'Projection [A|b]',
  intersect:        'Intersect Subspaces',
  transition:       'Transition Matrix',
  eval_cases:       'Evaluate Cases',
  find_cases:       'Find Cases',
  chain_multiply:   'Chain Multiply',
};

/* ── Status badge config ────────────────────────────────────────────────── */
const STATUS_CONFIG = {
  ready:     { cls: 'status-ready',     text: 'Ready',       cancel: false },
  computing: { cls: 'status-computing', text: 'Computing\u2026', cancel: true  },
  done:      { cls: 'status-done',      text: 'Done \u2713', cancel: false },
  error:     { cls: 'status-error',     text: 'Error',       cancel: false },
};

/* ── State ──────────────────────────────────────────────────────────────── */
const state = {
  rowsA: 2,
  colsA: 2,
  rowsB: 2,
  colsB: 1,
  textModeA: false,
  secondaryMode: null,    // null | 'rhs' | 'rhs-optional' | 'matrix2' | 'chain'
  stepsCollapsed: false,
  activeOp: null,
  currentAbort: null,     // AbortController for in-flight request
  rowsC: 2,
  colsC: 2,
  lastRaw: null,
  chain: {
    modA: { T: false, inv: false },
    modB: { T: false, inv: false },
    modC: { T: false, inv: false },
    showM3: false,
  },
};

/* ── DOM references ─────────────────────────────────────────────────────── */
const $ = id => document.getElementById(id);

const els = {
  rowsA:            $('rowsA'),
  colsA:            $('colsA'),
  updateA:          $('updateA'),
  clearA:           $('clearA'),
  gridA:            $('gridA'),
  textWrapA:        $('textWrapA'),
  textA:            $('textA'),
  toggleModeA:      $('toggleModeA'),
  cardB:            $('cardB'),
  labelB:           $('labelB'),
  dimCtrlB:         $('dimCtrlB'),
  rowsB:            $('rowsB'),
  colsB:            $('colsB'),
  updateB:          $('updateB'),
  gridB:            $('gridB'),
  hintB:            $('hintB'),
  opLabel:          $('opLabel'),
  statusBadge:      $('statusBadge'),
  cancelBtn:        $('cancelBtn'),
  answerShimmer:    $('answerShimmer'),
  resultDisplay:    $('resultDisplay'),
  stepsCard:        $('stepsCard'),
  stepsBody:        $('stepsBody'),
  toggleSteps:      $('toggleSteps'),
  toggleStepsLabel: $('toggleStepsLabel'),
  equivBtn:         $('equivBtn'),
  equivModal:       $('equivModal'),
  closeModal:       $('closeModal'),
  equivCategory:    $('equivCategory'),
  equivProps:       $('equivProps'),
  equivList:        $('equivList'),
  modsA:    $('modsA'),
  modAT:    $('modAT'),
  modAInv:  $('modAInv'),
  modsB:    $('modsB'),
  modBT:    $('modBT'),
  modBInv:  $('modBInv'),
  cardC:    $('cardC'),
  gridC:    $('gridC'),
  rowsC:    $('rowsC'),
  colsC:    $('colsC'),
  updateC:  $('updateC'),
  modsC:    $('modsC'),
  modCT:    $('modCT'),
  modCInv:  $('modCInv'),
  addM3Btn:      $('addM3Btn'),
  answerToolbar:   $('answerToolbar'),
  copyBtn:         $('copyBtn'),
  historyBtn:      $('historyBtn'),
  historyCount:    $('historyCount'),
  historyDrawer:   $('historyDrawer'),
  historyBackdrop: $('historyBackdrop'),
  clearHistoryBtn: $('clearHistoryBtn'),
  closeHistoryBtn: $('closeHistoryBtn'),
  historyList:     $('historyList'),
};

/* ─────────────────────────────────────────────────────────────────────────
   Grid helpers
   ───────────────────────────────────────────────────────────────────────── */

/**
 * Build a rows×cols input grid inside `containerId`.
 * Sets grid-template-columns and appends .grid-cell inputs.
 */
function createGrid(containerId, rows, cols) {
  const container = $(containerId);
  container.innerHTML = '';
  container.style.gridTemplateColumns = `repeat(${cols}, auto)`;

  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < cols; c++) {
      const input = document.createElement('input');
      input.type = 'text';
      input.className = 'grid-cell';
      input.dataset.row = r;
      input.dataset.col = c;
      input.placeholder = '0';
      input.autocomplete = 'off';
      input.spellcheck = false;

      // Navigation: Enter moves down, arrows move in all 4 directions.
      // preventDefault only fires when a target exists, so default caret
      // movement within a cell is preserved at grid boundaries.
      input.addEventListener('keydown', e => {
        const dirs = {
          Enter:       [1,  0],
          ArrowDown:   [1,  0],
          ArrowUp:     [-1, 0],
          ArrowRight:  [0,  1],
          ArrowLeft:   [0, -1],
        };
        const delta = dirs[e.key];
        if (!delta) return;
        const next = container.querySelector(
          `[data-row="${r + delta[0]}"][data-col="${c + delta[1]}"]`
        );
        if (next) { e.preventDefault(); next.focus(); }
      });

      container.appendChild(input);
    }
  }
}

/**
 * Read a grid into "[v00 v01; v10 v11]" format (Matrix.from_str compatible).
 * Empty cells become "0".
 */
function readGrid(containerId, rows, cols) {
  const container = $(containerId);
  const rowStrs = [];
  for (let r = 0; r < rows; r++) {
    const row = [];
    for (let c = 0; c < cols; c++) {
      const cell = container.querySelector(`[data-row="${r}"][data-col="${c}"]`);
      const val = (cell && cell.value.trim()) ? cell.value.trim() : '0';
      row.push(val);
    }
    rowStrs.push(row.join(' '));
  }
  return '[' + rowStrs.join('; ') + ']';
}

/** Zero-fill all grid cells. */
function clearGrid(containerId) {
  const container = $(containerId);
  container.querySelectorAll('.grid-cell').forEach(c => { c.value = ''; });
}

/* ─────────────────────────────────────────────────────────────────────────
   Matrix A management
   ───────────────────────────────────────────────────────────────────────── */

function initGridA() {
  createGrid('gridA', state.rowsA, state.colsA);
}

function syncDimInputsA() {
  els.rowsA.value = state.rowsA;
  els.colsA.value = state.colsA;
}

function applyDimA() {
  const r = parseInt(els.rowsA.value, 10);
  const c = parseInt(els.colsA.value, 10);
  if (!r || !c || r < 1 || c < 1) return;
  state.rowsA = r;
  state.colsA = c;
  createGrid('gridA', r, c);

  // Auto-sync rowsB when in rhs / rhs-optional mode
  if (state.secondaryMode === 'rhs' || state.secondaryMode === 'rhs-optional') {
    state.rowsB = r;
    els.rowsB.value = r;
    createGrid('gridB', state.rowsB, state.colsB);
  }
}

/** Read the current Matrix A string (grid or text mode). */
function getMatrixA() {
  if (state.textModeA) {
    return els.textA.value.trim();
  }
  return readGrid('gridA', state.rowsA, state.colsA);
}

/** Toggle grid ↔ text mode for Matrix A. */
function toggleTextModeA() {
  state.textModeA = !state.textModeA;
  if (state.textModeA) {
    els.textA.value = readGrid('gridA', state.rowsA, state.colsA);
    els.gridA.classList.add('hidden');
    els.textWrapA.classList.remove('hidden');
  } else {
    els.textWrapA.classList.add('hidden');
    els.gridA.classList.remove('hidden');
  }
}

/* ─────────────────────────────────────────────────────────────────────────
   Secondary input (cardB)
   ───────────────────────────────────────────────────────────────────────── */

/**
 * Show or hide cardB, configuring label, hint, and dim controls.
 * mode: null | 'rhs' | 'rhs-optional' | 'matrix2'
 */
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

function applyDimB() {
  const r = parseInt(els.rowsB.value, 10);
  const c = parseInt(els.colsB.value, 10);
  if (!r || !c || r < 1 || c < 1) return;
  state.rowsB = r;
  state.colsB = c;
  createGrid('gridB', r, c);
}

/** Read secondary input. Returns null if mode is rhs-optional and all cells empty. */
function getSecondaryValue() {
  const mode = state.secondaryMode;
  if (!mode) return null;

  const raw = readGrid('gridB', state.rowsB, state.colsB);

  if (mode === 'rhs-optional') {
    const allEmpty = Array.from(
      els.gridB.querySelectorAll('.grid-cell')
    ).every(c => c.value.trim() === '');
    if (allEmpty) return null;
  }

  return raw;
}

/* ─────────────────────────────────────────────────────────────────────────
   Status badge
   ───────────────────────────────────────────────────────────────────────── */

function setStatus(s) {
  const cfg = STATUS_CONFIG[s];
  if (!cfg) return;
  els.statusBadge.className = `status-badge ${cfg.cls}`;
  els.statusBadge.textContent = cfg.text;
  els.cancelBtn.classList.toggle('hidden', !cfg.cancel);
}

/* ─────────────────────────────────────────────────────────────────────────
   Result & steps rendering
   ───────────────────────────────────────────────────────────────────────── */

function showShimmer() {
  els.answerShimmer.classList.remove('hidden');
  els.resultDisplay.classList.add('hidden');
  els.resultDisplay.innerHTML = '';
  els.answerToolbar.classList.add('hidden');
  state.lastRaw = null;
}

function hideShimmer() {
  els.answerShimmer.classList.add('hidden');
  els.resultDisplay.classList.remove('hidden');
}

/** Typeset MathJax inside a container, no-op if MathJax not loaded. */
async function typesetMath(container) {
  if (window.MathJax && MathJax.typesetPromise) {
    await MathJax.typesetPromise([container]).catch(console.error);
  }
}

async function renderResult(html) {
  els.resultDisplay.innerHTML = html;
  await typesetMath(els.resultDisplay);
  hideShimmer();
}

function applyStepsVisibility() {
  if (state.stepsCollapsed) {
    els.stepsBody.classList.add('hidden');
    els.toggleStepsLabel.textContent = 'Show steps';
    els.toggleSteps.setAttribute('aria-expanded', 'false');
  } else {
    els.stepsBody.classList.remove('hidden');
    els.toggleStepsLabel.textContent = 'Hide steps';
    els.toggleSteps.setAttribute('aria-expanded', 'true');
  }
}

function renderSteps(html) {
  els.stepsBody.innerHTML = html;
  els.stepsCard.classList.remove('hidden');
  applyStepsVisibility();
  typesetMath(els.stepsBody);
}

function clearSteps() {
  els.stepsCard.classList.add('hidden');
  els.stepsBody.innerHTML = '';
}

/* ─────────────────────────────────────────────────────────────────────────
   Chain multiply helpers
   ───────────────────────────────────────────────────────────────────────── */

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
  state.chain.modA.T = false; state.chain.modA.inv = false;
  state.chain.modB.T = false; state.chain.modB.inv = false;
  state.chain.modC.T = false; state.chain.modC.inv = false;
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

/* ─────────────────────────────────────────────────────────────────────────
   Core operation handler
   ───────────────────────────────────────────────────────────────────────── */

let _opGeneration = 0;

async function runOperation(op, needs) {
  if (state.currentAbort) {
    state.currentAbort.abort();
    state.currentAbort = null;
  }
  const myGen = ++_opGeneration;

  opBtns.forEach(b => b.classList.remove('active'));
  const btn = document.querySelector(`[data-op="${op}"]`);
  if (btn) btn.classList.add('active');

  state.activeOp = op;
  els.opLabel.textContent = OP_LABELS[op] || op;
  setStatus('computing');
  clearSteps();
  showShimmer();

  showSecondary(needs || null);

  const body = { operation: op };

  const matA = getMatrixA();
  if (!matA) {
    setStatus('error');
    await renderResult('<div class="error-message">Matrix A is empty.</div>');
    return;
  }
  body.matrix = matA;

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

  const controller = new AbortController();
  state.currentAbort = controller;

  try {
    const resp = await fetch('/api/process', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
      signal: controller.signal,
    });

    state.currentAbort = null;
    if (myGen !== _opGeneration) return;
    const data = await resp.json();

    if (data.error) {
      setStatus('error');
      await renderResult(`<div class="error-message">Could not compute \u2014 ${escapeHtml(data.error)}</div>`);
      return;
    }

    setStatus('done');
    await renderResult(data.result || '<span class="placeholder">No result returned.</span>');
    state.lastRaw = data.raw || null;
    if (state.lastRaw) {
      els.answerToolbar.classList.remove('hidden');
    } else {
      els.answerToolbar.classList.add('hidden');
    }

    // Record history
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

    if (data.steps && data.steps.trim()) {
      renderSteps(data.steps);
    }
  } catch (err) {
    state.currentAbort = null;
    if (err.name === 'AbortError') {
      if (myGen !== _opGeneration) return;
      els.resultDisplay.innerHTML = '<p class="placeholder">Cancelled. Select an operation from the left panel.</p>';
      hideShimmer();
      setStatus('ready');
      clearSteps();
    } else {
      if (myGen !== _opGeneration) return;
      setStatus('error');
      await renderResult(`<div class="error-message">Network error: ${escapeHtml(err.message)}</div>`);
    }
  }
}

/* ─────────────────────────────────────────────────────────────────────────
   Equivalent Statements modal
   ───────────────────────────────────────────────────────────────────────── */

let _closeTimer   = null;
let _modalOpener  = null;
let _modalFocusable = [];

/** Collect all keyboard-focusable elements inside a container. */
function getFocusable(container) {
  return Array.from(container.querySelectorAll(
    'a[href], button:not([disabled]), input:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
  ));
}

async function openEquivModal() {
  const matA = getMatrixA();
  if (!matA) {
    alert('Please enter a matrix first.');
    return;
  }

  clearTimeout(_closeTimer);
  _modalOpener = document.activeElement;

  els.equivCategory.textContent = 'Loading\u2026';
  els.equivProps.innerHTML = '';
  els.equivList.innerHTML = '';

  els.equivModal.classList.remove('hidden');
  requestAnimationFrame(() =>
    requestAnimationFrame(() => {
      els.equivModal.classList.add('modal-visible');
      _modalFocusable = getFocusable(els.equivModal);
      if (_modalFocusable.length) _modalFocusable[0].focus();
    })
  );

  try {
    const resp = await fetch('/api/equivalent', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ matrix: matA }),
    });

    const data = await resp.json();

    if (data.error) {
      els.equivCategory.textContent = 'Error';
      els.equivList.innerHTML = `<li><div class="error-message">${escapeHtml(data.error)}</div></li>`;
      return;
    }

    els.equivCategory.textContent = data.category || '';

    const p = data.properties || {};
    const tagDefs = [
      { cls: 'tag-rows',    label: `rows = ${p.rows}` },
      { cls: 'tag-cols',    label: `cols = ${p.cols}` },
      { cls: 'tag-rank',    label: `rank = ${p.rank}` },
      { cls: 'tag-nullity', label: `nullity = ${p.nullity}` },
    ];
    els.equivProps.innerHTML = tagDefs
      .map(t => `<span class="prop-tag ${t.cls}">${escapeHtml(t.label)}</span>`)
      .join('');

    const stmts = data.statements || [];
    els.equivList.innerHTML = stmts.map(s => `<li>${s}</li>`).join('');

    typesetMath(els.equivModal);
  } catch (err) {
    els.equivCategory.textContent = 'Network error';
    els.equivList.innerHTML = `<li><div class="error-message">${escapeHtml(err.message)}</div></li>`;
  }
}

function closeEquivModal() {
  clearTimeout(_closeTimer);
  els.equivModal.classList.remove('modal-visible');
  _closeTimer = setTimeout(() => {
    els.equivModal.classList.add('hidden');
    if (_modalOpener && typeof _modalOpener.focus === 'function') {
      _modalOpener.focus();
    }
    _modalOpener = null;
  }, 200);
}

/* ─────────────────────────────────────────────────────────────────────────
   Utility
   ───────────────────────────────────────────────────────────────────────── */

function escapeHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

/* ─────────────────────────────────────────────────────────────────────────
   Initialisation
   ───────────────────────────────────────────────────────────────────────── */

// Cached NodeList for active-state management — buttons don't change after init
let opBtns;

/* ─────────────────────────────────────────────────────────────────────────
   History
   ───────────────────────────────────────────────────────────────────────── */

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

function init() {
  // 1. Apply op-group colors and wire accordion toggle with localStorage
  document.querySelectorAll('.op-group').forEach(g => {
    g.style.setProperty('--group-color', g.dataset.color);

    const header = g.querySelector('.group-header');
    const body   = g.querySelector('.group-body');
    if (!header || !body) return;

    const labelText  = g.querySelector('.group-label')?.textContent.trim() || '';
    const storageKey = labelText ? `la-studio-op-group-${labelText}` : null;

    if (storageKey && localStorage.getItem(storageKey) === 'collapsed') {
      g.classList.add('collapsed');
      header.setAttribute('aria-expanded', 'false');
    } else {
      header.setAttribute('aria-expanded', 'true');
    }

    header.addEventListener('click', () => {
      const nowCollapsed = g.classList.toggle('collapsed');
      header.setAttribute('aria-expanded', nowCollapsed ? 'false' : 'true');
      if (storageKey) localStorage.setItem(storageKey, nowCollapsed ? 'collapsed' : 'open');
    });

    header.addEventListener('keydown', e => {
      if (e.key === ' ' || e.key === 'Enter') { e.preventDefault(); header.click(); }
    });
  });

  // 2. Build Matrix A grid
  initGridA();

  // 3. Matrix A dim controls
  els.updateA.addEventListener('click', applyDimA);
  els.rowsA.addEventListener('keydown', e => e.key === 'Enter' && applyDimA());
  els.colsA.addEventListener('keydown', e => e.key === 'Enter' && applyDimA());
  els.clearA.addEventListener('click', () => clearGrid('gridA'));

  // 4. Text mode toggle for Matrix A
  els.toggleModeA.addEventListener('click', toggleTextModeA);

  // 5. Matrix B dim controls
  els.updateB.addEventListener('click', applyDimB);
  els.rowsB.addEventListener('keydown', e => e.key === 'Enter' && applyDimB());
  els.colsB.addEventListener('keydown', e => e.key === 'Enter' && applyDimB());

  // 5b. Chain multiply: modifier buttons
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
      state.chain.modC.T = false;
      state.chain.modC.inv = false;
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

  // 6. Operation buttons
  opBtns = document.querySelectorAll('.op-btn');
  opBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const op = btn.dataset.op;
      if (!op) return;
      runOperation(op, btn.dataset.needs);
    });
  });

  // 7. Steps collapse toggle
  els.toggleSteps.addEventListener('click', () => {
    state.stepsCollapsed = !state.stepsCollapsed;
    applyStepsVisibility();
  });

  // 8. Equivalent statements
  els.equivBtn.addEventListener('click', openEquivModal);
  els.closeModal.addEventListener('click', closeEquivModal);

  // 9. Cancel button
  els.cancelBtn.addEventListener('click', () => {
    if (state.currentAbort) {
      state.currentAbort.abort();
      state.currentAbort = null;
    }
  });

  // 10. Copy button
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

  // Close modal on backdrop click
  els.equivModal.addEventListener('click', e => {
    if (e.target === els.equivModal) closeEquivModal();
  });

  // History drawer
  els.historyBtn.addEventListener('click', openHistoryDrawer);
  els.closeHistoryBtn.addEventListener('click', closeHistoryDrawer);
  els.historyBackdrop.addEventListener('click', closeHistoryDrawer);
  els.clearHistoryBtn.addEventListener('click', () => {
    _history.length = 0;
    updateHistoryCount();
    renderHistoryList();
  });

  // Modal keyboard: Escape closes, Tab is trapped inside
  document.addEventListener('keydown', e => {
    if (!els.historyBackdrop.classList.contains('hidden')) {
      if (e.key === 'Escape') { closeHistoryDrawer(); return; }
    }
    if (els.equivModal.classList.contains('hidden')) return;
    if (e.key === 'Escape') {
      closeEquivModal();
    } else if (e.key === 'Tab') {
      if (!_modalFocusable.length) { e.preventDefault(); return; }
      const first = _modalFocusable[0];
      const last  = _modalFocusable[_modalFocusable.length - 1];
      if (e.shiftKey) {
        if (document.activeElement === first) { e.preventDefault(); last.focus(); }
      } else {
        if (document.activeElement === last)  { e.preventDefault(); first.focus(); }
      }
    }
  });
}

document.addEventListener('DOMContentLoaded', init);
