# JupyterLab 4 / Notebook 7 Extension — Round 1 POC Test

This is the deterministic acceptance test for the Round 1 “bicycle” in
[`JUPYTER_EXTENSION_ROADMAP.md`](JUPYTER_EXTENSION_ROADMAP.md). It exercises a real
JupyterLab frontend, Python kernel, pandas DataFrame, PyGWalker frontend, and kernel-side
`CommHandler`; it does not use a mock data service or insert a `pyg.walk()` cell.

## Prerequisites

- Python 3.10 or newer with JupyterLab `>=4.2,<5` or Notebook `>=7.2,<8`
- Node.js and Yarn versions listed in [`../AGENTS.md`](../AGENTS.md)
- A checkout of this repository

## Build and install

Run from the repository root:

```bash
pip install -e ".[dev]"
# Notebook 7 users also need the notebook host:
pip install "notebook>=7.2,<8"
yarn --cwd app install --frozen-lockfile
yarn --cwd packages/pygwalker-jupyter install --frozen-lockfile
yarn --cwd packages/pygwalker-jupyter build
pip install -e packages/pygwalker-jupyter --no-deps
jupyter labextension list
# Start the host being tested:
jupyter lab
jupyter notebook
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

2. Open the DataFrame selector:
   - In JupyterLab 4, open the PyGWalker sidebar.
   - In Notebook 7, select **PyGWalker** in the notebook toolbar; confirm that the native left
     panel opens.
   Select **Refresh DataFrames** if the initial refresh has not completed. Confirm that `df`
   is listed as `3 rows × 2 columns`.
3. Select `df`. In JupyterLab, confirm that a main-area tab titled **PyGWalker: df** opens. In
   Notebook 7, confirm that the selector collapses and the native resizable right panel opens.
   In either host, confirm that the explorer shows the `category` and `value` fields.
4. Resize the host pane on both sides of `768px`. Confirm that the explorer expands with wider
   panes and preserves its three-column layout at narrower sizes, where the pane becomes
   horizontally scrollable rather than clipping the content.
5. With the explorer open, change the active Jupyter theme from light to dark and back. Confirm
   that PyGWalker inherits the theme used when it first opens, follows both live theme changes,
   and keeps the active PyGWalker tab and selected DataFrame instead of remounting the app.
   Confirm that the PyGWalker background and empty host area match, and that its primary,
   surface, text, border, and focus colors follow the active Jupyter palette.
   Check computed colors inside Graphic Walker's shadow root and an open chart menu, not
   only the outer PyGWalker wrapper. Add a second chart before changing themes and confirm
   it survives both changes. Verify the Code Export dialog opens, uses the host palette, and
   closes with Cancel. Save must be absent because this POC has no spec-file target.
   Compare notebook Markdown margins, heading sizes, and toolbar styles before and after
   opening the companion, before running any `pyg.walk()` cell. They must remain unchanged.
6. Open the data table and confirm it contains `A/3`, `B/5`, and `A/8`. This proves that the
   rendered app can query the selected live kernel object.
7. Drag `category` to the X/columns channel and `value` to the Y/rows channel. Confirm that a
   chart is rendered.
8. In a notebook cell in each host, also run:

   ```python
   import pygwalker as pyg

   pyg.walk(df)
   ```

   Confirm that the existing anywidget UI still renders while the companion extension is
   installed.
9. Disable the companion, restart the current Jupyter host, and repeat step 8 to verify the
   core-only path. Re-enable it after the test:

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

The complete JupyterLab journey passed on 2026-08-02 with JupyterLab 4.2.0 and Python 3.10.
The Notebook host journey passed on 2026-08-09 with Notebook 7.2.0 and Python 3.10.9. Both
hosts found the live `df`, rendered the real PyGWalker UI, and reached the kernel bridge. The
JupyterLab host used a main-area split; Notebook 7 used its toolbar entry and native right
panel. Browser measurements also verified the shared responsive rule: a `399px` Notebook
panel kept a `768px` content surface and scrolled horizontally, while wider Notebook and
JupyterLab panes expanded the content to `1079px` and `940px`. On 2026-08-10, both hosts also
inherited the active dark theme on first mount and synchronized dark/light changes in place;
the selected Data tab, live DataFrame, and kernel session remained intact. A real JupyterLab
4.2.7 browser run also verified that the host and PyGWalker root both resolved to `#111111`
in dark mode, while PyGWalker's primary token matched Jupyter's brand color (`#2196f3` dark,
`#1976d2` light) and its surfaces and borders resolved from the corresponding Jupyter theme
tokens. The legacy
`pyg.walk(df)` anywidget path remained separate. A clean-process regression test also verifies
that importing the core package does not import or activate the extension bridge. Unrelated
host/telemetry console errors were isolated from these results.

## Pre-merge regression result, 2026-09-05

Re-tested the production companion build with Python 3.10, JupyterLab 4.2.0, and
Notebook 7.2.0. Both hosts passed DataFrame discovery, real kernel table queries, drag-to-chart,
live dark/light changes with the Data tab preserved, chart menus, Code Export, and an
ordinary `pyg.walk(df)` output alongside the companion. Notebook Markdown styles stayed
unchanged. The editor resolved to `rgb(17, 17, 17)` in dark mode and white in light mode;
its primary color followed Jupyter's brand token. Save is absent without a spec-file target.

Automated checks passed: 330 Python tests, five notebook tests, two Playwright tests,
Python lint/format checks, the full frontend build, and the companion production build.
The mount regression test covers host CSS, both palettes, accessible chart menus, Code Export
portals, preservation of an added chart, and cleanup. CI also builds the companion against
JupyterLab 4.2.0. One rapid-theme-switch run exposed JupyterLab 4.2's own splash-screen
removal race in `jlab_core`; waiting for the host theme transition completed the same flow.
Notebook 7 completed without page errors.

## Uninstall

```bash
pip uninstall pygwalker-jupyter
```

The companion package owns the prebuilt JupyterLab files, so no core PyGWalker files or APIs
are removed. Verify with `jupyter labextension list`; the existing `pyg.walk()` workflow
remains available from the separately installed `pygwalker` package.
