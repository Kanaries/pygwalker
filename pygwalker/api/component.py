from typing import List, Optional, Dict, Any, Union
from typing_extensions import Literal
from copy import deepcopy

from pydantic import BaseModel, Field
import sqlglot
import sqlglot.expressions as exp

from .pygwalker import PygWalker
from pygwalker._typing import DataFrame, IAppearance, IThemeKey, ISpecIOMode
from pygwalker.data_parsers.base import FieldSpec
from pygwalker.data_parsers.database_parser import Connector
from pygwalker.utils.randoms import rand_str


GRAPHIC_WALKER_AGG_FUNCS = {
    "sum", "mean", "median",
    "min", "max", "variance", "stddev",
}

GRAPHIC_WALKER_FIELD_FUNCS = {
    "bin", "bin_count"
}


def _convert_sql_to_field(sql: str, is_agg_sql: bool) -> Dict[str, Any]:
    """Convert sql to field info."""
    fid = "gw_" + rand_str(6)
    field_item = {
        "fid": fid,
        "name": sql,
        "analyticType": "dimension",
        "semanticType": "nominal",
        "computed": True,
        "expression": {
            "as": fid,
            "op": "expr",
            "params": [
                {"type": "sql", "value": sql}
            ]
        }
    }
    if is_agg_sql:
        field_item["aggName"] = "expr"
        field_item["analyticType"] = "measure"
        field_item["semanticType"] = "quantitative"
    return field_item


def _convert_gw_agg_function_to_field(func_name: str, field_name: str) -> Dict[str, Any]:
    """Convert graphic walker agg function to field info."""
    field_name = field_name.strip("\"'")
    field_item = {
        "fid": field_name,
        "name": field_name,
        "analyticType": "measure",
        "semanticType": "quantitative",
        "aggName": func_name,
    }
    return field_item


def _convert_gw_bin_function_to_field(func_name: str, field_name: str, num: int) -> Dict[str, Any]:
    """Convert graphic walker bin function to field info."""
    fid = "gw_" + rand_str(6)
    field_name = field_name.strip("\"'")
    field_item = {
        "fid": fid,
        "name": f"{func_name}{num}({field_name})",
        "analyticType": "dimension",
        "semanticType": "ordinal",
        "computed": True,
        "expression": {
            "op": func_name,
            "as": fid,
            "params": [
                {"type": "field", "value": field_name},
            ],
            "num": num,
        }
    }
    return field_item


def _handle_anonymous(ast: exp.Anonymous, origin_str: str) -> Dict[str, Any]:
    """Handle anonymous expression."""
    func_name = str(ast.this).lower()
    if func_name in GRAPHIC_WALKER_AGG_FUNCS:
        return _convert_gw_agg_function_to_field(func_name, str(ast.expressions[0]))
    if func_name in GRAPHIC_WALKER_FIELD_FUNCS:
        return _convert_gw_bin_function_to_field(func_name, str(ast.expressions[0]), int(str(ast.expressions[1])))
    return _convert_sql_to_field(origin_str, False)


def _handle_agg_func(ast: exp.AggFunc, origin_str: str) -> Dict[str, Any]:
    """Handle agg function expression."""
    func_name = ast.sql_name().lower()
    if func_name in GRAPHIC_WALKER_AGG_FUNCS:
        return _convert_gw_agg_function_to_field(func_name, str(ast.this))
    return _convert_sql_to_field(origin_str, True)


class Expression(BaseModel):
    op: str
    as_: str = Field(alias="as")
    params: List[Dict[str, Any]]


class FieldInfo(BaseModel):
    fid: str
    name: str
    semantic_type: str = Field(alias="semanticType")
    analytic_type: str = Field(alias="analyticType")
    computed: bool
    agg_name: str = Field(alias="aggName")
    expression: Expression


