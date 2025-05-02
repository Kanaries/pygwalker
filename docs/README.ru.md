[English](README.md) | [Español](./docs/README.es.md) | [Français](./docs/README.fr.md) | [Deutsch](./docs/README.de.md) | [中文](./docs/README.zh.md) | [Türkçe](./docs/README.tr.md) | [日本語](./docs/README.ja.md) | [한국어](./docs/README.ko.md)

<p align="center"><a href="https://github.com/Kanaries/pygwalker"><img width=100% alt="" src="https://github.com/user-attachments/assets/f90db669-6e5a-45d3-942e-547c9d0471c9" /></a></p>

<h2 align="center">PyGWalker: Библиотека Python для разведочного анализа данных с визуализацией</h2>

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
        <img alt="Twitter Follow" src="https://img.shields.io/twitter/follow/kanaries_data?style=social" align="center" />
    </a>
    <a href="https://kanaries-community.slack.com/join/shared_invite/zt-20kpp56wl-ke9S0MxTcNQjUhKf6SOfvQ#/shared-invite/email">
      <img src="https://img.shields.io/badge/Slack-green?style=flat-square&logo=slack&logoColor=white" alt="Join Kanaries on Slack" align="center" />
    </a> 
</p>

**PyGWalker** (произносится как «Пиг Уокер», просто для забавы) — это сочетание слов **Py**thon и **Graphic Walker**. Он интегрирует Jupyter Notebook с [Graphic Walker](https://github.com/Kanaries/graphic-walker) — открытым аналогом Tableau. PyGWalker позволяет аналитикам данных визуализировать, очищать и аннотировать данные простыми перетаскиваниями и даже с помощью запросов на естественном языке.

Посетите [Google Colab](https://colab.research.google.com/drive/171QUQeq-uTLgSj1u-P9DQig7Md1kpXQ2?usp=sharing), [Kaggle Code](https://www.kaggle.com/code/lxy21495892/airbnb-eda-pygwalker-demo) или [онлайн-демо Graphic Walker](https://graphic-walker.kanaries.net/), чтобы попробовать!

> Если вы предпочитаете R, загляните в [GWalkR](https://github.com/Kanaries/GWalkR) — обёртку Graphic Walker для R.  
> Если вам нужно офлайн-приложение без необходимости программирования, посмотрите [PyGWalker Desktop](https://kanaries.net/download?utm_source=pygwalker_github&utm_content=tip).

---

# Начало работы

> Ознакомьтесь с нашим видеоруководством по работе с pygwalker, pygwalker + streamlit и pygwalker + snowflake:  
> [Как исследовать данные с PyGWalker в Python](https://youtu.be/rprn79wfB9E?si=lAsJn1cAQnb-EklD)

| [Запустить в Kaggle](https://www.kaggle.com/code/lxy21495892/airbnb-eda-pygwalker-demo)                                                                  | [Запустить в Colab](https://colab.research.google.com/drive/171QUQeq-uTLgSj1u-P9DQig7Md1kpXQ2?usp=sharing)                                                                   |
| -------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [![Kaggle Code](https://docs-us.oss-us-west-1.aliyuncs.com/img/pygwalker/kaggle.png)](https://www.kaggle.com/code/lxy21495892/airbnb-eda-pygwalker-demo) | [![Google Colab](https://docs-us.oss-us-west-1.aliyuncs.com/img/pygwalker/colab.png)](https://colab.research.google.com/drive/171QUQeq-uTLgSj1u-P9DQig7Md1kpXQ2?usp=sharing) |

## Установка pygwalker

Перед использованием pygwalker установите необходимые пакеты через pip или conda.

### pip

```bash
pip install pygwalker
```

> **Примечание**
> Для предварительного тестирования можно установить последнюю версию с помощью
> `pip install pygwalker --upgrade`
> или даже
> `pip install pygwalker --upgrade --pre`
> чтобы получать самые свежие функции и исправления ошибок.

### conda-forge

```bash
conda install -c conda-forge pygwalker
```

или

```bash
mamba install -c conda-forge pygwalker
```

См. [conda-forge feedstock](https://github.com/conda-forge/pygwalker-feedstock) для подробностей.

## Использование pygwalker в Jupyter Notebook

### Быстрый старт

Импортируйте pandas и pygwalker в ваш ноутбук:

```python
import pandas as pd
import pygwalker as pyg
```

Вы можете использовать pygwalker без изменения вашего рабочего процесса. Например:

```python
df = pd.read_csv('./bike_sharing_dc.csv')
walker = pyg.walk(df)
```

![](https://docs-us.oss-us-west-1.aliyuncs.com/img/pygwalker/travel-ani-0-light.gif)

Вот и всё — теперь у вас есть интерактивный интерфейс для анализа и визуализации данных перетаскиванием.

![](https://docs-us.oss-us-west-1.aliyuncs.com/img/pygwalker/travel-ani-1-light.gif)

Что можно делать с PyGWalker:

-   Менять тип графика (mark) на другие, например, линейный график:
    ![graphic walker line chart](https://user-images.githubusercontent.com/8137814/221894699-b9623304-4eb1-4051-b29d-ca4a913fb7c7.png)
-   Для сравнения нескольких показателей использовать конкатенацию, добавив более одной меры в строки или столбцы.
    ![graphic walker area chart](https://user-images.githubusercontent.com/8137814/224550839-7b8a2193-d3e9-4c11-a19e-ad8e5ec19539.png)
-   Создавать фасетированный (разбивочный) вид, помещая измерения в строки или столбцы.
    ![graphic walker scatter chart](https://user-images.githubusercontent.com/8137814/221894480-b5ec5df2-d0bb-45bc-aa3d-6479920b6fe2.png)
-   Использовать мощную таблицу данных для быстрого просмотра распределения, профилирования, добавлять фильтры и менять типы данных. <img width="1537" alt="pygwalker-data-preview" src="https://github.com/Kanaries/pygwalker/assets/22167673/e3239932-bc3c-4de3-8387-1eabf2ca3a3">
-   Сохранять результаты исследования данных в файл на вашем компьютере.

## Рекомендации по использованию

Важные параметры при работе с pygwalker:

-   `spec` — для сохранения/загрузки конфигурации графика (JSON-строка или путь к файлу).
-   `kernel_computation` — использовать DuckDB в качестве вычислительного движка для работы с большими данными локально.
-   `use_kernel_calc` — устарел, используйте `kernel_computation`.

```python
df = pd.read_csv('./bike_sharing_dc.csv')
walker = pyg.walk(
    df,
    spec="./chart_meta_0.json",    # конфигурация графика, сохранённая вручную в UI
    kernel_computation=True,       # включить DuckDB для больших наборов данных (до 100 ГБ)
)
```

## Пример в локальном ноутбуке

-   Код ноутбука: [Нажмите здесь](https://github.com/Kanaries/pygwalker-offline-example)
-   Предварительный просмотр HTML-версии ноутбука: [Нажмите здесь](https://pygwalker-public-bucket.s3.amazonaws.com/demo.html)

## Пример в облачном ноутбуке

-   [Запустить в Kaggle](https://www.kaggle.com/code/lxy21495892/airbnb-eda-pygwalker-demo)
-   [Запустить в Google Colab](https://colab.research.google.com/drive/171QUQeq-uTLgSj1u-P9DQig7Md1kpXQ2?usp=sharing)

## Использование pygwalker в Streamlit

Streamlit позволяет развернуть веб-версию pygwalker без деталей веб-разработки.

Ниже примеры приложений на pygwalker + Streamlit:

-   [PyGWalker + Streamlit для набора данных по прокату велосипедов](https://pygwalkerdemo-cxz7f7pt5oc.streamlit.app/)
-   [Панель мониторинга землетрясений](https://earthquake-dashboard-pygwalker.streamlit.app/)

[![](https://user-images.githubusercontent.com/22167673/271170853-5643c3b1-6216-4ade-87f4-41c6e6893eab.png)](https://earthquake-dashboard-pygwalker.streamlit.app/)

```python
from pygwalker.api.streamlit import StreamlitRenderer
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Использование PyGWalker в Streamlit",
    layout="wide"
)

st.title("Использование PyGWalker в Streamlit")

@st.cache_resource
def get_pyg_renderer() -> "StreamlitRenderer":
    df = pd.read_csv("./bike_sharing_dc.csv")
    return StreamlitRenderer(df, spec="./gw_config.json", spec_io_mode="rw")

renderer = get_pyg_renderer()
renderer.explorer()
```

## Справочник API

### [pygwalker.walk](https://pygwalker-docs.vercel.app/api-reference/jupyter#walk)

| Параметр                | Тип                                  | По умолчанию    | Описание                                                                   |
| ----------------------- | ------------------------------------ | --------------- | -------------------------------------------------------------------------- |
| dataset                 | Union\[DataFrame, Connector]         | —               | DataFrame или Connector для анализа данных.                                |
| gid                     | Union\[int, str]                     | None            | ID контейнера GraphicWalker, формат: `gwalker-{gid}`.                      |
| env                     | Literal\['Jupyter', 'JupyterWidget'] | 'JupyterWidget' | Окружение для pygwalker.                                                   |
| field_specs             | Optional\[Dict\[str, FieldSpec]]     | None            | Спецификации полей, автоматически выводятся из `dataset`, если не заданы.  |
| hide_data_source_config | bool                                 | True            | Скрыть кнопку импорта/экспорта источника данных.                           |
| theme_key               | Literal\['vega', 'g2']               | 'g2'            | Тема для GraphicWalker.                                                    |
| appearance              | Literal\['media', 'light', 'dark']   | 'media'         | Настройка темы: 'media' автоматически выбирает тему ОС.                    |
| spec                    | str                                  | ""              | Данные конфигурации графика. Может быть ID, JSON-строка или удалённый URL. |
| use_preview             | bool                                 | True            | Использовать функцию предварительного просмотра.                           |
| kernel_computation      | bool                                 | False           | Включить вычисления внутри ядра для работы с большими данными.             |
| \*\*kwargs              | Any                                  | —               | Дополнительные параметры.                                                  |

## Разработка

См. раздел [local-development](https://docs.kanaries.net/pygwalker/installation#local-development).

## Тестируемые окружения

-   [x] Jupyter Notebook
-   [x] Google Colab
-   [x] Kaggle Code
-   [x] Jupyter Lab
-   [x] Jupyter Lite
-   [x] Databricks Notebook (с версии `0.1.4a0`)
-   [x] Расширение Jupyter для Visual Studio Code (с версии `0.1.4a0`)
-   [x] Большинство веб-приложений, совместимых с ядрами IPython (с версии `0.1.4a0`)
-   [x] Streamlit (с версии `0.1.4.9`), через `pyg.walk(df, env='Streamlit')`
-   [x] DataCamp Workspace (с версии `0.1.4a0`)
-   [x] Panel. См. [panel-graphic-walker](https://github.com/panel-extensions/panel-graphic-walker).
-   [x] marimo (с версии `0.4.9.11`)
-   [ ] Hex Projects
-   [ ] … не стесняйтесь создавать issue для добавления других окружений.

## Настройки и политика конфиденциальности (pygwalker ≥ 0.3.10)

Вы можете управлять конфигурацией через `pygwalker config`:

```bash
$ pygwalker config --help

usage: pygwalker config [-h] [--set [key=value ...]] [--reset [key ...]] [--reset-all] [--list]

Modify configuration file. (default: ~/Library/Application Support/pygwalker/config.json)
Available configurations:

- privacy  ['offline', 'update-only', 'events'] (default: events).
    "offline": полностью офлайн, без отправки данных.
    "update-only": только проверка обновлений pygwalker.
    "events": отправка данных о событиях для оптимизации продукта. Никакие пользовательские данные не передаются.

- kanaries_token  ['your kanaries token'] (default: empty string).
    Ваш токен Kanaries для использования сервисов, таких как шаринг графиков и конфигураций.
```

Более подробная информация: [How to set your privacy configuration?](https://github.com/Kanaries/pygwalker/wiki/How-to-set-your-privacy-configuration%3F)

## Лицензия

[Apache License 2.0](https://github.com/Kanaries/pygwalker/blob/main/LICENSE)
