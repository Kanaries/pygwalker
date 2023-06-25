import base64


def fname_encode(fname: str):
    """Encode fname in base64

    Args:
        - fname (str): Suppose to be str

    Returns:
        str
    """
    return base64.b64encode(bytes(str(fname), 'utf-8')).decode()


def fname_decode(fname: str):
    return base64.b64decode(str(fname).encode()).decode().rsplit('_', 1)[0]
