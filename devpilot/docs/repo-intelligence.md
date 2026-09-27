# Repository Intelligence

Added on top of DevPilot's Phase 1 foundation (project creation, isolated
workspaces, file tree, Monaco editor) for the IBM Bob 2.0 hackathon
submission. It is **not** the Phase 2 agent described in the main README's
roadmap — it doesn't write or execute code. It gives a developer an
actionable understanding of a codebase already open in DevPilot: structure,
architecture, likely issues, test gaps, and a grounded Q&A interface.

## How it works

Everything starts from a **scan**: `POST /api/projects/{id}/repo-intel/scan`
walks the project's workspace through the existing `LocalSandbox` (the same
path-safety boundary the file explorer uses — Repository Intelligence never
touches the filesystem directly), reads every eligible text file within a
budget (40 KB/file, ~1.2 MB total, 400 files), and skips binaries, lockfiles,
build output, and anything `.gitignore`-style directories like
`node_modules`/`dist`/`__pycache__` would contain. The result is cached
in-process per project (same singleton pattern as `local_sandbox`) and
re-used by all the read endpoints below, so opening each tab doesn't re-scan.

- **Overview** (`/repo-intel/overview`) — language/framework detection from
  file extensions and manifests (`requirements.txt`, `pyproject.toml`,
  `package.json`), important files by filename convention, key modules
  ranked by file count, and parsed dependency lists. Pure heuristics, no LLM.
- **Architecture** (`/repo-intel/architecture`) — an internal import graph
  built from real `import`/`from ... import` statements (Python `ast`) and
  relative `import`/`require` statements (JS/TS, resolved against the
  scanned file set — only internal edges are kept, not third-party
  packages). Rendered as a small dependency-free SVG diagram (grid layout,
  no charting library). The prose explanation is generated from these same
  extracted facts; if `OPENAI_API_KEY` is set, those facts are handed to an
  LLM to write better prose (the prompt explicitly forbids inventing
  anything not in the facts) — otherwise a template-based explanation is
  used. The UI always labels which one produced the text.
- **Issues** (`/repo-intel/issues`) — a small, deterministic rule set (not a
  full linter): swallowed exceptions (bare/empty `except`), hardcoded-looking
  secrets, overly long functions, mutable default arguments, and large files
  for Python (via `ast`); empty `catch` blocks, `console.log`/`debugger`
  statements, and TODO/FIXME comments for JS/TS (via regex). Every issue
  carries a `rule_id` so it's auditable.
- **Tests** (`/repo-intel/tests`) — every public top-level function gets a
  plain-English suggestion (happy path, edge case, error case if the
  function raises). A real pytest skeleton is generated **only** for Python
  functions with ≤3 args, no decorators, and no `try`/`with`/calls to
  obviously side-effecting names (`open`, `requests`, `session`, `commit`,
  ...) — anything more complex (FastAPI routes, DB access, React components)
  gets a suggestion only, deliberately, rather than a plausible-looking but
  wrong test.
- **Ask DevPilot** (`/repo-intel/ask`) — chunks every scanned file (~40
  lines, 8-line overlap) and ranks chunks against the question with a
  dependency-free keyword-overlap score (no embeddings/vector store). If
  `OPENAI_API_KEY` is set, the top 5 chunks are handed to the model with an
  instruction to answer only from them and say so when they don't contain
  the answer; the raw excerpts are always shown too. Without a key (or if
  the call fails for any reason — timeout, no network, bad response), the
  excerpts themselves are returned as the answer instead of an LLM
  paraphrase, so the feature degrades to "grep with ranking," not silence.

## What this deliberately does *not* do

- **No repository import.** It analyzes whatever files already exist in the
  currently open project's workspace — there's no "paste a GitHub URL"/git
  clone flow. Real Git integration is called out as later-phase work in the
  main README/architecture doc, and building it here would have meant
  fabricating a feature outside this task's scope.
- **Not a real linter or static analyzer.** The issue rules are a small,
  intentionally readable set of syntactic patterns, not `ruff`/`eslint`/
  `mypy`. It will miss real problems and won't try to type-check anything.
- **No code execution.** Nothing here runs the scanned code, so generated
  test skeletons are not verified to pass — they're a starting point.
- **In-memory cache only.** Scan results live in the backend process's
  memory (same as everything else in Phase 1 — see the main
  `docs/architecture.md`). Restarting the backend clears them; re-scanning
  is cheap for the project sizes this phase handles.
- **LLM calls are best-effort and optional.** `OPENAI_API_KEY` is read from
  `backend/.env` exactly as already documented for Phase 2; nothing here
  requires it, and no repository content is sent anywhere unless it's set.

## Honest testing note

This was written and syntax-checked in a sandboxed environment without
package-registry access (same constraint the main README already discloses
for Phase 1: `pip`/`npm install` could not be run here). What *was* done:

- Every backend file passed `python -m py_compile`.
- The core algorithmic logic (import resolution for both Python and JS/TS,
  issue-detection rules, question-chunking/retrieval scoring) was exercised
  directly against hand-written sample code with stubbed-out dependencies,
  and produced correct results.
- The frontend was checked with the TypeScript compiler for syntax errors
  and structural type errors; the only errors reported are the same
  "missing `@types/react`" class of false positives that already exist on
  the untouched Phase 1 files in this environment (no `node_modules`), not
  errors introduced by this feature.

Please run `pip install -r requirements.txt` and `npm install` yourself and
exercise the feature end-to-end before treating it as demo-verified — the
same caveat Phase 1's own README already gives for its own test suite.

## Demo script (2-3 minutes)

1. Open DevPilot, create (or open) a project — e.g. the FastAPI demo
   project, or better, one you've built out a bit in the editor first so
   there's real structure to show.
2. Click **Repository Intelligence** in the top bar.
3. Click **Scan Repository** — point out this is reading real files through
   the same sandboxed file API the editor uses, nothing fabricated.
4. **Overview** tab: detected language/framework, dependencies, key modules.
5. **Architecture** tab: the generated explanation and the module diagram —
   point out an edge and note it came from an actual `import` line.
6. **Ask DevPilot** tab: ask "Where is the API layer?" or "How does file
   writing work?" — show the answer and the exact file/line-range excerpts
   it's grounded in.
7. **Issues** tab: point at one high-severity finding and its rule_id.
8. **Tests** tab: expand a suggestion that has a generated pytest skeleton.
9. Close with: this turns "read the whole repo yourself" into a five-minute
   orientation, and every claim it makes points back at a real file — it
   doesn't just take AI's word for it.
