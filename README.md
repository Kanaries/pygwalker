[English](README.md) | [Español](./docs/README.es.md) | [Français](./docs/README.fr.md) | [Deutsch](./docs/README.de.md) | [中文](./docs/README.zh.md) | [Türkçe](./docs/README.tr.md) | [日本語](./docs/README.ja.md) | [한국어](./docs/README.ko.md) | [Русский](./docs/README.ru.md)

> [!NOTE]
> The English README is the source of truth for the API reference, installation, and development instructions. Translated READMEs are community-maintained and may lag behind this file.


<p align="center"><a href="https://github.com/Kanaries/pygwalker"><img width=100% alt="" src="https://github.com/user-attachments/assets/f90db669-6e5a-45d3-942e-547c9d0471c9" /></a></p>

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
     

https://github.com/Kanaries/pygwalker/assets/22167673/2b940e11-cf8b-4cde-b7f6-190fb10ee44b

> [!TIP]
> If you want more AI features, we also build [runcell](https://runcell.dev), an AI Code Agent in Jupyter that understands your code/data/cells and generate code, execute cells and take actions for you. It can be used in jupyter lab with `pip install runcell`



https://github.com/user-attachments/assets/9ec64252-864d-4bd1-8755-83f9b0396d38




Visit [Google Colab](https://colab.research.google.com/drive/171QUQeq-uTLgSj1u-P9DQig7Md1kpXQ2?usp=sharing), [Kaggle Code](https://www.kaggle.com/code/lxy21495892/airbnb-eda-pygwalker-demo) or [Graphic Walker Online Demo](https://graphic-walker.kanaries.net/) to test it out!

> If you prefer using R, check [GWalkR](https://github.com/Kanaries/GWalkR), the R wrapper of Graphic Walker.
> If you prefer a Desktop App that can be used offline and without any coding, check out [PyGWalker Desktop](https://kanaries.net/download?utm_source=pygwalker_github&utm_content=tip).


# Features
PyGWalker is a Python library that simplifies data analysis and visualization workflows by turning pandas, polars, and pyarrow table data into interactive visual interfaces.
It offers a variety of features that make it a powerful tool for data exploration:
- ##### Interactive Data Exploration:
    - Drag-and-drop interface for easy visualization creation.   
    - Real-time updates as you make changes to the visualization.
    - Ability to zoom, pan, and filter the data.   
- ##### Data Cleaning and Transformation:
    - Visual data cleaning tools to identify and remove outliers or inconsistencies.   
    - Ability to create new variables and features based on existing data.   
- ##### Advanced Visualization Capabilities:
    - Support for various chart types (bar charts, line charts, scatter plots, etc.). 
    - Customization options for colors, labels, and other visual elements.   
    - Interactive features like tooltips and drill-down capabilities.   
- ##### Integration with Jupyter Notebooks:
    - Seamless integration with Jupyter Notebooks for a smooth workflow.   
- ##### Open-Source and Free:
    - Available for free and allows for customization and extension.



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
> For an early trial, you can install with `pip install pygwalker --upgrade` to keep your version up to date with the latest release or even `pip install pygwalker --upgrade --pre` to obtain latest features and bug-fixes.

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

+ `spec_path`: local file path for saving/loading chart config.
+ `spec`: chart config object, JSON string, config ID, or remote URL.
+ `computation`: choose where data queries run. Use `"browser"` for frontend-only computation, `"kernel"` for local DuckDB-backed Python computation, `"cloud"` for Kanaries cloud computation, or omit it for the default automatic behavior.
+ `kernel_computation`: legacy boolean for using DuckDB as computing engine. Prefer `computation="kernel"` or `computation="browser"`; this legacy flag is scheduled for removal in PyGWalker 0.7.0.
+ `cloud_computation`: legacy boolean for Kanaries cloud computation. Prefer `computation="cloud"`; this legacy flag is scheduled for removal in PyGWalker 0.7.0.
+ `use_kernel_calc`: deprecated alias for kernel computation. Prefer `computation="kernel"` or `computation="browser"`; this legacy flag is scheduled for removal in PyGWalker 0.7.0.

```python
df = pd.read_csv('./bike_sharing_dc.csv')
walker = pyg.walk(
    df,
    spec_path="./chart_meta_0.json",  # local file used to load and save chart state.
    computation="kernel",          # use DuckDB in the Python kernel for larger datasets.
)
```

For new code on the 0.6 line, prefer a reusable `Walker` object and choose where to render it:

```python
walker = pyg.Walker(df, spec_path="./chart_meta_0.json", computation="browser")
walker.show()       # auto-detects notebook or script mode
html = walker.to_html()
html = pyg.to_html(walker)
```

See [PyGWalker 0.6 Release Notes](./docs/RELEASE_0_6.md) for the compatibility policy, deprecation timeline, and tested runtime support.

After exploring in the UI, export the current chart state as reproducible Python code:

```python
code = walker.to_code(dataset_name="df")
print(code)
```

If you have an older saved spec, migrate it to the current schema before committing it:

```python
migrated_spec = pyg.spec.migrate(open("./old_chart_meta.json").read())
```

### Example in local notebook

* Notebook Code: [Click Here](https://github.com/Kanaries/pygwalker-offline-example)
* Preview Notebook Html: [Click Here](https://pygwalker-public-bucket.s3.amazonaws.com/demo.html)

### Example in cloud notebook

* [Use PyGWalker in Kaggle](https://www.kaggle.com/code/lxy21495892/airbnb-eda-pygwalker-demo)
* [Use PyGWalker in Google Colab](https://colab.research.google.com/drive/171QUQeq-uTLgSj1u-P9DQig7Md1kpXQ2?usp=sharing)

### Programmatic Export of Charts

After saving a chart from the UI, you can retrieve the image directly from Python.

```python
walker = pyg.walk(df, spec_path="./chart_meta_0.json")
# edit the chart in the UI and click the save button
walker.save_chart_to_file("Chart 1", "chart1.svg", save_type="svg")
png_bytes = walker.export_chart_png("Chart 1")
svg_bytes = walker.export_chart_svg("Chart 1")
```

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
    return StreamlitRenderer(df, spec_path="./gw_config.json", spec_io_mode="rw")


renderer = get_pyg_renderer()

renderer.explorer()
```

If you already created a reusable `Walker`, Streamlit can render it directly:

```python
import pygwalker as pyg
from pygwalker.api.streamlit import StreamlitRenderer

walker = pyg.Walker(df, spec_path="./gw_config.json", computation="kernel")
renderer = StreamlitRenderer(walker)
renderer.explorer()
```

## [API Reference](https://pygwalker-docs.vercel.app/api-reference/jupyter)

### [pygwalker.walk](https://pygwalker-docs.vercel.app/api-reference/jupyter#walk)


| Parameter          | Type                                                      | Default         | Description                                                                                                                       |
|--------------------|-----------------------------------------------------------|-----------------|-----------------------------------------------------------------------------------------------------------------------------------|
| dataset            | Union[DataFrame, pyarrow.Table, Connector, str, Walker]   | -               | DataFrame, pyarrow table, database connector, SQL/data source string, or reusable Walker object to explore.                        |
| gid                | Union[int, str]                                           | None            | ID for the GraphicWalker container div, formatted as `gwalker-{gid}`.                                                              |
| env                | Literal['JupyterAnywidget', 'Jupyter', 'JupyterWidget']   | 'JupyterAnywidget' | Notebook rendering environment. Use `JupyterAnywidget` or omit `env`; `Jupyter` and `JupyterWidget` are deprecated aliases to the anywidget transport and are scheduled for removal in PyGWalker 0.7.0. |
| field_specs        | Optional[List[FieldSpec]]                                 | None            | Field specifications. They will be inferred from `dataset` if not specified.                                                       |
| theme_key          | Literal['vega', 'g2', 'streamlit']                        | 'g2'            | Theme type for Graphic Walker.                                                                                                     |
| appearance         | Literal['media', 'light', 'dark']                         | 'media'         | Theme appearance. `media` follows the operating system preference.                                                                 |
| spec               | str                                                       | ""              | Chart configuration data. Can be a configuration ID, JSON string, local file path, or remote file URL.                             |
| spec_path          | Optional[str]                                             | None            | Local chart configuration file path. Prefer this over passing a local file path through `spec`.                                    |
| computation        | Optional[Literal['auto', 'browser', 'kernel', 'cloud']]   | None            | Computation backend. Omit it for automatic behavior; use `browser`, `kernel`, or `cloud` to choose explicitly.                     |
| use_kernel_calc    | Optional[bool]                                            | None            | Deprecated; scheduled for removal in PyGWalker 0.7.0. Use `computation="kernel"` or `computation="browser"` instead.              |
| kernel_computation | Optional[bool]                                            | None            | Legacy boolean for local DuckDB-backed kernel computation; scheduled for removal in PyGWalker 0.7.0. Prefer `computation`.         |
| cloud_computation  | bool                                                      | False           | Legacy boolean for Kanaries cloud computation; scheduled for removal in PyGWalker 0.7.0. Prefer `computation="cloud"`.             |
| show_cloud_tool    | bool                                                      | True            | Whether to show the Kanaries cloud tool when available.                                                                            |
| kanaries_api_key   | str                                                       | ""              | Kanaries API key used by cloud features.                                                                                           |
| default_tab        | Literal['data', 'vis']                                    | 'vis'           | Default tab to show when the UI opens.                                                                                             |
| **kwargs           | Any                                                       | -               | Additional keyword arguments.                                                                                                      |

## Development

Local development is documented in this repository:

- [AGENTS.md](AGENTS.md) — repo map, the one-command dev stack (`python scripts/dev.py`), and log locations (written for both human and AI-agent contributors).
- [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) — hot-reload dev workflow and troubleshooting.
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — how the Python and frontend halves are built and talk to each other.
- [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) — validation commands, CI, and package builds.

See also the hosted guide: [local-development](https://docs.kanaries.net/pygwalker/installation#local-development).

## Tested Environments

- [x] Jupyter Notebook
- [x] Google Colab
- [x] Kaggle Code
- [x] Jupyter Lab
- [x] Jupyter Lite
- [x] Databricks Notebook (Since version `0.1.4a0`)
- [x] Jupyter Extension for Visual Studio Code (Since version `0.1.4a0`)
- [x] Most web applications compatiable with IPython kernels. (Since version `0.1.4a0`)
- [x] **Streamlit (Since version `0.1.4.9`)**, enabled with `pygwalker.api.streamlit.StreamlitRenderer`
- [x] DataCamp Workspace (Since version `0.1.4a0`)
- [x] Panel. See [panel-graphic-walker](https://github.com/panel-extensions/panel-graphic-walker).
- [x] marimo (Since version `0.4.9.11`)
- [ ] Hex Projects 
- [ ] ...feel free to raise an issue for more environments.

## Configuration And Privacy Policy(pygwalker >= 0.3.10)

You can use `pygwalker config` to set your privacy configuration.

```bash
$ pygwalker config --help

usage: pygwalker config [-h] [--set [key=value ...]] [--reset [key ...]] [--reset-all] [--list]

Modify configuration file. (default: ~/Library/Application Support/pygwalker/config.json) 
Available configurations:

- privacy  ['offline', 'update-only', 'events'] (default: update-only).
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

# Contribution Guideline
You are encouraged to contribute to PyGWalker in any way that suits your interests. This may include:
- Answering questions and providing support
- Sharing ideas for new features
- Reporting bugs and glitches
- Contributing code to the project
- Offering suggestions for website improvements and better documentation

# Resources

> PyGWalker Cloud is released! You can now save your charts to cloud, publish the interactive cell as a web app and use advanced GPT-powered features. Check out the [PyGWalker Cloud](https://kanaries.net/pygwalker?from=gh_md) for more details.

+ Check out more resources about PyGWalker on [Kanaries PyGWalker](https://kanaries.net/pygwalker)
+ PyGWalker Paper [PyGWalker: On-the-fly Assistant for Exploratory Visual Data Analysis
](https://arxiv.org/abs/2406.11637)
+ We are also working on [RATH](https://kanaries.net): an Open Source, Automate exploratory data analysis software that redefines the workflow of data wrangling, exploration and visualization with AI-powered automation. Check out the [Kanaries website](https://kanaries.net) and [RATH GitHub](https://github.com/Kanaries/Rath) for more!
+ [Youtube: How to explore data with PyGWalker in Python
](https://youtu.be/rprn79wfB9E?si=lAsJn1cAQnb-EklD)
+ [Use pygwalker to build visual analysis app in streamlit](https://docs.kanaries.net/pygwalker/use-pygwalker-with-streamlit)
+ Use [panel-graphic-walker](https://github.com/panel-extensions/panel-graphic-walker) to build data visualization apps with Panel.
+ If you encounter any issues and need support, please join our [Discord](https://discord.gg/Z4ngFWXz2U) channel or raise an issue on github.
+ Share pygwalker on these social media platforms if you like it!
[![Reddit](https://img.shields.io/badge/share%20on-reddit-red?style=flat-square&logo=reddit)](https://reddit.com/submit?url=https://github.com/Kanaries/pygwalker&title=Say%20Hello%20to%20pygwalker%3A%20Combining%20Jupyter%20Notebook%20with%20a%20Tableau-like%20UI)
[![HackerNews](https://img.shields.io/badge/share%20on-hacker%20news-orange?style=flat-square&logo=ycombinator)](https://news.ycombinator.com/submitlink?u=https://github.com/Kanaries/pygwalker)
[![Twitter](https://img.shields.io/badge/share%20on-twitter-03A9F4?style=flat-square&logo=twitter)](https://twitter.com/share?url=https://github.com/Kanaries/pygwalker&text=Say%20Hello%20to%20pygwalker%3A%20Combining%20Jupyter%20Notebook%20with%20a%20Tableau-alternative%20UI)
[![Facebook](https://img.shields.io/badge/share%20on-facebook-1976D2?style=flat-square&logo=facebook)](https://www.facebook.com/sharer/sharer.php?u=https://github.com/Kanaries/pygwalker)
[![LinkedIn](https://img.shields.io/badge/share%20on-linkedin-3949AB?style=flat-square&logo=linkedin)](https://www.linkedin.com/shareArticle?url=https://github.com/Kanaries/pygwalker&&title=Say%20Hello%20to%20pygwalker%3A%20Combining%20Jupyter%20Notebook%20with%20a%20Tableau-alternative%20UI)
