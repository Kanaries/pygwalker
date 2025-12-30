# PyGWalker Development Setup

This guide explains how to set up a local development environment for PyGWalker with hot-reloading support.

## Prerequisites

- Python 3.7+
- Node.js 16+
- Yarn

## Quick Start

### 1. Clone and Set Up Python Environment

```bash
git clone https://github.com/Kanaries/pygwalker.git
cd pygwalker

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install pygwalker in editable mode with dev dependencies
pip install -e ".[dev]"
```

### 2. Install Frontend Dependencies

```bash
cd app
yarn install
```

### 3. Build the Frontend (Required for First Run)

```bash
yarn build
```

## Development Workflow

### Option A: Simple Development (Rebuild on Changes)

1. Make changes to files in `app/src/`
2. Rebuild the frontend:
   ```bash
   cd app
   yarn build:app  # Faster than full build
   ```
3. Restart your Jupyter kernel
4. Test your changes

### Option B: Hot-Reload Development (Recommended)

This setup enables live reloading when you change frontend code.

#### Step 1: Start the Vite Dev Server

```bash
cd app
yarn dev
```

The dev server will start at `http://localhost:8769/pyg_dev_app/`

#### Step 2: Start JupyterLab with Server Proxy

In a new terminal:

```bash
source venv/bin/activate
jupyter lab --ServerProxy.servers="{'pyg_dev_app': {'command': [], 'absolute_url': True, 'port': 8769, 'timeout': 30}}"
```

#### Step 3: Configure PyGWalker to Use Dev Server

In your Jupyter notebook, **before** importing pygwalker:

```python
from pygwalker.services.global_var import GlobalVarManager

# Point pygwalker to the dev server
GlobalVarManager.set_component_url("/pyg_dev_app/")

# Now use pygwalker as normal
import pygwalker as pyg
pyg.walk(df)
```

Now any changes you make in `app/src/` will hot-reload automatically!

#### Step 4: Disable Dev Server (Return to Bundled Version)

```python
GlobalVarManager.set_component_url("")  # Empty string = use bundled JS
```

## Troubleshooting

### Clean Rebuild

If you encounter React version errors or other strange issues, try a clean rebuild:

```bash
cd app
rm -rf node_modules
yarn install
yarn build
```

### WASM 404 Errors

If you see 404 errors for `.wasm` files when using the dev server, ensure `vite.config.ts` has:

```typescript
optimizeDeps: {
  exclude: ['@kanaries/gw-dsl-parser'],
},
```

### Cross-Origin Errors

If you see CORS errors, make sure you're using the jupyter-server-proxy setup (Option B) rather than accessing the dev server directly.

## Project Structure

```
pygwalker/
├── app/                    # Frontend React application
│   ├── src/
│   │   ├── index.tsx      # Main entry point
│   │   ├── components/    # React components
│   │   └── ...
│   ├── package.json
│   └── vite.config.ts
├── pygwalker/              # Python package
│   ├── api/               # Python API
│   ├── templates/         # HTML templates & built JS
│   │   └── dist/          # Built frontend assets
│   └── ...
└── docs/
```

## Building for Production

```bash
cd app
yarn build  # Builds all variants (iife, es, dsl-to-workflow, vega-to-dsl)
```

The built files are placed in `pygwalker/templates/dist/`.


