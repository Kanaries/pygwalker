# PyGWalker Jupyter extension — Round 1 POC

This companion extension is the Round 1 vertical POC described in
[`docs/JUPYTER_EXTENSION_ROADMAP.md`](../../docs/JUPYTER_EXTENSION_ROADMAP.md). Round 1
supports JupyterLab `>=4.2,<5` and Notebook `>=7.2,<8` and intentionally does not change the
existing `pyg.walk()`/anywidget path.

## Development install

From the repository root, install the editable PyGWalker core, build the prebuilt extension,
and install its companion Python package:

```bash
pip install -e ".[dev]"
# Notebook 7 users also need the notebook host:
pip install "notebook>=7.2,<8"
yarn --cwd app install --frozen-lockfile
yarn --cwd packages/pygwalker-jupyter install --frozen-lockfile
yarn --cwd packages/pygwalker-jupyter build
pip install -e packages/pygwalker-jupyter --no-deps
jupyter labextension list
# Start either supported host:
jupyter lab
jupyter notebook
```

For release artifacts, build in a JupyterLab 4.2 environment, the minimum supported host.
The builder derives shared-package requirements from the installed JupyterLab version.

Open a Python notebook and run:

```python
import pandas as pd

df = pd.DataFrame({"category": ["A", "B", "A"], "value": [3, 5, 8]})
```

In JupyterLab, open the PyGWalker sidebar, refresh, select `df`, and use the resulting
PyGWalker document in the main work area. In Notebook 7, select **PyGWalker** in the notebook
toolbar, choose `df` from the native left panel, and use the explorer in the resizable native
right panel. Neither host inserts a `pyg.walk(df)` cell.

The Jupyter-owned pane remains freely resizable. The embedded explorer preserves a `768px`
minimum content width (the `md` breakpoint); above that width it expands with the pane, and
below it the pane scrolls horizontally instead of compressing or clipping PyGWalker's
three-column layout. The explorer also inherits the active Jupyter light or dark theme when it
opens and follows later host-theme changes without remounting or losing its current state. In
the companion view, PyGWalker's shadcn background, surface, text, primary, border, and focus
tokens are derived from the active Jupyter theme; other PyGWalker hosts keep their existing
palette. App CSS is isolated from notebook Markdown and Jupyter toolbars. Graphic Walker
and its menus receive the same host palette. Appearance follows Jupyter's theme setting.

The POC has no spec-file target, so it does not offer Save. Use Export Code to copy a chart
specification. Kernel restart/reconnect and notebook switching recovery remain Round 2 work;
after restarting a kernel, run the DataFrame cell and reload the host page before reopening
the explorer.

After rebuilding the extension, reinstall its generated prebuilt assets and restart the
Jupyter server (both frontends cache the federated-extension manifest):

```bash
yarn --cwd packages/pygwalker-jupyter build
pip install -e packages/pygwalker-jupyter --no-deps --force-reinstall
```

## Checks

```bash
python -m pytest tests/test_jupyter_extension.py tests/test_integration_apis.py
yarn --cwd app typecheck
yarn --cwd packages/pygwalker-jupyter typecheck
yarn --cwd packages/pygwalker-jupyter build:prod
jupyter labextension list
```

The complete Round 1 browser smoke test is documented in
[`docs/JUPYTER_EXTENSION_POC_TEST.md`](../../docs/JUPYTER_EXTENSION_POC_TEST.md).

## Uninstall / disable

```bash
pip uninstall pygwalker-jupyter
```

This removes only the companion extension. The core `pygwalker` package and `pyg.walk()`
remain installed.
