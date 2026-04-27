# Linear Algebra Studio — UI Overhaul Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete UI overhaul — light professional theme (IBM Plex Sans, warm white), single-scroll result panel, operation accordion with localStorage persistence, improved math display hierarchy, shimmer skeleton, and targeted JS fixes.

**Architecture:** Three static files only — `style.css` (complete rewrite), `index.html` (full restructure), `script.js` (targeted function edits). Backend `app.py` is unchanged. No new JS dependencies, no build step.

**Tech Stack:** Vanilla JS, CSS3, MathJax 3, IBM Plex Sans + IBM Plex Mono (Google Fonts), FastAPI static file serving.

---

## File Map

| File | Action | Responsibility |
|------|--------|----------------|
| `src/gui/static/style.css` | Complete rewrite | All visual design tokens, layout, components |
| `src/gui/static/index.html` | Complete rewrite | HTML structure — new op-bar, answer-card, steps-section, accordion groups |
| `src/gui/static/script.js` | Targeted edits | Arrow keys, accordion, shimmer, async typesetPromise, modal animation |

---

## Task 1: Complete CSS Rewrite

**Files:**
- Overwrite: `src/gui/static/style.css`

- [ ] **Step 1: Replace style.css with the complete new stylesheet**

Write the following as the entire contents of `src/gui/static/style.css`:

