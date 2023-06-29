import json


class DataFrameEncoder(json.JSONEncoder):
    def default(self, o):
        try:
            return str(o)
        except TypeError:
            pass
        return json.JSONEncoder.default(self, o)
