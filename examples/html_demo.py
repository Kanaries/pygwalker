import pygwalker as pyg
import pandas as pd


df = pd.read_csv("https://kanaries-app.s3.ap-northeast-1.amazonaws.com/public-datasets/bike_sharing_dc.csv")

with open("pyg_demo.html", "w", encoding="utf-8") as f:
    html = pyg.to_html(df)
    f.write(html)
