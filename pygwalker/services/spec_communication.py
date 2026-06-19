from typing import TYPE_CHECKING, Optional

from pygwalker import __version__
from pygwalker.communications.protocol import (
    EmptyResponse,
    LatestVisSpecResponse,
    SaveChartRequest,
    UpdateSpecRequest,
    dump_response,
)
from pygwalker.services.preview_image import PreviewImageTool
from pygwalker.utils.pydantic_compat import model_dump

if TYPE_CHECKING:
    from pygwalker.api.pygwalker import PygWalker


class SpecCommunicationService:
    """Serve spec state communication endpoints for a walker."""

    def __init__(self, walker: "PygWalker", preview_tool: Optional[PreviewImageTool] = None):
        self.walker = walker
        self.preview_tool = preview_tool

    def get_latest_vis_spec(self, _):
        return dump_response(LatestVisSpecResponse(visSpec=self.walker.vis_spec))

    def save_chart(self, request: SaveChartRequest):
        self.walker.spec_manager.save_chart_payload(model_dump(request, by_alias=True))
        return dump_response(EmptyResponse())

    def update_spec(self, request: UpdateSpecRequest):
        self.walker.spec_manager.update_runtime_state(
            vis_spec=request.vis_spec,
            workflow_list=request.workflow_list,
            chart_data=request.chart_data,
            version=__version__,
        )

        if self.walker.use_preview:
            self.preview_tool.async_render_gw_review(self.walker._get_gw_preview_html())

        self.walker.spec_manager.write_back(self.walker.cloud_service, __version__)
        return dump_response(EmptyResponse())