# pylint: disable=protected-access
class Component:
    """
    Component class for creating a chain of components.

    Kargs:
        - walker (PygWalker): PygWalker instance.
        - render_type (str): render type.
        - field_map (Dict[str, Any]): field map.
        - single_chart_spec (Dict[str, Any]): single chart
    """
    def __init__(
        self,
        *,
        walker: PygWalker,
        render_type: str,
        field_map: Dict[str, Any],
        single_chart_spec: Dict[str, Any],
    ):
        self.walker = walker
        self._render_type = render_type
        self._field_map = field_map
        self._single_chart_spec = single_chart_spec
        self._runtime_time = None

    def copy(self) -> "Component":
        """return new copied component."""
        return self.__class__(
            walker=self.walker,
            render_type=self._render_type,
            field_map=deepcopy(self._field_map),
            single_chart_spec=deepcopy(self._single_chart_spec)
        )

    def _update_single_chart_spec(self, key: str, value: Any) -> Dict[str, Any]:
        """update single chart spec."""
        cur_obj = self._single_chart_spec
        keys = key.split("__")
        for k in keys[:-1]:
            cur_obj = cur_obj[k]
        cur_obj[keys[-1]] = value

    def _convert_string_to_field_info(self, s: str) -> Dict[str, Any]:
        """
        example: sum(field_name), field_name
        """
        ast = sqlglot.parse_one(s, dialect="duckdb")
        if isinstance(ast, exp.Anonymous):
            return _handle_anonymous(ast, s)
        elif isinstance(ast, exp.AggFunc):
            return _handle_agg_func(ast, s)
        elif isinstance(ast, exp.Func):
            return _convert_sql_to_field(s, False)
        elif isinstance(ast, exp.Column):
            return {
                "fid": s,
                "name": s,
                "analyticType": "dimension",
                "semanticType": "nominal",
                "computed": False,
                **self._field_map.get(s, {})
            }
        return {}

    def _repr_html_(self) -> str:
        return self.to_html()

    def to_html(self) -> str:
        if self._render_type == "pure_chart":
            return self._get_single_chart_html()
        if self._render_type == "explorer":
            return self._get_explorer_html()
        if self._render_type == "profiling":
            return self._get_profiling_html()
        return ""

    def _get_single_chart_html(self) -> str:
        return self.walker.get_single_chart_html_by_spec(spec=self._single_chart_spec)

    def _get_explorer_html(self) -> str:
        all_datas = None
        if self.walker.kernel_computation:
            all_datas = self.walker.data_parser.to_records()
        pyg_props = self.walker._get_props(data_source=all_datas)
        pyg_props["visSpec"] = [self._single_chart_spec]

        return self.walker._get_render_iframe(pyg_props)

    def _get_profiling_html(self) -> str:
        all_datas = None
        if self.walker.kernel_computation:
            all_datas = self.walker.data_parser.to_records()
        pyg_props = self.walker._get_props(data_source=all_datas)
        pyg_props["gwMode"] = "table"
        return self.walker._get_render_iframe(pyg_props)

    def bar(self) -> "Component":
        """Bar chart."""
        copied_obj = self.copy()
        copied_obj._update_single_chart_spec("config__geoms", ["bar"])
        copied_obj._update_single_chart_spec("config__coordSystem", "generic")
        return copied_obj

    def line(self) -> "Component":
        """Line chart."""
        copied_obj = self.copy()
        copied_obj._update_single_chart_spec("config__geoms", ["line"])
        copied_obj._update_single_chart_spec("config__coordSystem", "generic")
        return copied_obj

    def area(self) -> "Component":
        """Area chart."""
        copied_obj = self.copy()
        copied_obj._update_single_chart_spec("config__geoms", ["area"])
        copied_obj._update_single_chart_spec("config__coordSystem", "generic")
        return copied_obj

    def trail(self) -> "Component":
        """Trail chart."""
        copied_obj = self.copy()
        copied_obj._update_single_chart_spec("config__geoms", ["trail"])
        copied_obj._update_single_chart_spec("config__coordSystem", "generic")
        return copied_obj

    def scatter(self) -> "Component":
        """Scatter chart."""
        copied_obj = self.copy()
        copied_obj._update_single_chart_spec("config__geoms", ["point"])
        copied_obj._update_single_chart_spec("config__coordSystem", "generic")
        return copied_obj

    def circle(self) -> "Component":
        """Circle chart."""
        copied_obj = self.copy()
        copied_obj._update_single_chart_spec("config__geoms", ["circle"])
        copied_obj._update_single_chart_spec("config__coordSystem", "generic")
        return copied_obj

    def tick(self) -> "Component":
        """Tick chart."""
        copied_obj = self.copy()
        copied_obj._update_single_chart_spec("config__geoms", ["tick"])
        copied_obj._update_single_chart_spec("config__coordSystem", "generic")
        return copied_obj

    def rect(self) -> "Component":
        """Rect chart."""
        copied_obj = self.copy()
        copied_obj._update_single_chart_spec("config__geoms", ["rect"])
        copied_obj._update_single_chart_spec("config__coordSystem", "generic")
        return copied_obj

    def arc(self) -> "Component":
        """Arc chart."""
        copied_obj = self.copy()
        copied_obj._update_single_chart_spec("config__geoms", ["arc"])
        copied_obj._update_single_chart_spec("config__coordSystem", "generic")
        return copied_obj

    def text(self) -> "Component":
        """Text chart."""
        copied_obj = self.copy()
        copied_obj._update_single_chart_spec("config__geoms", ["text"])
        copied_obj._update_single_chart_spec("config__coordSystem", "generic")
        return copied_obj

    def box(self) -> "Component":
        """Box chart."""
        copied_obj = self.copy()
        copied_obj._update_single_chart_spec("config__geoms", ["boxplot"])
        copied_obj._update_single_chart_spec("config__coordSystem", "generic")
        return copied_obj

    def table(self) -> "Component":
        """Table chart."""
        copied_obj = self.copy()
        copied_obj._update_single_chart_spec("config__geoms", ["table"])
        copied_obj._update_single_chart_spec("config__coordSystem", "generic")
        return copied_obj

    def poi(self) -> "Component":
        """Poi chart."""
        copied_obj = self.copy()
        copied_obj._update_single_chart_spec("config__geoms", ["poi"])
        copied_obj._update_single_chart_spec("config__coordSystem", "geographic")
        return copied_obj

    # pylint: disable=unused-argument
    def encode(
        self,
        x: Union[str, List[str]] = "",
        y: Union[str, List[str]] = "",
        color: str = "",
        opacity: str = "",
        size: str = "",
        shape: str = "",
        radius: str = "",
        theta: str = "",
        longitude: str = "",
        latitude: str = "",
        geoid: str = "",
        details: str = "",
        text: str = "",
    ) -> "Component":
        """
        Encode fields.
        example: .encode(x="field_0", y="field_1", color="field_2")
        .encode(x="field_0", y="SUM(field_1)")
        """
        all_params = {
            key: [value] if isinstance(value, str) else value
            for key, value in locals().items()
            if key != "self"
        }
        copied_obj = self.copy()
        params_key_map = {
            "x": "columns",
            "y": "rows",
            "geoid": "geoId",
        }

        for key, field_str_list in all_params.items():
            field_list = []
            for field_str in field_str_list:
                if not field_str:
                    continue
                field_info = copied_obj._convert_string_to_field_info(field_str)
                if field_info.get("aggName"):
                    copied_obj._update_single_chart_spec("config__defaultAggregated", True)
                field_list.append(field_info)
                if field_info["fid"] not in copied_obj._field_map:
                    copied_obj._field_map[field_info["fid"]] = field_info
                    if field_info["analyticType"] == "dimension":
                        copied_obj._single_chart_spec["encodings"]["dimensions"].append(field_info)
                    else:
                        copied_obj._single_chart_spec["encodings"]["measures"].append(field_info)
            copied_obj._single_chart_spec["encodings"][params_key_map.get(key, key)] = field_list

        return copied_obj

    # pylint: enable=unused-argument
    def layout(
        self,
        *,
        mode: Optional[Literal["auto", "fixed", "container"]] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        **kwargs
    ) -> "Component":
        """
        Set layout config.
        example: .layout(resolve__color=False)
        {
            "colorPalette": "paired",
            "format": {},
            "geoKey": "name",
            "interactiveScale": False,
            "resolve": {
                "color": False,
                "opacity": False,
                "shape": False,
                "size": False,
                "x": False,
                "y": False,
            },
            "scale": {
                "opacity": {},
                "size": {},
            },
            "scaleIncludeUnmatchedChoropleth": False,
            "showActions": False,
            "showTableSummary": False,
            "size": {
                "mode": "fixed",
                "width": 360,
                "height": 360,
            },
            "stack": "stack",
            "useSvg": False,
            "zeroScale": True,
        }
        """
        copied_obj = self.copy()
        layout_info = {
            "size__mode": mode,
            "size__width": width,
            "size__height": height,
            **kwargs
        }
        for key, value in layout_info.items():
            if value is None:
                continue
            copied_obj._update_single_chart_spec("layout__" + key, value)

        return copied_obj

    def profiling(self) -> "Component":
        """Profiling mode."""
        copied_obj = self.copy()
        copied_obj._render_type = "profiling"
        return copied_obj

    def explorer(self) -> "Component":
        """Explorer mode."""
        copied_obj = self.copy()
        copied_obj._render_type = "explorer"
        return copied_obj
