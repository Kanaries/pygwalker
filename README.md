<!-- <p align="center"><a href="#"><img width=60% alt="" src="https://docs-us.oss-us-west-1.aliyuncs.com/img/pygwalker/screenshot-top-img.png"></a></p> -->
<p align="center"><a href="https://github.com/Kanaries/pygwalker"><img width=100% alt="" src="https://docs-us.oss-us-west-1.aliyuncs.com/img/pygwalker/frontpage-rendered.png"></a></p>
<h2 align="center">PyGWalker: A Python Library for Exploratory Data Analysis with Visualization</h2>

<p align="center">
    <a href="https://badge.fury.io/py/pygwalker">
        <img src="https://badge.fury.io/py/pygwalker.svg" alt="PyPI version" height="18" align="center">
    </a>
    <a href="https://mybinder.org/v2/gh/Kanaries/pygwalker/main">
      <img src="https://mybinder.org/badge_logo.svg" alt="binder" height="18" align="center">
    </a>
    <a href="https://discord.gg/Z4ngFWXz2U">
      <img alt="discord invitation link" src="https://dcbadge.vercel.app/api/server/Z4ngFWXz2U?style=flat" align="center">
    </a>
    <a href='https://twitter.com/intent/follow?original_referer=https%3A%2F%2Fpublish.twitter.com%2F&ref_src=twsrc%5Etfw&screen_name=kanaries_data&tw_p=followbutton'>
        <img alt="Twitter Follow" src="https://img.shields.io/twitter/follow/kanaries_data?style=social" alt='Twitter' align="center"/>
    </a>
</p>

