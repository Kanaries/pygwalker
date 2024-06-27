[English](README.md) | [Español](./docs/README.es.md) | [Français](./docs/README.fr.md) | [Deutsch](./docs/README.de.md) | [中文](./docs/README.zh.md) | [Türkçe](./docs/README.tr.md) | [日本語](./docs/README.ja.md) | [한국어](./docs/README.ko.md)

<p align="center"><a href="https://github.com/Kanaries/pygwalker"><img width=100% alt="" src="https://github.com/Kanaries/pygwalker/assets/22167673/bed8b3db-fda8-43e7-8ad2-71f6afb9dddd" /></a></p>

<h2 align="center">PyGWalker: A Python Library for Exploratory Data Analysis with Visualization</h2>

<p align="center">
    <a href="https://arxiv.org/abs/2406.11637">
      <img src="https://img.shields.io/badge/arXiv-2406.11637-b31b1b.svg" height="18" align="center">
    </a>
    <a href="https://badge.fury.io/py/pygwalker">
        <img src="https://badge.fury.io/py/pygwalker.svg" alt="PyPI version" height="18" align="center" />
    </a>
    <a href="https://mybinder.org/v2/gh/Kanaries/pygwalker/main">
      <img src="https://mybinder.org/badge_logo.svg" alt="binder" height="18" align="center" />
    </a>
    <a href="https://pypi.org/project/pygwalker">
      <img src="https://img.shields.io/pypi/dm/pygwalker" alt="PyPI downloads" height="18" align="center" />
    </a>
    <a href="https://anaconda.org/conda-forge/pygwalker"> <img src="https://anaconda.org/conda-forge/pygwalker/badges/version.svg" alt="conda-forge" height="18" align="center" /> </a>
</p>

<p align="center">
    <a href="https://discord.gg/Z4ngFWXz2U">
      <img alt="discord invitation link" src="https://dcbadge.vercel.app/api/server/Z4ngFWXz2U?style=flat" align="center" />
    </a>
    <a href='https://twitter.com/intent/follow?original_referer=https%3A%2F%2Fpublish.twitter.com%2F&ref_src=twsrc%5Etfw&screen_name=kanaries_data&tw_p=followbutton'>
        <img alt="Twitter Follow" src="https://img.shields.io/twitter/follow/kanaries_data?style=social" alt='Twitter' align="center" />
    </a>
    <a href="https://kanaries-community.slack.com/join/shared_invite/zt-20kpp56wl-ke9S0MxTcNQjUhKf6SOfvQ#/shared-invite/email">
      <img src="https://img.shields.io/badge/Slack-green?style=flat-square&logo=slack&logoColor=white" alt="Join Kanaries on Slack" align="center" />
    </a> 
</p>

