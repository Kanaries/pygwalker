from datetime import datetime, timezone
import random
import string


def rand_str(n: int = 8, options: str = string.ascii_letters + string.digits) -> str:
    return ''.join(random.sample(options, n))


def generate_hash_code() -> str:
    now_time = int(datetime.now(timezone.utc).timestamp() * 1000 * 1000)
    pre_str = format(now_time, "x")
    pre_str = pre_str.zfill(16)
    return pre_str + rand_str(16)