```css
/* ─────────────────────────────────────────────────────────────────────────
   Linear Algebra Studio — Professional Light Theme
   ───────────────────────────────────────────────────────────────────────── */

/* ── Design tokens ──────────────────────────────────────────────────────── */
:root {
  /* Backgrounds */
  --bg:          #fafaf8;
  --surface:     #ffffff;
  --surface-2:   #f5f5f2;
  --surface-3:   #eeede9;

  /* Borders */
  --border:        #e4e4de;
  --border-bright: #cfcfc7;

  /* Text */
  --text:       #18181b;
  --text-sub:   #52525b;
  --text-muted: #a1a1aa;

  /* Accent — deep indigo */
  --accent:       #3730a3;
  --accent-light: #6366f1;
  --accent-dim:   rgba(55, 48, 163, 0.07);
  --accent-glow:  rgba(55, 48, 163, 0.14);

  /* Semantic colours */
  --green:  #15803d;
  --amber:  #b45309;
  --rose:   #be123c;
  --purple: #6d28d9;
  --teal:   #0f766e;
  --sky:    #0369a1;

  /* Step element colours */
  --step-ero-bg:     #fffbeb;
  --step-ero-border: #fbbf24;
  --step-ero-color:  #78350f;
  --step-matrix-bg:  #f8f8f5;

  /* Typography */
  --font:   'IBM Plex Sans', system-ui, sans-serif;
  --mono:   'IBM Plex Mono', 'Fira Code', monospace;
  --radius: 8px;

  /* Shadows */
  --shadow-sm: 0 1px 3px rgba(0,0,0,0.07), 0 1px 2px rgba(0,0,0,0.05);
  --shadow-md: 0 4px 14px rgba(0,0,0,0.09), 0 2px 6px rgba(0,0,0,0.05);
  --shadow-lg: 0 20px 50px rgba(0,0,0,0.14), 0 8px 20px rgba(0,0,0,0.07);
}

/* ── Reset ──────────────────────────────────────────────────────────────── */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
html, body { height: 100%; overflow: hidden; }
body {
  font-family: var(--font);
  background: var(--bg);
  color: var(--text);
  font-size: 14px;
  line-height: 1.5;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

/* ── Animations ─────────────────────────────────────────────────────────── */
@keyframes fadeUp {
  from { opacity: 0; transform: translateY(7px); }
  to   { opacity: 1; transform: translateY(0); }
}
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50%       { opacity: 0.42; }
}
@keyframes shimmer {
  0%   { background-position: -400px 0; }
  100% { background-position:  400px 0; }
}

/* ── Layout ─────────────────────────────────────────────────────────────── */
.layout { display: flex; height: 100vh; overflow: hidden; }

/* ── Left Panel ─────────────────────────────────────────────────────────── */
.left-panel {
  width: 360px;
  min-width: 360px;
  flex-shrink: 0;
  height: 100vh;
  overflow-y: auto;
  overflow-x: hidden;
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding: 0.875rem;
  background: var(--surface-2);
  scrollbar-width: thin;
  scrollbar-color: var(--border-bright) transparent;
  animation: fadeUp 0.3s ease both;
}
.left-panel::-webkit-scrollbar { width: 4px; }
.left-panel::-webkit-scrollbar-track { background: transparent; }
.left-panel::-webkit-scrollbar-thumb { background: var(--border-bright); border-radius: 2px; }

/* ── Brand ──────────────────────────────────────────────────────────────── */
.brand {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  padding: 0.25rem 0 0.75rem;
  border-bottom: 1px solid var(--border);
  margin-bottom: 0.125rem;
  flex-shrink: 0;
}
.brand-icon { display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.brand-name { font-size: 0.92rem; font-weight: 400; color: var(--text-sub); letter-spacing: 0.01em; }
.brand-name strong { font-weight: 700; color: var(--text); }

/* ── Input Cards ────────────────────────────────────────────────────────── */
.input-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  flex-shrink: 0;
  box-shadow: var(--shadow-sm);
  transition: border-color 0.15s, box-shadow 0.15s;
  overflow: hidden;
}
.input-card:focus-within {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px var(--accent-glow), var(--shadow-sm);
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.5rem 0.75rem;
  border-bottom: 1px solid var(--border);
  gap: 0.5rem;
  flex-wrap: wrap;
  min-height: 40px;
  background: var(--surface);
}
.card-label {
  font-size: 0.72rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--text-sub);
}

/* ── Dimension controls ─────────────────────────────────────────────────── */
.dim-controls { display: flex; align-items: center; gap: 0.28rem; }
.dim-controls input[type="number"] {
  width: 36px;
  height: 26px;
  background: var(--surface-2);
  border: 1px solid var(--border);
  border-radius: 5px;
  color: var(--text);
  font-family: var(--mono);
  font-size: 0.8rem;
  text-align: center;
  padding: 0;
  -moz-appearance: textfield;
  transition: border-color 0.15s;
}
.dim-controls input[type="number"]::-webkit-inner-spin-button,
.dim-controls input[type="number"]::-webkit-outer-spin-button { -webkit-appearance: none; }
.dim-controls input[type="number"]:focus { outline: none; border-color: var(--accent); }
.dim-sep { font-size: 0.78rem; color: var(--text-muted); }

/* ── Small buttons ──────────────────────────────────────────────────────── */
.btn-sm {
  height: 26px;
  padding: 0 0.6rem;
  background: var(--surface-2);
  border: 1px solid var(--border-bright);
  border-radius: 5px;
  color: var(--text-sub);
  font-family: var(--font);
  font-size: 0.73rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.12s, color 0.12s, border-color 0.12s;
  white-space: nowrap;
}
.btn-sm:hover { background: var(--accent-dim); border-color: var(--accent); color: var(--accent); }
.btn-sm-ghost { background: transparent; border-color: var(--border); color: var(--text-muted); }
.btn-sm-ghost:hover { background: rgba(190,18,60,0.06); border-color: rgba(190,18,60,0.3); color: var(--rose); }

/* ── Matrix grid ────────────────────────────────────────────────────────── */
.matrix-grid {
  display: grid;
  gap: 5px;
  padding: 0.75rem;
  background: var(--surface-2);
  overflow-x: auto;
  justify-content: start;
  scrollbar-width: thin;
  scrollbar-color: var(--border) transparent;
}
.matrix-grid::-webkit-scrollbar { height: 3px; }
.matrix-grid::-webkit-scrollbar-thumb { background: var(--border-bright); border-radius: 2px; }

.grid-cell {
  width: 68px;
  height: 40px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 5px;
  color: var(--text);
  font-family: var(--mono);
  font-size: 0.92rem;
  text-align: center;
  padding: 0 0.35rem;
  transition: border-color 0.15s, box-shadow 0.15s;
}
.grid-cell:focus {
  outline: none;
  border-color: var(--accent);
  box-shadow: 0 0 0 3px var(--accent-glow);
}
.grid-cell::placeholder { color: var(--text-muted); }

/* ── Text mode ──────────────────────────────────────────────────────────── */
#textWrapA { padding: 0.75rem; background: var(--surface-2); }
#textA {
  width: 100%;
  min-height: 78px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  color: var(--text);
  font-family: var(--mono);
  font-size: 0.82rem;
  padding: 0.55rem 0.75rem;
  resize: vertical;
  transition: border-color 0.15s, box-shadow 0.15s;
  line-height: 1.65;
}
#textA:focus { outline: none; border-color: var(--accent); box-shadow: 0 0 0 3px var(--accent-glow); }
#textA::placeholder { color: var(--text-muted); }

/* ── Mode toggle ────────────────────────────────────────────────────────── */
.mode-toggle {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  width: 100%;
  padding: 0.38rem 0.75rem;
  background: transparent;
  border: none;
  border-top: 1px solid var(--border);
  color: var(--text-muted);
  font-family: var(--font);
  font-size: 0.72rem;
  font-weight: 500;
  cursor: pointer;
  transition: color 0.15s, background 0.15s;
  text-align: left;
}
.mode-toggle:hover { color: var(--accent); background: var(--accent-dim); }

/* ── Equiv button ───────────────────────────────────────────────────────── */
.equiv-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  width: 100%;
  padding: 0.58rem 1rem;
  flex-shrink: 0;
  background: var(--accent-dim);
  border: 1px solid rgba(55, 48, 163, 0.2);
  border-radius: var(--radius);
  color: var(--accent);
  font-family: var(--font);
  font-size: 0.83rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s, border-color 0.15s, box-shadow 0.15s;
  letter-spacing: 0.01em;
}
.equiv-btn:hover {
  background: rgba(55, 48, 163, 0.11);
  border-color: var(--accent);
  box-shadow: 0 0 0 3px var(--accent-glow);
}

/* ── Secondary card ─────────────────────────────────────────────────────── */
.secondary-card { border-color: rgba(21, 128, 61, 0.25); position: relative; }
.secondary-card::before {
  content: '';
  position: absolute;
  left: 0; top: 0; bottom: 0;
  width: 3px;
  background: var(--green);
  border-radius: var(--radius) 0 0 var(--radius);
  z-index: 1;
}
.hint { font-size: 0.72rem; color: var(--text-muted); padding: 0.3rem 0.75rem 0.55rem; font-style: italic; line-height: 1.4; }

/* ── Ops panel ──────────────────────────────────────────────────────────── */
.ops-panel { display: flex; flex-direction: column; flex-shrink: 0; gap: 0.1rem; }

.op-group {
  border-left: 3px solid var(--group-color, var(--border-bright));
  padding-left: 0.65rem;
  margin-bottom: 0.2rem;
}

/* ── Group header (accordion button) ────────────────────────────────────── */
.group-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  background: none;
  border: none;
  cursor: pointer;
  padding: 0.35rem 0.25rem 0.3rem 0;
  gap: 0.4rem;
  border-radius: 4px;
  transition: background 0.12s;
  text-align: left;
}
.group-header:hover { background: var(--surface-3); }
.group-header:focus { outline: 2px solid var(--accent); outline-offset: 1px; border-radius: 4px; }

.group-label {
  font-size: 0.68rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.09em;
  color: var(--text-muted);
}

.chevron {
  flex-shrink: 0;
  color: var(--text-muted);
  transition: transform 0.2s ease;
}
.op-group.collapsed .chevron { transform: rotate(-90deg); }

.group-body { padding-bottom: 0.35rem; overflow: hidden; }
.op-group.collapsed .group-body { display: none; }

.group-btns { display: flex; flex-wrap: wrap; gap: 0.3rem; padding-top: 0.22rem; }

/* ── Operation buttons ──────────────────────────────────────────────────── */
.op-btn {
  background: var(--surface);
  border: 1px solid var(--border);
  color: var(--text-sub);
  padding: 0.36rem 0.65rem;
  border-radius: 6px;
  font-family: var(--font);
  font-size: 0.8rem;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.12s, border-color 0.12s, color 0.12s, box-shadow 0.12s;
  position: relative;
  line-height: 1;
  white-space: nowrap;
  box-shadow: var(--shadow-sm);
}
.op-btn:hover { background: var(--accent-dim); border-color: var(--accent); color: var(--accent); }
.op-btn.active { background: var(--accent); border-color: var(--accent); color: #fff; box-shadow: var(--shadow-sm); }
.op-btn.steps-badge::after {
  content: '✦';
  font-size: 0.5rem;
  color: var(--amber);
  position: absolute;
  top: 3px; right: 4px;
  line-height: 1;
}
.op-btn.active.steps-badge::after { color: rgba(255,255,255,0.65); }

/* ── Right Panel ────────────────────────────────────────────────────────── */
.right-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-width: 0;
  background: var(--bg);
  animation: fadeUp 0.3s 0.05s ease both;
}

/* ── Op bar (sticky header) ─────────────────────────────────────────────── */
.op-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.7rem 1.75rem;
  border-bottom: 1px solid var(--border);
  background: var(--surface);
  flex-shrink: 0;
  z-index: 10;
  box-shadow: var(--shadow-sm);
}
.op-bar-right { display: flex; align-items: center; gap: 0.5rem; }
.op-label { font-size: 0.88rem; font-weight: 600; color: var(--text-sub); letter-spacing: 0.01em; }

/* ── Cancel button ──────────────────────────────────────────────────────── */
.btn-cancel {
  height: 26px;
  padding: 0 0.65rem;
  background: rgba(190,18,60,0.06);
  border: 1px solid rgba(190,18,60,0.28);
  border-radius: 5px;
  color: var(--rose);
  font-family: var(--font);
  font-size: 0.73rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s, border-color 0.15s;
  white-space: nowrap;
}
.btn-cancel:hover { background: rgba(190,18,60,0.12); border-color: var(--rose); }

/* ── Status badge ───────────────────────────────────────────────────────── */
.status-badge {
  font-size: 0.68rem;
  font-weight: 700;
  padding: 0.18rem 0.6rem;
  border-radius: 100px;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  border: 1px solid transparent;
  transition: background 0.2s ease, color 0.2s ease, border-color 0.2s ease;
}
.status-ready    { background: rgba(161,161,170,0.1);  border-color: rgba(161,161,170,0.2);  color: var(--text-muted); }
.status-computing{ background: rgba(180,83,9,0.08);    border-color: rgba(180,83,9,0.22);    color: var(--amber); animation: pulse 1.1s ease-in-out infinite; }
.status-done     { background: rgba(21,128,61,0.08);   border-color: rgba(21,128,61,0.22);   color: var(--green); }
.status-error    { background: rgba(190,18,60,0.07);   border-color: rgba(190,18,60,0.2);    color: var(--rose); }

/* ── Result scroll container ────────────────────────────────────────────── */
.result-scroll {
  flex: 1;
  overflow-y: auto;
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
  scrollbar-width: thin;
  scrollbar-color: var(--border-bright) transparent;
}
.result-scroll::-webkit-scrollbar { width: 5px; }
.result-scroll::-webkit-scrollbar-thumb { background: var(--border-bright); border-radius: 3px; }

/* ── Answer card ────────────────────────────────────────────────────────── */
.answer-card {
  background: var(--surface);
  border-radius: 12px;
  border-top: 3px solid var(--accent);
  box-shadow: var(--shadow-md);
  overflow: hidden;
  min-height: 140px;
}

/* ── Shimmer skeleton ───────────────────────────────────────────────────── */
.answer-shimmer {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 3rem 2rem;
}
.shimmer-block {
  height: 44px;
  width: 300px;
  max-width: 100%;
  border-radius: 8px;
  background: linear-gradient(
    90deg,
    var(--surface-2) 25%,
    var(--surface-3) 50%,
    var(--surface-2) 75%
  );
  background-size: 400px 100%;
  animation: shimmer 1.4s ease infinite;
}

/* ── Result body ────────────────────────────────────────────────────────── */
.result-body {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 140px;
  padding: 2rem 2.5rem;
  text-align: center;
  font-size: 1.1rem;
  overflow-x: auto;
}
.placeholder { color: var(--text-muted); font-size: 0.85rem; font-style: italic; }
.error-message {
  color: var(--rose);
  font-size: 0.83rem;
  background: rgba(190,18,60,0.05);
  border: 1px solid rgba(190,18,60,0.18);
  border-radius: var(--radius);
  padding: 0.75rem 1rem;
  font-family: var(--mono);
  text-align: left;
  max-width: 100%;
  word-break: break-word;
  line-height: 1.55;
}

/* ── Steps section ──────────────────────────────────────────────────────── */
.steps-section {
  background: var(--surface);
  border-radius: 12px;
  box-shadow: var(--shadow-sm);
  overflow: hidden;
  border: 1px solid var(--border);
}
.steps-section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.65rem 1.25rem;
  border-bottom: 1px solid var(--border);
  background: var(--surface-2);
}
.steps-title-group { display: flex; align-items: center; gap: 0.5rem; }
.steps-title {
  font-size: 0.72rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--amber);
}
.collapse-btn {
  background: none;
  border: 1px solid var(--border);
  border-radius: 5px;
  color: var(--text-muted);
  font-family: var(--font);
  font-size: 0.72rem;
  font-weight: 500;
  cursor: pointer;
  padding: 0.2rem 0.55rem;
  transition: all 0.15s;
}
.collapse-btn:hover { color: var(--text-sub); background: var(--surface-3); border-color: var(--border-bright); }

.steps-body {
  padding: 1rem 1.25rem 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
}

/* ── Step elements ──────────────────────────────────────────────────────── */
.step-ero {
  display: block;
  padding: 0.32rem 0.875rem;
  background: var(--step-ero-bg);
  border: 1px solid var(--step-ero-border);
  border-radius: 100px;
  color: var(--step-ero-color);
  font-size: 0.95rem;
  margin: 0.5rem 0;
  width: fit-content;
  max-width: 100%;
  line-height: 1.5;
}
.step-matrix {
  background: var(--step-matrix-bg);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 0.875rem 1.5rem;
  margin: 0.3rem 0;
  text-align: center;
  overflow-x: auto;
  line-height: 1.9;
  scrollbar-width: thin;
  scrollbar-color: var(--border) transparent;
}
.step-matrix::-webkit-scrollbar { height: 3px; }
.step-matrix::-webkit-scrollbar-thumb { background: var(--border-bright); border-radius: 2px; }

.step-text { font-size: 0.82rem; color: var(--text-sub); padding: 0.15rem 0; line-height: 1.5; }

.step-case {
  font-weight: 700;
  font-size: 0.92rem;
  color: var(--accent);
  padding: 0.65rem 0 0.3rem;
  border-top: 1px solid var(--border);
  margin-top: 0.5rem;
  letter-spacing: 0.01em;
}
.step-case:first-child { border-top: none; margin-top: 0; }

/* ── Modal ──────────────────────────────────────────────────────────────── */
.modal {
  position: fixed;
  inset: 0;
  background: rgba(24, 24, 27, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
  backdrop-filter: blur(4px);
  padding: 1rem;
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.2s ease;
}
.modal.hidden { display: none; }
.modal.modal-visible { opacity: 1; pointer-events: auto; }

.modal-box {
  position: relative;
  background: var(--surface);
  border: 1px solid var(--border-bright);
  border-radius: 12px;
  padding: 1.75rem 2rem 2rem;
  max-width: 660px;
  width: 100%;
  max-height: 82vh;
  overflow-y: auto;
  box-shadow: var(--shadow-lg);
  transform: scale(0.96);
  transition: transform 0.2s ease;
  scrollbar-width: thin;
  scrollbar-color: var(--border-bright) transparent;
}
.modal-box::-webkit-scrollbar { width: 4px; }
.modal-box::-webkit-scrollbar-thumb { background: var(--border-bright); border-radius: 2px; }
.modal.modal-visible .modal-box { transform: scale(1); }

.modal-close {
  position: absolute;
  top: 1rem; right: 1rem;
  background: var(--surface-2);
  border: 1px solid var(--border);
  border-radius: 6px;
  color: var(--text-muted);
  width: 28px; height: 28px;
  display: flex; align-items: center; justify-content: center;
  cursor: pointer;
  transition: color 0.15s, background 0.15s, border-color 0.15s;
  flex-shrink: 0;
}
.modal-close:hover { color: var(--rose); background: rgba(190,18,60,0.07); border-color: rgba(190,18,60,0.35); }

.modal-header { display: flex; align-items: flex-start; gap: 0.75rem; margin-bottom: 1rem; padding-right: 2.5rem; }
.modal-icon { flex-shrink: 0; margin-top: 0.15rem; }
.modal-title { font-size: 1rem; font-weight: 700; color: var(--text); line-height: 1.4; }

.equiv-props { display: flex; flex-wrap: wrap; gap: 0.4rem; margin-bottom: 1.25rem; }
.prop-tag {
  display: inline-flex; align-items: center; gap: 0.28rem;
  padding: 0.22rem 0.6rem; border-radius: 100px;
  font-size: 0.72rem; font-weight: 700; font-family: var(--mono); letter-spacing: 0.03em;
}
.prop-tag.tag-rows    { background: rgba(3,105,161,0.08);   border: 1px solid rgba(3,105,161,0.22);   color: var(--sky);    }
.prop-tag.tag-cols    { background: rgba(109,40,217,0.08);  border: 1px solid rgba(109,40,217,0.22);  color: var(--purple); }
.prop-tag.tag-rank    { background: rgba(21,128,61,0.08);   border: 1px solid rgba(21,128,61,0.22);   color: var(--green);  }
.prop-tag.tag-nullity { background: rgba(180,83,9,0.08);    border: 1px solid rgba(180,83,9,0.22);    color: var(--amber);  }

.equiv-list {
  list-style: none;
  counter-reset: eq-item;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  overflow: hidden;
}
.equiv-list li {
  counter-increment: eq-item;
  padding: 0.62rem 1rem;
  font-size: 0.88rem;
  line-height: 1.65;
  border-bottom: 1px solid var(--border);
  display: flex; align-items: flex-start; gap: 0.65rem;
  transition: background 0.12s;
}
.equiv-list li:last-child { border-bottom: none; }
.equiv-list li:hover { background: var(--surface-2); }
.equiv-list li::before {
  content: counter(eq-item);
  flex-shrink: 0;
  width: 18px; height: 18px;
  display: flex; align-items: center; justify-content: center;
  background: var(--surface-2);
  border: 1px solid var(--border);
  border-radius: 4px;
  font-size: 0.65rem; font-weight: 700;
  color: var(--text-muted);
  font-family: var(--mono);
  margin-top: 0.22rem;
}

/* ── Utilities ──────────────────────────────────────────────────────────── */
.hidden { display: none !important; }
mjx-container { overflow-x: auto; overflow-y: hidden; max-width: 100%; }

/* ── Responsive ─────────────────────────────────────────────────────────── */
@media (max-width: 1023px) {
  html, body { height: auto; overflow: auto; }
  .layout { flex-direction: column; height: auto; overflow: visible; }
  .left-panel { width: 100%; min-width: 0; height: auto; overflow: visible; border-right: none; border-bottom: 1px solid var(--border); }
  .right-panel { overflow: visible; }
  .result-scroll { overflow: visible; flex: none; }
  .modal-box { max-height: 90vh; }
}
@media (max-width: 540px) {
  .left-panel { padding: 0.75rem; }
  .op-bar { padding-left: 1rem; padding-right: 1rem; }
  .result-scroll { padding: 1rem; }
  .modal-box { padding: 1.25rem 1rem 1.5rem; }
  .card-header { flex-direction: column; align-items: flex-start; gap: 0.4rem; }
}
```

