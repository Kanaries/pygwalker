> PyGWalker 0.3 yayınlandı! [changelog](https://github.com/Kanaries/pygwalker/releases/tag/0.3.0) daha fazla ayrıntı için. Artık daha büyük veri kümeleri için son derece hızlı bir şekilde duckdb modunu etkinleştirebilirsiniz.
<p align="center"><a href="https://github.com/Kanaries/pygwalker"><img width=100% alt="" src="https://user-images.githubusercontent.com/8137814/221879671-70379d15-81ac-44b9-b267-a8fa3842a0d9.png"></a></p>

<h2 align="center">PyGWalker: Görselleştirmeyle Keşif Amaçlı Veri Analizi için Python Kütüphanesi</h2>

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

[**PyGWalker**](https://github.com/Kanaries/pygwalker) pandas dataframe (ve polars dataframe) görsel keşif için Tableau tarzı bir Kullanıcı Arayüzüne dönüştürerek Jupyter Notebook veri analizi ve veri görselleştirme iş akışınızı basitleştirebilir.

**PyGWalker** (şöyle telaffuz edilir "Pig Walker", sadece eğlence için) kısaltması olarak adlandırılır "**Py**thon binding of **G**raphic **Walker**". Jupyter Notebook'u (veya diğer jupyter tabanlı not defterlerini), Tableau'ya farklı türde bir açık kaynak alternatifi olan [Graphic Walker](https://github.com/Kanaries/graphic-walker) ile entegre eder. Veri bilimcilerinin basit sürükle ve bırak işlemleriyle verileri analiz etmelerine ve kalıpları görselleştirmelerine olanak tanır.
     
Visit [Google Colab](https://colab.research.google.com/drive/171QUQeq-uTLgSj1u-P9DQig7Md1kpXQ2?usp=sharing), [Kaggle Code](https://www.kaggle.com/asmdef/pygwalker-test) or [Graphic Walker Online Demo](https://graphic-walker.kanaries.net/) to test it out!

> R kullanmayı tercih ediyorsanız şimdi [GWalkR](https://github.com/Kanaries/GWalkR)'a göz atabilirsiniz!

# Başlarken

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

## kurmak pygwalker

Pygwalker'ı kullanmadan önce paketleri komut satırından pip veya conda kullanarak yüklediğinizden emin olun.

### pip

```bash
pip install pygwalker
```
> **Not**
> 
> Erken deneme için, sürümünüzü en son sürümle güncel tutmak için `pip install pygwalker --upgrade` ile, hatta en son özellikleri ve hata düzeltmelerini elde etmek için `pip install pygwaler --upgrade --pre` ile kurulum yapabilirsiniz.

### Conda-forge
```bash
conda install -c conda-forge pygwalker
```
or
```bash
mamba install -c conda-forge pygwalker
```
Daha fazla yardım için [conda-forge feedstock](https://github.com/conda-forge/pygwalker-feedstock) bakın.


## Jupyter Notebook'ta pygwalker'ı kullanın

### Hızlı başlangıç

Başlamak için pygwalker ve pandas Jupyter Notebook'unuza aktarın.

```python    
import pandas as pd
import pygwalker as pyg
```

Pygwalker'ı mevcut iş akışınızı bozmadan kullanabilirsiniz. Örneğin, dataframe şu şekilde yüklenmişken Graphic Walker'ı çağırabilirsiniz:

```python
df = pd.read_csv('./bike_sharing_dc.csv')
walker = pyg.walk(df)
```

### Daha İyi Uygulama

```python
df = pd.read_csv('./bike_sharing_dc.csv')
walker = pyg.walk(
    df,
    spec="./chart_meta_0.json",    # bu json dosyası grafik durumunuzu kaydedecektir, bir grafiği bitirdiğinizde kullanıcı arayüzü kılavuzundaki kaydet düğmesine tıklamanız gerekir, 'otomatik kaydetme' gelecekte desteklenecektir
    use_kernel_calc=True,          # `use_kernel_calc=True` ayarını yapın, pygwalker bilgi işlem motoru olarak duckdb'yi kullanacak, daha büyük veri kümesini keşfetmenizi destekleyecektir (<=100GB).
)
```

### Çevrimdışı Örnek

* Notebook Code: [Click Here](https://github.com/Kanaries/pygwalker-offline-example)
* Preview Notebook Html: [Click Here](https://pygwalker-public-bucket.s3.amazonaws.com/demo.html)

### Çevrimiçi Örnek

* [Kaggle Code For New Pygwalker](https://www.kaggle.com/code/lxy21495892/airbnb-eda-pygwalker-demo)
* [Kanaries Share page](https://kanaries.net/share/notebook/cwa8g22r6kg0#heading-0)
* [Kaggle Code](https://www.kaggle.com/asmdef/pygwalker-test)
* [Google Colab](https://colab.research.google.com/drive/171QUQeq-uTLgSj1u-P9DQig7Md1kpXQ2?usp=sharing)

***

<!-- ![](https://docs-us.oss-us-west-1.aliyuncs.com/img/pygwalker/screenshot-top-img.png) -->
<!-- ![](https://docs-us.oss-us-west-1.aliyuncs.com/img/pygwalker/1-8ms.gif) -->
![](https://docs-us.oss-us-west-1.aliyuncs.com/img/pygwalker/travel-ani-0-light.gif)

Bu kadar. Artık değişkenleri sürükleyip bırakarak verileri analiz etmek ve görselleştirmek için Tableau benzeri bir kullanıcı arayüzünüz var.

<!-- ![](https://docs-us.oss-us-west-1.aliyuncs.com/img/pygwalker/2-8ms.gif) -->
![](https://docs-us.oss-us-west-1.aliyuncs.com/img/pygwalker/travel-ani-1-light.gif)


<!-- To Be Updated
[![Manually explore your data with a Tableau-like UI](https://docs-us.oss-us-west-1.aliyuncs.com/img/pygwalker/drag-and-drop.gif)](https://docs.kanaries.net/graphic-walker/overview)
-->

Graphic Walker ile yapabileceğiniz harika şeyler:

+ Çizgi grafiği gibi farklı grafikler oluşturmak için işaret türünü başka türlerle değiştirebilirsiniz:

![graphic walker line chart](https://user-images.githubusercontent.com/8137814/221894699-b9623304-4eb1-4051-b29d-ca4a913fb7c7.png)

<!-- ![graphic walker line chart](https://docs-us.oss-us-west-1.aliyuncs.com/images/graphic-walker/gw-line-01.png) -->
<!-- ![graphic walker line chart](https://docs-us.oss-us-west-1.aliyuncs.com/img/pygwalker/fullscreen-timeseries.png) -->


+ Farklı ölçüleri karşılaştırmak için satırlara/sütunlara birden fazla ölçü ekleyerek birleşik görünüm oluşturabilirsiniz.

![graphic walker area chart](https://user-images.githubusercontent.com/8137814/224550839-7b8a2193-d3e9-4c11-a19e-ad8e5ec19539.png)

<!-- ![graphic walker area chart](https://docs-us.oss-us-west-1.aliyuncs.com/images/graphic-walker/gw-area-01.png) -->
<!-- ![graphic walker area chart](https://docs-us.oss-us-west-1.aliyuncs.com/img/pygwalker/fullscreen2-timeseries-area.png) -->


+ Boyuttaki değere bölünen çeşitli alt görünümlerden oluşan bir görünüm oluşturmak için boyutları satırlara veya sütunlara yerleştirerek bir görünüm görünümü oluşturun. Kurallar Tableau'ya benzer.

![graphic walker scatter chart](https://user-images.githubusercontent.com/8137814/221894480-b5ec5df2-d0bb-45bc-aa3d-6479920b6fe2.png)
<!-- ![graphic walker scatter chart](https://docs-us.oss-us-west-1.aliyuncs.com/images/graphic-walker/gw-scatter-01.png) -->
<!-- ![graphic walker scatter chart](https://docs-us.oss-us-west-1.aliyuncs.com/img/pygwalker/fullscreen-scatter-3.png) -->

+ Veri çerçevesini bir tabloda görüntüleyebilir ve analitik türleri ile anlamsal türleri yapılandırabilirsiniz.

![page-data-view-light](https://user-images.githubusercontent.com/8137814/221895610-76165bc6-95ee-4567-a55b-41d47d3310eb.png)


+ Veri araştırma sonucunu yerel bir dosyaya kaydedebilirsiniz

Daha ayrıntılı talimatlar için [Graphic Walker GitHub page](https://github.com/Kanaries/graphic-walker) ziyaret edin..

## Test Edilen Ortamlar

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

## Yapılandırma

`pygwalker>=0.1.7a0` olduğundan, kullanıcı çapındaki yapılandırmayı komut satırı arayüzü aracılığıyla değiştirme olanağı sağlıyoruz
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

+ [Graphic Walker GitHub](https://github.com/Kanaries/graphic-walker)'da Graphic Walker hakkında daha fazla kaynağa göz atın
+ Ayrıca, yapay zeka destekli otomasyonla veri düzenleme, keşif ve görselleştirme iş akışını yeniden tanımlayan Açık Kaynaklı, Otomatik keşif amaçlı veri analizi yazılımı olan [RATH](https://kanaries.net) üzerinde de çalışıyoruz. Daha fazla bilgi için [Kanaries web sitesine](https://kanaries.net) ve [RATH GitHub'a](https://github.com/Kanaries/Rath) göz atın!
+ [Use pygwalker to build visual analysis app in streamlit](https://docs.kanaries.net/pygwalker/use-pygwalker-with-streamlit)
+ Herhangi bir sorunla karşılaşırsanız ve desteğe ihtiyacınız varsa [Slack](https://join.slack.com/t/kanaries-community/shared_invite/zt-1pcosgbua-E_GBPawQOI79C41dPDyyvw) veya [Discord](https://discord.gg/Z4ngFWXz2U) kanalları.
+ Pygwalker'ı şu sosyal medya platformlarında paylaşın:

[![Reddit](https://img.shields.io/badge/share%20on-reddit-red?style=flat-square&logo=reddit)](https://reddit.com/submit?url=https://github.com/Kanaries/pygwalker&title=Say%20Hello%20to%20pygwalker%3A%20Combining%20Jupyter%20Notebook%20with%20a%20Tableau-like%20UI)
[![HackerNews](https://img.shields.io/badge/share%20on-hacker%20news-orange?style=flat-square&logo=ycombinator)](https://news.ycombinator.com/submitlink?u=https://github.com/Kanaries/pygwalker)
[![Twitter](https://img.shields.io/badge/share%20on-twitter-03A9F4?style=flat-square&logo=twitter)](https://twitter.com/share?url=https://github.com/Kanaries/pygwalker&text=Say%20Hello%20to%20pygwalker%3A%20Combining%20Jupyter%20Notebook%20with%20a%20Tableau-like%20UI)
[![Facebook](https://img.shields.io/badge/share%20on-facebook-1976D2?style=flat-square&logo=facebook)](https://www.facebook.com/sharer/sharer.php?u=https://github.com/Kanaries/pygwalker)
[![LinkedIn](https://img.shields.io/badge/share%20on-linkedin-3949AB?style=flat-square&logo=linkedin)](https://www.linkedin.com/shareArticle?url=https://github.com/Kanaries/pygwalker&&title=Say%20Hello%20to%20pygwalker%3A%20Combining%20Jupyter%20Notebook%20with%20a%20Tableau-like%20UI)
