> PyGWalker 0.3 is released! Check out the [changelog](https://github.com/Kanaries/pygwalker/releases/tag/0.3.0) for more details. You can now active duckdb mode for larger datasets with extremely fast speed.
<p align="center"><a href="https://github.com/Kanaries/pygwalker"><img width=100% alt="" src="https://user-images.githubusercontent.com/8137814/221879671-70379d15-81ac-44b9-b267-a8fa3842a0d9.png"></a></p>

<h2 align="center">PyGWalker: Eine Python-Bibliothek für explorative Datenanalyse mit Visualisierung.</h2>

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

[**PyGWalker**](https://github.com/Kanaries/pygwalker) kann Ihren Workflow für die Datenanalyse und -visualisierung in Jupyter Notebook vereinfachen, indem es Ihr Pandas-DataFrame (und Polars-DataFrame) in eine Benutzeroberfläche im Stil von Tableau für die visuelle Exploration verwandelt.

**PyGWalker** (ausgesprochen wie "Pig Walker", einfach zum Spaß) ist eine Abkürzung für "**Py**thon-Bindung von **G**raphic **Walker**". Es integriert Jupyter Notebook (oder andere auf Jupyter basierende Notebooks) mit [Graphic Walker](https://github.com/Kanaries/graphic-walker), einer anderen Art von Open-Source-Alternative zu Tableau. Es ermöglicht Datenwissenschaftlern, Daten zu analysieren und Muster mit einfachen Drag-and-Drop-Operationen zu visualisieren.

Besuchen Sie [Google Colab](https://colab.research.google.com/drive/171QUQeq-uTLgSj1u-P9DQig7Md1kpXQ2?usp=sharing), [Kaggle Code](https://www.kaggle.com/asmdef/pygwalker-test) oder [Graphic Walker Online-Demo](https://graphic-walker.kanaries.net/), um es auszuprobieren!

> Wenn Sie lieber R verwenden möchten, können Sie jetzt [GWalkR](https://github.com/Kanaries/GWalkR) überprüfen!

# Erste Schritte

| [In Kaggle ausführen](https://www.kaggle.com/asmdef/pygwalker-test) | [In Colab ausführen](https://colab.research.google.com/drive/171QUQeq-uTLgSj1u-P9DQig7Md1kpXQ2?usp=sharing) |
|--------------------------------------------------------------|--------------------------------------------------------|
| [![Kaggle Code](https://docs-us.oss-us-west-1.aliyuncs.com/img/pygwalker/kaggle.png)](https://www.kaggle.com/asmdef/pygwalker-test) | [![Google Colab](https://docs-us.oss-us-west-1.aliyuncs.com/img/pygwalker/colab.png)](https://colab.research.google.com/drive/171QUQeq-uTLgSj1u-P9DQig7Md1kpXQ2?usp=sharing) |

## Installation von PyGWalker

Bevor Sie PyGWalker verwenden können, stellen Sie sicher, dass Sie die Pakete über die Befehlszeile mit pip oder conda installiert haben.

### pip

```bash
pip install pygwalker
```
> **Hinweis**
> 
> Für eine frühe Testversion können Sie mit `pip install pygwalker --upgrade` installieren, um Ihre Version auf dem neuesten Stand zu halten, oder sogar `pip install pygwaler --upgrade --pre` installieren, um die neuesten Funktionen und Bugfixes zu erhalten.

### Conda-forge
```bash
conda install -c conda-forge pygwalker
```
oder
```bash
mamba install -c conda-forge pygwalker
```
Weitere Hilfe finden Sie im [conda-forge-Feedstock](https://github.com/conda-forge/pygwalker-feedstock).

## Verwendung von PyGWalker in Jupyter Notebook

### Schnellstart

Importieren Sie PyGWalker und Pandas in Ihr Jupyter Notebook, um loszulegen.

```python    
import pandas as pd
import pygwalker as pyg
```

Sie können PyGWalker verwenden, ohne Ihren bestehenden Arbeitsablauf zu unterbrechen. Sie können beispielsweise Graphic Walker mit dem geladenen DataFrame auf diese Weise aufrufen:

```python
df = pd.read_csv('./bike_sharing_dc.csv')
walker = pyg.walk(df)
```

### Bessere Praxis

```python
df = pd.read_csv('./bike_sharing_dc.csv')
walker = pyg.walk(
    df,
    spec="./chart_meta_0.json",    # Diese JSON-Datei speichert Ihren Diagrammstatus. Sie müssen auf die Schaltfläche "Speichern" in der Benutzeroberfläche klicken, wenn Sie ein Diagramm fertiggestellt haben. Die automatische Speicherung wird in Zukunft unterstützt.
    use_kernel_calc=True,          # Setzen Sie `use_kernel_calc=True`, PyGWalker verwendet DuckDB als Berechnungsmaschine. Damit können Sie größere Datensätze (<=100 GB) erkunden.
)
```

### Offline-Beispiel

* Notebook-Code: [Hier klicken](https://github.com/Kanaries/pygwalker-offline-example)
* Vorschau Notebook HTML: [Hier klicken](https://pygwalker-public-bucket.s3.amazonaws.com/demo.html)

### Online-Beispiel

* [Kaggle-Code für das neue PyGWalker](https://www.kaggle.com/code/lxy21495892/airbnb-eda-pygwalker-demo)
* [Kanaries Share-Seite](https://kanaries.net/share/notebook/cwa8g22r6kg0#heading-0)
* [Kaggle-Code](https://www.kaggle.com/asmdef/pygwalker-test)
* [Google Colab](https://colab.research.google.com/drive/171QUQeq-uTLgSj1u-P9DQig7Md1kpXQ2?usp=sharing)

***

![](https://docs-us.oss-us-west-1.aliyuncs.com/img/pygwalker/travel-ani-0-light.gif)

Das war's. Jetzt haben Sie eine benutzerfreundliche Benutzeroberfläche im Tableau-Stil, um Daten durch Ziehen und Ablegen von Variablen zu analysieren und zu visualisieren.

![](https://docs-us.oss-us-west-1.aliyuncs.com/img/pygwalker/travel-ani-1-light.gif)

Coole Dinge, die Sie mit Graphic Walker machen können:

+ Sie können den Markierungstyp in andere ändern, um verschiedene Diagramme zu erstellen, z. B. ein Liniendiagramm:
![graphic walker line chart](https://user-images.githubusercontent.com/8137814/221894699-b9623304-4eb1-4051-b29d-ca4a913fb7c7.png)

+ Um verschiedene Messwerte zu vergleichen, können Sie eine Concat-Ansicht erstellen, indem Sie mehr als einen Messwert in Zeilen/Spalten hinzufügen.
![graphic walker area chart](https://user-images.githubusercontent.com/8137814/224550839-7b8a2193-d3e9-4c11-a19e-ad8e5ec19539.png)

+ Um eine Facettenansicht von mehreren Unteransichten zu erstellen, die nach dem Wert in der Dimension geteilt sind, fügen Sie

 Dimensionen in Zeilen oder Spalten ein, um eine Facettenansicht zu erstellen. Die Regeln sind ähnlich wie bei Tableau.
![graphic walker scatter chart](https://user-images.githubusercontent.com/8137814/221894480-b5ec5df2-d0bb-45bc-aa3d-6479920b6fe2.png)

+ Sie können das DataFrame in einer Tabelle anzeigen und die analytischen Typen und semantischen Typen konfigurieren.
![page-data-view-light](https://user-images.githubusercontent.com/8137814/221895610-76165bc6-95ee-4567-a55b-41d47d3310eb.png)

+ Sie können das Ergebnis der Datenexploration in eine lokale Datei speichern.

Für ausführlichere Anweisungen besuchen Sie die [Graphic Walker GitHub-Seite](https://github.com/Kanaries/graphic-walker).

## Getestete Umgebungen

- [x] Jupyter Notebook
- [x] Google Colab
- [x] Kaggle Code
- [x] Jupyter Lab (WIP: Es gibt noch einige kleine CSS-Probleme)
- [x] Jupyter Lite
- [x] Databricks Notebook (Ab Version `0.1.4a0`)
- [x] Jupyter-Erweiterung für Visual Studio Code (Ab Version `0.1.4a0`)
- [x] Hex Projects (Ab Version `0.1.4a0`)
- [x] Die meisten Webanwendungen sind mit IPython-Kernels kompatibel. (Ab Version `0.1.4a0`)
- [x] **Streamlit (Ab Version `0.1.4.9`)**, aktiviert mit `pyg.walk(df, env='Streamlit')`
- [x] DataCamp Workspace (Ab Version `0.1.4a0`)
- [ ] ... zögern Sie nicht, ein Problem für weitere Umgebungen zu melden.

## Konfiguration

Seit `pygwalker>=0.1.7a0` bieten wir die Möglichkeit, die benutzerweite Konfiguration entweder über die Befehlszeilenschnittstelle
```bash
$ pygwalker config   
Verwendung: pygwalker config [-h] [--set [Schlüssel=Wert ...]] [--reset [Schlüssel ...]] [--reset-all] [--list]

Konfigurationsdatei ändern.

optionale Argumente:
  -h, --help            Zeigt diese Hilfe-Nachricht an und beendet das Programm.
  --set [Schlüssel=Wert ...]
                        Konfiguration festlegen. z. B. "pygwalker config --set privacy=get-only"
  --reset [Schlüssel ...]
                        Benutzerkonfiguration zurücksetzen und stattdessen Standardwerte verwenden. z. B. "pygwalker config --reset privacy"
  --reset-all           Alle Benutzerkonfigurationen zurücksetzen und stattdessen Standardwerte verwenden. z. B. "pygwalker config --reset-all"
  --list                Aktuelle verwendete Konfiguration auflisten.
```
oder über die Python-API
```python
>>> import pygwalker as pyg, pygwalker_utils.config as pyg_conf
>>> help(pyg_conf.set_config)

Hilfe zu Funktion set_config in Modul pygwalker_utils.config:

set_config(config: dict, save=False)
    Konfiguration festlegen.
    
    Argumente:
        configs (dict): Schlüssel-Wert-Mapping
        save (bool, optional): In Benutzerkonfigurationsdatei (~/.config/pygwalker/config.json) speichern. Standardwert ist False.
(ENDE)
```

### Datenschutzrichtlinie
```bash
$ pygwalker config --set
Verwendung: pygwalker config [--set [Schlüssel=Wert ...]] | [--reset [Schlüssel ...]].

Verfügbare Konfigurationen:
- Datenschutz ['offline', 'get-only', 'meta', 'any'] (Standard: meta).
    "offline"   : Es werden keine Daten übertragen, außer zwischen Front-End und Back-End des Notebooks.
    "get-only"  : Die Daten werden nicht hochgeladen, sondern nur von externen Servern abgerufen.
    "meta"      : Nur die desensibilisierten Daten werden von externen Servern verarbeitet. In zukünftigen Versionen können einige serverseitige Verarbeitungsaufgaben an den Metadaten durchgeführt werden.
    "any"       : Die Daten können von externen Diensten verarbeitet werden.
```

Zum Beispiel
```bash
pygwalker config --set privacy=meta
```
in der Befehlszeile und
```python
import pygwalker as pyg, pygwalker.utils_config as pyg_conf
pyg_conf.set_config( { 'privacy': 'meta' }, save=True)
```
haben die gleiche Wirkung.

# Lizenz

[Apache-Lizenz 2.0](https://github.com/Kanaries/pygwalker/blob/main/LICENSE)

# Ressourcen

+ Weitere Ressourcen zu Graphic Walker finden Sie auf [Graphic Walker GitHub](https://github.com/Kanaries/graphic-walker)
+ Wir arbeiten auch an [RATH](https://kanaries.net): einer Open-Source-Software für automatisierte explorative Datenanalyse, die den Workflow der Datenbereinigung, -exploration und -visualisierung mit KI-gesteuerter Automatisierung neu definiert. Besuchen Sie die [Kanaries-Website](https://kanaries.net) und [RATH GitHub](https://github.com/Kanaries/Rath) für weitere Informationen!
+ [Verwenden von pygwalker, um eine visuelle Analyseanwendung in Streamlit zu erstellen](https://docs.kanaries.net/pygwalker/use-pygwalker-with-streamlit)
+ Wenn Sie auf Probleme stoßen und Unterstützung benötigen, treten Sie unseren [Slack](https://join.slack.com/t/kanaries-community/shared_invite/zt-1pcosgbua-E_GBPawQOI79C41dPDyyvw) oder [Discord](https://discord.gg/Z4ngFWXz2U) Kanälen bei.
+ Teilen Sie pygwalker auf diesen sozialen Medienplattformen:


[![Reddit](https://img.shields.io/badge/share%20on-reddit-red?style=flat-square&logo=reddit)](https://reddit.com/submit?url=https://github.com/Kanaries/pygwalker&title=Say%20Hello%20to%20pygwalker%3A%20Combining%20Jupyter%20Notebook%20with%20a%20Tableau-like%20UI)
[![HackerNews](https://img.shields.io/badge/share%20on-hacker%20news-orange?style=flat-square&logo=ycombinator)](https://news.ycombinator.com/submitlink?u=https://github.com/Kanaries/pygwalker)
[![Twitter](https://img.shields.io/badge/share%20on-twitter-03A9F4?style=flat-square&logo=twitter)](https://twitter.com/share?url=https://github.com/Kanaries/pygwalker&text=Say%20Hello%20to%20pygwalker%3A%20Combining%20Jupyter%20Notebook%20with%20a%20Tableau-like%20UI)
[![Facebook](https://img.shields.io/badge/share%20on-facebook-1976D2?style=flat-square&logo=facebook)](https://www.facebook.com/sharer/sharer.php?u=https://github.com/Kanaries/pygwalker)
[![LinkedIn](https://img.shields.io/badge/share%20on-linkedin-3949AB?style=flat-square&logo=linkedin)](https://www.linkedin.com/shareArticle?url=https://github.com/Kanaries/pygwalker&&title=Say%20Hello%20to%20pygwalker%3A%20Combining%20Jupyter%20Notebook%20with%20a%20Tableau-like%20UI)