[**PyGWalker**](https://github.com/Kanaries/pygwalker) can simplify your Jupyter Notebook data analysis and data visualization workflow, by turning your pandas dataframe into an interactive user interface for visual exploration.

**PyGWalker** (pronounced like "Pig Walker", just for fun) is named as an abbreviation of "**Py**thon binding of **G**raphic **Walker**". It integrates Jupyter Notebook with [Graphic Walker](https://github.com/Kanaries/graphic-walker), an open-source alternative to Tableau. It allows data scientists to visualize / clean / annotates the data with simple drag-and-drop operations and even natural language queries.
     
Visit [Google Colab](https://colab.research.google.com/drive/171QUQeq-uTLgSj1u-P9DQig7Md1kpXQ2?usp=sharing), [Kaggle Code](https://www.kaggle.com/code/lxy21495892/airbnb-eda-pygwalker-demo) or [Graphic Walker Online Demo](https://graphic-walker.kanaries.net/) to test it out!

> If you prefer using R, check [GWalkR](https://github.com/Kanaries/GWalkR), the R wrapper of Graphic Walker.



https://github.com/Kanaries/pygwalker/assets/22167673/2b940e11-cf8b-4cde-b7f6-190fb10ee44b



# Getting Started
> Check our video tutorial about using pygwalker, pygwalker + streamlit and pygwalker + snowflake, [How to explore data with PyGWalker in Python
](https://youtu.be/rprn79wfB9E?si=lAsJn1cAQnb-EklD)

| [Run in Kaggle](https://www.kaggle.com/code/lxy21495892/airbnb-eda-pygwalker-demo) | [Run in Colab](https://colab.research.google.com/drive/171QUQeq-uTLgSj1u-P9DQig7Md1kpXQ2?usp=sharing) |
|--------------------------------------------------------------|--------------------------------------------------------|
| [![Kaggle Code](https://docs-us.oss-us-west-1.aliyuncs.com/img/pygwalker/kaggle.png)](https://www.kaggle.com/code/lxy21495892/airbnb-eda-pygwalker-demo) | [![Google Colab](https://docs-us.oss-us-west-1.aliyuncs.com/img/pygwalker/colab.png)](https://colab.research.google.com/drive/171QUQeq-uTLgSj1u-P9DQig7Md1kpXQ2?usp=sharing) |

## Setup pygwalker

Before using pygwalker, make sure to install the packages through the command line using pip or conda.

### pip

```bash
pip install pygwalker
```
> **Note**
> 
> For an early trial, you can install with `pip install pygwalker --upgrade` to keep your version up to date with the latest release or even `pip install pygwaler --upgrade --pre` to obtain latest features and bug-fixes.

### Conda-forge
```bash
conda install -c conda-forge pygwalker
```
or
```bash
mamba install -c conda-forge pygwalker
```
See [conda-forge feedstock](https://github.com/conda-forge/pygwalker-feedstock) for more help.


## Use pygwalker in Jupyter Notebook

### Quick Start

Import pygwalker and pandas to your Jupyter Notebook to get started.

```python    
import pandas as pd
import pygwalker as pyg
```

You can use pygwalker without breaking your existing workflow. For example, you can call up PyGWalker with the dataframe loaded in this way:

```python
df = pd.read_csv('./bike_sharing_dc.csv')
walker = pyg.walk(df)
```

![](https://docs-us.oss-us-west-1.aliyuncs.com/img/pygwalker/travel-ani-0-light.gif)

That's it. Now you have an interactive UI to analyze and visualize data with simple drag-and-drop operations.

![](https://docs-us.oss-us-west-1.aliyuncs.com/img/pygwalker/travel-ani-1-light.gif)

Cool things you can do with PyGwalker:

+ You can change the mark type into others to make different charts, for example, a line chart:
![graphic walker line chart](https://user-images.githubusercontent.com/8137814/221894699-b9623304-4eb1-4051-b29d-ca4a913fb7c7.png)

+ To compare different measures, you can create a concat view by adding more than one measure into rows/columns.
![graphic walker area chart](https://user-images.githubusercontent.com/8137814/224550839-7b8a2193-d3e9-4c11-a19e-ad8e5ec19539.png)

+ To make a facet view of several subviews divided by the value in dimension, put dimensions into rows or columns to make a facets view.
![graphic walker scatter chart](https://user-images.githubusercontent.com/8137814/221894480-b5ec5df2-d0bb-45bc-aa3d-6479920b6fe2.png)

+ PyGWalker contains a powerful data table, which provides a quick view of data and its distribution, profiling. You can also add filters or change the data types in the table.
<img width="1537" alt="pygwalker-data-preview" src="https://github.com/Kanaries/pygwalker/assets/22167673/e3239932-bc3c-4de3-8387-1eabf2ca3a3a">

+ You can save the data exploration result to a local file

### Better Practices

There are some important parameters you should know when using pygwalker: 

+ `spec`: for save/load chart config (json string or file path)
+ `kernel_computation`: for using duckdb as computing engine which allows you to handle larger dataset faster in your local machine.
+ `use_kernel_calc`: Deprecated, use `kernel_computation` instead.

```python
df = pd.read_csv('./bike_sharing_dc.csv')
walker = pyg.walk(
    df,
    spec="./chart_meta_0.json",    # this json file will save your chart state, you need to click save button in ui mannual when you finish a chart, 'autosave' will be supported in the future.
    kernel_computation=True,          # set `kernel_computation=True`, pygwalker will use duckdb as computing engine, it support you explore bigger dataset(<=100GB).
)
```

### Example in local notebook

* Notebook Code: [Click Here](https://github.com/Kanaries/pygwalker-offline-example)
* Preview Notebook Html: [Click Here](https://pygwalker-public-bucket.s3.amazonaws.com/demo.html)

### Example in cloud notebook

* [Use PyGWalker in Kaggle](https://www.kaggle.com/code/lxy21495892/airbnb-eda-pygwalker-demo)
* [Use PyGWalker in Google Colab](https://colab.research.google.com/drive/171QUQeq-uTLgSj1u-P9DQig7Md1kpXQ2?usp=sharing)

## Use pygwalker in Streamlit
Streamlit allows you to host a web version of pygwalker without figuring out details of how web application works.

Here are some of the app examples build with pygwalker and streamlit:
+ [PyGWalker + streamlit for Bike sharing dataset](https://pygwalkerdemo-cxz7f7pt5oc.streamlit.app/)
+ [Earthquake Dashboard](https://earthquake-dashboard-pygwalker.streamlit.app/)

[![](https://user-images.githubusercontent.com/22167673/271170853-5643c3b1-6216-4ade-87f4-41c6e6893eab.png)](https://earthquake-dashboard-pygwalker.streamlit.app/)

```python
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
    df = pd.read_csv("./bike_sharing_dc.csv")
    # If you want to use feature of saving chart config, set `spec_io_mode="rw"`
    return StreamlitRenderer(df, spec="./gw_config.json", spec_io_mode="rw")


renderer = get_pyg_renderer()

renderer.explorer()
```

## [API Reference](https://pygwalker-docs.vercel.app/api-reference/jupyter)

### [pygwalker.walk](https://pygwalker-docs.vercel.app/api-reference/jupyter#walk)


| Parameter              | Type                                                      | Default              | Description                                                                                                                                      |
|------------------------|-----------------------------------------------------------|----------------------|--------------------------------------------------------------------------------------------------------------------------------------------------|
| dataset                | Union[DataFrame, Connector]                               | -                    | The dataframe or connector to be used.                                                                                                           |
| gid                    | Union[int, str]                                           | None                 | ID for the GraphicWalker container div, formatted as 'gwalker-{gid}'.                                                                            |
| env                    | Literal['Jupyter', 'JupyterWidget']          | 'JupyterWidget'      | Environment using pygwalker.                                                                                                                     |
| field_specs             | Optional[Dict[str, FieldSpec]]                            | None                 | Specifications of fields. Will be automatically inferred from `dataset` if not specified.                                                        |
| hide_data_source_config   | bool                                                      | True                 | If True, hides DataSource import and export button.                                                                                              |
| theme_key               | Literal['vega', 'g2']                                     | 'g2'                 | Theme type for the GraphicWalker.                                                                                                                |
| appearance                   | Literal['media', 'light', 'dark']                         | 'media'              | Theme setting. 'media' will auto-detect the OS theme.                                                                                            |
| spec                   | str                                                       | ""                   | Chart configuration data. Can be a configuration ID, JSON, or remote file URL.                                                                   |
| use_preview            | bool                                                      | True                 | If True, uses the preview function.                                                                                                              |
| kernel_computation        | bool                                                      | False                | If True, uses kernel computation for data.                                                                                                       |
| **kwargs               | Any                                                       | -                    | Additional keyword arguments.                                                                                                                    |

## Development

Refer it: [local-development](https://docs.kanaries.net/pygwalker/installation#local-development)

## Tested Environments

- [x] Jupyter Notebook
- [x] Google Colab
- [x] Kaggle Code
- [x] Jupyter Lab
- [x] Jupyter Lite
- [x] Databricks Notebook (Since version `0.1.4a0`)
- [x] Jupyter Extension for Visual Studio Code (Since version `0.1.4a0`)
- [x] Most web applications compatiable with IPython kernels. (Since version `0.1.4a0`)
- [x] **Streamlit (Since version `0.1.4.9`)**, enabled with `pyg.walk(df, env='Streamlit')`
- [x] DataCamp Workspace (Since version `0.1.4a0`)
- [ ] Hex Projects 
- [ ] ...feel free to raise an issue for more environments.

## Configuration And Privacy Policy(pygwlaker >= 0.3.10)

You can use `pygwalker config` to set your privacy configuration.

```bash
$ pygwalker config --help

usage: pygwalker config [-h] [--set [key=value ...]] [--reset [key ...]] [--reset-all] [--list]

Modify configuration file. (default: ~/Library/Application Support/pygwalker/config.json) 
Available configurations:

- privacy  ['offline', 'update-only', 'events'] (default: events).
    "offline": fully offline, no data is send or api is requested
    "update-only": only check whether this is a new version of pygwalker to update
    "events": share which events about which feature is used in pygwalker, it only contains events data about which feature you arrive for product optimization. No DATA YOU ANALYSIS IS SEND. Events data will bind with a unique id, which is generated by pygwalker when it is installed based on timestamp. We will not collect any other information about you.
    
- kanaries_token  ['your kanaries token'] (default: empty string).
    your kanaries token, you can get it from https://kanaries.net.
    refer: https://space.kanaries.net/t/how-to-get-api-key-of-kanaries.
    by kanaries token, you can use kanaries service in pygwalker, such as share chart, share config.
    

options:
  -h, --help            show this help message and exit
  --set [key=value ...]
                        Set configuration. e.g. "pygwalker config --set privacy=update-only"
  --reset [key ...]     Reset user configuration and use default values instead. e.g. "pygwalker config --reset privacy"
  --reset-all           Reset all user configuration and use default values instead. e.g. "pygwalker config --reset-all"
  --list                List current used configuration.
```

More details, refer it: [How to set your privacy configuration?](https://github.com/Kanaries/pygwalker/wiki/How-to-set-your-privacy-configuration%3F)

# License

[Apache License 2.0](https://github.com/Kanaries/pygwalker/blob/main/LICENSE)

# Resources

> PyGWalker Cloud is released! You can now save your charts to cloud, publish the interactive cell as a web app and use advanced GPT-powered features. Check out the [PyGWalker Cloud](https://kanaries.net/pygwalker?from=gh_md) for more details.

+ Check out more resources about PyGWalker on [Kanaries PyGWalker](https://kanaries.net/pygwalker)
+ PyGWalker Paper [PyGWalker: On-the-fly Assistant for Exploratory Visual Data Analysis
](https://arxiv.org/abs/2406.11637)
+ We are also working on [RATH](https://kanaries.net): an Open Source, Automate exploratory data analysis software that redefines the workflow of data wrangling, exploration and visualization with AI-powered automation. Check out the [Kanaries website](https://kanaries.net) and [RATH GitHub](https://github.com/Kanaries/Rath) for more!
+ [Youtube: How to explore data with PyGWalker in Python
](https://youtu.be/rprn79wfB9E?si=lAsJn1cAQnb-EklD)
+ [Use pygwalker to build visual analysis app in streamlit](https://docs.kanaries.net/pygwalker/use-pygwalker-with-streamlit)
+ If you encounter any issues and need support, please join our [Discord](https://discord.gg/Z4ngFWXz2U) channel or raise an issue on github.
+ Share pygwalker on these social media platforms if you like it!
[![Reddit](https://img.shields.io/badge/share%20on-reddit-red?style=flat-square&logo=reddit)](https://reddit.com/submit?url=https://github.com/Kanaries/pygwalker&title=Say%20Hello%20to%20pygwalker%3A%20Combining%20Jupyter%20Notebook%20with%20a%20Tableau-like%20UI)
[![HackerNews](https://img.shields.io/badge/share%20on-hacker%20news-orange?style=flat-square&logo=ycombinator)](https://news.ycombinator.com/submitlink?u=https://github.com/Kanaries/pygwalker)
[![Twitter](https://img.shields.io/badge/share%20on-twitter-03A9F4?style=flat-square&logo=twitter)](https://twitter.com/share?url=https://github.com/Kanaries/pygwalker&text=Say%20Hello%20to%20pygwalker%3A%20Combining%20Jupyter%20Notebook%20with%20a%20Tableau-alternative%20UI)
[![Facebook](https://img.shields.io/badge/share%20on-facebook-1976D2?style=flat-square&logo=facebook)](https://www.facebook.com/sharer/sharer.php?u=https://github.com/Kanaries/pygwalker)
[![LinkedIn](https://img.shields.io/badge/share%20on-linkedin-3949AB?style=flat-square&logo=linkedin)](https://www.linkedin.com/shareArticle?url=https://github.com/Kanaries/pygwalker&&title=Say%20Hello%20to%20pygwalker%3A%20Combining%20Jupyter%20Notebook%20with%20a%20Tableau-alternative%20UI)
