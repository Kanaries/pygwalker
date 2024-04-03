
def fallback_value(*values):
    """Return the first non-None value in a list of values."""
    for value in values:
        if value is not None:
            return value