# pylint: enable=protected-access


def component(
    dataset: Union[DataFrame, Connector, str],
    *,
    field_specs: Optional[List[FieldSpec]] = None,
    spec: str = "",
    spec_io_mode: ISpecIOMode = "rw",
    theme_key: IThemeKey = "vega",
    appearance: IAppearance = "media",
    show_cloud_tool: Optional[bool] = False,
    kernel_computation: Optional[bool] = None,
    kanaries_api_key: str = "",
    **kwargs
) -> Component:
    """
    Component class for creating a chain of components.

    Args:
        - dataset (pl.DataFrame | pd.DataFrame | Connector, optional): dataframe.

    Kargs:
        - field_specs (List[FieldSpec], optional): Specifications of some fields. They'll been automatically inferred from `df` if some fields are not specified.
        - spec (str): chart config data. config id, json, remote file url
        - spec_io_mode (ISpecIOMode): spec io mode, Default to "r", "r" for read, "rw" for read and write.
        - theme_key ('vega' | 'g2' | 'streamlit'): theme type.
        - appearance (Literal['media' | 'light' | 'dark']): 'media': auto detect OS theme.
        - kernel_computation(bool): Whether to use kernel compute for datas, Default to None.
        - kanaries_api_key (str): kanaries api key, Default to "".
    """
    walker = PygWalker(
        gid=None,
        dataset=dataset,
        field_specs=field_specs,
        spec=spec,
        source_invoke_code="",
        theme_key=theme_key,
        appearance=appearance,
        show_cloud_tool=show_cloud_tool,
        use_preview=True,
        kernel_computation=isinstance(dataset, (Connector, str)) or kernel_computation,
        use_save_tool="w" in spec_io_mode,
        gw_mode="explore",
        is_export_dataframe="w" in spec_io_mode,
        kanaries_api_key=kanaries_api_key,
        default_tab="data",
        cloud_computation=False,
        **kwargs
    )
    render_type = "pure_chart"
    field_map = {
        field["fid"]: field
        for field in walker.data_parser.raw_fields
    }
    single_chart_spec = {
        "name": "Chart 1",
        "visId": "",
        "config": {
            "coordSystem": "generic",
            "defaultAggregated": False,
            "geoms": ["auto"],
            "limit": -1,
            "timezoneDisplayOffset": 0,
        },
        "encodings": {
            "dimensions": [field for field in walker.data_parser.raw_fields if field["analyticType"] == "dimension"],
            "measures": [field for field in walker.data_parser.raw_fields if field["analyticType"] == "measure"],
            "rows": [],
            "columns": [],
            "color": [],
            "opacity": [],
            "size": [],
            "shape": [],
            "radius": [],
            "theta": [],
            "longitude": [],
            "latitude": [],
            "geoId": [],
            "details": [],
            "filters": [],
            "text": [],
        },
        "layout": {
            "format": {},
            "geoKey": "name",
            "interactiveScale": False,
            "resolve": {
                "color": False,
                "opacity": False,
                "shape": False,
                "size": False,
                "x": False,
                "y": False,
            },
            "showActions": False,
            "showTableSummary": False,
            "size": {
                "mode": "fixed",
                "width": 360,
                "height": 360,
            },
            "stack": "stack",
            "zeroScale": True,
        }
    }
    return Component(
        walker=walker,
        render_type=render_type,
        field_map=field_map,
        single_chart_spec=single_chart_spec,
    )
