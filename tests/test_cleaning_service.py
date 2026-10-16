import pytest
import pandas as pd
from app.services.cleaning_service import CleaningService

def test_remove_duplicates():
    df = pd.DataFrame({
        "id": [1, 2, 1],
        "name": ["A", "B", "A"]
    })
    original = df.copy()
    cleaned, log, err = CleaningService.apply_operation(df, {"type": "remove_duplicates", "params": {}})
    
    assert err is None
    assert len(cleaned) == 2
    assert log["rows_affected"] == 1
    # Verify original is untouched
    assert len(df) == 3
    pd.testing.assert_frame_equal(df, original)

def test_remove_missing_rows():
    df = pd.DataFrame({
        "a": [1, 2, None, 4],
        "b": ["x", "y", "z", ""]
    })
    cleaned, log, err = CleaningService.apply_operation(df, {
        "type": "remove_missing_rows",
        "params": {"column": "__all__", "how": "any"}
    })
    assert err is None
    assert len(cleaned) == 2  # Row 2 (None in a) and Row 3 ("" in b) removed
    assert log["rows_affected"] == 2

def test_fill_missing_constant():
    df = pd.DataFrame({"city": ["London", "", "Paris", None]})
    cleaned, log, err = CleaningService.apply_operation(df, {
        "type": "fill_missing",
        "params": {"column": "city", "strategy": "constant", "value": "Unknown"}
    })
    assert err is None
    assert (cleaned["city"] == "Unknown").sum() == 2

def test_fill_missing_mean():
    df = pd.DataFrame({"score": ["10", "20", "30", ""]})
    cleaned, log, err = CleaningService.apply_operation(df, {
        "type": "fill_missing",
        "params": {"column": "score", "strategy": "mean"}
    })
    assert err is None
    assert cleaned.loc[3, "score"] == "20.0"

def test_convert_type():
    df = pd.DataFrame({"age": ["25.0", "30", "invalid", ""]})
    cleaned, log, err = CleaningService.apply_operation(df, {
        "type": "convert_type",
        "params": {"column": "age", "target_type": "integer"}
    })
    assert err is None
    assert cleaned.loc[0, "age"] == "25"
    assert cleaned.loc[1, "age"] == "30"
    assert cleaned.loc[2, "age"] == ""

def test_strip_whitespace():
    df = pd.DataFrame({"text": ["  hello  ", " world   "]})
    cleaned, log, err = CleaningService.apply_operation(df, {
        "type": "strip_whitespace",
        "params": {"column": "text"}
    })
    assert err is None
    assert cleaned.loc[0, "text"] == "hello"
    assert cleaned.loc[1, "text"] == "world"

def test_drop_column():
    df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
    cleaned, log, err = CleaningService.apply_operation(df, {
        "type": "drop_column",
        "params": {"column": "b"}
    })
    assert err is None
    assert "b" not in cleaned.columns
    assert "a" in cleaned.columns
