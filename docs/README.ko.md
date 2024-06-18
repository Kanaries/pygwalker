> PyGWalker 0.3 is released! Check out the [changelog](https://github.com/Kanaries/pygwalker/releases/tag/0.3.0) for more details. You can now active duckdb mode for larger datasets with extremely fast speed.
<p align="center"><a href="https://github.com/Kanaries/pygwalker"><img width=100% alt="" src="https://github.com/Kanaries/pygwalker/assets/22167673/bed8b3db-fda8-43e7-8ad2-71f6afb9dddd"></a></p>

<h2 align="center">PyGWalker: 시각화와 함께 탐색적 데이터 분석을 위한 Python 라이브러리</h2>

<p align="center">
    <a href="https://arxiv.org/abs/2406.11637">
      <img src="https://img.shields.io/badge/arXiv-2406.11637-b31b1b.svg" height="18" align="center">
    </a>
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

[**PyGWalker**](https://github.com/Kanaries/pygwalker)는 판다스 데이터프레임 (및 폴라 데이터프레임)을 Tableau 스타일의 사용자 인터페이스로 변환하여 Jupyter Notebook 데이터 분석 및 데이터 시각화 워크플로우를 간소화할 수 있습니다.

**PyGWalker** (즐겁게 발음하는 "Pig Walker"와 같이 발음됩니다)는 "**Py**thon binding of **G**raphic **Walker**"의 약자로 이름이 지어졌습니다. 이는 [Graphic Walker](https://github.com/Kanaries/graphic-walker)와 Jupyter Notebook (또는 다른 Jupyter 기반 노트북)를 통합하여 Tableau의 대체 오픈 소스 유형을 제공합니다. 이를 사용하면 데이터 과학자들은 간단한 드래그 앤 드롭 작업으로 데이터를 분석하고 패턴을 시각화할 수 있습니다.

[Test를 위해 Google Colab](https://colab.research.google.com/drive/171QUQeq-uTLgSj1u-P9DQig7Md1kpXQ2?usp=sharing), [Kaggle Code](https://www.kaggle.com/asmdef/pygwalker-test) 또는 [Graphic Walker Online Demo](https://graphic-walker.kanaries.net/)를 방문하여 테스트해보세요!

> R을 사용하는 것을 선호하신다면 [GWalkR](https://github.com/Kanaries/GWalkR)을 확인해보세요!

# 시작하기

| [Kaggle에서 실행](https://www.kaggle.com/asmdef/pygwalker-test) | [Colab에서 실행](https://colab.research.google.com/drive/171QUQeq-uTLgSj1u-P9DQig7Md1kpXQ2?usp=sharing) |
|--------------------------------------------------------------|--------------------------------------------------------|
| [![Kaggle Code](https://docs-us.oss-us-west-1.aliyuncs.com/img/pygwalker/kaggle.png)](https://www.kaggle.com/asmdef/pygwalker-test) | [![Google Colab](https://docs-us.oss-us-west-1.aliyuncs.com/img/pygwalker/colab.png)](https://colab.research.google.com/drive/171QUQeq-uTLgSj1u-P9DQig7Md1kpXQ2?usp=sharing) |

## pygwalker 설정하기

pygwalker를 사용하기 전에 pip 또는 conda를 사용하여 패키지를 설치해야 합니다.

### pip

```bash
pip install pygwalker
```
> **참고**
> 
> 초기 시험을 위해 `pip install pygwalker --upgrade`로 설치하여 최신 릴리스와 버그 수정을 최신 상태로 유지하거나 `pip install pygwalker --upgrade --pre`로 최신 기능과 버그 수정을 얻을 수 있습니다.

### Conda-forge
```bash
conda install -c conda-forge pygwalker
```
또는
```bash
mamba install -c conda-forge pygwalker
```
더 많은 도움말을 보려면 [conda-forge feedstock](https://github.com/conda-forge/pygwalker-feedstock)을 참조하세요.


## Jupyter Notebook에서 pygwalker 사용하기

### 빠른 시작

pygwalker 및 판다스를 Jupyter Notebook에 가져와 시작하세요.

```python    
import pandas as pd
import pygwalker as pyg
```

기존 워크플로우를 변경하지 않고 pygwalker를 사용할 수 있습니다. 예를 들어 다음과 같이 데이터프레임을 로드하고 Graphic Walker를 호출할 수 있습니다.

```python
df = pd.read_csv('./bike_sharing_dc.csv')
walker = pyg.walk(df)
```

### 더 나은 방법

```python
df = pd.read_csv('./bike_sharing_dc.csv')
walker = pyg.walk(
    df,
    spec="./chart_meta_0.json",    # 이 json 파일은 차트 상태를 저장하며, 차트를 완료할 때 수동으로 저장 버튼을 클릭해야 합니다. 'autosave'는 미래에 지원될 예정입니다.
    kernel_computation=True,          # `kernel_computation=True`로 설정하면 pygwalker가 계산 엔진으로 duckdb를 사용하며, 더 큰 데이터셋(<=100GB)을 탐색할 수 있습니다.
)
```

### 오프라인 예제

* 노트북 코드: [여기를 클릭](https://github.com/Kanaries/pygwalker-offline-example)
* 미리보기 노트북 HTML: [여기를 클릭](https://pygwalker-public-bucket.s3.amazonaws.com/demo.html)

### 온라인 예제

* [Use PyGWalker in Kaggle](https://www.kaggle.com/code/lxy21495892/airbnb-eda-pygwalker-demo)
* [Use PyGWalker in Google Colab](https://colab.research.google.com/drive/171QUQeq-uTLgSj1u-P9DQig7Md1kpXQ2?usp=sharing)

***

![](https://docs-us.oss-us-west-1.aliyuncs.com/img/pygwalker/travel-ani-0-light.gif)

이제 Tableau와 유사한 사용자 인터페이스를 사용하여 변수를 드래그 앤 드롭하여 데이터를 분석하고 시각화할 수 있습니다.

![](https://docs-us.oss-us-west-1.aliyuncs.com/img/pygwalker/travel-ani-1-light.gif)

Graphic Walker로 수행할 수 있는 멋진 작업:

+ 다른 차트 유형으로 마크 유형을 변경하여 다른 차트를 만들 수 있습니다. 예를 들어, 라인

 차트:
![graphic walker line chart](https://user-images.githubusercontent.com/8137814/221894699-b9623304-4eb1-4051-b29d-ca4a913fb7c7.png)

+ 다른 측정값을 비교하려면 행/열에 하나 이상의 측정값을 추가하여 concat 뷰를 생성할 수 있습니다.
![graphic walker area chart](https://user-images.githubusercontent.com/8137814/224550839-7b8a2193-d3e9-4c11-a19e-ad8e5ec19539.png)

+ 차원의 값으로 나누어진 여러 하위 뷰를 만들려면 행 또는 열에 차원을 추가하여 패싯 뷰를 만들 수 있습니다. 규칙은 Tableau와 유사합니다.
![graphic walker scatter chart](https://user-images.githubusercontent.com/8137814/221894480-b5ec5df2-d0bb-45bc-aa3d-6479920b6fe2.png)

+ 테이블에서 데이터 프레임을 볼 수 있으며 분석 유형 및 의미 유형을 구성할 수 있습니다.
![page-data-view-light](https://user-images.githubusercontent.com/8137814/221895610-76165bc6-95ee-4567-a55b-41d47d3310eb.png)

+ 데이터 탐색 결과를 로컬 파일에 저장할 수 있습니다.

자세한 지침은 [Graphic Walker GitHub 페이지](https://github.com/Kanaries/graphic-walker)를 방문하세요.

## 테스트된 환경

- [x] Jupyter Notebook
- [x] Google Colab
- [x] Kaggle Code
- [x] Jupyter Lab (작업 중: 아직 일부 작은 CSS 문제가 있음)
- [x] Jupyter Lite
- [x] Databricks Notebook (버전 `0.1.4a0`부터)
- [x] Visual Studio Code용 Jupyter 확장 (버전 `0.1.4a0`부터)
- [x] Hex Projects (버전 `0.1.4a0`부터)
- [x] IPython 커널과 호환되는 대부분의 웹 응용 프로그램 (버전 `0.1.4a0`부터)
- [x] **Streamlit (버전 `0.1.4.9`부터)**, `pyg.walk(df, env='Streamlit')`을 사용하여 활성화됨
- [x] DataCamp Workspace (버전 `0.1.4a0`부터)
- [ ] ...더 많은 환경에 대한 이슈를 제기하십시오.

## 구성 및 개인 정보 보호 정책(pygwlaker >= 0.3.10)

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

자세한 내용은 참조하세요: [How to set your privacy configuration?](https://github.com/Kanaries/pygwalker/wiki/How-to-set-your-privacy-configuration%3F)

# 라이선스

[Apache License 2.0](https://github.com/Kanaries/pygwalker/blob/main/LICENSE)

# 자원

+ PyGWalker Paper [PyGWalker: On-the-fly Assistant for Exploratory Visual Data Analysis
](https://arxiv.org/abs/2406.11637)
+ [Graphic Walker에 대한 자세한 자료](https://github.com/Kanaries/graphic-walker)
+ [RATH](https://kanaries.net) (작업 중인 항목): 인공 지능 기반 자동화를 통해 데이터 처리, 탐색 및 시각화 워크플로우를 재정의하는 오픈 소스 자동 탐색 데이터 분석 소프트웨어입니다. 더 많은 정보를 보려면 [Kanaries 웹 사이트](https://kanaries.net)

 및 [RATH GitHub](https://github.com/Kanaries/Rath)를 확인하세요!
+ [Streamlit에서 시각 분석 앱을 빌드하기 위해 pygwalker 사용하기](https://docs.kanaries.net/pygwalker/use-pygwalker-with-streamlit)
+ 문제가 발생하거나 지원이 필요한 경우 [Slack](https://join.slack.com/t/kanaries-community/shared_invite/zt-1pcosgbua-E_GBPawQOI79C41dPDyyvw) 또는 [Discord](https://discord.gg/Z4ngFWXz2U) 채널에 참여하세요.
+ pygwalker를 이러한 소셜 미디어 플랫폼에서 공유하세요:

[![Reddit](https://img.shields.io/badge/share%20on-reddit-red?style=flat-square&logo=reddit)](https://reddit.com/submit?url=https://github.com/Kanaries/pygwalker&title=Say%20Hello%20to%20pygwalker%3A%20Combining%20Jupyter%20Notebook%20with%20a%20Tableau-like%20UI)
[![HackerNews](https://img.shields.io/badge/share%20on-hacker%20news-orange?style=flat-square&logo=ycombinator)](https://news.ycombinator.com/submitlink?u=https://github.com/Kanaries/pygwalker)
[![Twitter](https://img.shields.io/badge/share%20on-twitter-03A9F4?style=flat-square&logo=twitter)](https://twitter.com/share?url=https://github.com/Kanaries/pygwalker&text=Say%20Hello%20to%20pygwalker%3A%20Combining%20Jupyter%20Notebook%20with%20a%20Tableau-like%20UI)
[![Facebook](https://img.shields.io/badge/share%20on-facebook-1976D2?style=flat-square&logo=facebook)](https://www.facebook.com/sharer/sharer.php?u=https://github.com/Kanaries/pygwalker)
[![LinkedIn](https://img.shields.io/badge/share%20on-linkedin-3949AB?style=flat-square&logo=linkedin)](https://www.linkedin.com/shareArticle?url=https://github.com/Kanaries/pygwalker&&title=Say%20Hello%20to%20pygwalker%3A%20Combining%20Jupyter%20Notebook%20with%20a%20Tableau-like%20UI)
