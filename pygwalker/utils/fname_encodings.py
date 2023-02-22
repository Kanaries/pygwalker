import base64

def fname_encode(fname: str):
    return base64.b64encode(bytes(fname, 'utf-8')).decode()

def fname_decode(fname: str):
    return base64.b64decode(fname.encode()).decode()