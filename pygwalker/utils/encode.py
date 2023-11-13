import json
from datetime import datetime
from decimal import Decimal


class DataFrameEncoder(json.JSONEncoder):
    """JSON encoder for DataFrame"""
    def default(self, o):
        if isinstance(o, datetime):
            return int(o.timestamp() * 1000)
        if isinstance(o, Decimal):
            return float(o)

        try:
            return json.JSONEncoder.default(self, o)
        except Exception:
            try:
                return str(o)
            except TypeError:
                return None