[**PyGWalker**](https://github.com/Kanaries/pygwalker) can simplify your Jupyter Notebook data analysis and data visualization workflow. By turning your pandas dataframe into a Tableau-style User Interface for visual exploration.

**PyGWalker** (pronounced like "Pig Walker", just for fun) is named as an abbreviation of "**Py**thon binding of **G**raphic **Walker**". It integrates Jupyter Notebook (or other jupyter-based notebooks) with [Graphic Walker](https://github.com/Kanaries/graphic-walker), a different type of open-source alternative to Tableau. It allows data scientists to analyze data and visualize patterns with simple drag-and-drop operations.
     
Visit [Google Colab](https://colab.research.google.com/drive/171QUQeq-uTLgSj1u-P9DQig7Md1kpXQ2?usp=sharing), [Kaggle Code](https://www.kaggle.com/asmdef/pygwalker-test), [![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/Kanaries/pygwalker/main?labpath=tests%2Fmain.ipynb) or [Graphic Walker Online Demo](https://graphic-walker.kanaries.net/) to test it out!

> PyGWalker will add more support such as R in the future.

# Getting Started

## Tested Environments

- [x] Jupyter Notebook
- [x] Google Colab
- [x] Kaggle Code
- [x] Jupyter Lab (WIP: There're still some tiny CSS issues)
- [x] Databricks Notebook (Since version `0.1.4a0`, needs more tests)
- [ ] Visual Studio Code
- [ ] ...feel free to raise an issue for more environments.

<table>
<thead>
  <tr>
    <th>
      <a href="https://www.kaggle.com/asmdef/pygwalker-test">Run in Kaggle</a>
    </th>
    <th>
      <a href="https://colab.research.google.com/drive/171QUQeq-uTLgSj1u-P9DQig7Md1kpXQ2?usp=sharing">Run in Colab</a>
    </th>
  </tr>
</thead>
<tbody>
  <tr>
    <td>
      <a href="https://www.kaggle.com/asmdef/pygwalker-test">
        <img src="https://docs-us.oss-us-west-1.aliyuncs.com/img/pygwalker/kaggle.png" alt="Kaggle Code" />
      </a>
    </td>
    <td>
      <a href="https://colab.research.google.com/drive/171QUQeq-uTLgSj1u-P9DQig7Md1kpXQ2?usp=sharing">
        <img src="https://docs-us.oss-us-west-1.aliyuncs.com/img/pygwalker/colab.png" alt="Google Colab" />
      </a>
    </td>
</tr>
</tbody>
</table>

## Setup pygwalker

Before using pygwalker, make sure to install the packages through the command line using pip.

```bash
pip install pygwalker
```

## Use pygwalker in Jupyter Notebook

Import pygwalker and pandas to your Jupyter Notebook to get started.

```python    
import pandas as pd
import pygwalker as pyg
```

You can use pygwalker without changing your existing workflow. For example, you can call up Graphic Walker with the dataframe loaded in this way:

```python
df = pd.read_csv('./bike_sharing_dc.csv', parse_dates=['date'])
gwalker = pyg.walk(df)
```

You can even try it online, simply visiting [![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/Kanaries/pygwalker/main?labpath=tests%2Fmain.ipynb), [Google Colab](https://colab.research.google.com/drive/171QUQeq-uTLgSj1u-P9DQig7Md1kpXQ2?usp=sharing) or [Kaggle Code](https://www.kaggle.com/code/asmdef/notebook1cc9d36936).

<!-- ![](https://docs-us.oss-us-west-1.aliyuncs.com/img/pygwalker/screenshot-top-img.png) -->
![](https://docs-us.oss-us-west-1.aliyuncs.com/img/pygwalker/1-8ms.gif)

That's it. Now you have a Tableau-like user interface to analyze and visualize data by dragging and dropping variables.

![](https://docs-us.oss-us-west-1.aliyuncs.com/img/pygwalker/2-8ms.gif)

[![Manually explore your data with a Tableau-like UI](https://docs-us.oss-us-west-1.aliyuncs.com/img/pygwalker/drag-and-drop.gif)](https://docs.kanaries.net/graphic-walker/overview)

Cool things you can do with Graphic Walker:

+ You can change the mark type into others to make different charts, for example, a line chart:

<!-- ![graphic walker line chart](https://docs-us.oss-us-west-1.aliyuncs.com/images/graphic-walker/gw-line-01.png) -->
![graphic walker line chart](https://docs-us.oss-us-west-1.aliyuncs.com/img/pygwalker/fullscreen-timeseries.png)


+ To compare different measures, you can create a concat view by adding more than one measure into rows/columns.

<!-- ![graphic walker area chart](https://docs-us.oss-us-west-1.aliyuncs.com/images/graphic-walker/gw-area-01.png) -->
![graphic walker area chart](https://docs-us.oss-us-west-1.aliyuncs.com/img/pygwalker/fullscreen2-timeseries-area.png)

+ To make a facet view of several subviews divided by the value in dimension, put dimensions into rows or columns to make a facets view. The rules are similar to Tableau.

<!-- ![graphic walker scatter chart](https://docs-us.oss-us-west-1.aliyuncs.com/images/graphic-walker/gw-scatter-01.png) -->
![graphic walker scatter chart](https://docs-us.oss-us-west-1.aliyuncs.com/img/pygwalker/fullscreen-scatter-3.png)

+ You can save the data exploration result to a local file.

For more detailed instructions, visit the [Graphic Walker GitHub page](https://github.com/Kanaries/graphic-walker).

# License

[Apache License 2.0](https://github.com/Kanaries/pygwalker/blob/main/LICENSE)

# Resources

+ Check out more resources about Graphic Walker on [Graphic Walker GitHub](https://github.com/Kanaries/graphic-walker)
+ We are also working on [RATH](https://kanaries.net): an Open Source, Automate exploratory data analysis tool that redefines the workflow of data wrangling, exploration and visualization with AI-powered automation. Check out the [Kanaries website](https://kanaries.net) and [RATH GitHub](https://github.com/Kanaries/Rath) for more!
+ If you encounter any issues and need support, join our [Slack](https://join.slack.com/t/kanaries/shared_invite/zt-1k60sgaxu-aGcuS7CwGeJUccE61iGopg) or [Discord](https://discord.gg/Z4ngFWXz2U) channels.
+ Share pygwalker on these social media platforms:

[![Reddit](https://img.shields.io/badge/share%20on-reddit-red?style=flat-square&logo=reddit)](https://reddit.com/submit?url=https://github.com/Kanaries/pygwalker&title=Say%20Hello%20to%20pygwalker%3A%20Combining%20Jupyter%20Notebook%20with%20a%20Tableau-like%20UI)
[![HackerNews](https://img.shields.io/badge/share%20on-hacker%20news-orange?style=flat-square&logo=ycombinator)](https://news.ycombinator.com/submitlink?u=https://github.com/Kanaries/pygwalker)
[![Twitter](https://img.shields.io/badge/share%20on-twitter-03A9F4?style=flat-square&logo=twitter)](https://twitter.com/share?url=https://github.com/Kanaries/pygwalker&text=Say%20Hello%20to%20pygwalker%3A%20Combining%20Jupyter%20Notebook%20with%20a%20Tableau-like%20UI)
[![Facebook](https://img.shields.io/badge/share%20on-facebook-1976D2?style=flat-square&logo=facebook)](https://www.facebook.com/sharer/sharer.php?u=https://github.com/Kanaries/pygwalker)
[![LinkedIn](https://img.shields.io/badge/share%20on-linkedin-3949AB?style=flat-square&logo=linkedin)](https://www.linkedin.com/shareArticle?url=https://github.com/Kanaries/pygwalker&&title=Say%20Hello%20to%20pygwalker%3A%20Combining%20Jupyter%20Notebook%20with%20a%20Tableau-like%20UI)
