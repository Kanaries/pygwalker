from typing import Dict, Any, List


def get_default_props(
    data_source: List[Dict[str, Any]],
    field_specs: Dict[str, Any],
    **kwargs: Dict[str, Any]
) -> Dict[str, Any]:
    return {
        'dataSource': data_source,
        'rawFields': field_specs,
        'hideDataSourceConfig': True,
        'fieldkeyGuard': False,
        'themeKey': 'g2',
        **kwargs,
    }
