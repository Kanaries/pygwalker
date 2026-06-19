from typing import TYPE_CHECKING

from pygwalker.communications.protocol import EmptyResponse, dump_response
from pygwalker.services.upload_data import BatchUploadDatasToolOnWidgets

if TYPE_CHECKING:
    from pygwalker.api.pygwalker import PygWalker


class DataUploadCommunicationService:
    """Serve browser data upload communication endpoints for a walker."""

    def __init__(self, walker: "PygWalker", upload_tool: BatchUploadDatasToolOnWidgets):
        self.walker = walker
        self.upload_tool = upload_tool

    def request_data(self, _):
        self.upload_tool.run(
            records=self.walker.origin_data_source,
            sample_data_count=0,
            data_source_id=self.walker.data_source_id,
        )
        return dump_response(EmptyResponse())
