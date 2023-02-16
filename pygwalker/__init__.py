__name__ = 'pygwalker'
import os, sys, json
import pandas as pd
import typing as tp
import IPython
from IPython.display import display, Javascript, HTML

HERE = os.path.dirname(os.path.abspath(__file__))

def loadJs():
    with open(os.path.join(HERE, 'templates', 'graphic-walker.umd.js'), 'r') as f:
        gwalker_js = "const process={env:{NODE_ENV:'production'} };" + f.read()
        display(HTML(f"""<head>
            <meta charset="UTF-8">
            <meta http-equiv="X-UA-Compatible" content="IE=edge">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <script>{gwalker_js}</script></head>"""))
    
loadJs()


class GWalker:
    global_gid = 0
    def __init__(self, df: pd.DataFrame=None, **kwargs):
        self.gid = GWalker.global_gid
        GWalker.global_gid += 1
        self.df = df
    
    def walk(self, **kwargs):
        from jinja2 import Environment, PackageLoader, select_autoescape
        props = {
            'dataSource': self.dataSource,
            'rawFields': self.rawFields,
        }
        env = Environment(
            loader=PackageLoader("pygwalker"),
            autoescape=select_autoescape()
        )
        template = env.get_template("index.html")
        html = template.render(gwalker={'id': self.gid})
        
        walker_template = env.get_template("walk.js")
        js = walker_template.render(gwalker={'id': self.gid, 'props': json.dumps(props)} )
        
        display(HTML(html), Javascript(js))
        
    def update(self, df: pd.DataFrame=None, **kwargs):
        pass
    
    @property
    def dataSource(self) -> tp.List[tp.Dict]:
        return self.df.to_dict(orient='records')
    
    @property
    def rawFields(self) -> tp.List:
        return [
            GWalker.inferType(self.df[col], i)
            for i, col in enumerate(self.df.columns)
        ]
    
    @staticmethod
    def inferType(s: pd.Series, i=None) -> tp.Dict:
        """get IMutField

        Args:
            s (pd.Series): the column
            i (int, optional): column id. Defaults to None.

        Returns:
            tp.Dict: _description_
        """
        kind = s.dtype.kind
        semanticType = 'quantitative' if \
            (kind in 'fcmiu' and len(s.value_counts()) > 16) \
                else 'temporal' if kind in 'M' \
                    else 'nominal' if kind in 'bSUV' \
                        else 'ordinal'
        # 'quantitative' | 'nominal' | 'ordinal' | 'temporal';
        analyticType = 'measure' if \
            kind in 'fcm' or (kind in 'iu' and len(s.value_counts()) > 16) \
                else 'dimension'
        return {
            'fid': s.name, # f'col-{i}-{s.name}' if i is not None else s.name,
            'name': s.name,
            'semanticType': semanticType,
            'analyticType': analyticType
        }