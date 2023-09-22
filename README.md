[English](README.md) | [中文](./docs/README.zh.md) | [Türkçe](./docs/README.tr.md) | [Español](./docs/README.es.md) | [Français](./docs/README.fr.md) | [Deutsch](./docs/README.de.md) | [日本語](./docs/README.ja.md) | [한국어](./docs/README.ko.md)

> PyGWalker 0.3 is released! Check out the [changelog](https://github.com/Kanaries/pygwalker/releases/tag/0.3.0) for more details. You can now active duckdb mode for larger datasets with extremely fast speed.
<p align="center"><a href="https://github.com/Kanaries/pygwalker"><img width=100% alt="" src="https://user-images.githubusercontent.com/8137814/221879671-70379d15-81ac-44b9-b267-a8fa3842a0d9.png"></a></p>

<h2 align="center">PyGWalker: A Python Library for Exploratory Data Analysis with Visualization</h2>

<p align="center">
    <a href="https://badge.fury.io/py/pygwalker">
        <img src="https://badge.fury.io/py/pygwalker.svg" alt="PyPI version" height="18" align="center">
    </a>
    <a href="https://mybinder.org/v2/gh/Kanaries/pygwalker/main">
      <img src="https://mybinder.org/badge_logo.svg" alt="binder" height="18" align="center">
    </a>
    <a href="https://pypi.org/project/pygwalker">
      <img src="https://img.shields.io/pypi/dm/pygwalker" alt="PyPI downloads" height="18" align="center">
    </a>
    <a href="https://anaconda.org/conda-forge/pygwalker"> <img src="https://anaconda.org/conda-forge/pygwalker/badges/version.svg" alt="conda-forge" height="18" align="center" /> </a>
</p>

<p align="center">
    <a href="https://discord.gg/Z4ngFWXz2U">
      <img alt="discord invitation link" src="https://dcbadge.vercel.app/api/server/Z4ngFWXz2U?style=flat" align="center">
    </a>
    <a href='https://twitter.com/intent/follow?original_referer=https%3A%2F%2Fpublish.twitter.com%2F&ref_src=twsrc%5Etfw&screen_name=kanaries_data&tw_p=followbutton'>
        <img alt="Twitter Follow" src="https://img.shields.io/twitter/follow/kanaries_data?style=social" alt='Twitter' align="center"/>
    </a>
    <a href="https://kanaries-community.slack.com/join/shared_invite/zt-20kpp56wl-ke9S0MxTcNQjUhKf6SOfvQ#/shared-invite/email">
      <img src="https://img.shields.io/badge/Slack-green?style=flat-square&logo=slack&logoColor=white" alt="Join Kanaries on Slack" align="center"/>
    </a> 
</p>

[**PyGWalker**](https://github.com/Kanaries/pygwalker) can simplify your Jupyter Notebook data analysis and data visualization workflow, by turning your pandas dataframe (and polars dataframe) into a Tableau-style User Interface for visual exploration.

**PyGWalker** (pronounced like "Pig Walker", just for fun) is named as an abbreviation of "**Py**thon binding of **G**raphic **Walker**". It integrates Jupyter Notebook (or other jupyter-based notebooks) with [Graphic Walker](https://github.com/Kanaries/graphic-walker), a different type of open-source alternative to Tableau. It allows data scientists to analyze data and visualize patterns with simple drag-and-drop operations.
     
Visit [Google Colab](https://colab.research.google.com/drive/171QUQeq-uTLgSj1u-P9DQig7Md1kpXQ2?usp=sharing), [Kaggle Code](https://www.kaggle.com/asmdef/pygwalker-test) or [Graphic Walker Online Demo](https://graphic-walker.kanaries.net/) to test it out!

> If you prefer using R, you can check out [GWalkR](https://github.com/Kanaries/GWalkR) now!

# Getting Started

| [Run in Kaggle](https://www.kaggle.com/asmdef/pygwalker-test) | [Run in Colab](https://colab.research.google.com/drive/171QUQeq-uTLgSj1u-P9DQig7Md1kpXQ2?usp=sharing) |
|--------------------------------------------------------------|--------------------------------------------------------|
| [![Kaggle Code](https://docs-us.oss-us-west-1.aliyuncs.com/img/pygwalker/kaggle.png)](https://www.kaggle.com/asmdef/pygwalker-test) | [![Google Colab](https://docs-us.oss-us-west-1.aliyuncs.com/img/pygwalker/colab.png)](https://colab.research.google.com/drive/171QUQeq-uTLgSj1u-P9DQig7Md1kpXQ2?usp=sharing) |

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

You can use pygwalker without breaking your existing workflow. For example, you can call up Graphic Walker with the dataframe loaded in this way:

```python
df = pd.read_csv('./bike_sharing_dc.csv')
walker = pyg.walk(df)
```

### Better Practice

```python
df = pd.read_csv('./bike_sharing_dc.csv')
walker = pyg.walk(
    df,
    spec="./chart_meta_0.json",    # this json file will save your chart state, you need to click save button in ui mannual when you finish a chart, 'autosave' will be supported in the future.
    use_kernel_calc=True,          # set `use_kernel_calc=True`, pygwalker will use duckdb as computing engine, it support you explore bigger dataset(<=100GB).
)
```

### Offline Example

* Notebook Code: [Click Here](https://github.com/Kanaries/pygwalker-offline-example)
* Preview Notebook Html: [Click Here](https://pygwalker-public-bucket.s3.amazonaws.com/demo.html)

### Online Example

* [Kaggle Code For New Pygwalker](https://www.kaggle.com/code/lxy21495892/airbnb-eda-pygwalker-demo)
* [Kanaries Share page](https://kanaries.net/share/notebook/cwa8g22r6kg0#heading-0)
* [Kaggle Code](https://www.kaggle.com/asmdef/pygwalker-test)
* [Google Colab](https://colab.research.google.com/drive/171QUQeq-uTLgSj1u-P9DQig7Md1kpXQ2?usp=sharing)

***

![](https://docs-us.oss-us-west-1.aliyuncs.com/img/pygwalker/travel-ani-0-light.gif)

That's it. Now you have a Tableau-like user interface to analyze and visualize data by dragging and dropping variables.

![](https://docs-us.oss-us-west-1.aliyuncs.com/img/pygwalker/travel-ani-1-light.gif)

Cool things you can do with Graphic Walker:

+ You can change the mark type into others to make different charts, for example, a line chart:
![graphic walker line chart](https://user-images.githubusercontent.com/8137814/221894699-b9623304-4eb1-4051-b29d-ca4a913fb7c7.png)

+ To compare different measures, you can create a concat view by adding more than one measure into rows/columns.
![graphic walker area chart](https://user-images.githubusercontent.com/8137814/224550839-7b8a2193-d3e9-4c11-a19e-ad8e5ec19539.png)

+ To make a facet view of several subviews divided by the value in dimension, put dimensions into rows or columns to make a facets view. The rules are similar to Tableau.
![graphic walker scatter chart](https://user-images.githubusercontent.com/8137814/221894480-b5ec5df2-d0bb-45bc-aa3d-6479920b6fe2.png)

+ You can view the data frame in a table and configure the analytic types and semantic types.
![page-data-view-light](https://user-images.githubusercontent.com/8137814/221895610-76165bc6-95ee-4567-a55b-41d47d3310eb.png)


+ You can save the data exploration result to a local file

For more detailed instructions, visit the [Graphic Walker GitHub page](https://github.com/Kanaries/graphic-walker).

## Tested Environments

- [x] Jupyter Notebook
- [x] Google Colab
- [x] Kaggle Code
- [x] Jupyter Lab (WIP: There're still some tiny CSS issues)
- [x] Jupyter Lite
- [x] Databricks Notebook (Since version `0.1.4a0`)
- [x] Jupyter Extension for Visual Studio Code (Since version `0.1.4a0`)
- [x] Hex Projects (Since version `0.1.4a0`)
- [x] Most web applications compatiable with IPython kernels. (Since version `0.1.4a0`)
- [x] **Streamlit (Since version `0.1.4.9`)**, enabled with `pyg.walk(df, env='Streamlit')`
- [x] DataCamp Workspace (Since version `0.1.4a0`)
- [ ] ...feel free to raise an issue for more environments.

## Configuration

Since `pygwalker>=0.1.7a0`, we provide the ability to modify user-wide configuration either through the command line interface
```bash
$ pygwalker config   
usage: pygwalker config [-h] [--set [key=value ...]] [--reset [key ...]] [--reset-all] [--list]

Modify configuration file.

optional arguments:
  -h, --help            show this help message and exit
  --set [key=value ...]
                        Set configuration. e.g. "pygwalker config --set privacy=get-only"
  --reset [key ...]     Reset user configuration and use default values instead. e.g. "pygwalker config --reset privacy"
  --reset-all           Reset all user configuration and use default values instead. e.g. "pygwalker config --reset-all"
  --list                List current used configuration.
```
or through Python API
```python
>>> import pygwalker as pyg, pygwalker_utils.config as pyg_conf
>>> help(pyg_conf.set_config)

Help on function set_config in module pygwalker_utils.config:

set_config(config: dict, save=False)
    Set configuration.
    
    Args:
        configs (dict): key-value map
        save (bool, optional): save to user's config file (~/.config/pygwalker/config.json). Defaults to False.
(END)
```

### Privacy Policy
```bash
$ pygwalker config --set
usage: pygwalker config [--set [key=value ...]] | [--reset [key ...]].

Available configurations:
- privacy        ['offline', 'get-only', 'meta', 'any'] (default: meta).
    "offline"   : no data will be transfered other than the front-end and back-end of the notebook.
    "get-only"  : the data will not be uploaded but only fetched from external servers.
    "meta"      : only the desensitized data will be processed by external servers. There might be some server-side processing tasks performed on the metadata in future versions.
    "any"       : the data can be processed by external services.
```

For example,
```bash
pygwalker config --set privacy=meta
```
in command line and
```python
import pygwalker as pyg, pygwalker.utils_config as pyg_conf
pyg_conf.set_config( { 'privacy': 'meta' }, save=True)
```
have the same effect.

# License

[Apache License 2.0](https://github.com/Kanaries/pygwalker/blob/main/LICENSE)

# Resources

+ Check out more resources about Graphic Walker on [Graphic Walker GitHub](https://github.com/Kanaries/graphic-walker)
+ We are also working on [RATH](https://kanaries.net): an Open Source, Automate exploratory data analysis software that redefines the workflow of data wrangling, exploration and visualization with AI-powered automation. Check out the [Kanaries website](https://kanaries.net) and [RATH GitHub](https://github.com/Kanaries/Rath) for more!
+ [Use pygwalker to build visual analysis app in streamlit](https://docs.kanaries.net/pygwalker/use-pygwalker-with-streamlit)
+ If you encounter any issues and need support, join our [Slack](https://join.slack.com/t/kanaries-community/shared_invite/zt-1pcosgbua-E_GBPawQOI79C41dPDyyvw) or [Discord](https://discord.gg/Z4ngFWXz2U) channels.
+ Share pygwalker on these social media platforms:

[![Reddit](https://img.shields.io/badge/share%20on-reddit-red?style=flat-square&logo=reddit)](https://reddit.com/submit?url=https://github.com/Kanaries/pygwalker&title=Say%20Hello%20to%20pygwalker%3A%20Combining%20Jupyter%20Notebook%20with%20a%20Tableau-like%20UI)
[![HackerNews](https://img.shields.io/badge/share%20on-hacker%20news-orange?style=flat-square&logo=ycombinator)](https://news.ycombinator.com/submitlink?u=https://github.com/Kanaries/pygwalker)
[![Twitter](https://img.shields.io/badge/share%20on-twitter-03A9F4?style=flat-square&logo=twitter)](https://twitter.com/share?url=https://github.com/Kanaries/pygwalker&text=Say%20Hello%20to%20pygwalker%3A%20Combining%20Jupyter%20Notebook%20with%20a%20Tableau-like%20UI)
[![Facebook](https://img.shields.io/badge/share%20on-facebook-1976D2?style=flat-square&logo=facebook)](https://www.facebook.com/sharer/sharer.php?u=https://github.com/Kanaries/pygwalker)
[![LinkedIn](https://img.shields.io/badge/share%20on-linkedin-3949AB?style=flat-square&logo=linkedin)](https://www.linkedin.com/shareArticle?url=https://github.com/Kanaries/pygwalker&&title=Say%20Hello%20to%20pygwalker%3A%20Combining%20Jupyter%20Notebook%20with%20a%20Tableau-like%20UI)
