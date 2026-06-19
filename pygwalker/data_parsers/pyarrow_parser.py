from typing import Dict, List

import pyarrow as pa

from .base import FieldSpec
from .pandas_parser import PandasDataFrameDataParser


class PyArrowTableDataParser(PandasDataFrameDataParser):
    """Parser for pyarrow.Table inputs using the existing pandas-backed data path."""

    def __init__(
        self,
        table: pa.Table,
        field_specs: List[FieldSpec],
        infer_string_to_date: bool,
        infer_number_to_dimension: bool,
        other_params: Dict,
    ):
        self.origin_table = table
        super().__init__(
            table.to_pandas(),
            field_specs,
            infer_string_to_date,
            infer_number_to_dimension,
            other_params,
        )

    @property
    def dataset_type(self) -> str:
        return "pyarrow_table"
