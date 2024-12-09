class CodeStorage:
    def __init__(self):
        self.code_snippets = []

    def add_code(self, code):
        self.code_snippets.append(code)

    def execute_all(self):
        for code in self.code_snippets:
            exec(code)

    def output_all(self):
        return "\n".join(self.code_snippets)
    
def auto_mark(sub_view_fields_semantic_types):
    """
    Determine the appropriate mark type based on semantic types.
    Args:
        sub_view_fields_semantic_types: List of semantic types, max length 2
    Returns:
        str: The recommended mark type
    """
    if len(sub_view_fields_semantic_types) < 2:
        if sub_view_fields_semantic_types[0] in ["temporal", "quantitative"]:
            return "tick"
        return "bar"

    counter = {
        "nominal": 0,
        "ordinal": 0,
        "quantitative": 0,
        "temporal": 0
    }

    for st in sub_view_fields_semantic_types:
        counter[st] = counter.get(st, 0) + 1

    if counter["nominal"] == 1 or counter["ordinal"] == 1:
        return "bar"
    
    if counter["temporal"] == 1 and counter["quantitative"] == 1:
        return "line"
    
    if counter["quantitative"] == 2:
        return "point"
    
    return "point"