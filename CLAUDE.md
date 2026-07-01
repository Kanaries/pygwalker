# CLAUDE.md

This project's contributor & agent guide is maintained in **[AGENTS.md](AGENTS.md)** — a
single source of truth for the architecture, dev-mode workflow, and log locations. Read it
before making changes.

@AGENTS.md

## TL;DR for a coding agent

- **Setup:** `python -m venv venv && source venv/bin/activate && pip install -e ".[dev]"`,
  then `cd app && yarn install && yarn build`.
- **Run everything in dev mode with live reload + centralized logs:** `python scripts/dev.py`
  (starts the frontend watch build + JupyterLab with `PYGWALKER_DEV=1` / `ANYWIDGET_HMR=1`).
  Pass `--no-browser` for headless runs.
- **Logs:** `logs/frontend.log` (build/watch), `logs/jupyter.log` (server URL + token),
  `logs/pygwalker.log` (kernel-side Python logs). Frontend runtime logs are in the browser
  console.
- **In a notebook:** just `import pygwalker as pyg; pyg.walk(df)` — no special setup; edits
  under `app/src/` hot-reload into the widget.
- **Before pushing:** `python scripts/local_ci.py` (or, narrower, `yarn typecheck` + `yarn build`
  in `app/`, and `ruff check`/`ruff format --check`/`pytest` from the root).
- **Don't:** commit `pygwalker/templates/dist/`, hand-edit `app/src/interfaces/comm.generated.ts`,
  or rely on `PYGWALKER_DEV`/`ANYWIDGET_HMR` at runtime for end users.
