import json
from typing import Any, Dict, List

from pygwalker.services.preview_image import ChartData
from pygwalker.services.spec import fill_new_fields, get_spec_json
from pygwalker.utils.pydantic_compat import model_dump, model_validate


class SpecManager:
    """Manage loaded spec state and saved chart previews."""

    def __init__(self, spec: Any, field_specs: List[Dict[str, str]]):
        self.spec = spec
        spec_obj, spec_type = get_spec_json(spec)
        self.spec_type = spec_type
        if spec_type.startswith("vega"):
            self.update_vis_spec(spec_obj["config"])
        else:
            self.update_vis_spec(spec_obj["config"] and fill_new_fields(spec_obj["config"], field_specs))
        self.chart_map = self._parse_chart_map_dict(spec_obj["chart_map"])
        self.spec_version = spec_obj.get("version", None)
        self.workflow_list = spec_obj.get("workflow_list", [])

    @property
    def chart_list(self) -> List[str]:
        return list(self.chart_map.keys())

    def update_vis_spec(self, vis_spec: List[Dict[str, Any]]) -> None:
        self.vis_spec = vis_spec
        self.chart_name_index_map = {
            item["name"]: index
            for index, item in enumerate(vis_spec)
            if "name" in item
        }

    def save_chart(self, chart_data: ChartData) -> None:
        self.chart_map[chart_data.title] = chart_data

    def save_chart_payload(self, data: Dict[str, Any]) -> None:
        self.save_chart(model_validate(ChartData, data))

    def update_runtime_state(
        self,
        *,
        vis_spec: List[Dict[str, Any]],
        workflow_list: List[Dict[str, Any]],
        chart_data: Dict[str, Any],
        version: str,
    ) -> None:
        self.update_vis_spec(vis_spec)
        self.spec_version = version
        self.workflow_list = workflow_list
        self.save_chart_payload(chart_data)

    def build_spec_obj(self, version: str) -> Dict[str, Any]:
        return {
            "config": self.vis_spec,
            "chart_map": {},
            "version": version,
            "workflow_list": self.workflow_list,
        }

    def write_back(self, cloud_service, version: str) -> None:
        spec_obj = self.build_spec_obj(version)
        if self.spec_type == "json_file":
            with open(self.spec, "w", encoding="utf-8") as f:
                f.write(json.dumps(spec_obj))
        if self.spec_type == "json_ksf":
            cloud_service.write_config_to_cloud(self.spec[6:], json.dumps(spec_obj))

    def get_chart_by_name(self, chart_name: str) -> ChartData:
        if chart_name not in self.chart_map:
            raise ValueError(f"chart_name: {chart_name} not found, please confirm whether to save")
        return self.chart_map[chart_name]

    def get_chart_index(self, chart_name: str) -> int:
        if chart_name not in self.chart_name_index_map:
            raise ValueError(f"chart_name: {chart_name} not found.")
        return self.chart_name_index_map[chart_name]

    def _get_chart_map_dict(self, chart_map: Dict[str, ChartData]) -> Dict[str, Any]:
        return {
            key: model_dump(value, by_alias=True)
            for key, value in chart_map.items()
        }

    def _parse_chart_map_dict(self, chart_map_dict: Dict[str, Any]) -> Dict[str, ChartData]:
        return {
            key: model_validate(ChartData, value)
            for key, value in chart_map_dict.items()
        }
