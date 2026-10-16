from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
import re

def infer_column_type(series: pd.Series) -> str:
    """
    Infers the true intended data type of a pandas Series (stored as object).
    Returns one of: 'Integer', 'Decimal', 'Datetime', 'Boolean', 'Text'.
    """
    # Drop missing values to check actual data
    non_null = series.dropna()
    if non_null.empty:
        return "Empty / Unknown"
    
    # Check boolean
    bool_values = {"true", "false", "yes", "no", "t", "f", "1", "0", "y", "n"}
    str_series = non_null.astype(str).str.strip().str.lower()
    if str_series.isin(bool_values).all():
        return "Boolean"
        
    # Check numeric (integer or decimal)
    numeric_converted = pd.to_numeric(non_null, errors="coerce")
    valid_numeric_count = numeric_converted.notna().sum()
    
    # If >= 70% of non-null values can convert to numeric, consider it numeric
    if valid_numeric_count / len(non_null) >= 0.7:
        # Check if all valid numerics are whole numbers
        valid_nums = numeric_converted.dropna()
        if (valid_nums % 1 == 0).all():
            return "Integer"
        else:
            return "Decimal"
            
    # Check datetime
    # Sample up to 100 values to avoid slow date parsing
    sample_to_check = non_null.sample(min(100, len(non_null)), random_state=42).astype(str)
    # Check if strings match common date patterns before invoking to_datetime
    date_pattern = re.compile(r"^\d{4}[-/]\d{1,2}[-/]\d{1,2}|^\d{1,2}[-/]\d{1,2}[-/]\d{2,4}")
    has_date_like = sample_to_check.str.contains(date_pattern).sum()
    if has_date_like / len(sample_to_check) >= 0.6:
        try:
            converted_dates = pd.to_datetime(sample_to_check, errors="coerce")
            if converted_dates.notna().sum() / len(sample_to_check) >= 0.6:
                return "Datetime"
        except Exception:
            pass
            
    return "Text"

def detect_type_inconsistencies(series: pd.Series, inferred_type: str, max_samples: int = 10) -> Dict[str, Any]:
    """
    Finds values in a column that do not conform to its inferred data type.
    """
    inconsistencies = []
    non_null = series.dropna()
    
    if inferred_type in ("Integer", "Decimal"):
        for idx, val in non_null.items():
            val_str = str(val).strip()
            try:
                num = float(val_str)
                if inferred_type == "Integer" and num % 1 != 0:
                    inconsistencies.append({
                        "row_index": int(idx) + 1,  # 1-indexed for display
                        "value": val_str,
                        "reason": "Decimal value found in an integer column."
                    })
            except ValueError:
                inconsistencies.append({
                    "row_index": int(idx) + 1,
                    "value": val_str,
                    "reason": "Non-numeric string found in a numeric column."
                })
                
    elif inferred_type == "Datetime":
        for idx, val in non_null.items():
            val_str = str(val).strip()
            try:
                res = pd.to_datetime(val_str)
                if pd.isna(res):
                    inconsistencies.append({
                        "row_index": int(idx) + 1,
                        "value": val_str,
                        "reason": "Unparseable date format."
                    })
            except Exception:
                inconsistencies.append({
                    "row_index": int(idx) + 1,
                    "value": val_str,
                    "reason": "Value cannot be parsed as a valid date."
                })

    return {
        "count": len(inconsistencies),
        "samples": inconsistencies[:max_samples]
    }

def analyze_dataset(df: pd.DataFrame, preview_rows: int = 10) -> Dict[str, Any]:
    """
    Performs comprehensive data quality analysis on the DataFrame.
    Does NOT modify the original DataFrame.
    """
    total_rows = len(df)
    total_cols = len(df.columns)
    total_cells = total_rows * total_cols
    
    # 1. Missing values
    missing_by_col = []
    total_missing_cells = 0
    
    for col in df.columns:
        s = df[col]
        # Check nulls (both NaN and whitespace-only strings)
        is_missing_mask = s.isna() | (s.astype(str).str.strip().isin(["", "nan", "None", "null"]))
        missing_count = int(is_missing_mask.sum())
        total_missing_cells += missing_count
        missing_pct = round((missing_count / total_rows * 100), 2) if total_rows > 0 else 0.0
        
        # Collect sample row indices (1-indexed)
        sample_indices = (df.index[is_missing_mask] + 1).tolist()[:10]
        
        missing_by_col.append({
            "column": col,
            "missing_count": missing_count,
            "missing_percentage": missing_pct,
            "sample_row_indices": sample_indices
        })
        
    overall_missing_pct = round((total_missing_cells / total_cells * 100), 2) if total_cells > 0 else 0.0
    
    # 2. Duplicate detection
    # Exact duplicate across all columns
    duplicate_mask = df.duplicated(keep="first")
    duplicate_count = int(duplicate_mask.sum())
    duplicate_pct = round((duplicate_count / total_rows * 100), 2) if total_rows > 0 else 0.0
    duplicate_indices = (df.index[duplicate_mask] + 1).tolist()[:15]
    
    # Sample duplicated rows for preview
    dup_preview = []
    if duplicate_count > 0:
        dup_df = df[duplicate_mask].head(5)
        for idx, row in dup_df.iterrows():
            row_dict = {str(k): (None if pd.isna(v) else str(v)) for k, v in row.items()}
            row_dict["_row_number"] = int(idx) + 1
            dup_preview.append(row_dict)

    # 3. Column types and inconsistencies
    column_profiles = []
    total_type_inconsistencies = 0
    
    for col in df.columns:
        inferred_type = infer_column_type(df[col])
        inconsistency_info = detect_type_inconsistencies(df[col], inferred_type)
        total_type_inconsistencies += inconsistency_info["count"]
        
        column_profiles.append({
            "name": col,
            "inferred_type": inferred_type,
            "pandas_dtype": str(df[col].dtype),
            "inconsistencies_count": inconsistency_info["count"],
            "inconsistent_samples": inconsistency_info["samples"]
        })
        
    # 4. Preview data (limited to preview_rows)
    preview_df = df.head(preview_rows)
    preview_records = []
    for idx, row in preview_df.iterrows():
        record = {str(k): ("" if pd.isna(v) else str(v)) for k, v in row.items()}
        record["_row_number"] = int(idx) + 1
        preview_records.append(record)
        
    return {
        "dimensions": {
            "total_rows": total_rows,
            "total_columns": total_cols,
            "total_cells": total_cells
        },
        "missing_summary": {
            "total_missing_cells": total_missing_cells,
            "missing_percentage": overall_missing_pct,
            "by_column": missing_by_col
        },
        "duplicate_summary": {
            "duplicate_count": duplicate_count,
            "duplicate_percentage": duplicate_pct,
            "rule": "Exact match across all column values",
            "sample_row_indices": duplicate_indices,
            "sample_rows": dup_preview
        },
        "columns": column_profiles,
        "total_type_inconsistencies": total_type_inconsistencies,
        "preview_rows": preview_records
    }
