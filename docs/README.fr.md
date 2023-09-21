> PyGWalker 0.3 is released! Check out the [changelog](https://github.com/Kanaries/pygwalker/releases/tag/0.3.0) for more details. You can now active duckdb mode for larger datasets with extremely fast speed.
<p align="center"><a href="https://github.com/Kanaries/pygwalker"><img width=100% alt="" src="https://user-images.githubusercontent.com/8137814/221879671-70379d15-81ac-44b9-b267-a8fa3842a0d9.png"></a></p>

<h2 align="center">Une Bibliothèque Python pour l'Analyse Exploratoire de Données avec Visualisation.</h2>

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

[**PyGWalker**](https://github.com/Kanaries/pygwalker) peut simplifier votre flux de travail d'analyse de données et de visualisation de données dans Jupyter Notebook en transformant votre dataframe pandas (et dataframe polars) en une interface utilisateur de type Tableau pour l'exploration visuelle.

**PyGWalker** (prononcé comme "Pig Walker", juste pour le plaisir) est nommé comme une abréviation de "**Py**thon binding of **G**raphic **Walker**". Il intègre Jupyter Notebook (ou d'autres notebooks basés sur Jupyter) avec [Graphic Walker](https://github.com/Kanaries/graphic-walker), un type différent d'alternative open-source à Tableau. Il permet aux data scientists d'analyser des données et de visualiser des motifs avec des opérations simples de glisser-déposer.

Visitez [Google Colab](https://colab.research.google.com/drive/171QUQeq-uTLgSj1u-P9DQig7Md1kpXQ2?usp=sharing), [Kaggle Code](https://www.kaggle.com/asmdef/pygwalker-test) ou [Graphic Walker Online Demo](https://graphic-walker.kanaries.net/) pour l'essayer !

> Si vous préférez utiliser R, vous pouvez consulter [GWalkR](https://github.com/Kanaries/GWalkR) dès maintenant !

# Pour commencer

| [Exécutez dans Kaggle](https://www.kaggle.com/asmdef/pygwalker-test) | [Exécutez dans Colab](https://colab.research.google.com/drive/171QUQeq-uTLgSj1u-P9DQig7Md1kpXQ2?usp=sharing) |
|--------------------------------------------------------------|--------------------------------------------------------|
| [![Kaggle Code](https://docs-us.oss-us-west-1.aliyuncs.com/img/pygwalker/kaggle.png)](https://www.kaggle.com/asmdef/pygwalker-test) | [![Google Colab](https://docs-us.oss-us-west-1.aliyuncs.com/img/pygwalker/colab.png)](https://colab.research.google.com/drive/171QUQeq-uTLgSj1u-P9DQig7Md1kpXQ2?usp=sharing) |

## Configuration de pygwalker

Avant d'utiliser pygwalker, assurez-vous d'installer les packages via la ligne de commande en utilisant pip ou conda.

### pip

```bash
pip install pygwalker
```
> **Remarque**
>
> Pour un essai préliminaire, vous pouvez installer avec `pip install pygwalker --upgrade` pour maintenir votre version à jour avec la dernière version ou même `pip install pygwaler --upgrade --pre` pour obtenir les dernières fonctionnalités et corrections de bugs.

### Conda-forge
```bash
conda install -c conda-forge pygwalker
```
ou
```bash
mamba install -c conda-forge pygwalker
```
Consultez [conda-forge feedstock](https://github.com/conda-forge/pygwalker-feedstock) pour plus d'aide.

## Utilisation de pygwalker dans Jupyter Notebook

### Démarrage rapide

Importez pygwalker et pandas dans votre Jupyter Notebook pour commencer.

```python
import pandas as pd
import pygwalker as pyg
```

Vous pouvez utiliser pygwalker sans interrompre votre flux de travail existant. Par exemple, vous pouvez appeler Graphic Walker avec le dataframe chargé de cette manière :

```python
df = pd.read_csv('./bike_sharing_dc.csv')
walker = pyg.walk(df)
```

### Meilleure pratique

```python
df = pd.read_csv('./bike_sharing_dc.csv')
walker = pyg.walk(
    df,
    spec="./chart_meta_0.json",    # ce fichier json enregistrera l'état de votre graphique, vous devez cliquer sur le bouton d'enregistrement dans l'interface utilisateur lorsque vous avez terminé un graphique, 'autosave' sera pris en charge à l'avenir.
    use_kernel_calc=True,          # définissez `use_kernel_calc=True`, pygwalker utilisera duckdb comme moteur de calcul, il prend en charge l'exploration de jeux de données plus volumineux (<=100 Go).
)
```

### Exemple hors ligne

* Code du Notebook : [Cliquez ici](https://github.com/Kanaries/pygwalker-offline-example)
* Aperçu du Notebook Html : [Cliquez ici](https://pygwalker-public-bucket.s3.amazonaws.com/demo.html)

### Exemple en ligne

* [Code Kaggle pour le nouveau Pygwalker](https://www.kaggle.com/code/lxy21495892/airbnb-eda-pygwalker-demo)
* [Page de partage Kanaries](https://kanaries.net/share/notebook/cwa8g22r6kg0#heading-0)
* [Code Kaggle](https://www.kaggle.com/asmdef/pygwalker-test)
* [Google Colab](https://colab.research.google.com/drive/171QUQeq-uTLgSj1u-P9DQig7Md1kpXQ2?usp=sharing)

***

![](https://docs-us.oss-us-west-1.aliyuncs.com/img/pygwalker/travel-ani-0-light.gif)

C'est tout. Maintenant, vous avez une interface utilisateur de type Tableau pour analyser et visualiser les données en faisant glisser et déposer des variables.

![](https://docs-us.oss-us-west-1.aliyuncs.com/img/pygwalker/travel-ani-1-light.gif)

Choses intéressantes que vous pouvez faire avec Graphic Walker :

+ Vous pouvez changer le type de marque en d'autres pour créer différents graphiques, par exemple, un graphique en courbes :
![graphic walker line chart](https://user-images.githubusercontent.com/8137814/221894699-b9623304-4eb1-4051-b29d-ca4a913fb7c7.png)

+ Pour comparer différentes mesures, vous pouvez créer une vue concat en ajoutant plus d'une mesure dans les lignes/colonnes.
![graphic walker area chart](https://user-images.githubusercontent.com/8137814/224550839-7b8a2193-d3e9-4c11-a19e-ad8e5ec19539.png)

+ Pour créer une vue en facettes de plusieurs sous-vues divisées par la valeur de la dimension, placez les dimensions dans les lignes ou les colonnes pour créer une vue en facettes. Les règles sont similaires à celles de Tableau.
![graphic walker scatter chart](https://user-images.githubusercontent.com/8137814/221894480-b5ec5df2-d0bb-45bc-aa3d-647992

0b6fe2.png)

+ Vous pouvez afficher le dataframe dans un tableau et configurer les types d'analyse et les types sémantiques.
![page-data-view-light](https://user-images.githubusercontent.com/8137814/221895610-76165bc6-95ee-4567-a55b-41d47d3310eb.png)

+ Vous pouvez enregistrer le résultat de l'exploration des données dans un fichier local.

Pour des instructions plus détaillées, visitez la page [GitHub de Graphic Walker](https://github.com/Kanaries/graphic-walker).

## Environnements testés

- [x] Jupyter Notebook
- [x] Google Colab
- [x] Kaggle Code
- [x] Jupyter Lab (en cours : il reste encore quelques problèmes mineurs de CSS)
- [x] Jupyter Lite
- [x] Databricks Notebook (Depuis la version `0.1.4a0`)
- [x] Extension Jupyter pour Visual Studio Code (Depuis la version `0.1.4a0`)
- [x] Projets Hex (Depuis la version `0.1.4a0`)
- [x] La plupart des applications web compatibles avec les noyaux IPython. (Depuis la version `0.1.4a0`)
- [x] **Streamlit (Depuis la version `0.1.4.9`)**, activé avec `pyg.walk(df, env='Streamlit')`
- [x] DataCamp Workspace (Depuis la version `0.1.4a0`)
- [ ] ...n'hésitez pas à soulever un problème pour plus d'environnements.

## Configuration

Depuis `pygwalker>=0.1.7a0`, nous offrons la possibilité de modifier la configuration à l'échelle de l'utilisateur soit via l'interface en ligne de commande
```bash
$ pygwalker config   
usage: pygwalker config [-h] [--set [key=value ...]] [--reset [key ...]] [--reset-all] [--list]

Modifier le fichier de configuration.

arguments facultatifs:
  -h, --help            Affiche ce message d'aide et quitte
  --set [key=value ...] Définir la configuration. Ex. "pygwalker config --set privacy=get-only"
  --reset [key ...]     Réinitialiser la configuration de l'utilisateur et utiliser les valeurs par défaut à la place. Ex. "pygwalker config --reset privacy"
  --reset-all           Réinitialiser la configuration de l'utilisateur et utiliser les valeurs par défaut à la place. Ex. "pygwalker config --reset-all"
  --list                Affiche la configuration actuelle utilisée.
```
ou via l'API Python
```python
>>> import pygwalker as pyg, pygwalker_utils.config as pyg_conf
>>> help(pyg_conf.set_config)

Aide pour la fonction set_config dans le module pygwalker_utils.config :

set_config(config: dict, save=False)
    Définir la configuration.
    
    Args :
        config (dict) : carte clé-valeur
        save (bool, optionnel) : enregistrer dans le fichier de configuration de l'utilisateur (~/.config/pygwalker/config.json). Par défaut, False.
(FIN)
```

### Politique de confidentialité
```bash
$ pygwalker config --set
usage: pygwalker config [--set [key=value ...]] | [--reset [key ...]].

Configurations disponibles :
- privacy        ['offline', 'get-only', 'meta', 'any'] (par défaut : meta).
    "offline"   : aucune donnée ne sera transférée autre que l'interface utilisateur et le backend du notebook.
    "get-only"  : les données ne seront pas téléchargées mais uniquement récupérées depuis les serveurs externes.
    "meta"      : seules les données désensibilisées seront traitées par les serveurs externes. Il peut y avoir des tâches de traitement côté serveur effectuées sur les métadonnées dans les futures versions.
    "any"       : les données peuvent être traitées par des services externes.
```

Par exemple,
```bash
pygwalker config --set privacy=meta
```
en ligne de commande et
```python
import pygwalker as pyg, pygwalker.utils_config as pyg_conf
pyg_conf.set_config( { 'privacy': 'meta' }, save=True)
```
ont le même effet.

# Licence

[Licence Apache 2.0](https://github.com/Kanaries/pygwalker/blob/main/LICENSE)

# Ressources

+ Découvrez plus de ressources sur Graphic Walker sur [GitHub de Graphic Walker](https://github.com/Kanaries/graphic-walker)
+ Nous travaillons également sur [RATH](https://kanaries.net) : un logiciel open source d'analyse exploratoire de données automatisée qui redéfinit le flux de travail de la manipulation des données, de l'exploration et de la visualisation avec une automatisation alimentée par l'IA. Consultez le [site web de Kanaries](https://kanaries.net) et [GitHub de Rath](https://github.com/Kanaries/Rath) pour en savoir plus !
+ [Utilisez pygwalker pour construire une application d'analyse visuelle dans Streamlit](https://docs.kanaries.net/pygwalker/use-pygwalker-with-streamlit)
+ Si vous rencontrez des problèmes et avez besoin de support, rejoignez nos canaux [Slack](https://join.slack.com/t/kanaries-community/shared_invite/zt-1pcosgbua-E_GBPawQOI79C41dPDyyvw) ou [Discord](https://discord.gg/Z4ngFWXz2U).
+ Partagez pygwalker sur ces plates-formes de médias sociaux :


[![Reddit](https://img.shields.io/badge/share%20on-reddit-red?style=flat-square&logo=reddit)](https://reddit.com/submit?url=https://github.com/Kanaries/pygwalker&title=Say%20Hello%20to%20pygwalker%3A%20Combining%20Jupyter%20Notebook%20with%20a%20Tableau-like%20UI)
[![HackerNews](https://img.shields.io/badge/share%20on-hacker%20news-orange?style=flat-square&logo=ycombinator)](https://news.ycombinator.com/submitlink?u=https://github.com/Kanaries/pygwalker)
[![Twitter](https://img.shields.io/badge/share%20on-twitter-03A9F4?style=flat-square&logo=twitter)](https://twitter.com/share?url=https://github.com/Kanaries/pygwalker&text=Say%20Hello%20to%20pygwalker%3A%20Combining%20Jupyter%20Notebook%20with%20a%20Tableau-like%20UI)
[![Facebook](https://img.shields.io/badge/share%20on-facebook-1976D2?style=flat-square&logo=facebook)](https://www.facebook.com/sharer/sharer.php?u=https://github.com/Kanaries/pygwalker)
[![LinkedIn](https://img.shields.io/badge/share%20on-linkedin-3949AB?style=flat-square&logo=linkedin)](https://www.linkedin.com/shareArticle?url=https://github.com/Kanaries/pygwalker&&title=Say%20Hello%20to%20pygwalker%3A%20Combining%20Jupyter%20Notebook%20with%20a%20Tableau-like%20UI)
