import json
from datetime import datetime


class DataFrameEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            return int(o.timestamp() * 1000)

        try:
            return str(o)
        except TypeError:
            pass
        return json.JSONEncoder.default(self, o)
