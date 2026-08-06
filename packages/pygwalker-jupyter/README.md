# PyGWalker Jupyter extension — Round 1 POC

This companion extension is the Round 1 vertical POC described in
[`docs/JUPYTER_EXTENSION_ROADMAP.md`](../../docs/JUPYTER_EXTENSION_ROADMAP.md). Round 1
supports JupyterLab `>=4.2,<5` and intentionally does not change the existing
`pyg.walk()`/anywidget path.

## Development install

From the repository root, install the editable PyGWalker core, build the prebuilt extension,
and install its companion Python package:

```bash
pip install -e ".[dev]"
yarn --cwd app install --frozen-lockfile
yarn --cwd packages/pygwalker-jupyter install --frozen-lockfile
yarn --cwd packages/pygwalker-jupyter build
pip install -e packages/pygwalker-jupyter --no-deps
jupyter labextension list
jupyter lab
```

Open a Python notebook and run:

```python
import pandas as pd

df = pd.DataFrame({"category": ["A", "B", "A"], "value": [3, 5, 8]})
```

Open the PyGWalker sidebar, refresh, select `df`, and use the resulting PyGWalker document in
the main work area. No `pyg.walk(df)` cell is inserted.

After rebuilding the extension, reinstall its generated prebuilt assets and restart the
JupyterLab server (the server caches the federated-extension manifest):

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
