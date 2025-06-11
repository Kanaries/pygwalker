"""
PyGWalker + Reflex integration demo.

This demo shows how to integrate PyGWalker with Reflex, a Python web framework.

To run this demo:
1. Make sure you have installed PyGWalker with the Reflex plugin:
   pip install "pygwalker[reflex]"

2. Navigate to this directory:
   cd examples/reflex_demo

3. Run the app:
   reflex run
"""

import os
import sys
import traceback
import pandas as pd
import reflex as rx

# Add the project root directory to sys.path to ensure pygwalker can be imported
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Try to import PyGWalker Reflex components, fall back to basic demo if not available
try:
    from pygwalker.api.reflex import get_component
    from pygwalker.communications.reflex_comm import register_pygwalker_api
    PYGWALKER_AVAILABLE = True
    print("✅ PyGWalker Reflex integration is available!")
except Exception as e:
    print(f"⚠️  PyGWalker Reflex integration not available: {e}")
    print("Running in fallback mode with basic Reflex demo.")
    PYGWALKER_AVAILABLE = False
    get_component = None
    register_pygwalker_api = None


class State(rx.State):
    """The app state."""
    pass


def index() -> rx.Component:
    """PyGWalker + Reflex demo page."""
    if PYGWALKER_AVAILABLE:
        return pygwalker_demo()
    else:
        return fallback_demo()


def pygwalker_demo() -> rx.Component:
    """PyGWalker integration demo."""
    try:
        # Use local data to avoid network issues
        df = pd.DataFrame({
            'Date': pd.date_range('2023-01-01', periods=100),
            'Temperature': [20 + 10 * (i % 10) / 10 for i in range(100)],
            'Humidity': [50 + 30 * (i % 7) / 7 for i in range(100)],
            'City': ['New York', 'London', 'Tokyo', 'Paris', 'Sydney'] * 20
        })
        
        # Create a PyGWalker component
        pyg_component = get_component(
            df,
            theme_key="g2",
            appearance="media",
            default_tab="vis"
        )
        
        return rx.vstack(
            rx.heading("Use Pygwalker In Reflex", size="3"),
            rx.text("This demo shows PyGWalker integrated with Reflex framework."),
            rx.text("✅ PyGWalker components with full API integration!", color="green"),
            pyg_component,
            spacing="4",
            width="100%",
            align_items="stretch",
        )
    except Exception as e:
        print(f"Error in pygwalker_demo: {e}")
        print(traceback.format_exc())
        return fallback_demo_with_error(str(e))


def fallback_demo() -> rx.Component:
    """Fallback demo when PyGWalker is not available."""
    # Sample data
    df = pd.DataFrame({
        'Date': pd.date_range('2023-01-01', periods=10),
        'Temperature': [20, 22, 25, 28, 30, 27, 24, 21, 19, 23],
        'Humidity': [45, 50, 55, 60, 65, 58, 52, 48, 44, 49],
        'City': ['New York'] * 10
    })
    
    return rx.vstack(
        rx.heading("PyGWalker + Reflex Demo", size="3"),
        rx.text("PyGWalker Reflex integration is not available.", color="orange"),
        rx.text("Install it with: pip install 'pygwalker[reflex]'", font_family="monospace"),
        
        rx.heading("Sample Data", size="2", margin_top="20px"),
        rx.text(f"Data shape: {df.shape}"),
        
        rx.box(
            rx.text("Temperature Data:", font_weight="bold"),
            rx.text(f"Min: {df['Temperature'].min()}°C, Max: {df['Temperature'].max()}°C"),
            rx.text("Humidity Data:", font_weight="bold"),
            rx.text(f"Min: {df['Humidity'].min()}%, Max: {df['Humidity'].max()}%"),
            padding="15px",
            border="1px solid #ccc",
            border_radius="8px",
            margin_top="10px",
        ),
        
        rx.text(
            "This demo shows the basic Reflex setup working. "
            "When PyGWalker Reflex integration is available, "
            "this will display an interactive data visualization component.",
            margin_top="20px",
            font_style="italic"
        ),
        
        spacing="4",
        width="100%",
        align_items="stretch",
        padding="20px",
    )


def fallback_demo_with_error(error_msg: str) -> rx.Component:
    """Fallback demo when PyGWalker components fail."""
    return rx.vstack(
        rx.heading("PyGWalker + Reflex Demo", size="3"),
        rx.text("PyGWalker components encountered an error:", color="red"),
        rx.code(error_msg, padding="10px", background_color="gray.100"),
        rx.text("Falling back to basic demo.", color="orange"),
        
        rx.text(
            "This suggests there might be a compatibility issue between "
            "PyGWalker and the current version of Reflex. The basic Reflex "
            "framework is working correctly.",
            margin_top="20px",
            font_style="italic"
        ),
        
        spacing="4",
        width="100%",
        align_items="stretch",
        padding="20px",
    )


# Create a Reflex app with the fixed PyGWalker API transformer
try:
    if PYGWALKER_AVAILABLE:
        try:
            app = rx.App(api_transformer=register_pygwalker_api)
            print("✅ Reflex app created with PyGWalker API transformer!")
        except Exception as e:
            print(f"⚠️  PyGWalker API transformer failed: {e}")
            print("Creating basic Reflex app without transformer...")
            app = rx.App()
            print("✅ Reflex app created without PyGWalker transformer!")
    else:
        app = rx.App()
        print("✅ Basic Reflex app created!")
    
    app.add_page(index)
    print("✅ Pages added successfully!")
    
except Exception as e:
    print(f"❌ Error creating Reflex app: {e}")
    print(traceback.format_exc())
    raise 