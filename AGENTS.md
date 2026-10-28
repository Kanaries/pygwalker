# AGENTS.md — PyGWalker contributor & agent guide

This is the fast-start map of the PyGWalker repo for both human contributors and coding
agents. It explains how the project is put together, how to run it in **dev mode with live
frontend reload**, and where all the logs go. Read this first — it is written to save you
from re-deriving the architecture by grepping.

> Deeper references: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) (how it is built),
> [`docs/DEVELOPMENT.md`](docs/DEVELOPMENT.md) (dev workflow + troubleshooting),
> [`docs/CONTRIBUTING.md`](docs/CONTRIBUTING.md) (validation & CI).

---

## 1. What PyGWalker is (30-second model)

PyGWalker turns a pandas / polars / pyarrow dataframe into an interactive
[Graphic Walker](https://github.com/Kanaries/graphic-walker) UI inside notebooks, Streamlit,
and plain web servers. It has **two halves that ship together**:

- **Python package** (`pygwalker/`) — public API (`walk`, `render`, `table`, `Walker`,
  `to_html`), data parsing, and the transports that talk to the UI.
- **Frontend app** (`app/`, React + Vite) — the UI. It is compiled into JavaScript bundles
  that are checked into the wheel under `pygwalker/templates/dist/` and loaded by the Python
  side at render time.

The Python side never renders charts itself; it hands built JS + serialized data to a
notebook/browser and then answers data/spec requests over a message channel.

---

## 2. Repo map

| Path | What lives here |
|------|-----------------|
| `pygwalker/api/` | Public entry points. `adapter.py` picks jupyter vs webserver; `jupyter.py` = notebook dispatch; `walker.py` = the reusable `Walker`; `pygwalker.py` = the core `PygWalker`. |
| `pygwalker/services/` | Rendering + display. `anywidget_widget.py` (default transport), `render.py` + `templates/*.html` (iframe transport), `global_var.py` (runtime globals), `jupyter_display.py`. |
| `pygwalker/communications/` | Kernel⇄frontend transports: `anywidget_comm.py` (default), `hacker_comm.py` (iframe), `streamlit_comm.py`, `gradio_comm.py`, `reflex_comm.py`. `protocol.py` is the shared message schema. |
| `pygwalker/data_parsers/` | Dataframe/connector adapters (pandas, polars, pyarrow, SQL, spark…). |
| `pygwalker/templates/dist/` | **Build output** (git-ignored). The JS bundles the Python side loads. |
| `pygwalker/utils/` | Helpers: `frontend_assets.py` (locate/load bundles), `log.py` (logging), encoders. |
| `app/src/` | Frontend source. `index.tsx` = entry; `utils/communication.tsx` = transports; `dataSource/` = data ingest; `interfaces/comm.generated.ts` = **generated** protocol types; `store/` = MobX state. |
| `scripts/` | `dev.py` (dev orchestrator), `compile.sh` (build frontend), `local_ci.py` (mirror CI), `generate_comm_protocol_ts.py` (regenerate protocol types). |
| `tests/` | Python tests + `*.ipynb` notebooks run by `nbmake`. `app/tests/` holds Playwright smoke tests. |

---

## 3. How the two halves fit together (build & load model)

```
app/src/*  --(vite build)-->  pygwalker/templates/dist/*.js  --(read at runtime)-->  Python renders it
```

**Frontend build variants** (`app/vite.config.ts`, output to `pygwalker/templates/dist/`):

| Bundle | Built from | Loaded by |
|--------|-----------|-----------|
| `pygwalker-app.es.js` | `src/index.tsx` | **anywidget** transport (the default `pyg.walk` path) |
| `pygwalker-app.iife.js` | `src/index.tsx` | iframe transport / static `to_html()` |
| `dsl-to-workflow.umd.js` | `src/lib/dslToWorkflow.ts` | kernel-side DSL→workflow conversion |
| `vega-to-dsl.umd.js` | `src/lib/vegaToDsl.ts` | kernel-side Vega→DSL conversion |

`yarn build` builds all four (+ typecheck). `yarn build:app` builds only the two app
bundles (fast, no typecheck) — good for a quick manual rebuild, not for CI.

**The message protocol is generated, not hand-written.** Python Pydantic models in
`pygwalker/communications/protocol.py` are the source of truth. Running
`python scripts/generate_comm_protocol_ts.py` regenerates
`app/src/interfaces/comm.generated.ts`. **If you change `protocol.py`, regenerate and rebuild
the frontend.** Never edit `comm.generated.ts` by hand.

**Transports.** The default notebook transport is **anywidget** (`env='JupyterAnywidget'`).
`env='Jupyter'` / `env='JupyterWidget'` are deprecated aliases that are coerced to anywidget
and slated for removal in 0.7.0. Streamlit/Gradio/Reflex/web-server have their own transports.

---

## 4. First-time setup

Requires **Python 3.10+**, **Node.js 22.x**, **Yarn 1.x**.

```bash
# Python (editable install with dev extras)
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -e ".[dev]"

# Frontend deps + one full build so pygwalker/templates/dist/ is populated
cd app && yarn install && yarn build && cd ..
```

---

## 5. Dev mode: edit the frontend and see it live (anywidget HMR)

The default `pyg.walk(df)` uses the anywidget transport, which loads
`pygwalker-app.es.js` from disk. In dev mode we (a) rebuild that bundle on every source
change and (b) let anywidget hot-reload it into open widgets. **One command starts
everything and captures all logs:**

```bash
source venv/bin/activate
python scripts/dev.py
```

This launches, and tees the output of, two long-running processes:

- **frontend** — `cd app && yarn dev:build` (`vite build --watch`) rebuilds the bundles into
  `pygwalker/templates/dist/` on every edit under `app/src/`. → `logs/frontend.log`
- **jupyter** — `jupyter lab` started with `PYGWALKER_DEV=1` and `ANYWIDGET_HMR=1` in its
  environment (inherited by kernels). → `logs/jupyter.log`

Then, in a notebook cell, **no special setup is needed** — just use PyGWalker normally:

```python
import pandas as pd, pygwalker as pyg
pyg.walk(pd.DataFrame({"x": [1, 2, 3], "y": [4, 5, 6]}))
```

Edit a file under `app/src/`, wait for the rebuild to finish in `logs/frontend.log`
(`built in …`), and the widget hot-reloads in place — usually without re-running the cell.
For a heavy change you can always re-run the cell.

**Why it works:** with `ANYWIDGET_HMR=1` (or `PYGWALKER_DEV=1`), `WalkerAnyWidget._esm` is set
to a `pathlib.Path` pointing at the built `pygwalker-app.es.js` instead of an embedded string.
anywidget then reads that file and watches it (via `watchfiles`), pushing new code to the
frontend when `vite build --watch` rewrites it. With the flags **off** (normal installs), the
bundle is embedded as a string exactly as before — production behavior is unchanged.

Useful flags: `--no-jupyter` (only rebuild the frontend), `--no-frontend` (only Jupyter),
`--jupyter-port N`, `--no-browser` (auto-enabled when output is not a TTY, e.g. agent runs),
`--log-dir DIR`. Stop everything with **Ctrl+C** (services are torn down cleanly).

> Alternative (Vite dev server + browser refresh, using the legacy iframe transport) is
> documented in [`docs/DEVELOPMENT.md`](docs/DEVELOPMENT.md#appendix-vite-dev-server-iframe-transport).
> Prefer the anywidget HMR path above.

---

## 6. Logs: one place to look

`scripts/dev.py` writes everything under `logs/` (git-ignored) at the repo root:

| File | Contents |
|------|----------|
| `logs/frontend.log` | Vite build/watch output — watch for `built in …` (rebuild done) and TypeScript errors. |
| `logs/jupyter.log` | JupyterLab server output — **the URL + token to open the notebook is here**. |
| `logs/pygwalker.log` | Kernel-side PyGWalker Python logs (set via `PYGWALKER_LOG_FILE`). |

**Python log controls** (honored by `pygwalker/utils/log.py`, independent of the orchestrator):

- `PYGWALKER_LOG_FILE=/path/to/file.log` — also append Python logs to a file.
- `PYGWALKER_LOG_LEVEL=DEBUG` — raise/lower verbosity (default `INFO`).

**Frontend runtime logs** (what happens in the browser, e.g. comm errors) appear in the
**browser devtools console**, not in `logs/`. The frontend surfaces user-facing errors as
in-app toast notifications rather than `console.log`.

Agent tip: tail `logs/jupyter.log` for the server URL, `logs/frontend.log` to know when a
rebuild finished, and `logs/pygwalker.log` for kernel-side errors.

---

## 7. Everyday commands

```bash
# Frontend (run from app/)
yarn build            # full build: typecheck + all 4 bundles (CI-equivalent)
yarn build:app        # fast: only the two app bundles, no typecheck
yarn dev:build        # rebuild-on-change (what scripts/dev.py runs)
yarn typecheck        # tsc --noEmit
yarn test:front_end   # Playwright smoke test (run `yarn playwright install chromium` once)

# Python (run from repo root, venv active)
python -m ruff check pygwalker tests scripts bin pygwalker_tools
python -m ruff format --check pygwalker tests scripts bin pygwalker_tools
python -X faulthandler -W error::DeprecationWarning:pygwalker -m pytest -o faulthandler_timeout=60 tests
python -m pytest --nbmake --nbmake-kernel=python tests/*.ipynb   # notebook tests

# Regenerate the JS protocol types after editing pygwalker/communications/protocol.py
python scripts/generate_comm_protocol_ts.py

# Run the whole CI flow locally (frontend build + smoke test + notebooks + python)
python scripts/local_ci.py            # add --skip-frontend / --skip-notebooks to narrow
```

---

## 8. Rules & gotchas

- **Do not commit `pygwalker/templates/dist/`** — it is generated and git-ignored. The wheel
  build (and CI) rebuilds it via the Hatch jupyter-builder hook.
- **Regenerate + rebuild after protocol changes.** Editing `communications/protocol.py`
  without running `scripts/generate_comm_protocol_ts.py` and rebuilding the frontend leaves
  Python and JS out of sync.
- **`yarn build:app` skips typecheck** and the DSL bundles. Run full `yarn build` (or
  `yarn typecheck`) before pushing frontend changes.
- **anywidget is the transport of record.** Don't reach for the deprecated `env='Jupyter'` /
  iframe path for new work; it is removed in 0.7.0.
- **Dev-mode flags are opt-in.** `PYGWALKER_DEV` / `ANYWIDGET_HMR` only affect a dev session.
  Never rely on them being set at runtime for end users.
- **First run needs a build.** In dev mode the widget loads `dist/pygwalker-app.es.js` from
  disk; if it is missing you'll get a clear "Missing PyGWalker frontend asset" error — run the
  frontend build (or wait for `scripts/dev.py`'s first build to finish).

---

## 9. Where to look for X

| Question | Start here |
|----------|-----------|
| How does `pyg.walk()` decide what to display? | `pygwalker/api/adapter.py` → `api/jupyter.py` (`env_display_map`) |
| How is the frontend bundle loaded / dev-swapped? | `pygwalker/services/anywidget_widget.py`, `utils/frontend_assets.py` |
| What messages can the frontend send the kernel? | `pygwalker/communications/protocol.py` ⇄ `app/src/interfaces/comm.generated.ts` |
| How is data sent to the browser? | `pygwalker/services/data_communication.py`, `app/src/dataSource/` |
| How is a chart exported to PNG/SVG/code? | `pygwalker/services/chart_export.py`, `app/src/tools/` |
| How does the iframe/static-HTML path render? | `pygwalker/services/render.py` + `pygwalker/templates/*.html` |
