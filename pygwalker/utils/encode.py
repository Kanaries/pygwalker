import json
from datetime import datetime
from decimal import Decimal

import pytz


class DataFrameEncoder(json.JSONEncoder):
    """JSON encoder for DataFrame"""
    def default(self, o):
        if isinstance(o, datetime):
            if o.tzinfo is None:
                o = pytz.utc.localize(o)
            return int(o.timestamp() * 1000)
        if isinstance(o, Decimal):
            if o.is_nan():
                return None
            return float(o)

        try:
            return json.JSONEncoder.default(self, o)
        except Exception:
            try:
                return str(o)
            except TypeError:
                return None
