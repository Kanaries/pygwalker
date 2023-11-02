import segment.analytics as analytics

from pygwalker.services.global_var import GlobalVarManager
from pygwalker.services.config import get_local_user_id

analytics.write_key = 'z58N15R8LShkpUbBSt1ZjdDSdSEF5VpR'


def track_event(event: str, properties=None):
    if GlobalVarManager.privacy == "events":
        analytics.track(
            user_id=get_local_user_id(),
            event=event,
            properties=properties
        )
