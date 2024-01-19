from typing import List, Dict, Any, Union, Optional
from decimal import Decimal
import json

import altair as alt
import pandas as pd

from pygwalker._typing import DataFrame
from pygwalker.data_parsers.database_parser import Connector
from pygwalker.services.data_parsers import get_parser
from .core import get_metrics_sql


class _JSONEncoder(json.JSONEncoder):
    """JSON encoder"""
    def default(self, o):
        if isinstance(o, Decimal):
            if o.is_nan():
                return None
            return float(o)

        return json.JSONEncoder.default(self, o)


def get_metrics_datas(
    dataset: Union[DataFrame, Connector],
    metrics_name: str,
    field_map: Dict[str, str],
    params: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    Example: get 1 day retention datas
    ```python
    from pygwalker_tools.metrics import get_metrics_datas
    datas = get_metrics_datas(
        dataset=dataset,
        metrics_name="retention",
        field_map={
            "date": "your_date_field",
            "user_id": "your_user_id_field",
            "user_signup_date": "your_user_signup_date_field"
        },
        params={
            "time_unit": "day",
            "time_size": 1
    )
    ```
    Available metrics:
    - pv: Page Views
        - fields: ['date']
        - dimensions: ['date']
        - params: []
    - uv: User Views
        - fields: ['date', 'user_id']
        - dimensions: ['date']
        - params: []
    - mau: Monthly Active Users
        - fields: ['date', 'user_id']
        - dimensions: ['date']
        - params: []
    - retention: Retention
        - fields: ['date', 'user_id', 'user_signup_date']
        - dimensions: ['date']
        - params: ['time_unit', 'time_size']
    - new_user_count: New User Count
        - fields: ['date', 'user_id', 'user_signup_date']
        - dimensions: ['date']
        - params: []
    - active_user: Active User
        - fields: ['date', 'user_id']
        - dimensions: ['date']
        - params: ['within_active_days']
    - active_user_count: Active User Count
        - fields: ['date', 'user_id']
        - dimensions: ['date']
        - params: ['within_active_days']
    - user_churn_rate_base_active: User Churn Rate Base Active
        - fields: ['date', 'user_id']
        - dimensions: ['date']
        - params: ['within_active_days']
    """
    if isinstance(dataset, str):
        raise TypeError("Unsupported cloud dataset type")

    if params is None:
        params = {}

    parser = get_parser(dataset)

    sql = get_metrics_sql(
        name=metrics_name,
        field_map=field_map,
        params=params,
        origin_table_name=parser.placeholder_table_name
    )

    if isinstance(dataset, Connector):
        return parser._get_datas_by_sql(sql)
    else:
        return parser.get_datas_by_sql(sql)


class MetricsChart:
    """
    Example: get 7 day retention chart
    ```python
    from pygwalker_tools.metrics import MetricsChart
    MetricsChart(
        dataset,
        {"date": "your_date_field", "user_id": "your_user_id_field", "user_signup_date": "your_user_signup_date_field"},
        params={"time_unit": "day", "time_size": 7}
    ).retention()
    ```
    Available metrics:
    - pv: Page Views
        - fields: ['date']
        - dimensions: ['date']
        - params: []
    - uv: User Views
        - fields: ['date', 'user_id']
        - dimensions: ['date']
        - params: []
    - mau: Monthly Active Users
        - fields: ['date', 'user_id']
        - dimensions: ['date']
        - params: []
    - retention: Retention
        - fields: ['date', 'user_id', 'user_signup_date']
        - dimensions: ['date']
        - params: ['time_unit', 'time_size']
    - new_user_count: New User Count
        - fields: ['date', 'user_id', 'user_signup_date']
        - dimensions: ['date']
        - params: []
    - cohort_matrix: Cohort Matrix
        - fields: ['date', 'user_id', 'user_signup_date']
        - dimensions: ['date', 'time_size']
        - params: []
    - active_user_count: Active User Count
        - fields: ['date', 'user_id']
        - dimensions: ['date']
        - params: ['within_active_days']
    - user_churn_rate_base_active: User Churn Rate Base Active
        - fields: ['date', 'user_id']
        - dimensions: ['date']
        - params: ['within_active_days']
    """
    def __init__(
        self,
        dataset: Union[DataFrame, Connector],
        field_map: Dict[str, str],
        params: Optional[Dict[str, Any]] = None,
        reverse_axis: bool = False
    ):
        self.dataset = dataset
        self.field_map = field_map
        self.params = params
        self.reverse_axis = reverse_axis

    def _get_datas(self, metrics_name: str, params: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
        datas = get_metrics_datas(
            dataset=self.dataset,
            metrics_name=metrics_name,
            field_map=self.field_map,
            params=params or self.params
        )
        return pd.DataFrame(json.loads(json.dumps(datas, cls=_JSONEncoder)))

    def _format_encode(self, encode_params: Dict[str, Any]) -> Dict[str, Any]:
        if self.reverse_axis:
            encode_params["x"], encode_params["y"] = encode_params["y"], encode_params["x"]
        return encode_params

    def pv(self) -> alt.Chart:
        datas = self._get_datas("pv")
        encode_params = {
            "x": "date",
            "y": "pv",
            "tooltip": ["date", "pv"]
        }
        return alt.Chart(datas).mark_line().encode(
            **self._format_encode(encode_params)
        )

    def uv(self) -> alt.Chart:
        datas = self._get_datas("uv")
        encode_params = {
            "x": "date",
            "y": "uv",
            "tooltip": ["date", "uv"]
        }
        return alt.Chart(datas).mark_line().encode(
            **self._format_encode(encode_params)
        )

    def mau(self) -> alt.Chart:
        datas = self._get_datas("mau")
        encode_params = {
            "x": "date",
            "y": "mau",
            "tooltip": ["date", "mau"]
        }
        return alt.Chart(datas).mark_line().encode(
            **self._format_encode(encode_params)
        )

    def retention(self) -> alt.Chart:
        datas = self._get_datas("retention")
        encode_params = {
            "x": "date",
            "y": "retention",
            "tooltip": ["date", "retention"]
        }
        return alt.Chart(datas).mark_line().encode(
            **self._format_encode(encode_params)
        )

    def new_user_count(self) -> alt.Chart:
        datas = self._get_datas("new_user_count")
        encode_params = {
            "x": "date",
            "y": "new_user_count",
            "tooltip": ["date", "new_user_count"],
        }
        return alt.Chart(datas).mark_bar().encode(
            **self._format_encode(encode_params)
        )

    def cohort_matrix(self) -> alt.Chart:
        all_df = []
        for i in range(1, 31):
            df = self._get_datas("retention", {"time_unit": "day", "time_size": i})
            df["time_size"] = i
            all_df.append(df)

        datas = pd.concat(all_df)
        encode_params = {
            "x": "time_size:O",
            "y": "date:O",
            "color": "retention",
            "tooltip": ["date", "time_size", "retention"]
        }
        return alt.Chart(datas).mark_rect().encode(
            **self._format_encode(encode_params)
        )

    def active_user_count(self) -> alt.Chart:
        datas = self._get_datas("active_user_count")
        encode_params = {
            "x": "date",
            "y": "active_user_count",
            "tooltip": ["date", "active_user_count"],
        }
        return alt.Chart(datas).mark_bar().encode(
            **self._format_encode(encode_params)
        )

    def user_churn_rate_base_active(self) -> alt.Chart:
        datas = self._get_datas("user_churn_rate_base_active")
        encode_params = {
            "x": "date",
            "y": "user_churn_rate",
            "tooltip": ["date", "user_churn_rate"],
        }
        return alt.Chart(datas).mark_line().encode(
            **self._format_encode(encode_params)
        )
