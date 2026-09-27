# DevPilot

**DevPilot is an AI coding agent that turns natural-language development
tasks into planned, executable and testable code changes inside isolated
project workspaces.**

> This repo is being built in phases. **This README reflects Phase 1
> only:** project creation, isolated workspaces, a real file tree, and a
> Monaco editor wired to the actual filesystem. There is no agent yet —
> see [What's not built yet](#known-limitations-phase-1).

## Problem

Traditional AI coding assistants can generate code, but a useful coding
agent needs to operate *within* a real software project: understand
existing code, execute changes, observe failures, and iterate safely.

## Solution

```text
Project
  ↓
Agent        (Phase 2)
  ↓
Tools        (Phase 2)
  ↓
Sandbox      (Phase 1: file I/O — Phase 3: command execution)
  ↓
Execution    (Phase 3)
  ↓
Observation  (Phase 4)
  ↓
Iteration    (Phase 4)
```

See `docs/architecture.md` for how the pieces fit together and
`docs/security.md` for an honest account of the current security
boundaries.

## Stack

- **Frontend:** React, TypeScript, Vite, Tailwind CSS, Monaco Editor, Framer
  Motion, lucide-react, React Router.
- **Backend:** FastAPI, Pydantic v2, SQLAlchemy 2.0, PostgreSQL.
- **AI:** none wired up yet (Phase 2). `OPENAI_API_KEY` / `OPENAI_MODEL` are
  already in `backend/.env.example` for when the planner/coder land.

## Project structure

```text
devpilot/
├── frontend/          React + TS + Vite app
│   └── src/
│       ├── components/   FileTree, CodeEditor (Monaco), AgentPanel, TerminalPanel, ...
│       ├── pages/        Landing, Workspace
│       ├── services/     api.ts — typed fetch client
│       └── types/        Project, FileNode, ...
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── api/           projects.py, files.py, health.py
│   │   ├── models/        Project (SQLAlchemy)
│   │   ├── schemas/       Pydantic request/response shapes
│   │   ├── services/
│   │   │   └── sandbox/   SandboxManager interface + LocalSandbox
│   │   └── db/
│   └── tests/
├── workspaces/         created/destroyed per project at runtime (gitignored)
└── docs/
    ├── architecture.md
    └── security.md
```

## Running it

### 1. Database

```bash
docker compose up -d postgres
```

(Or point `DATABASE_URL` in `backend/.env` at any Postgres instance you
already have.)

### 2. Backend

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

The API is now at `http://localhost:8000` (`/api/health` should return
`{"status":"ok"}`, and `/docs` has interactive OpenAPI docs).

### 3. Frontend

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

Open `http://localhost:5173`.

### 4. Try it

- **Create Project** → name it, pick a template (Python / FastAPI / React /
  Node.js) → you land in the workspace with real starter files on disk
  under `workspaces/{project_id}/`.
- **Try Demo** → creates (or reopens) a small FastAPI demo project the same
  way.
- Click a file in the tree to load it into Monaco; edit it, `Cmd/Ctrl+S` or
  the **Save** button writes it back to disk — reload the page and your
  change is still there.
- Create/delete files and folders from the tree — they're real filesystem
  operations, not local UI state.

## What was tested

`backend/tests/` (pytest + `TestClient`, isolated SQLite DB and a temp
workspace root per test — nothing touches your real `workspaces/`):

- Project creation actually creates a workspace directory with real
  template files (not just a DB row).
- Listing/getting/deleting projects, including that delete removes the
  workspace directory too.
- File read/write round-trips actual disk content.
- File create (file + directory), delete, and rename.
- Path traversal is rejected (`../../etc/passwd`, encoded variants, mixed
  `..` segments) — see `test_path_traversal_is_rejected`.
- Two projects with the same relative path never see each other's content
  (`test_reading_file_in_other_project_is_isolated`).

Run them with:

```bash
cd backend
pytest
```

> **Note on this environment:** this codebase was written in a sandboxed
> container with no network access, so `pip install` / `npm install`
> could not be run here and the test suite above has **not** been executed
> in this session — only syntax-checked (`python -m py_compile` on every
> backend file) and the `LocalSandbox` path-safety logic was smoke-tested
> directly (traversal attempts, CRUD round-trips) with a stubbed-out
> config/pydantic layer, since `pydantic`/`fastapi` themselves couldn't be
> installed either. Please run `pytest` yourself after `pip install -r
> requirements.txt` to get a real pass/fail signal before treating Phase 1
> as verified.

Frontend automated tests are not set up yet — Phase 1 was manually
exercised by reasoning through each flow (create → browse → edit → save →
delete) against the real API contract; there's no CI wiring for React
Testing Library / Vitest yet.

## Known limitations (Phase 1)

- No agent. The "AI Task Input" and terminal panels are visibly disabled
  with a "not implemented yet" message rather than faking activity.
- No command execution at all — `SandboxManager.execute()` is defined on
  the interface but `LocalSandbox.execute()` raises `NotImplementedError`.
- No auth — single-user, local-only threat model. See `docs/security.md`.
- DB schema creation uses `Base.metadata.create_all()` on startup, not
  Alembic migrations — fine for Phase 1, should change before this holds
  real data.
- No WebSocket/SSE — nothing to stream yet since there's no agent.

## Repository Intelligence

Alongside Phase 1's editor workflow, DevPilot now has a **Repository
Intelligence** view (added for the IBM Bob 2.0 hackathon submission — see
`docs/repo-intelligence.md` for the full design and honest limitations).
From any open project, click **Repository Intelligence** in the top bar to:

- Scan the project's workspace (structure, detected language/framework,
  dependencies, important files, key modules).
- See a generated architecture explanation and a module-relationship
  diagram, built from actual `import`/`from` statements found in the code.
- Review a list of detected issues (swallowed exceptions, hardcoded-looking
  secrets, overly long functions, mutable default arguments, empty JS/TS
  `catch` blocks, `console.log`/`debugger` left in source, TODO/FIXME).
- Review test suggestions per function, with a generated pytest skeleton for
  simple, side-effect-free Python functions.
- Ask natural-language questions about the codebase and see exactly which
  file excerpts the answer is grounded in.

This works fully offline (heuristic-only). If `OPENAI_API_KEY` is set, the
architecture summary and Ask answers are additionally polished/answered by
an LLM call — grounded in the same extracted facts, never sent the whole
repo, and every screen clearly shows whether it's looking at an AI answer or
a heuristic/retrieval one.

## Environment variables


See `backend/.env.example` and `frontend/.env.example`. Nothing here
hardcodes a secret; `OPENAI_API_KEY` is read from the environment and is
never sent to the frontend or into any executed code.

---

Next: **Phase 2 — Agent** (LLM integration, planner, tool calling, file
operations through agent tools, explicit agent state). Waiting for the
go-ahead before starting it.
