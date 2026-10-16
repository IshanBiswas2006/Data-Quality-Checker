import io
import pytest
from werkzeug.datastructures import FileStorage
from app.services.file_validator import validate_uploaded_file

def test_validate_none_file():
    is_valid, msg, name = validate_uploaded_file(None)
    assert not is_valid
    assert "No file was selected" in msg

def test_validate_empty_filename():
    storage = FileStorage(io.BytesIO(b"data"), filename="")
    is_valid, msg, name = validate_uploaded_file(storage)
    assert not is_valid
    assert "No file was selected" in msg

def test_validate_invalid_extension():
    storage = FileStorage(io.BytesIO(b"data"), filename="test.txt")
    is_valid, msg, name = validate_uploaded_file(storage)
    assert not is_valid
    assert "Unsupported file extension" in msg

def test_validate_empty_file():
    storage = FileStorage(io.BytesIO(b""), filename="empty.csv")
    is_valid, msg, name = validate_uploaded_file(storage)
    assert not is_valid
    assert "The uploaded file is empty" in msg

def test_validate_file_too_large():
    storage = FileStorage(io.BytesIO(b"x" * 1024), filename="large.csv")
    is_valid, msg, name = validate_uploaded_file(storage, max_size_bytes=500)
    assert not is_valid
    assert "File size exceeds the maximum limit" in msg

def test_validate_valid_csv():
    storage = FileStorage(io.BytesIO(b"a,b\n1,2"), filename="valid.csv")
    is_valid, msg, name = validate_uploaded_file(storage)
    assert is_valid
    assert msg == ""
    assert name == "valid.csv"
