import pandas as pd
import pytest

from pygwalker_tools.metrics import get_metrics_datas
from pygwalker_tools.metrics.core import get_metrics_sql


def _event_dataframe():
    return pd.DataFrame(
        [
            {"date": "2024-01-01", "user_id": "alice", "user_signup_date": "2024-01-01"},
            {"date": "2024-01-01", "user_id": "bob", "user_signup_date": "2024-01-01"},
            {"date": "2024-01-02", "user_id": "alice", "user_signup_date": "2024-01-01"},
        ]
    )


def test_metrics_sql_maps_fields_into_subquery():
    sql = get_metrics_sql(
        name="pv",
        field_map={"date": "event_date"},
        params={},
        origin_table_name="pygwalker_mid_table",
    )

    assert 'CAST("event_date" AS TIMESTAMP) AS "date"' in sql
    assert 'FROM "pygwalker_mid_table"' in sql
    assert 'COUNT(1) AS "pv"' in sql


def test_metrics_sql_validates_metric_fields_and_params():
    with pytest.raises(ValueError, match="Unknown metrics name: missing"):
        get_metrics_sql(name="missing", field_map={}, params={}, origin_table_name="source")

    with pytest.raises(ValueError, match="Field not found: user_id"):
        get_metrics_sql(name="uv", field_map={"date": "date"}, params={}, origin_table_name="source")

    with pytest.raises(ValueError, match="Param not found: time_unit"):
        get_metrics_sql(
            name="retention",
            field_map={"date": "date", "user_id": "user_id", "user_signup_date": "signup_date"},
            params={},
            origin_table_name="source",
        )


def test_get_metrics_datas_queries_pandas_dataset():
    datas = get_metrics_datas(
        _event_dataframe(),
        "uv",
        {"date": "date", "user_id": "user_id"},
    )

    assert sorted(datas, key=lambda row: row["date"]) == [
        {"date": "2024-01-01", "uv": 2},
        {"date": "2024-01-02", "uv": 1},
    ]


def test_get_metrics_datas_rejects_cloud_dataset_id():
    with pytest.raises(TypeError, match="Unsupported cloud dataset type"):
        get_metrics_datas("cloud-dataset-id", "pv", {"date": "date"})
