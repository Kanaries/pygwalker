"""
PyGWalker + Reflex integration demo.

This demo shows how to integrate PyGWalker with Reflex, a Python web framework.

To run this demo:
1. Make sure you have installed PyGWalker with the Reflex plugin:
   pip install "pygwalker[reflex]"

2. Run the app:
   cd examples
   reflex run
"""

import os
import sys
import traceback
import pandas as pd
import reflex as rx

# Add the parent directory to sys.path to ensure pygwalker can be imported
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

try:
    from pygwalker.api.reflex import get_component
    from pygwalker.communications.reflex_comm import register_pygwalker_api
except Exception as e:
    print(f"Error importing pygwalker: {e}")
    print(traceback.format_exc())
    raise


class State(rx.State):
    """The app state."""
    pass


def index() -> rx.Component:
    """PyGWalker + Reflex demo page."""
    try:
        df = pd.read_csv("https://kanaries-app.s3.ap-northeast-1.amazonaws.com/public-datasets/bike_sharing_dc.csv")
        
        # Create a PyGWalker component
        pyg_component = get_component(
            df,
            theme_key="g2",
            appearance="media",
            default_tab="vis"
        )
        
        return rx.vstack(
            rx.heading("Use Pygwalker In Reflex", size="3"),
            pyg_component,
            spacing="4",
            width="100%",
            align_items="stretch",
        )
    except Exception as e:
        print(f"Error in index function: {e}")
        print(traceback.format_exc())
        # Return an error component instead
        return rx.vstack(
            rx.heading("Error Loading PyGWalker", size="3", color="red"),
            rx.text(f"Error: {str(e)}"),
            rx.code(traceback.format_exc()),
            spacing="4",
        )


# Create a Reflex app with the PyGWalker API transformer
try:
    app = rx.App(api_transformer=register_pygwalker_api)
    app.add_page(index)
except Exception as e:
    print(f"Error creating Reflex app: {e}")
    print(traceback.format_exc())
    raise

# Note: This file is meant to be copied to a Reflex app directory
# See the docstring at the top for instructions 