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
    """
    Track an event in Segment and Kanaries.
    When privacy config of user is 'events',
    PygWalker will collect certain user behavioral data (excluding analyzed data by the user, configuration information of data charts and config file name).
    We only use these datas to improve the user experience of pygwalker.

    - privacy  ['offline', 'update-only', 'events'] (default: events).
        "offline": fully offline, no data is send or api is requested
        "update-only": only check whether this is a new version of pygwalker to update
        "events": share which events about which feature is used in pygwalker, it only contains events data about which feature you arrive for product optimization. No DATA YOU ANALYSIS IS SEND.
    """
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
