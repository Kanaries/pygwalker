import random
import string


def rand_str(n: int = 8, options: str = string.ascii_letters + string.digits) -> str:
    return ''.join(random.sample(options, n))
