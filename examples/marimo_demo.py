# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "marimo",
#     "pandas==2.2.3",
#     "pygwalker==0.4.9.13",
# ]
# ///

import marimo

__generated_with = "0.9.15"
app = marimo.App(width="medium")


@app.cell
def __(pd, walk):
    _df = pd.read_csv("https://kanaries-app.s3.ap-northeast-1.amazonaws.com/public-datasets/bike_sharing_dc.csv")
    walk(_df)
    return


@app.cell
def __(pd, pyg):
    _df = pd.read_csv("https://kanaries-app.s3.ap-northeast-1.amazonaws.com/public-datasets/bike_sharing_dc.csv")
    pyg.walk(_df)
    return


@app.cell
def __():
    # import libraries
    import marimo as mo
    import pandas as pd
    from pygwalker.api.marimo import walk # Usage - directly use walk("<dataset-path>")
    import pygwalker.api.marimo as pyg # Usage - directly use pyg.walk("<dataset-path>")
    return mo, pd, pyg, walk


if __name__ == "__main__":
    app.run()
