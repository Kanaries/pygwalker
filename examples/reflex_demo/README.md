# PyGWalker Reflex Demo

This demo shows how to integrate PyGWalker with Reflex, a Python web framework for building interactive web applications.

## Prerequisites

Make sure you have PyGWalker installed with the Reflex plugin:

```bash
pip install "pygwalker[reflex]"
```

## Running the Demo

1. Navigate to this directory:
   ```bash
   cd examples/reflex_demo
   ```

2. Initialize Reflex (first time only):
   ```bash
   reflex init
   ```

3. Run the application:
   ```bash
   reflex run
   ```

4. Open your browser and navigate to `http://localhost:3002`

## What This Demo Shows

- **Full PyGWalker + Reflex Integration**: Complete integration with API transformer
- Proper Reflex package structure (`app/app.py`)
- Interactive data visualization components within Reflex
- Automatic fallback when PyGWalker is not available
- Proper error handling and graceful degradation

## Files in This Demo

- `app/app.py` - Main application file with PyGWalker integration
- `app/__init__.py` - Package initialization 
- `rxconfig.py` - Reflex configuration file
- `README.md` - This documentation file

## Package Structure

The demo follows the standard Reflex package structure:

```
examples/reflex_demo/
├── app/
│   ├── __init__.py
│   └── app.py          # Main app with PyGWalker integration
├── rxconfig.py         # Reflex configuration
├── README.md
└── .gitignore
```

This structure allows Reflex to properly import the app as `app.app` where:
- `app_name="app"` in `rxconfig.py`
- `app/` directory contains the Python package
- `app/app.py` contains the `app = rx.App()` object

## Demo Features

- **Full Integration**: Uses PyGWalker's `register_pygwalker_api` transformer for complete functionality
- **Local Data**: Uses generated sample data (weather data) to avoid network dependencies  
- **Error Handling**: Gracefully handles import and runtime errors with fallback mode
- **Interactive UI**: Provides full PyGWalker data visualization capabilities

## Fixed Issues

This demo includes fixes for:
- ✅ **ASGI Mounting Errors**: Fixed PyGWalker's `register_pygwalker_api` function to properly mount FastAPI sub-applications
- ✅ **Package Structure**: Proper Reflex package structure following `app_name/app_name.py` convention
- ✅ **Route Registration**: Improved API route registration using FastAPI mounting instead of direct route appending

The demo now provides complete PyGWalker integration within a Reflex web application with full API communication support. 