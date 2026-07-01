# PyGWalker Architecture

How the project is constructed across its Python and frontend halves, and how they load and
talk to each other at runtime. This is the orientation doc for contributors and agents; for
the hands-on dev workflow see [`DEVELOPMENT.md`](./DEVELOPMENT.md), and for the quick map see
[`../AGENTS.md`](../AGENTS.md).

## Two halves that ship together

PyGWalker is a Python library plus a React frontend, packaged as one wheel:

- **Python package** — `pygwalker/`. The public API, dataframe parsing, and the transports
  that exchange data and chart specs with the UI.
- **Frontend app** — `app/`. A React + Vite application built into JavaScript bundles that are
  placed in `pygwalker/templates/dist/` and shipped inside the wheel.

At render time the Python side serializes the dataframe + config and hands the built
JavaScript to a notebook/browser. The running UI then calls back into the Python kernel to
fetch data, run queries, and save chart specs.

```
┌────────────────────────┐        build         ┌──────────────────────────────┐
│  app/  (React + Vite)  │ ───────────────────▶ │ pygwalker/templates/dist/*.js │
└────────────────────────┘   vite build          └──────────────┬───────────────┘
                                                                 │ read at runtime
                                                                 ▼
┌───────────────────────────────────────────────────────────────────────────────┐
│  pygwalker/ (Python)   walk()/render()/table()/Walker → transport → rendered UI │
└───────────────────────────────────────────────────────────────────────────────┘
                    ▲                                            │
                    │      messages (data, spec, export)         │
                    └────────────────────────────────────────────┘
```

## Python package layout

| Module | Responsibility |
|--------|----------------|
| `api/adapter.py` | Top-level `walk`/`render`/`table`. Detects environment (`get_current_env`) and routes to the notebook (`api/jupyter.py`) or web-server (`api/webserver.py`) path. |
| `api/jupyter.py` | Notebook dispatch. Maps `env` → a display method (`env_display_map`). Default `JupyterAnywidget`. |
| `api/walker.py` | `Walker`, the reusable object (`.show()`, `.to_html()`, `.to_streamlit()`). |
| `api/pygwalker.py` | `PygWalker`, the core object holding data source, spec, and props. |
| `services/anywidget_widget.py` | **Default transport.** Wraps the built ESM in an `anywidget.AnyWidget`. |
| `services/render.py` + `templates/*.html` | Iframe / static-HTML transport (Jinja templates). |
| `services/jupyter_display.py` | The concrete display flows (anywidget, iframe, widgets, preview, convert). |
| `services/global_var.py` | Process-wide runtime settings (`GlobalVarManager`): component URL, API keys, feature flags. |
| `communications/` | Kernel⇄frontend transports + the shared message `protocol.py`. |
| `data_parsers/` | Adapters that normalize pandas/polars/pyarrow/SQL/spark sources to a common interface. |
| `utils/frontend_assets.py` | Locates and loads the built bundles from `templates/dist/`. |
| `utils/log.py` | The shared `pygwalker` logger (console + optional file). |

## Frontend app layout

| Path | Responsibility |
|------|----------------|
| `src/index.tsx` | Entry point. Exports `GWalker` (iframe/http), `AnywidgetGWalkerApp` (anywidget), Streamlit and preview apps. Selects a transport by `env`. |
| `src/utils/communication.tsx` | The four client transports: Jupyter widgets, HTTP (Streamlit/Gradio/web), and anywidget. |
| `src/dataSource/` | Receives chunked data from the kernel and delegates kernel computation. |
| `src/interfaces/comm.generated.ts` | **Generated** protocol types (request/response envelopes, action map). Do not hand-edit. |
| `src/store/` | MobX stores for UI state, notifications, and the active communication instance. |
| `src/tools/` | Toolbar actions: save, export chart, export dataframe, open-in-desktop. |
| `src/lib/` | Standalone transforms (`dslToWorkflow.ts`, `vegaToDsl.ts`) built as separate UMD bundles. |

## Build pipeline

**Frontend → bundles.** `app/vite.config.ts` defines the build. `yarn build` runs a typecheck
then produces four artifacts into `pygwalker/templates/dist/`:

