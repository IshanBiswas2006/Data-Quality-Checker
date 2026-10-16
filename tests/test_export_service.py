import io
import pytest
import pandas as pd
from app.services.export_service import ExportService

def test_export_to_csv_bytes():
    df = pd.DataFrame({"colA": [1, 2], "colB": ["hello", "world"]})
    csv_bytes, filename, err = ExportService.export_to_csv_bytes(df, original_filename="my_data.csv")
    assert err is None
    assert filename == "cleaned_my_data.csv"
    assert b"colA" in csv_bytes
    assert b"hello" in csv_bytes

def test_formula_injection_sanitization():
    df = pd.DataFrame({"cmd": ["=cmd|' /C calc'!A0", "+1+1", "@SUM(A1:A2)", "normal text"]})
    sanitized = ExportService.sanitize_for_csv(df)
    assert sanitized.loc[0, "cmd"].startswith("'=")
    assert sanitized.loc[2, "cmd"].startswith("'@")
    assert sanitized.loc[3, "cmd"] == "normal text"
