from pygwalker.api.streamlit import StreamlitRenderer
import pandas as pd
import streamlit as st

# Adjust the width of the Streamlit page
st.set_page_config(
    page_title="Use Pygwalker In Streamlit",
    layout="wide"
)

# Add Title
st.title("Use Pygwalker In Streamlit")

# You should cache your pygwalker renderer, if you don't want your memory to explode
@st.cache_resource
def get_pyg_renderer() -> "StreamlitRenderer":
    df = pd.read_csv("https://kanaries-app.s3.ap-northeast-1.amazonaws.com/public-datasets/bike_sharing_dc.csv")
    # If you want to use feature of saving chart config, set `spec_io_mode="rw"`
    return StreamlitRenderer(df, spec="./gw_config.json")


renderer = get_pyg_renderer()

st.subheader("Display Explore UI")

tab1, tab2, tab3, tab4 = st.tabs(
    ["graphic walker", "data profiling", "graphic renderer", "pure chart"]
)

with tab1:
    renderer.explorer()

with tab2:
    renderer.explorer(default_tab="data")

with tab3:
    renderer.render_filter_renderer()

with tab4:
    st.markdown("### registered per weekday")
    renderer.chart(0)
    st.markdown("### registered per day")
    renderer.chart(1)
