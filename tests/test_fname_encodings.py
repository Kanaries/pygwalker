from pygwalker.services.fname_encodings import (
    base36encode,
    fname_decode,
    fname_encode,
    base36decode
)


def test_base36_encode():
    assert base36encode("hello") == "5PZCSZU7"
    assert base36encode("hello world") == "FUVRSIVVNFRBJWAJO"
    assert base36encode("") == "0"


def test_base36_decode():
    assert base36decode("5PZCSZU7") == "hello"
    assert base36decode("FUVRSIVVNFRBJWAJO") == "hello world"
    assert base36decode("0") == ""


def test_fname_encode():
    assert fname_encode("city") == "GW_RKZXIX"
    assert fname_encode("student_1") == "GW_CHGZ1K89ZCF86P"
    assert fname_encode("class_3") == "GW_7NJX6443QYB"


def test_fname_decode():
    assert fname_decode("GW_RKZXIX") == "city"
    assert fname_decode("GW_CHGZ1K89ZCF86P") == "student"
    assert fname_decode("GW_7NJX6443QYB") == "class"
