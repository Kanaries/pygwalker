# Contributing to PyGWalker

This guide covers the local development path used by the Python package and the
React frontend in `app/`.

> **New here?** Start with [`../AGENTS.md`](../AGENTS.md) (repo map + one-command dev stack)
> and [`ARCHITECTURE.md`](./ARCHITECTURE.md) (how the two halves are built). For the
> hot-reload dev workflow, see [`DEVELOPMENT.md`](./DEVELOPMENT.md). The fastest way to run
> everything locally with live frontend reload and centralized logs is `python scripts/dev.py`.

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

## Dev Server / Hot Reload

For iterating on the frontend, use the one-command dev stack, which rebuilds the app on every
change and hot-reloads it into open notebook widgets via anywidget HMR:

```bash
python scripts/dev.py
```

This starts `yarn dev:build` (`vite build --watch`) and JupyterLab with `PYGWALKER_DEV=1` /
`ANYWIDGET_HMR=1`, teeing all output into `logs/`. See
[`DEVELOPMENT.md`](./DEVELOPMENT.md) for the full workflow, flags, and log locations.

The older Vite dev-server + `GlobalVarManager.set_component_url("/pyg_dev_app/")` +
`jupyter-server-proxy` flow only drives the deprecated iframe transport (`env='Jupyter'`) and
is documented as an appendix in [`DEVELOPMENT.md`](./DEVELOPMENT.md#appendix-vite-dev-server-iframe-transport).

## Validation

To run the full CI flow locally in one command (frontend build + Playwright smoke test +
notebook tests + Python lint/tests), use:

```bash
python scripts/local_ci.py        # add --skip-frontend / --skip-notebooks to narrow scope
```

Or run the individual steps below.

Run Python formatting, lint, and tests from the repository root:

```bash
python -m ruff check pygwalker tests scripts bin pygwalker_tools
python -m ruff format --check pygwalker tests scripts bin pygwalker_tools
python -X faulthandler -W error::DeprecationWarning:pygwalker -m pytest -o faulthandler_timeout=60 tests
python -m pytest --nbmake --nbmake-kernel=python tests/*.ipynb
```

`pygwalker_tools/` is an active packaged helper namespace. Its currently
supported surface is `pygwalker_tools.metrics`, covered by
`tests/test_metrics_tools.py`, so keep it in lint, test, wheel, and sdist paths.

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