- [ ] **Step 2: Verify CSS loads without errors**

Run: `PYTHONPATH=src uv run uvicorn src.gui.app:app --port 8000 --reload`

Open `http://localhost:8000` in browser. Open DevTools Console — confirm no CSS parse errors. The left panel should be white/light gray, the background warm white.

- [ ] **Step 3: Commit**

```bash
git add src/gui/static/style.css
git commit -m "style: complete CSS rewrite — light professional theme"
```

---

## Task 2: HTML Restructure

**Files:**
- Overwrite: `src/gui/static/index.html`

- [ ] **Step 1: Replace index.html with the new structure**

Write the following as the entire contents of `src/gui/static/index.html`:

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Linear Algebra Studio</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@300;400;500;600;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="/static/style.css">
  <script>
    window.MathJax = {
      tex: {
        inlineMath: [['\\(', '\\)']],
        displayMath: [['$$', '$$'], ['\\[', '\\]']],
        processEscapes: true
      },
      options: {
        skipHtmlTags: ['script', 'noscript', 'style', 'textarea']
      }
    };
  </script>
  <script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml.js"></script>
</head>
<body>
  <div class="layout">

    <!-- ═══════════════ LEFT PANEL ═══════════════ -->
    <aside class="left-panel">

      <div class="brand">
        <div class="brand-icon">
          <svg width="26" height="26" viewBox="0 0 26 26" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M8 3L5 3L5 23L8 23" stroke="#3730a3" stroke-width="1.6" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M18 3L21 3L21 23L18 23" stroke="#3730a3" stroke-width="1.6" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
            <circle cx="10.5" cy="10" r="1.5" fill="#3730a3" opacity="0.85"/>
            <circle cx="15.5" cy="10" r="1.5" fill="#6d28d9" opacity="0.85"/>
            <circle cx="10.5" cy="16" r="1.5" fill="#0f766e" opacity="0.85"/>
            <circle cx="15.5" cy="16" r="1.5" fill="#15803d" opacity="0.85"/>
          </svg>
        </div>
        <span class="brand-name">Linear Algebra <strong>Studio</strong></span>
      </div>

      <!-- Matrix A Input -->
      <div class="input-card" id="cardA">
        <div class="card-header">
          <span class="card-label">Matrix A</span>
          <div class="dim-controls">
            <input type="number" id="rowsA" value="2" min="1" max="10" aria-label="Rows">
            <span class="dim-sep">×</span>
            <input type="number" id="colsA" value="2" min="1" max="10" aria-label="Cols">
            <button class="btn-sm" id="updateA">Set</button>
            <button class="btn-sm btn-sm-ghost" id="clearA">Clear</button>
          </div>
        </div>
        <div id="gridA" class="matrix-grid"></div>
        <div id="textWrapA" class="hidden">
          <textarea id="textA" placeholder="[1 2; 3 4]  or  [[1,2],[3,4]]  or  LaTeX" spellcheck="false"></textarea>
        </div>
        <button class="mode-toggle" id="toggleModeA">
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none"><path d="M2 4h10M2 7h7M2 10h5" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/></svg>
          Text / LaTeX mode
        </button>
      </div>

      <!-- Equivalent Statements (moved above ops panel) -->
      <button class="equiv-btn" id="equivBtn">
        <svg width="15" height="15" viewBox="0 0 15 15" fill="none"><path d="M2 4.5h11M2 7.5h8M2 10.5h5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/><circle cx="12.5" cy="10.5" r="2" stroke="currentColor" stroke-width="1.2"/></svg>
        Equivalent Statements
      </button>

      <!-- Secondary Input (b vector or matrix B) -->
      <div class="input-card secondary-card hidden" id="cardB">
        <div class="card-header">
          <span class="card-label" id="labelB">Vector b</span>
          <div class="dim-controls" id="dimCtrlB">
            <input type="number" id="rowsB" value="2" min="1" max="10" aria-label="Rows B">
            <span class="dim-sep">×</span>
            <input type="number" id="colsB" value="1" min="1" max="10" aria-label="Cols B">
            <button class="btn-sm" id="updateB">Set</button>
          </div>
        </div>
        <div id="gridB" class="matrix-grid"></div>
        <p class="hint" id="hintB"></p>
      </div>

      <!-- Operations Accordion -->
      <div class="ops-panel">

        <!-- Row Reduction -->
        <div class="op-group" data-color="var(--accent)">
          <button class="group-header" type="button">
            <span class="group-label">Row Reduction</span>
            <svg class="chevron" width="12" height="12" viewBox="0 0 12 12" fill="none"><path d="M2 4l4 4 4-4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
          </button>
          <div class="group-body">
            <div class="group-btns">
              <button class="op-btn" data-op="rref" data-needs="">RREF</button>
              <button class="op-btn steps-badge" data-op="ref" data-needs="">REF</button>
            </div>
          </div>
        </div>

        <!-- Factorizations -->
        <div class="op-group" data-color="var(--purple)">
          <button class="group-header" type="button">
            <span class="group-label">Factorizations</span>
            <svg class="chevron" width="12" height="12" viewBox="0 0 12 12" fill="none"><path d="M2 4l4 4 4-4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
          </button>
          <div class="group-body">
            <div class="group-btns">
              <button class="op-btn steps-badge" data-op="lu" data-needs="">LU / PLU</button>
              <button class="op-btn steps-badge" data-op="qr" data-needs="">QR</button>
              <button class="op-btn" data-op="svd" data-needs="">SVD</button>
              <button class="op-btn steps-badge" data-op="gram_schmidt" data-needs="">Gram-Schmidt</button>
            </div>
          </div>
        </div>

        <!-- Properties -->
        <div class="op-group" data-color="var(--sky)">
          <button class="group-header" type="button">
            <span class="group-label">Properties</span>
            <svg class="chevron" width="12" height="12" viewBox="0 0 12 12" fill="none"><path d="M2 4l4 4 4-4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
          </button>
          <div class="group-body">
            <div class="group-btns">
              <button class="op-btn" data-op="det" data-needs="">Determinant</button>
              <button class="op-btn steps-badge" data-op="inv" data-needs="">Inverse</button>
              <button class="op-btn" data-op="rank" data-needs="">Rank &amp; Nullity</button>
            </div>
          </div>
        </div>

        <!-- Eigen Analysis -->
        <div class="op-group" data-color="var(--amber)">
          <button class="group-header" type="button">
            <span class="group-label">Eigen Analysis</span>
            <svg class="chevron" width="12" height="12" viewBox="0 0 12 12" fill="none"><path d="M2 4l4 4 4-4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
          </button>
          <div class="group-body">
            <div class="group-btns">
              <button class="op-btn" data-op="eigenvals" data-needs="">Eigenvalues</button>
              <button class="op-btn" data-op="eigenvects" data-needs="">Eigenvectors</button>
              <button class="op-btn steps-badge" data-op="diagonalize" data-needs="">Diagonalize</button>
              <button class="op-btn steps-badge" data-op="orth_diagonalize" data-needs="">Orth. Diag.</button>
            </div>
          </div>
        </div>

        <!-- Vector Spaces -->
        <div class="op-group" data-color="var(--teal)">
          <button class="group-header" type="button">
            <span class="group-label">Vector Spaces</span>
            <svg class="chevron" width="12" height="12" viewBox="0 0 12 12" fill="none"><path d="M2 4l4 4 4-4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
          </button>
          <div class="group-body">
            <div class="group-btns">
              <button class="op-btn" data-op="nullspace" data-needs="">Nullspace</button>
              <button class="op-btn" data-op="colspace" data-needs="">Col. Space</button>
              <button class="op-btn steps-badge" data-op="orth_complement" data-needs="">Orth. Complement</button>
              <button class="op-btn steps-badge" data-op="col_constraints" data-needs="">Col. Constraints</button>
              <button class="op-btn steps-badge" data-op="extend_basis" data-needs="">Extend Basis</button>
            </div>
          </div>
        </div>

        <!-- Linear Systems -->
        <div class="op-group" data-color="var(--green)">
          <button class="group-header" type="button">
            <span class="group-label">Linear Systems</span>
            <svg class="chevron" width="12" height="12" viewBox="0 0 12 12" fill="none"><path d="M2 4l4 4 4-4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
          </button>
          <div class="group-body">
            <div class="group-btns">
              <button class="op-btn" data-op="solve" data-needs="rhs">Solve Ax = b</button>
              <button class="op-btn steps-badge" data-op="least_squares" data-needs="rhs">Least Squares</button>
              <button class="op-btn steps-badge" data-op="projection" data-needs="">Projection [A|b]</button>
            </div>
          </div>
        </div>

        <!-- Subspaces -->
        <div class="op-group" data-color="var(--rose)">
          <button class="group-header" type="button">
            <span class="group-label">Subspaces</span>
            <svg class="chevron" width="12" height="12" viewBox="0 0 12 12" fill="none"><path d="M2 4l4 4 4-4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
          </button>
          <div class="group-body">
            <div class="group-btns">
              <button class="op-btn steps-badge" data-op="intersect" data-needs="matrix2">Intersect</button>
              <button class="op-btn steps-badge" data-op="transition" data-needs="matrix2">Transition Matrix</button>
            </div>
          </div>
        </div>

        <!-- Symbolic -->
        <div class="op-group" data-color="var(--text-muted)">
          <button class="group-header" type="button">
            <span class="group-label">Symbolic / Parametric</span>
            <svg class="chevron" width="12" height="12" viewBox="0 0 12 12" fill="none"><path d="M2 4l4 4 4-4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
          </button>
          <div class="group-body">
            <div class="group-btns">
              <button class="op-btn steps-badge" data-op="eval_cases" data-needs="rhs-optional">Evaluate Cases</button>
              <button class="op-btn" data-op="find_cases" data-needs="">Find Cases</button>
            </div>
          </div>
        </div>

      </div><!-- /ops-panel -->

    </aside><!-- /left-panel -->

    <!-- ═══════════════ RIGHT PANEL ═══════════════ -->
    <main class="right-panel">

      <!-- Sticky operation bar -->
      <div class="op-bar">
        <span id="opLabel" class="op-label">—</span>
        <div class="op-bar-right">
          <button id="cancelBtn" class="btn-cancel hidden" aria-label="Cancel computation">✕ Cancel</button>
          <span id="statusBadge" class="status-badge status-ready">Ready</span>
        </div>
      </div>

      <!-- Single scrollable content area -->
      <div class="result-scroll">

        <!-- Answer card -->
        <div class="answer-card">
          <div class="answer-shimmer hidden" id="answerShimmer">
            <div class="shimmer-block"></div>
          </div>
          <div id="resultDisplay" class="result-body">
            <p class="placeholder">Select an operation from the left panel</p>
          </div>
        </div>

        <!-- Working steps (inline section, expands freely) -->
        <div class="steps-section hidden" id="stepsCard">
          <div class="steps-section-header">
            <div class="steps-title-group">
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none"><path d="M1 3.5h12M1 7h12M1 10.5h12" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/></svg>
              <span class="steps-title">Working Steps</span>
            </div>
            <button class="collapse-btn" id="toggleSteps">
              <span id="toggleStepsLabel">Hide steps</span>
            </button>
          </div>
          <div id="stepsBody" class="steps-body"></div>
        </div>

      </div><!-- /result-scroll -->

    </main><!-- /right-panel -->

  </div><!-- /layout -->

  <!-- ═══════════════ MODAL ═══════════════ -->
  <div class="modal hidden" id="equivModal" role="dialog" aria-modal="true" aria-labelledby="equivCategory">
    <div class="modal-box">
      <button class="modal-close" id="closeModal" aria-label="Close">
        <svg width="14" height="14" viewBox="0 0 14 14" fill="none"><path d="M1 1l12 12M13 1L1 13" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>
      </button>
      <div class="modal-header">
        <div class="modal-icon">
          <svg width="18" height="18" viewBox="0 0 18 18" fill="none"><path d="M2 5h14M2 9h10M2 13h7" stroke="var(--accent)" stroke-width="1.6" stroke-linecap="round"/></svg>
        </div>
        <h2 id="equivCategory" class="modal-title"></h2>
      </div>
      <div id="equivProps" class="equiv-props"></div>
      <ul id="equivList" class="equiv-list"></ul>
    </div>
  </div>

  <script src="/static/script.js"></script>
