import pandas as pd
import reflex as rx

from pygwalker.api.reflex import get_component, register_pygwalker_api


def index() -> rx.Component:
    df = pd.read_csv("https://kanaries-app.s3.ap-northeast-1.amazonaws.com/public-datasets/bike_sharing_dc.csv")
    pyg_component = get_component(df, spec="./gw_config.json")
    return rx.vstack(
        rx.heading("Use Pygwalker In Reflex"),
        pyg_component,
    )

app = rx.App()
app.add_page(index)
register_pygwalker_api(app.api)

if __name__ == "__main__":
    app.run()
