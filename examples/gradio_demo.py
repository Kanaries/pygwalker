import gradio as gr
import pandas as pd

from pygwalker.api.gradio import PYGWALKER_ROUTE, get_html_on_gradio

with gr.Blocks() as demo:
    df = pd.read_csv("https://kanaries-app.s3.ap-northeast-1.amazonaws.com/public-datasets/bike_sharing_dc.csv")
    pyg_html = get_html_on_gradio(df, spec="/Users/douding/Desktop/github/pygwalker-in-streamlit/gw_config.json", debug=True)
    gr.HTML(pyg_html)


app = demo.launch(app_kwargs={
    "routes": [PYGWALKER_ROUTE]
})
