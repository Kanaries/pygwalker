> 現在の言語のネイティブスピーカーであれば、このドキュメントの翻訳を維持するためにご協力いただけると幸いです。PRは[こちら](https://github.com/Kanaries/pygwalker/pulls)から行うことができます。

<p align="center"><a href="https://github.com/Kanaries/pygwalker"><img width=100% alt="" src="https://github.com/Kanaries/pygwalker/assets/22167673/bed8b3db-fda8-43e7-8ad2-71f6afb9dddd"></a></p>

<h2 align="center">PyGWalker：データ探索と可視化のためのPythonライブラリ</h2>

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

[**PyGWalker**](https://github.com/Kanaries/pygwalker)は、pandasデータフレーム（およびpolarsデータフレーム）を使用して、Jupyter Notebookのデータ分析およびデータ可視化ワークフローを簡素化し、Tableauスタイルのユーザーインターフェースに変換することで、視覚的な探索を可能にします。

**PyGWalker**（"Pig Walker"のように発音、楽しみのために）は、「**Py**thon binding of **G**raphic **Walker**」の略称として命名されています。これは、Jupyter Notebook（または他のJupyterベースのノートブック）を[Graphic Walker](https://github.com/Kanaries/graphic-walker)に統合するもので、Tableauのオープンソースの代替手段です。これにより、データサイエンティストは、シンプルなドラッグアンドドロップ操作でデータを分析し、パターンを可視化できます。

[Google Colab](https://colab.research.google.com/drive/171QUQeq-uTLgSj1u-P9DQig7Md1kpXQ2?usp=sharing)、[Kaggle Code](https://www.kaggle.com/asmdef/pygwalker-test)、または[Graphic Walker Online Demo](https://graphic-walker.kanaries.net/)を試すために訪れてみてください！

> Rを使用する場合は、[GWalkR](https://github.com/Kanaries/GWalkR)をチェックしてみてください！

# スタートガイド

| [Kaggleで実行](https://www.kaggle.com/asmdef/pygwalker-test) | [Colabで実行](https://colab.research.google.com/drive/171QUQeq-uTLgSj1u-P9DQig7Md1kpXQ2?usp=sharing) |
|--------------------------------------------------------------|--------------------------------------------------------|
| [![Kaggleコード](https://docs-us.oss-us-west-1.aliyuncs.com/img/pygwalker/kaggle.png)](https://www.kaggle.com/asmdef/pygwalker-test) | [![Google Colab](https://docs-us.oss-us-west-1.aliyuncs.com/img/pygwalker/colab.png)](https://colab.research.google.com/drive/171QUQeq-uTLgSj1u-P9DQig7Md1kpXQ2?usp=sharing) |

## pygwalkerのセットアップ

pygwalkerを使用する前に、コマンドラインを使用してpipまたはcondaを介してパッケージをインストールしてください。

### pip

```bash
pip install pygwalker
```
> **注意**
> 
> 早期の試用版の場合、`pip install pygwalker --upgrade`を使用してバージョンを最新に保つか、さらに`pip install pygwaler --upgrade --pre`を使用して最新の機能とバグ修正を取得できます。

### Conda-forge
```bash
conda install -c conda-forge pygwalker
```
または
```bash
mamba install -c conda-forge pygwalker
```
詳細なヘルプについては、[conda-forge feedstock](https://github.com/conda-forge/pygwalker-feedstock)を参照してください。

## Jupyter Notebookでpygwalkerを使用する

### クイックスタート

pygwalkerとpandasをJupyter Notebookにインポートして開始します。

```python    
import pandas as pd
import pygwalker as pyg
```

既存のワークフローを壊すことなくpygwalkerを使用できます。たとえば、次のようにデータフレームを読み込んでGraphic Walkerを呼び出すことができます。

```python
df = pd.read_csv('./bike_sharing_dc.csv')
walker = pyg.walk(df)
```

### より良いプラクティス

```python
df = pd.read_csv('./bike_sharing_dc.csv')
walker = pyg.walk(
    df,
    spec="./chart_meta_0.json",    # このJSONファイルにはチャートの状態が保存されます。チャートが完了したらUIで保存ボタンをクリックする必要があります。将来的には「自動保存」がサポートされる予定です。
    kernel_computation=True,          # `kernel_computation=True`を設定すると、pygwalkerは計算エンジンとしてduckdbを使用します。これにより、より大きなデータセット（<=100GB）を探索できます。
)
```

### オフライン例

* ノートブックコード：[こちらをクリック](https://github.com/Kanaries/pygwalker-offline-example)
* プレビューノートブックHTML：[こちらをクリック](https://pygwalker-public-bucket.s3.amazonaws.com/demo.html)

### オンライン例

* [Use PyGWalker in Kaggle](https://www.kaggle.com/code/lxy21495892/airbnb-eda-pygwalker-demo)
* [Use PyGWalker in Google Colab](https://colab.research.google.com/drive/171QUQeq-uTLgSj1u-P9DQig7Md1kpXQ2?usp=sharing)

***

![](https://docs-us.oss-us-west-1.aliyuncs.com/img/pygwalker/travel-ani-0-light.gif)

以上です。これで、ドラッグアンドドロップの変数を使用してデータを分析および可視化するTableauのようなユーザ

ーインターフェースが利用可能です。

![](https://docs-us.oss-us-west-1.aliyuncs.com/img/pygwalker/travel-ani-1-light.gif)

Graphic Walkerでできる素晴らしいこと：

+ マークタイプを他のものに変更して異なるチャートを作成できます。たとえば、ラインチャート：
![graphic walker line chart](https://user-images.githubusercontent.com/8137814/221894699-b9623304-4eb1-4051-b29d-ca4a913fb7c7.png)

+ 異なる測定値を比較するために、複数の測定値を行または列に追加して連結ビューを作成できます。
![graphic walker area chart](https://user-images.githubusercontent.com/8137814/224550839-7b8a2193-d3e9-4c11-a19e-ad8e5ec19539.png)

+ 次元の値によって分割されたいくつかのサブビューを持つファセットビューを作成するには、次元を行または列に追加してファセットビューを作成します。ルールはTableauと似ています。
![graphic walker scatter chart](https://user-images.githubusercontent.com/8137814/221894480-b5ec5df2-d0bb-45bc-aa3d-6479920b6fe2.png)

+ テーブルでデータフレームを表示し、分析タイプとセマンティックタイプを設定できます。
![page-data-view-light](https://user-images.githubusercontent.com/8137814/221895610-76165bc6-95ee-4567-a55b-41d47d3310eb.png)


+ データ探索結果をローカルファイルに保存できます

詳細な手順については、[Graphic Walker GitHubページ](https://github.com/Kanaries/graphic-walker)を参照してください。

## テストされた環境

- [x] Jupyter Notebook
- [x] Google Colab
- [x] Kaggle Code
- [x] Jupyter Lab（作業中：いくつかの小さなCSSの問題がまだあります）
- [x] Jupyter Lite
- [x] Databricks Notebook（バージョン`0.1.4a0`以降）
- [x] Visual Studio Code用Jupyter拡張機能（バージョン`0.1.4a0`以降）
- [x] Hex Projects（バージョン`0.1.4a0`以降）
- [x] IPythonカーネルと互換性のあるほとんどのWebアプリケーション（バージョン`0.1.4a0`以降）
- [x] **Streamlit（バージョン`0.1.4.9`以降）**、`pyg.walk(df, env='Streamlit')`を有効にしました
- [x] DataCamp Workspace（バージョン`0.1.4a0`以降）
- [ ] ... 他の環境についての要望があれば、遠慮なく問題を提起してください。

## 構成とプライバシーポリシー(pygwlaker >= 0.3.10)

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

詳細は参照してください: [How to set your privacy configuration?](https://github.com/Kanaries/pygwalker/wiki/How-to-set-your-privacy-configuration%3F)

# ライセンス

[Apache License 2.0](https://github.com/Kanaries/pygwalker/blob/main/LICENSE)

# リソース

+ [Graphic Walkerに関する詳細な情報は、Graphic Walker GitHub](https://github.com/Kanaries/graphic-walker)をチェックしてください。
+ 私たちはまた、AIパワードの自動化を備えたデータ整理、探索、可視化のワークフローを再定義するオープンソースの探索的データ分析ソフトウェアである[RATH](https://kanaries.net)に取り組んでいます。[Kanariesのウェブサイト](https://kanaries.net)と[RATH GitHub](https://github.com/Kanaries/Rath)をチェックしてください！
+ [Streamlitで視覚的分析アプリを構築するためにpygwalkerを使用](https://docs.kanaries.net/pygwalker/use-pygwalker-with-streamlit)
+ 問題が発生した場合やサポートが必要な場合は、[Slack](https://join.slack.com/t/kanaries-community/shared_invite/zt-1pcosgbua-E_GBPawQOI79C41dPDyyvw)または[Discord](https://discord.gg/Z4ngFWXz2U)のチャンネルに参加してください。
+ pygwalkerを以下のソーシャルメディアプラットフォームで共有してください：

[![Reddit](https://img.shields.io/badge/share%20on-reddit-red?style=flat-square&logo=reddit)](https://reddit.com/submit?url=https://github.com/Kanaries/pygwalker&title=Say%20Hello%20to%20pygwalker%3A%20Combining%20Jupyter%20Notebook%20with%20a%20Tableau-like%20UI)
[![HackerNews](https://img.shields.io/badge/share%20on-hacker%20news-orange?style=flat-square&logo=ycombinator)](https://news.ycombinator.com/submitlink?u=https://github.com/Kanaries/pygwalker)
[![Twitter](https://img.shields.io/badge/share%20on-twitter-03A9F4?style=flat-square&logo=twitter)](https://twitter.com/share?url=https://github.com/Kanaries/pygwalker&text=Say%20Hello%20to%20pygwalker%3A%20Combining%20Jupyter%20Notebook%20with%20a%20Tableau-like%20UI)
[![Facebook](https://img.shields.io/badge/share%20on-facebook-1976D2?style=flat-square&logo=facebook)](https://www.facebook.com/sharer/sharer.php?u=https://github.com/Kanaries/pygwalker)
[![LinkedIn](https://img.shields.io/badge/share%20on-linkedin-3949AB?style=flat-square&logo=linkedin)](https://www.linkedin.com/shareArticle?url=https://github.com/Kanaries/pygwalker&&title=Say%20Hello%20to%20pygwalker%3A%20Combining%20Jupyter%20Notebook%20with%20a%20Tableau-like%20UI)
