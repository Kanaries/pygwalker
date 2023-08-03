from math import ceil


def base36encode(s: str) -> str:
    """Converts an string to a base36 string."""
    alphabet = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    number = int.from_bytes(s.encode(), "big")

    if not isinstance(number, int):
        raise TypeError('number must be an integer')

    base36 = ''

    if 0 <= number < len(alphabet):
        return alphabet[number]

    while number != 0:
        number, i = divmod(number, len(alphabet))
        base36 = alphabet[i] + base36

    return base36


def base36decode(s: str) -> str:
    """Converts a base36 string to an string."""
    number = int(s, 36)
    return number.to_bytes(ceil(number.bit_length() / 8), "big").decode()


def fname_encode(fname: str) -> str:
    """Encode fname in base32

    Args:
        - fname (str): Suppose to be str

    Returns:
        str
    """
    return "GW_" + base36encode(fname)


def fname_decode(encode_fname: str) -> str:
    """Decode fname in base32"""
    return base36decode(encode_fname[3:])
