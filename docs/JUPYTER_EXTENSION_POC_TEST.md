# JupyterLab 4 Extension — Round 1 POC Test

This is the deterministic acceptance test for the Round 1 “bicycle” in
[`JUPYTER_EXTENSION_ROADMAP.md`](JUPYTER_EXTENSION_ROADMAP.md). It exercises a real
JupyterLab frontend, Python kernel, pandas DataFrame, PyGWalker frontend, and kernel-side
`CommHandler`; it does not use a mock data service or insert a `pyg.walk()` cell.

## Prerequisites

- Python 3.10 or newer with JupyterLab `>=4.2,<5`
- Node.js and Yarn versions listed in [`../AGENTS.md`](../AGENTS.md)
- A checkout of this repository

## Build and install

Run from the repository root:

```bash
pip install -e ".[dev]"
yarn --cwd app install --frozen-lockfile
yarn --cwd packages/pygwalker-jupyter install --frozen-lockfile
yarn --cwd packages/pygwalker-jupyter build
pip install -e packages/pygwalker-jupyter --no-deps
jupyter labextension list
jupyter lab
```

`jupyter labextension list` must report `@kanaries/pygwalker-jupyter` as enabled and OK.
Build release/prebuilt artifacts with the minimum supported JupyterLab 4.2 environment: the
JupyterLab builder derives shared-package requirements from the host core used at build time.
After changing the extension source, rebuild, reinstall its generated assets, and restart the
JupyterLab server because the server caches the federated-extension manifest:

```bash
yarn --cwd packages/pygwalker-jupyter build
pip install -e packages/pygwalker-jupyter --no-deps --force-reinstall
```

If a rebuilt extension does not appear, run `jupyter --paths` and
`jupyter labextension list`. A higher-priority user-site copy can override a sys-prefix
development link; keep only the intended install or reinstall that copy.

## Browser journey

1. Create a Python notebook and run:

   ```python
   import pandas as pd

   df = pd.DataFrame({"category": ["A", "B", "A"], "value": [3, 5, 8]})
   ```

2. Open the PyGWalker sidebar. Select **Refresh DataFrames** if the initial refresh has not
   completed. Confirm that `df` is listed as `3 rows × 2 columns`.
3. Select `df`. Confirm that a main-area tab titled **PyGWalker: df** opens and shows the
   `category` and `value` fields.
4. Open the data table and confirm it contains `A/3`, `B/5`, and `A/8`. This proves that the
   rendered app can query the selected live kernel object.
5. Drag `category` to the X/columns channel and `value` to the Y/rows channel. Confirm that a
   chart is rendered.
6. In a notebook cell, also run:

   ```python
   import pygwalker as pyg

   pyg.walk(df)
   ```

   Confirm that the existing anywidget UI still renders while the companion extension is
   installed.
7. Disable the companion, restart JupyterLab, and repeat step 6 to verify the core-only path.
   Re-enable it after the test:

   ```bash
   jupyter labextension disable @kanaries/pygwalker-jupyter
   # Restart JupyterLab and verify pyg.walk(df), then:
   jupyter labextension enable @kanaries/pygwalker-jupyter
   ```

## Optional protocol evidence

Launch JupyterLab with kernel-side debug logging enabled:

```bash
PYGWALKER_LOG_LEVEL=DEBUG \
PYGWALKER_LOG_FILE="$PWD/logs/pygwalker-extension-debug.log" \
jupyter lab
```

The log should show the versioned comm opening and successful actions including
`extension_handshake`, `list_dataframes`, `open_dataframe`, `get_latest_vis_spec`, and
`batch_get_datas_by_sql`. Logs contain action names and request IDs, not DataFrame values.

## Recorded Round 1 result

The complete journey passed on 2026-08-02 with JupyterLab 4.2.0 and Python 3.10. The sidebar
found the live `df`, the extension rendered its real data table, field drags produced a bar
chart, `batch_get_datas_by_sql` traffic reached the kernel, and the legacy `pyg.walk(df)`
anywidget rendered alongside it. A clean-process regression test also verifies that importing
the core package does not import or activate the extension bridge. Unrelated third-party
extensions in that local Jupyter profile emitted their own browser errors; they were isolated
from this result.

## Uninstall

```bash
pip uninstall pygwalker-jupyter
```

The companion package owns the prebuilt JupyterLab files, so no core PyGWalker files or APIs
are removed. Verify with `jupyter labextension list`; the existing `pyg.walk()` workflow
remains available from the separately installed `pygwalker` package.
