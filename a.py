import pygwalker.api.repl as pyg
import pandas as pd

df = pd.read_csv("./bike_sharing_dc.csv")

walker = pyg.walk(df, spec="./gw_config.json", kernel_computation=True)