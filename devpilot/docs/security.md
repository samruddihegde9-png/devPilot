# DevPilot — Security Model

This document is honest about what is and isn't a real security boundary in
the current phase. **Nothing here should be treated as production-hardened.**

## What Phase 1 actually enforces

### Workspace isolation (implemented)

Every project's files live under `workspaces/{project_id}/`. All file
operations go through `LocalSandbox`, which:

1. Rejects absolute paths (`/etc/passwd`, `C:\Windows\...`).
2. Rejects any path segment equal to `..`.
3. Resolves the final path and independently verifies it is still inside
   that project's workspace directory (catches symlink edge cases that
   step 2 alone wouldn't).

This is covered by `backend/tests/test_files.py::test_path_traversal_is_rejected`
and `test_reading_file_in_other_project_is_isolated`.

### What is NOT yet enforced (later phases)

- **Command execution sandboxing** — not implemented at all yet
  (`LocalSandbox.execute()` raises `NotImplementedError`). Phase 3 adds
  subprocess execution with a timeout and output-size cap; Phase 2's
  optional `DockerSandbox` would add real process/filesystem isolation
  (container, no host network, CPU/memory limits). Until a `DockerSandbox`
  exists, "sandboxed" execution means "confined to one directory, with a
  timeout" — not a real security boundary against a determined attacker
  with code-execution.
- **Command allow-listing** — Phase 3/4 should restrict `run_command` to an
  explicit allow-list (`python`, `pytest`, `npm`, `node`, ...) rather than
  arbitrary shell.
- **Secrets** — the agent (Phase 2+) must never receive `OPENAI_API_KEY`,
  `DATABASE_URL`, or any other app secret as an environment variable inside
  a sandboxed execution. This is a requirement for Phase 2's tool design,
  not yet implemented because nothing executes code yet.
- **Auth** — there is no user/session model. Anyone who can reach the API
  can create, read, edit and delete any project. Fine for a local
  single-user MVP; not fine for anything multi-tenant.
- **Rate limiting / resource quotas** — none. A determined local user could
  fill disk with very large files; there's no per-project size cap yet.

## Reporting a gap

This is a portfolio project, not a monitored service — if you find a way to
read or write outside a project's workspace, it's a bug in `LocalSandbox`;
see `backend/app/services/sandbox/local.py`.
