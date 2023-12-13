from typing import Dict, Any, Optional

import segment.analytics as analytics
import kanaries_track

from pygwalker.services.global_var import GlobalVarManager
from pygwalker.services.config import get_local_user_id

analytics.write_key = 'z58N15R8LShkpUbBSt1ZjdDSdSEF5VpR'
kanaries_public_key = "tk-6572d7b34a03d7fcf6cf0c86-cOzZyr6xqd"
kanaries_track.config.auth_token = kanaries_public_key
kanaries_track.config.proxies = {}
kanaries_track.config.max_retries = 2


# pylint: disable=broad-exception-caught
def track_event(event: str, properties: Optional[Dict[str, Any]] = None):
    if GlobalVarManager.privacy == "events":
        try:
            analytics.track(
                user_id=get_local_user_id(),
                event=event,
                properties=properties
            )
            kanaries_track.track({**properties, "user_id": get_local_user_id()})
        except Exception:
            pass
