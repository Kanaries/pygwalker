# PyGWalker Development Setup

How to run PyGWalker locally with **live frontend reloading**, so you can edit the React app
under `app/src/` and see the change in a notebook without reinstalling anything.

- New to the codebase? Read [`../AGENTS.md`](../AGENTS.md) and
  [`ARCHITECTURE.md`](./ARCHITECTURE.md) first — they explain the two halves and the build.
- For the full validation/CI commands and package-build details, see
  [`CONTRIBUTING.md`](./CONTRIBUTING.md).

## Prerequisites

- Python 3.10+
- Node.js 22.x (matches CI)
- Yarn 1.x

## 1. Set up Python

```bash
git clone https://github.com/Kanaries/pygwalker.git
cd pygwalker

python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -e ".[dev]"
```

## 2. Set up the frontend

```bash
cd app
yarn install
yarn build      # first full build populates pygwalker/templates/dist/
cd ..
```

`yarn build` writes the JS bundles that the Python side loads into
`pygwalker/templates/dist/` (git-ignored, generated). You only need the full build once; the
dev workflow below rebuilds incrementally after that.

## Recommended: one-command dev stack with hot reload

PyGWalker's default notebook transport is **anywidget**, which loads
`pygwalker/templates/dist/pygwalker-app.es.js` from disk. In dev mode we rebuild that bundle on
every edit and let anywidget hot-reload it into open widgets. A single script starts both
processes and captures their logs centrally:

```bash
source venv/bin/activate
python scripts/dev.py
```

It launches, tees to your terminal, and logs to `logs/`:

- **`yarn dev:build`** (`vite build --watch`) — rebuilds the bundles when you edit `app/src/`.
  → `logs/frontend.log`
- **`jupyter lab`** with `PYGWALKER_DEV=1` and `ANYWIDGET_HMR=1` in its environment (kernels
  inherit these). → `logs/jupyter.log`

Open the JupyterLab URL printed in the console (or found in `logs/jupyter.log`) and run
PyGWalker normally — **no special notebook setup is required**:

```python
import pandas as pd
import pygwalker as pyg

pyg.walk(pd.DataFrame({"x": [1, 2, 3], "y": [4, 5, 6]}))
```

Now edit any file under `app/src/`. When `logs/frontend.log` shows the rebuild finished
(`built in …`), the widget hot-reloads in place — usually without re-running the cell. For a
large change, just re-run the cell.

Handy flags:

| Flag | Effect |
|------|--------|
| `--no-jupyter` | Only run the frontend watch build. |
| `--no-frontend` | Only start JupyterLab (bundle already built). |
| `--jupyter-port N` | Set the JupyterLab port. |
| `--no-browser` | Don't open a browser (auto-enabled when output isn't a TTY, e.g. agent runs). |
| `--log-dir DIR` | Change where per-service logs are written (default `logs/`). |

Stop the stack with **Ctrl+C** — both processes are torn down cleanly.

### How the dev swap works (and why it's safe)

`pygwalker/services/anywidget_widget.py` chooses the widget source based on the environment:

- **Normal installs:** `WalkerAnyWidget._esm` is the *contents* of `pygwalker-app.es.js`
  (a string embedded at import) — identical to historical behavior.
- **Dev mode** (`PYGWALKER_DEV=1` or `ANYWIDGET_HMR=1`): `_esm` is the *file path* of the
  bundle. anywidget reads it from disk and, with HMR, watches it (via `watchfiles`) and pushes
  new code to the browser whenever `vite build --watch` rewrites it.

Because the switch is opt-in via environment variables, end-user behavior is unchanged when the
flags are absent.

## Alternative: manual rebuild (no watcher)

If you prefer not to run the watcher:

1. Edit files under `app/src/`.
2. Rebuild: `cd app && yarn build:app` (fast; no typecheck) — or `yarn build` for the full set.
3. Re-run the notebook cell (restart the kernel if the change doesn't appear).

Before committing frontend changes, run the full validation path from
[`CONTRIBUTING.md`](./CONTRIBUTING.md): `yarn typecheck`, `yarn build`, and `yarn test:front_end`.

## Logs & debugging

`scripts/dev.py` centralizes logs under `logs/` (git-ignored):

| File | Contents |
|------|----------|
| `logs/frontend.log` | Vite build/watch output. Watch for `built in …` and TypeScript errors. |
| `logs/jupyter.log` | JupyterLab server output, including the URL + token to open. |
| `logs/pygwalker.log` | Kernel-side PyGWalker Python logs (via `PYGWALKER_LOG_FILE`). |

Python logging is configurable anywhere PyGWalker runs (not just under the orchestrator):

- `PYGWALKER_LOG_FILE=/path/to/file.log` — also append Python logs to a file.
- `PYGWALKER_LOG_LEVEL=DEBUG` — change verbosity (default `INFO`).

**Frontend runtime logs** (comm errors, render issues) show up in the **browser devtools
console**, not in `logs/`. User-facing problems are surfaced as in-app toast notifications.

## Troubleshooting

### "Missing PyGWalker frontend asset" error

The bundle hasn't been built yet. Run `cd app && yarn build` (or let `scripts/dev.py` finish
its first build) before rendering.

### Frontend edits don't appear

- Confirm `logs/frontend.log` shows a completed rebuild (`built in …`) after your edit.
- Confirm JupyterLab was started with `ANYWIDGET_HMR=1` (the orchestrator sets this for you).
- For a large change, re-run the cell; if needed, restart the kernel.

### React version errors or other strange issues (clean rebuild)

```bash
cd app
rm -rf node_modules
yarn install
yarn build
```

## Appendix: Vite dev server (iframe transport)

This is the **legacy** hot-reload path. It uses the Vite *dev server* plus the **iframe**
transport (`env='Jupyter'`) and the `GlobalVarManager.set_component_url(...)` hook — it does
**not** apply to the default anywidget transport. Prefer the anywidget HMR workflow above;
this remains only for working on the iframe/`to_html` rendering path, which is deprecated and
slated for removal in 0.7.0.

Start the Vite dev server (serves the app under `/pyg_dev_app/` on port 8769):

```bash
cd app
yarn dev:server
```

Start JupyterLab with a server proxy so the notebook can reach the dev server same-origin:

```bash
source venv/bin/activate
jupyter lab --ServerProxy.servers="{'pyg_dev_app': {'command': [], 'absolute_url': True, 'port': 8769, 'timeout': 30}}"
```

Point PyGWalker at the dev server and render through the iframe transport:

```python
from pygwalker.services.global_var import GlobalVarManager

GlobalVarManager.set_component_url("/pyg_dev_app/")   # "" to return to bundled assets

import pygwalker as pyg
pyg.walk(df, env="Jupyter")   # iframe transport honors component_url
```

If `.wasm` files 404 from the dev server, ensure `vite.config.ts` keeps
`optimizeDeps.exclude: ['@kanaries/gw-dsl-parser']`. If you hit CORS errors, use the
`jupyter-server-proxy` setup above rather than pointing at the dev server directly.
