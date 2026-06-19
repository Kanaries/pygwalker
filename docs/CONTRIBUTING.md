# Contributing to PyGWalker

This guide covers the local development path used by the Python package and the
React frontend in `app/`.

## Prerequisites

- Python 3.10 or newer
- Node.js 22.x, matching CI
- Yarn 1.x

## Python Setup

From the repository root:

```bash
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
```

On Windows, activate the environment with:

```powershell
venv\Scripts\activate
```

## Frontend Setup

Install frontend dependencies from `app/`:

```bash
cd app
yarn install
```

Build all frontend bundles:

```bash
yarn build
```

For a faster rebuild while working only on the main app bundle:

```bash
yarn build:app
```

The built assets are written to `pygwalker/templates/dist/`. They are generated
artifacts and should not be committed unless the release process explicitly asks
for them.

## Working With Local Graphic Walker Source

The npm package `@kanaries/graphic-walker` is normally installed from
`app/yarn.lock`. If you need to test PyGWalker against a local Graphic Walker
checkout, place it under the PyGWalker repository root so it is a sibling of
`app/`:

```text
pygwalker/
+-- app/
+-- graphic-walker/
    +-- packages/
        +-- graphic-walker/
```

Then build Graphic Walker before starting the PyGWalker frontend:

```bash
cd app
yarn dev:preinstall
```

`dev:preinstall` runs:

```bash
cd ../graphic-walker/packages/graphic-walker
yarn --frozen-lockfile
yarn build
```

If `../graphic-walker/packages/graphic-walker` does not exist, skip this command
and use the locked npm dependency.

## Frontend Dev Server

Start the Vite dev server from `app/`:

```bash
yarn dev:server
```

The dev server listens on port `8769` and serves the app under
`/pyg_dev_app/`.

For JupyterLab development, run Jupyter with `jupyter-server-proxy`:

```bash
jupyter lab --ServerProxy.servers="{'pyg_dev_app': {'command': [], 'absolute_url': True, 'port': 8769, 'timeout': 30}}"
```

In the notebook, point PyGWalker at the dev frontend before rendering:

```python
from pygwalker.services.global_var import GlobalVarManager

GlobalVarManager.set_component_url("/pyg_dev_app/")
```

Reset to bundled assets with:

```python
GlobalVarManager.set_component_url("")
```

## Validation

Run Python formatting, lint, and tests from the repository root:

```bash
python -m ruff check pygwalker tests scripts bin pygwalker_tools
python -m ruff format --check pygwalker tests scripts bin pygwalker_tools
python -X faulthandler -W error::DeprecationWarning:pygwalker -m pytest -o faulthandler_timeout=60 tests
python -m pytest --nbmake --nbmake-kernel=python tests/*.ipynb
```

Run frontend type checking, build, and smoke tests from `app/`:

```bash
yarn typecheck
yarn build
yarn playwright install chromium
yarn test:front_end
```

`yarn build:app` is useful for fast local iteration on the main app bundle, but
it does not run TypeScript checking or build the auxiliary DSL conversion
bundles that CI and package builds require.

Run a package build from the repository root:

```bash
python -m build --wheel --no-isolation
```

The package build now rebuilds the frontend bundles instead of reusing an
existing `pygwalker/templates/dist` file.

## CI Notes

The GitHub workflows build frontend assets with Node.js 22.x, run the frontend
Playwright smoke test, then run the Python test matrix. Python package builds
also set up Node.js and Yarn because the Hatch build hook rebuilds the frontend
during wheel creation.

Keep workflow changes aligned with `app/package.json`, `pyproject.toml`, and
`scripts/compile.sh`.