</body>
</html>
```

- [ ] **Step 2: Verify the HTML renders correctly**

Refresh `http://localhost:8000`. Confirm:
- Left panel: brand → Matrix A card → Equiv button → ops accordion (all 8 groups with chevrons)
- Right panel: sticky op-bar at top, then scrollable area with the answer card showing "Select an operation from the left panel"
- No broken layout, no JavaScript errors in console

- [ ] **Step 3: Commit**

```bash
git add src/gui/static/index.html
git commit -m "feat: restructure HTML — accordion groups, single-scroll result panel, shimmer"
```

---

## Task 3: JS — Accordion + Arrow Key Navigation

**Files:**
- Modify: `src/gui/static/script.js`

Two targeted changes: (1) add arrow-key navigation to `createGrid()`, (2) replace the op-group setup in `init()` with accordion logic.

- [ ] **Step 1: Add arrow-key navigation to `createGrid()`**

In `src/gui/static/script.js`, find the `createGrid()` function. The existing `keydown` listener only handles `Enter`. Replace the entire `input.addEventListener('keydown', ...)` block (lines ~110–117) with the expanded version below:

```js
      // Navigation: Enter moves down, arrows move in all 4 directions
      input.addEventListener('keydown', e => {
        if (e.key === 'Enter') {
          e.preventDefault();
          const next = container.querySelector(
            `[data-row="${r + 1}"][data-col="${c}"]`
          );
          if (next) next.focus();
        } else if (e.key === 'ArrowRight') {
          e.preventDefault();
          const next = container.querySelector(
            `[data-row="${r}"][data-col="${c + 1}"]`
          );
          if (next) next.focus();
        } else if (e.key === 'ArrowLeft') {
          e.preventDefault();
          const next = container.querySelector(
            `[data-row="${r}"][data-col="${c - 1}"]`
          );
          if (next) next.focus();
        } else if (e.key === 'ArrowDown') {
          e.preventDefault();
          const next = container.querySelector(
            `[data-row="${r + 1}"][data-col="${c}"]`
          );
          if (next) next.focus();
        } else if (e.key === 'ArrowUp') {
          e.preventDefault();
          const next = container.querySelector(
            `[data-row="${r - 1}"][data-col="${c}"]`
          );
          if (next) next.focus();
        }
      });
```

