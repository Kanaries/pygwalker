import pandas as pd
import polars as pl

from pygwalker.services.data_parsers import get_parser

datas = [
    {"name": "padnas", "count": 3, "date": "2022-01-01"},
    {"name": "polars", "count": 1, "date": "2022-01-01"},
    {"name": "modin", "count": 4, "date": "2022-01-01"},
    {"name": "pygwalker", "count": 2, "date": "2022-01-01"},
    {"name": "pygwalker", "count": 6, "date": "2022-01-01"},
]

sql = "SELECT COUNT(1) total FROM pygwalker_mid_table"
sql_result = [{"total": 5}]
raw_fields_result = [
    {'fid': 'GW_170Q6OGL68', 'name': 'name', 'semanticType': 'nominal', 'analyticType': 'dimension'},
    {'fid': 'GW_7NL4CV2YF5C', 'name': 'count', 'semanticType': 'ordinal', 'analyticType': 'dimension'},
    {'fid': 'GW_134F5I1A28', 'name': 'date', 'semanticType': 'temporal', 'analyticType': 'dimension'}
]
to_records_result = [{'GW_170Q6OGL68': 'padnas', 'GW_7NL4CV2YF5C': 3, 'GW_134F5I1A28': '2022-01-01'}]
to_records_no_kernrl_result = [{'GW_170Q6OGL68': 'padnas', 'GW_7NL4CV2YF5C': 3, 'GW_134F5I1A28': '2022-01-01'}]


def test_data_parser_on_padnas():
    df = pd.DataFrame(datas)
    dataset_parser = get_parser(df, True)
    assert dataset_parser.get_datas_by_sql(sql) == sql_result
    assert dataset_parser.raw_fields == raw_fields_result
    assert dataset_parser.to_records(1) == to_records_result
    dataset_parser = get_parser(df, False)
    assert dataset_parser.to_records(1) == to_records_no_kernrl_result


def test_data_parser_on_polars():
    df = pl.DataFrame(datas)
    dataset_parser = get_parser(df, True)
    assert dataset_parser.get_datas_by_sql(sql) == sql_result
    assert dataset_parser.raw_fields == raw_fields_result
    assert dataset_parser.to_records(1) == to_records_result
    dataset_parser = get_parser(df, False)
    assert dataset_parser.to_records(1) == to_records_no_kernrl_result


try:
    from modin import pandas as mpd
    def test_data_parser_on_modin():
        df = mpd.DataFrame(datas)
        dataset_parser = get_parser(df, True)
        assert dataset_parser.get_datas_by_sql(sql) == sql_result
        assert dataset_parser.raw_fields == raw_fields_result
        assert dataset_parser.to_records(1) == to_records_result
        dataset_parser = get_parser(df, False)
        assert dataset_parser.to_records(1) == to_records_no_kernrl_result
except ImportError:
    pass
