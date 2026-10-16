import pytest
import pandas as pd
from app.services.quality_analyzer import analyze_dataset, infer_column_type

def test_analyze_clean_dataset():
    df = pd.DataFrame({
        "id": [1, 2, 3],
        "name": ["A", "B", "C"],
        "age": [20, 30, 40]
    })
    res = analyze_dataset(df)
    assert res["dimensions"]["total_rows"] == 3
    assert res["dimensions"]["total_columns"] == 3
    assert res["missing_summary"]["total_missing_cells"] == 0
    assert res["duplicate_summary"]["duplicate_count"] == 0

def test_analyze_missing_values():
    df = pd.DataFrame({
        "a": [1, None, 3, "NA"],
        "b": ["x", "y", "", "w"]
    })
    res = analyze_dataset(df)
    assert res["missing_summary"]["total_missing_cells"] >= 2
    by_col = {c["column"]: c for c in res["missing_summary"]["by_column"]}
    assert by_col["a"]["missing_count"] >= 1
    assert by_col["b"]["missing_count"] >= 1

def test_analyze_duplicates():
    df = pd.DataFrame({
        "x": [10, 20, 10, 30],
        "y": ["a", "b", "a", "c"]
    })
    res = analyze_dataset(df)
    assert res["duplicate_summary"]["duplicate_count"] == 1
    assert res["duplicate_summary"]["sample_row_indices"] == [3]

def test_type_inference():
    s_int = pd.Series(["1", "2", "3", "4"])
    assert infer_column_type(s_int) == "Integer"

    s_dec = pd.Series(["1.5", "2.25", "3.14"])
    assert infer_column_type(s_dec) == "Decimal"

    s_bool = pd.Series(["true", "false", "true"])
    assert infer_column_type(s_bool) == "Boolean"

    s_date = pd.Series(["2026-01-01", "2026-01-02", "2026-01-03"])
    assert infer_column_type(s_date) == "Datetime"

    s_text = pd.Series(["apple", "banana", "cherry"])
    assert infer_column_type(s_text) == "Text"

def test_single_row_single_col():
    df = pd.DataFrame({"only_col": ["val"]})
    res = analyze_dataset(df)
    assert res["dimensions"]["total_rows"] == 1
    assert res["dimensions"]["total_columns"] == 1
    assert len(res["preview_rows"]) == 1
