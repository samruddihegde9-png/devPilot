# DevPilot — Architecture (Phase 1)

## What exists right now

```text
React (Vite)  ──HTTP──▶  FastAPI  ──▶  SQLAlchemy  ──▶  PostgreSQL   (project metadata)
                              │
                              └──▶  SandboxManager (LocalSandbox)  ──▶  workspaces/{project_id}/  (real files)
```

There is no agent yet. This phase proves the foundation the agent will run
on top of: every project has a database row *and* a real, isolated
directory on disk, and the frontend can create, browse, edit and save files
in that directory through the API — nothing is mocked.

## Layers

**`app/models/`** — SQLAlchemy models. `Project` is the only table so far.

**`app/schemas/`** — Pydantic request/response shapes, validated independently
of the DB models so the API contract doesn't leak SQLAlchemy internals.

**`app/services/sandbox/`** — the filesystem boundary.
- `manager.py` defines the abstract `SandboxManager` interface
  (`create_workspace`, `read_file`, `write_file`, ..., `execute`).
- `local.py` implements it against the local disk (`LocalSandbox`). It is
  the *only* file in the backend that builds a raw filesystem path for a
  project, and every path it resolves is checked against path traversal
  (see the docstring at the top of that file, and `docs/security.md`).
- `templates.py` holds the small per-template starter files written into a
  new workspace.
- `execute()` is defined on the interface but `LocalSandbox.execute()`
  currently raises `NotImplementedError` — command execution is Phase 3.

**`app/api/`** — thin FastAPI routers. They translate sandbox exceptions
(`PathTraversalError`, `NotFoundError`, `AlreadyExistsError`) into HTTP
status codes and otherwise just call into the sandbox / DB.

**`frontend/src/pages/Workspace.tsx`** — the three-pane workspace. It owns
the file-tree/editor state and calls the same `api.ts` client that Phase 2+
will reuse for agent runs.

## Why `SandboxManager` is an interface

Phase 1 only has `LocalSandbox`, but the interface already separates "what
the app needs from a sandbox" (read/write/list/execute, scoped to one
project) from "how that's implemented". Phase 3 adds real command execution
to `LocalSandbox.execute()` (subprocess, timeout, output caps). Phase 2's
optional `DockerSandbox` can implement the same interface later, routing
`execute()` into a container instead of a subprocess, without any API route
or agent tool changing.

## What's deliberately not here yet

- No agent, planner, coder, tester, debugger, or reviewer (Phase 2).
- No command execution — `run_tests` / `run_command` are not implemented;
  the terminal panel says so rather than faking output (Phase 3).
- No WebSocket/SSE event stream (Phase 5's "37. REAL-TIME AGENT EVENTS").
- No Git integration (Phase 5/"28. GIT INTEGRATION").
- No auth/users table — every project is visible to whoever can reach the
  API, which is fine for a local single-user MVP and called out in
  `docs/security.md`.
