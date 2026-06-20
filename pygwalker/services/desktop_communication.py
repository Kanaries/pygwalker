from typing import TYPE_CHECKING, Optional

from pygwalker.communications.protocol import EmptyResponse, OpenDesktopRequest, dump_response
from pygwalker.services.desktop_import import DesktopImportService

if TYPE_CHECKING:
    from pygwalker.api.pygwalker import PygWalker


class DesktopCommunicationService:
    """Serve desktop integration communication endpoints for a walker."""

    def __init__(self, walker: "PygWalker", desktop_import: Optional[DesktopImportService] = None):
        self.walker = walker
        self.desktop_import = desktop_import or DesktopImportService()

    def open_in_desktop(self, request: OpenDesktopRequest):
        self.desktop_import.import_to_desktop(
            spec=request.spec,
            fields=request.fields,
            records=self.walker.data_parser.to_records(),
        )
        return dump_response(EmptyResponse())
