from typing import List, Dict, Any
import json

from .encode import DataFrameEncoder


def estimate_average_data_size(datas: List[Dict[str, Any]]) -> int:
    """Estimate average data bytes size"""
    smp0 = datas[::max(len(datas)//32, 1)]
    smp1 = datas[::max(len(datas)//37, 1)]
    avg_size = len(json.dumps(smp0, cls=DataFrameEncoder)) / len(smp0)
    avg_size = max(avg_size, len(json.dumps(smp1, cls=DataFrameEncoder)) / len(smp1))
    return avg_size