- [ ] **Step 2: Replace op-group setup in `init()` with accordion logic**

In `init()`, find the comment `// 1. Apply op-group colors` and the `forEach` block below it (currently ~5 lines). Replace that entire block with:

```js
  // 1. Apply op-group colors and wire accordion toggle with localStorage
  document.querySelectorAll('.op-group').forEach(g => {
    g.style.setProperty('--group-color', g.dataset.color);

    const header = g.querySelector('.group-header');
    const body   = g.querySelector('.group-body');
    if (!header || !body) return;

    const labelText  = g.querySelector('.group-label')?.textContent.trim() ?? '';
    const storageKey = `la-studio-op-group-${labelText}`;

    // Restore collapsed state from localStorage
    if (localStorage.getItem(storageKey) === 'collapsed') {
      g.classList.add('collapsed');
    }

    header.addEventListener('click', () => {
      const nowCollapsed = g.classList.toggle('collapsed');
      localStorage.setItem(storageKey, nowCollapsed ? 'collapsed' : 'open');
    });

    header.addEventListener('keydown', e => {
      if (e.key === ' ' || e.key === 'Enter') {
        e.preventDefault();
        header.click();
      }
    });
  });
```

- [ ] **Step 3: Fix steps collapse toggle text**

In `init()`, find the steps toggle setup (step `// 7.`). The toggle currently sets `'\u25be Collapse'` / `'\u25b8 Expand'`. Replace the entire toggle block with:

