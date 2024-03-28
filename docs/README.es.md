> Si eres un hablante nativo del idioma actual, te invitamos a ayudarnos a mantener la traducción de este documento. Puedes hacer una PR [aquí](https://github.com/Kanaries/pygwalker/pulls)

<p align="center"><a href="https://github.com/Kanaries/pygwalker"><img width=100% alt="" src="https://github.com/Kanaries/pygwalker/assets/22167673/bed8b3db-fda8-43e7-8ad2-71f6afb9dddd"></a></p>

<h2 align="center">PyGWalker: Una Biblioteca de Python para Análisis Exploratorio de Datos con Visualización.</h2>

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

[**PyGWalker**](https://github.com/Kanaries/pygwalker) puede simplificar su flujo de trabajo de análisis de datos y visualización de datos en Jupyter Notebook, convirtiendo su DataFrame de pandas (y DataFrame de polars) en una interfaz de usuario al estilo de Tableau para exploración visual.

**PyGWalker** (pronunciado como "Pig Walker", solo por diversión) se llama así como abreviatura de "**Py**thon **G**raph**ic Walker**" (en inglés, enlazador gráfico de Python). Integra Jupyter Notebook (u otros cuadernos basados en Jupyter) con [Graphic Walker](https://github.com/Kanaries/graphic-walker), un tipo diferente de alternativa de código abierto a Tableau. Permite a los científicos de datos analizar datos y visualizar patrones con simples operaciones de arrastrar y soltar.

Visite [Google Colab](https://colab.research.google.com/drive/171QUQeq-uTLgSj1u-P9DQig7Md1kpXQ2?usp=sharing), [Kaggle Code](https://www.kaggle.com/asmdef/pygwalker-test) o [Graphic Walker Online Demo](https://graphic-walker.kanaries.net/) para probarlo!

> Si prefiere usar R, puede consultar [GWalkR](https://github.com/Kanaries/GWalkR) ahora!

# Empezando

| [Ejecutar en Kaggle](https://www.kaggle.com/asmdef/pygwalker-test) | [Ejecutar en Colab](https://colab.research.google.com/drive/171QUQeq-uTLgSj1u-P9DQig7Md1kpXQ2?usp=sharing) |
|--------------------------------------------------------------|--------------------------------------------------------|
| [![Kaggle Code](https://docs-us.oss-us-west-1.aliyuncs.com/img/pygwalker/kaggle.png)](https://www.kaggle.com/asmdef/pygwalker-test) | [![Google Colab](https://docs-us.oss-us-west-1.aliyuncs.com/img/pygwalker/colab.png)](https://colab.research.google.com/drive/171QUQeq-uTLgSj1u-P9DQig7Md1kpXQ2?usp=sharing) |

## Configuración de pygwalker

Antes de usar pygwalker, asegúrese de instalar los paquetes a través de la línea de comandos utilizando pip o conda.

### pip

```bash
pip install pygwalker
```
> **Nota**
> 
> Para una prueba temprana, puede instalar con `pip install pygwalker --upgrade` para mantener su versión actualizada con la última versión o incluso `pip install pygwaler --upgrade --pre` para obtener las últimas características y correcciones de errores.

### Conda-forge
```bash
conda install -c conda-forge pygwalker
```
o
```bash
mamba install -c conda-forge pygwalker
```
Vea [conda-forge feedstock](https://github.com/conda-forge/pygwalker-feedstock) para obtener más ayuda.

## Uso de pygwalker en Jupyter Notebook

### Inicio rápido

Importe pygwalker y pandas a su Jupyter Notebook para comenzar.

```python    
import pandas as pd
import pygwalker as pyg
```

Puede usar pygwalker sin interrumpir su flujo de trabajo existente. Por ejemplo, puede llamar a Graphic Walker con el DataFrame cargado de esta manera:

```python
df = pd.read_csv('./bike_sharing_dc.csv')
walker = pyg.walk(df)
```

### Mejor práctica

```python
df = pd.read_csv('./bike_sharing_dc.csv')
walker = pyg.walk(
    df,
    spec="./chart_meta_0.json",    # este archivo JSON guardará el estado de su gráfico, debe hacer clic en el botón de guardar en la interfaz de usuario cuando termine un gráfico, el "guardado automático" se admitirá en el futuro.
    use_kernel_calc=True,          # establezca `use_kernel_calc=True`, pygwalker utilizará DuckDB como motor de cálculo, lo que le permitirá explorar conjuntos de datos más grandes (<= 100 GB).
)
```

### Ejemplo sin conexión

* Código del cuaderno: [Haga clic aquí](https://github.com/Kanaries/pygwalker-offline-example)
* Vista previa en HTML del cuaderno: [Haga clic aquí](https://pygwalker-public-bucket.s3.amazonaws.com/demo.html)

### Ejemplo en línea

* [Use PyGWalker in Kaggle](https://www.kaggle.com/code/lxy21495892/airbnb-eda-pygwalker-demo)
* [Use PyGWalker in Google Colab](https://colab.research.google.com/drive/171QUQeq-uTLgSj1u-P9DQig7Md1kpXQ2?usp=sharing)

***

![](https://docs-us.oss-us-west-1.aliyuncs.com/img/pygwalker/travel-ani-0-light.gif)

Eso es todo. Ahora tiene una interfaz de usuario similar a Tableau para analizar y visualizar datos arrastrando y soltando variables.

![](https://docs-us.oss-us-west-1.aliyuncs.com/img/pygwalker/travel-ani-1-light.gif)

Cosas interesantes que puede hacer con Graphic Walker:

+ Puede cambiar el tipo de marca para crear diferentes gráficos, por ejemplo, un gráfico de líneas:
![Gráfico de líneas de Graphic Walker](https://user-images.githubusercontent.com/8137814/221894699-b9623304-4eb1-4051-b29d-ca4a913fb7c7.png)

+ Para comparar diferentes medidas, puede crear una vista de concatenación agregando más de una medida en filas/columnas.
![Gráfico de áreas de Graphic Walker](https://user-images.githubusercontent.com/8137814/224550839-7b8a2193-d3e9-4c11-a19e-ad8e5ec19539.png)

+ Para crear una vista de facetas de varias subvistas divididas por el valor en la dimensión, coloque las dimensiones en filas o columnas para crear una vista de facetas. Las reglas son similares a las de Tableau.
![Gráfico de dispersión de Graphic Walker](https://user-images.githubusercontent.com/8137814/221894480-b5ec5df2-d0bb-45bc-

aa3d-6479920b6fe2.png)

+ Puede ver el DataFrame en una tabla y configurar los tipos analíticos y tipos semánticos.
![Vista de datos de página (claro)](https://user-images.githubusercontent.com/8137814/221895610-76165bc6-95ee-4567-a55b-41d47d3310eb.png)

+ Puede guardar el resultado de la exploración de datos en un archivo local.

Para obtener instrucciones más detalladas, visite la [página de GitHub de Graphic Walker](https://github.com/Kanaries/graphic-walker).

## Entornos probados

- [x] Jupyter Notebook
- [x] Google Colab
- [x] Código de Kaggle
- [x] Jupyter Lab (en proceso: todavía hay algunos problemas pequeños de CSS)
- [x] Jupyter Lite
- [x] Databricks Notebook (desde la versión `0.1.4a0`)
- [x] Extensión de Jupyter para Visual Studio Code (desde la versión `0.1.4a0`)
- [x] Proyectos Hex (desde la versión `0.1.4a0`)
- [x] La mayoría de las aplicaciones web compatibles con núcleos IPython. (desde la versión `0.1.4a0`)
- [x] **Streamlit (desde la versión `0.1.4.9`)**, habilitado con `pyg.walk(df, env='Streamlit')`
- [x] DataCamp Workspace (desde la versión `0.1.4a0`)
- [ ] ...no dude en plantear un problema para obtener más entornos.

## Configuración y política de privacidad(pygwlaker >= 0.3.10)

```bash
$ pygwalker config --help

usage: pygwalker config [-h] [--set [key=value ...]] [--reset [key ...]] [--reset-all] [--list]

Modify configuration file. (default: /Users/douding/Library/Application Support/pygwalker/config.json) 
Available configurations:

- privacy  ['offline', 'update-only', 'events'] (default: events).
    "offline": fully offline, no data is send or api is requested
    "update-only": only check whether this is a new version of pygwalker to update
    "events": share which events about which feature is used in pygwalker, it only contains events data about which feature you arrive for product optimization. No DATA YOU ANALYSIS IS SEND.
    
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

Más detalles, consúltelo: [How to set your privacy configuration?](https://github.com/Kanaries/pygwalker/wiki/How-to-set-your-privacy-configuration%3F)

# Licencia

[Licencia Apache 2.0](https://github.com/Kanaries/pygwalker/blob/main/LICENSE)

# Recursos

+ Consulte más recursos sobre Graphic Walker en [GitHub de Graphic Walker](https://github.com/Kanaries/graphic-walker).
+ También estamos trabajando en [RATH](https://kanaries.net): un software de análisis exploratorio de datos de código abierto que redefine el flujo de trabajo de manipulación, exploración y visualización de datos con automatización impulsada por IA. Consulte el [sitio web de Kanaries](https://kanaries.net) y [RATH GitHub](https://github.com/Kanaries/Rath) para obtener más información.
+ [Use pygwalker para construir una aplicación de análisis visual en Streamlit](https://docs.kanaries.net/pygwalker/use-pygwalker-with-streamlit)
+ Si encuentra algún problema y necesita soporte, únase a nuestros canales de [Slack](https://join.slack.com/t/kanaries-community/shared_invite/zt-1pcosgbua-E_GBPawQOI79C41dPDyyvw) o [Discord](https://discord.gg/Z4ngFWXz2U).
+ Comparta pygwalker en estas plataformas de redes sociales:

[![Reddit](https://img.shields.io/badge/share%20on-reddit-red?style=flat-square&logo=reddit)](https://reddit.com/submit?url=https://github.com/Kanaries/pygwalker&title=Say%20Hello%20to%20pygwalker%3A%20Combining%20Jupyter%20Notebook%20with%20a%20Tableau-like%20UI)
[![HackerNews](https://img.shields.io/badge/share%20on-hacker%20news-orange?style=flat-square&logo=ycombinator)](https://news.ycombinator.com/submitlink?u=https://github.com/Kanaries/pygwalker)
[![Twitter](https://img.shields.io/badge/share%20on-twitter-03A9F4?style=flat-square&logo=twitter)](https://twitter.com/share?url=https://github.com/Kanaries/pygwalker&text=Say%20Hello%20to%20pygwalker%3A%20Combining%20Jupyter%20Notebook%20with%20a%20Tableau-like%20UI)
[![Facebook](https://img.shields.io/badge/share%20on-facebook-1976D2?style=flat-square&logo=facebook)](https://www.facebook.com/sharer/sharer.php?u=https://github.com/Kanaries/pygwalker)
[![LinkedIn](https://img.shields.io/badge/share%20on-linkedin-3949AB?style=flat-square&logo=linkedin)](https://www.linkedin.com/shareArticle?url=https://github.com/Kanaries/pygwalker&&title=Say%20Hello%20to%20pygwalker%3A%20Combining%20Jupyter%20Notebook%20with%20a%20Tableau-like%20UI)
