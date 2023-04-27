<p align="center"><a href="https://github.com/Kanaries/pygwalker"><img width=100% alt="" src="https://user-images.githubusercontent.com/8137814/221879671-70379d15-81ac-44b9-b267-a8fa3842a0d9.png"></a></p>

<h2 align="center">PyGWalker: 一行代码将数据集转化为交互式可视化分析工具</h2>

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
</p>

[**PyGWalker**](https://github.com/Kanaries/pygwalker)是个在Jupyter Notebook环境中运行的可视化探索式分析工具，仅一条命令即可生成一个可交互的图形界面，以类似Tableau/PowerBI的方式，通过拖拽字段进行数据分析。

过去在python中进行数据可视化分析时，经常需要查询大量的可视化类的代码，并编写胶水代码将其应用在数据集上。PyGWalker的目标是通过一行代码，将数据集转化为一个可视化分析工具，只需拖拉拽即可生成图表，从而减少数据分析师在数据可视化上的时间成本。

> 为什么叫PyGWalker？PyGWalker，全称为"Python binding of Graphic Walker"，将Jupyter Notebook(或类Jupyter Notebook)和[Graphic Walker](https://github.com/Kanaries/graphic-walker)集成。Graphic Walker是一个轻量级的Tableau/Power BI开源替代品，可以帮助数据分析师使用简单的拖拉拽操作，进行数据可视化和探索。

> PyGWalker 将来提供R语言支持

## 一键尝试PyGWalker

使用以下服务一键尝试PyGWalker：

| [Kaggle Notebook](https://www.kaggle.com/asmdef/pygwalker-test) | [Google Colab](https://colab.research.google.com/drive/171QUQeq-uTLgSj1u-P9DQig7Md1kpXQ2?usp=sharing) | [Graphic Walker Online Demo](https://graphic-walker.kanaries.net) |
|---|---|---|
| [![](https://docs-us.oss-us-west-1.aliyuncs.com/img/blog-cover-images/pygwalker-kaggle.png)](https://www.kaggle.com/asmdef/pygwalker-test) | [![](https://docs-us.oss-us-west-1.aliyuncs.com/img/blog-cover-images/pygwalker-google-colab.png)](https://colab.research.google.com/drive/171QUQeq-uTLgSj1u-P9DQig7Md1kpXQ2?usp=sharing) | [![](https://docs-us.oss-us-west-1.aliyuncs.com/img/blog-cover-images/pygwalker-graphic-walker.png)](https://graphic-walker.kanaries.net) |

Binder: [![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/Kanaries/pygwalker/main?labpath=tests%2Fmain.ipynb)


## 快速开始

使用pip或Conda安装pygwalker

### pip

```bash
pip install pygwalker
```
> **备注**
> 
> 使用 `pip install pygwalker --upgrade` 更新最新版PyGWalker
>
> 使用 `pip install pygwaler --upgrade --pre` 来尝鲜最新版，获得最新bug修复
> 

### Conda-forge
```bash
conda install -c conda-forge pygwalker
```
或者
```bash
mamba install -c conda-forge pygwalker
```
更多参考： [conda-forge feedstock](https://github.com/conda-forge/pygwalker-feedstock)


## 在Jupyter Notebook中使用PyGWalker

导入库

```python    
import pandas as pd
import pygwalker as pyg
```

将dataframe 导入PyGWalker

```python
df = pd.read_csv('./bike_sharing_dc.csv', parse_dates=['date'])
gwalker = pyg.walk(df)
```

使用Polars dataframe (需要 `pygwalker>=0.1.4.7a0`):

```python
import polars as pl
df = pl.read_csv('./bike_sharing_dc.csv',try_parse_dates = True)
gwalker = pyg.walk(df)
```

大功告成。现在你可以使用拖拉拽，直接操作dataframe，创建可视化视图，完成数据分析：

![](https://docs-us.oss-us-west-1.aliyuncs.com/img/pygwalker/travel-ani-0-light.gif)

范例：

![](https://docs-us.oss-us-west-1.aliyuncs.com/img/pygwalker/travel-ani-1-light.gif)

## 使用PyGWalker制作数据可视化图

| 快速预览数据 | 折线图 |
| --- | --- |
| ![page-data-view-light](https://user-images.githubusercontent.com/8137814/221895610-76165bc6-95ee-4567-a55b-41d47d3310eb.png) | ![](https://user-images.githubusercontent.com/8137814/221894699-b9623304-4eb1-4051-b29d-ca4a913fb7c7.png) | 
| 分面图 (Facet) |  连接视图(Concat) |
| ![graphic walker area chart](https://user-images.githubusercontent.com/8137814/224550839-7b8a2193-d3e9-4c11-a19e-ad8e5ec19539.png) | ![graphic walker scatter chart](https://user-images.githubusercontent.com/8137814/221894480-b5ec5df2-d0bb-45bc-aa3d-6479920b6fe2.png) |

更多参考： [Graphic Walker GitHub 页面](https://github.com/Kanaries/graphic-walker).

## 将数据可视化导出为代码

> 自PyGWalker 0.1.6.起，你可以将数据可视化导出为代码。

1. 单击工具栏上的**Export to Code** 按钮。 该按钮位于“导出为 PNG/SVG”按钮旁边。

     ![导出 PyGWalker 到代码](https://docs-us.oss-us-west-1.aliyuncs.com/img/pygwalker/export-button-pygwalker.png)

2.可视化以代码形式提供。 单击 **复制到 Clickboard** 按钮以保存代码。

     ![导出 PyGWalker 到代码](https://docs-us.oss-us-west-1.aliyuncs.com/img/pygwalker/export-to-string-pygwalker.png)

3. 要在 PyGWalker 中导入代码，只需将刚刚下载的代码导入为 `vis_spec`。
示例 vis_spec 字符串：

```
vis_spec = """
[{"visId":"65b894b5-23fb-4aa6-8f31-d0e1a795d9de","name":"Chart 1","encodings":{"dimensions":[{"dragId":"9e1666ef-461d-4550-ac6a-465a74eb281d","fid":"gwc_1","name":"date","semanticType":"temporal","analyticType":"dimension"},...],"color":[],"opacity":[],"size":[],"shape":[],"radius":[],"theta":[],"details":[],"filters":[]},"config":{"defaultAggregated":true,"geoms":["auto"],"stack":"stack","showActions":false,"interactiveScale":false,"sorted":"none","size":{"mode":"auto","width":320,"height":200},"exploration":{"mode":"none","brushDirection":"default"}}}]
"""
```

并使用 `vis_spec` 加载 PyGWalker：

```
pyg.walk(df, spec=vis_spec)
```
![加载数据可视化到 PyGWalker](https://docs-us.oss-us-west-1.aliyuncs.com/img/pygwalker/load-viz-pygwalker.png)

4. 调用内置帮助文档：

```
help(pyg.walk)
```

快速了解 vis_spec 字符串：

```
pyg.to_html(df, spec=vis_spec)
```

示例输出：

```
Signature: pyg.walk(df: 'pl.DataFrame | pd.DataFrame', gid: Union[int, str] = None, *, env: Literal['Jupyter', 'Streamlit'] = 'Jupyter', **kwargs)
Docstring:
Walk through pandas.DataFrame df with Graphic Walker

Args:
    - df (pl.DataFrame | pd.DataFrame, optional): dataframe.
    - gid (Union[int, str], optional): GraphicWalker container div's id ('gwalker-{gid}')

Kargs:
    - env: (Literal['Jupyter' | 'Streamlit'], optional): The enviroment using pygwalker. Default as 'Jupyter'
    - hideDataSourceConfig (bool, optional): Hide DataSource import and export button (True) or not (False). Default to True
    - themeKey ('vega' | 'g2'): theme type.
    - dark (Literal['media' | 'light' | 'dark']): 'media': auto detect OS theme.
    - return_html (bool, optional): Directly return a html string. Defaults to False.
File:      /usr/local/lib/python3.9/dist-packages/pygwalker/gwalker.py
Type:      function

```

更多参考： [PyGWalker 更新日志](https://docs.kanaries.net/zh/pygwalker/changelog/pygwalker-0-1-6)

## 测试环境

- [x] Jupyter Notebook
- [x] Google Colab
- [x] Kaggle Code
- [x] Jupyter Lab (存在关于CSS的一点小问题)
- [x] Jupyter Lite
- [x] Databricks Notebook (最低版本: `0.1.4a0`)
- [x] Jupyter Extension for Visual Studio Code (最低版本:  `0.1.4a0`)
- [x] Hex Projects (最低版本:  `0.1.4a0`)
- [x] 大多数与 IPython 内核兼容的 Web 应用程序. (最低版本:  `0.1.4a0`)
- [x] **Streamlit (最低版本:  `0.1.4.9`)**, 使用方法： `pyg.walk(df, env='Streamlit')`
- [x] DataCamp Workspace (最低版本:  `0.1.4a0`)
- [ ] 需要其他环境支持？请给我们提Issue！

## 配置

自 `pygwalker>=0.1.7a0` 以降，你可以使用命令行配置PyGWalker

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

或使用 Python API

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

### 隐私配置

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

如：

```bash
pygwalker config --set privacy=meta
```
也可以使用：

```python
import pygwalker as pyg, pygwalker.utils.config as pyg_conf
pyg_conf.set_config( { 'privacy': 'meta' }, save=True)
```

两种方法效果相同。

# License

[Apache License 2.0](https://github.com/Kanaries/pygwalker/blob/main/LICENSE)

# 更多阅读

+ 关于Graphic Walker，参考 [Graphic Walker GitHub](https://github.com/Kanaries/graphic-walker)
+ 我们也在开发新一代增强分析型BI：[RATH](https://kanaries.net)。RATH是新一代智能化数据分析工具。借助AI，因果推断，智能可视化引擎协助你进行数据分析，体验前所未有的自动化。更多请访问：[RATH GitHub](https://github.com/Kanaries/Rath)
+ 微信交流群

| kanaries微信交流群 | kanaries公众号 |
| --- | --- |
| ![wechat-group](https://user-images.githubusercontent.com/22167673/233818474-3340e05a-5fd7-4dce-9a15-60cc175d26de.jpg) | ![](https://kanaries-docs.oss-cn-hangzhou.aliyuncs.com/img/qrcode_for_gh_49e6f7d65120_860.jpg) |
