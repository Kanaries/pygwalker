import pandas as pd
import streamlit as st
import sys
sys.path.append(r"..")

df = pd.read_csv(r'./bike_sharing_dc.csv', parse_dates=['date'])

import pygwalker as pyg

st.dataframe(df)

st.empty()
pyg.walk(df,env='Streamlit')