```js
  // 7. Steps collapse toggle
  els.toggleSteps.addEventListener('click', () => {
    state.stepsCollapsed = !state.stepsCollapsed;
    if (state.stepsCollapsed) {
      els.stepsBody.classList.add('hidden');
      els.toggleStepsLabel.textContent = 'Show steps';
    } else {
      els.stepsBody.classList.remove('hidden');
      els.toggleStepsLabel.textContent = 'Hide steps';
    }
  });
```

Also update `renderSteps()` so the initial label matches — find the two lines inside `renderSteps()` that set `els.toggleStepsLabel.textContent`:

```js
    // Change:
    els.toggleStepsLabel.textContent = '\u25b8 Expand';
    // To:
    els.toggleStepsLabel.textContent = 'Show steps';

    // Change:
    els.toggleStepsLabel.textContent = '\u25be Collapse';
    // To:
    els.toggleStepsLabel.textContent = 'Hide steps';
```

- [ ] **Step 4: Verify accordion and navigation**

Refresh `http://localhost:8000`. Confirm:
- Clicking a group header collapses/expands it with chevron rotation
- Refreshing the page after collapsing a group keeps it collapsed
- Tabbing into a matrix cell and pressing arrow keys moves focus to adjacent cells

- [ ] **Step 5: Commit**

