DUCKDB_IMPORT_ERROR = (
    "PyGWalker requires duckdb for dataframe querying. Install it with `pip install duckdb` "
    "or reinstall PyGWalker from its project dependencies."
)


def raise_missing_duckdb(exc: ModuleNotFoundError) -> None:
    raise ModuleNotFoundError(DUCKDB_IMPORT_ERROR) from exc