| Bundle | Entry | Consumer |
|--------|-------|----------|
| `pygwalker-app.es.js` | `src/index.tsx` | anywidget transport (default notebook path) |
| `pygwalker-app.iife.js` | `src/index.tsx` | iframe transport / `to_html()` |
| `dsl-to-workflow.umd.js` | `src/lib/dslToWorkflow.ts` | kernel-side DSL→workflow conversion |
| `vega-to-dsl.umd.js` | `src/lib/vegaToDsl.ts` | kernel-side Vega→DSL conversion |

`yarn build:app` is a fast subset (only the two app bundles, no typecheck).

**Protocol types are generated.** The message contract is defined once, in Python Pydantic
models at `pygwalker/communications/protocol.py`.
`python scripts/generate_comm_protocol_ts.py` renders those models into
`app/src/interfaces/comm.generated.ts`. Change the Python models, regenerate, then rebuild the
frontend — otherwise the two sides drift.

**Wheel build.** `pyproject.toml` wires a Hatch `jupyter-builder` hook that runs the frontend
`build` during `python -m build`, so a released wheel always contains freshly built bundles.
`pygwalker/templates/dist/` is git-ignored and rebuilt on demand; never commit it.

## Runtime flow (default anywidget path)

1. `pyg.walk(df)` → `adapter.walk` detects a notebook → `jupyter.walk` with the default
   `env='JupyterAnywidget'`.
2. A `PygWalker` is created; `jupyter.py`'s `env_display_map` calls
   `display_on_jupyter_use_anywidget`.
3. `services/anywidget_widget.py` builds a `WalkerAnyWidget` whose `_esm` is the built
   `pygwalker-app.es.js`, sets `props` (serialized config + a data sample), and registers an
   `AnywidgetCommunication` channel.
4. In the browser, `AnywidgetGWalkerApp` mounts Graphic Walker and, as the user explores,
   sends typed requests (fetch data, run SQL, save spec, export) back over the anywidget
   channel. `communications/` validates each message against `protocol.py` and dispatches it.

The **iframe transport** (`services/render.py` + `templates/pygwalker_main_page.html`) is an
alternative that embeds the compressed `iife` bundle in an `iframe` `srcdoc`, or points the
iframe at a dev-server URL when `GlobalVarManager.component_url` is set. It backs
`to_html()` and the deprecated `env='Jupyter'`/`'JupyterWidget'` paths.

## Message protocol & transports

Every transport speaks the same envelope (see `protocol.py` /
`comm.generated.ts`): a request carries an `action`, a `data` payload, a request id `rid`, and
the widget/app id `gid`; a response carries `code`, `data`, and `message`. Actions include
data fetches (`get_datas`, `batch_get_datas_by_sql`), spec operations
(`get_latest_vis_spec`, `save_chart`, `update_spec`), export, and AI features.

| Transport | Module | Mechanism |
|-----------|--------|-----------|
| anywidget (default) | `communications/anywidget_comm.py` | anywidget model `send`/`on_msg` |
| iframe widgets | `communications/hacker_comm.py` | ipywidgets text fields observed by the frontend |
| Streamlit | `communications/streamlit_comm.py` | HTTP route under Streamlit's server |
| Gradio | `communications/gradio_comm.py` | Starlette mount |
| Reflex | `communications/reflex_comm.py` | Reflex endpoint |
| web server | `api/webserver.py` | standalone HTTP handler |

## Computation modes

`computation` selects where data queries run: `browser` (all data sent to the client and
computed there), `kernel` (a local DuckDB engine in the Python process answers queries on
demand — best for large data), or `cloud` (Kanaries cloud). In `kernel` mode the frontend
parses the Graphic Walker DSL to SQL (using the `gw-dsl-parser` WASM / the UMD bundles) and
asks the kernel to execute it, so only aggregated results cross the boundary.

## How dev mode changes asset loading

Normally `WalkerAnyWidget._esm` is the **contents** of `pygwalker-app.es.js` read once at
import — a plain string embedded in the widget. When `PYGWALKER_DEV=1` or `ANYWIDGET_HMR=1`
is set, `_esm` instead points at the **file path** of that bundle. anywidget then reads it from
disk and, under HMR, watches it and live-reloads the widget whenever `vite build --watch`
rewrites the file. This is entirely opt-in: with the flags unset, loading is byte-for-byte the
same as before. See [`DEVELOPMENT.md`](./DEVELOPMENT.md) for the workflow and
[`../AGENTS.md`](../AGENTS.md) for the one-command dev stack.