```bash
git add src/gui/static/script.js
git commit -m "feat: accordion localStorage, arrow-key grid nav, steps toggle text"
```

---

## Task 4: JS — Shimmer, Async typesetPromise, Error Prefix, Modal Animation

**Files:**
- Modify: `src/gui/static/script.js`

- [ ] **Step 1: Add `showShimmer()` and `hideShimmer()` helper functions**

Insert the following two functions immediately before the `renderResult()` function in `script.js`:

```js
/** Show shimmer skeleton while computing; hides the result display. */
function showShimmer() {
  const shimmer = $('answerShimmer');
  if (shimmer) shimmer.classList.remove('hidden');
  els.resultDisplay.classList.add('hidden');
  els.resultDisplay.innerHTML = '';
}

/** Hide shimmer skeleton and reveal the result display. */
function hideShimmer() {
  const shimmer = $('answerShimmer');
  if (shimmer) shimmer.classList.add('hidden');
  els.resultDisplay.classList.remove('hidden');
}
```

- [ ] **Step 2: Make `renderResult()` async and await `typesetPromise`**

Replace the existing `renderResult(html)` function with:

```js
async function renderResult(html) {
  els.resultDisplay.innerHTML = html;
  if (window.MathJax && MathJax.typesetPromise) {
    await MathJax.typesetPromise([els.resultDisplay]).catch(console.error);
  }
  hideShimmer();
}
```

- [ ] **Step 3: Update `runOperation()` to use shimmer and await renderResult**

Replace the entire `runOperation()` function with the version below. Key changes:
- `showShimmer()` replaces the `renderResult('Computing…')` call
- `await renderResult(...)` for success and error paths
- `hideShimmer()` for the abort path
- Error message prefixed with "Could not compute — "

```js
async function runOperation(op, needs) {
  // Abort any in-flight request
  if (state.currentAbort) {
    state.currentAbort.abort();
    state.currentAbort = null;
  }

  // Update active state
  document.querySelectorAll('.op-btn').forEach(b => b.classList.remove('active'));
  const btn = document.querySelector(`[data-op="${op}"]`);
  if (btn) btn.classList.add('active');

  state.activeOp = op;
  els.opLabel.textContent = OP_LABELS[op] || op;
  setStatus('computing');
  clearSteps();
  showShimmer();

  // Show / hide secondary input
  showSecondary(needs || null);

  // Build request body
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
    const m2 = readGrid('gridB', state.rowsB, state.colsB);
    body.matrix2 = m2;
  }

  // Create abort controller for this request
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
    const data = await resp.json();

    if (data.error) {
      setStatus('error');
      await renderResult(`<div class="error-message">Could not compute — ${escapeHtml(data.error)}</div>`);
      return;
    }

    setStatus('done');
    await renderResult(data.result || '<span class="placeholder">No result returned.</span>');

    if (data.steps && data.steps.trim()) {
      renderSteps(data.steps);
    }
  } catch (err) {
    state.currentAbort = null;
    if (err.name === 'AbortError') {
      hideShimmer();
      els.resultDisplay.innerHTML = '<p class="placeholder">Cancelled. Select an operation from the left panel.</p>';
      setStatus('ready');
      clearSteps();
    } else {
      setStatus('error');
      await renderResult(`<div class="error-message">Network error: ${escapeHtml(err.message)}</div>`);
    }
  }
}
```

- [ ] **Step 4: Add modal scale+fade animation to `openEquivModal()` and `closeEquivModal()`**

Replace the existing `openEquivModal()` function with:

```js
async function openEquivModal() {
  const matA = getMatrixA();
  if (!matA) {
    alert('Please enter a matrix first.');
    return;
  }

  // Reset modal content
  els.equivCategory.textContent = 'Loading\u2026';
  els.equivProps.innerHTML = '';
  els.equivList.innerHTML = '';

  // Show modal with animation
  els.equivModal.classList.remove('hidden');
  requestAnimationFrame(() => els.equivModal.classList.add('modal-visible'));

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

    // Category
    els.equivCategory.textContent = data.category || '';

    // Property tags
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

    // Statements list
    const stmts = data.statements || [];
    els.equivList.innerHTML = stmts
      .map(s => `<li>${s}</li>`)
      .join('');

    // Re-typeset LaTeX inside modal
    if (window.MathJax && MathJax.typesetPromise) {
      MathJax.typesetPromise([els.equivModal]).catch(console.error);
    }
  } catch (err) {
    els.equivCategory.textContent = 'Network error';
    els.equivList.innerHTML = `<li><div class="error-message">${escapeHtml(err.message)}</div></li>`;
  }
}
```

Replace `closeEquivModal()` with:

```js
function closeEquivModal() {
  els.equivModal.classList.remove('modal-visible');
  setTimeout(() => els.equivModal.classList.add('hidden'), 200);
}
```

- [ ] **Step 5: Full functional verification**

Refresh `http://localhost:8000`. Test the following scenarios:

1. **RREF:** Enter `[1 2; 3 4]` → click RREF → shimmer appears → result renders with large MathJax output → no unstyled flash
2. **REF (steps):** Click REF → working steps section appears below answer card, fully readable, no height cap
3. **LU / Diagonalize (long steps):** Confirm scrolling the right panel shows all steps
4. **Error:** Enter `[1 2; 3]` in text mode → click any op → error card shows "Could not compute — ..."
5. **Cancel:** Click an op, immediately click another → first aborts, second runs
6. **Accordion:** Collapse "Factorizations", refresh → still collapsed
7. **Arrow keys:** Tab into Matrix A cell, press arrow keys → focus moves correctly
8. **Equiv Statements:** Enter a matrix, click button → modal fades+scales in, shows category + props + list with LaTeX
9. **Modal close:** Click ✕ or backdrop → modal fades out, then hidden
10. **Steps toggle:** Run REF → click "Hide steps" → steps collapse; click "Show steps" → expand

- [ ] **Step 6: Commit**

```bash
git add src/gui/static/script.js
git commit -m "feat: shimmer skeleton, async typesetPromise, error prefix, modal animation"
```
