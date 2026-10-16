from typing import Dict, Any, List, Tuple, Optional
import pandas as pd
import numpy as np

class CleaningService:
    """
    Applies user-selected cleaning operations to a working copy of a DataFrame.
    Guarantees the original dataset is never mutated.
    """
    
    @staticmethod
    def apply_operation(df: pd.DataFrame, operation: Dict[str, Any]) -> Tuple[pd.DataFrame, Dict[str, Any], Optional[str]]:
        """
        Applies a single cleaning operation.
        
        Returns:
            (new_df, change_log_entry, error_message)
        """
        working_df = df.copy()
        op_type = operation.get("type")
        params = operation.get("params", {})
        
        initial_rows = len(working_df)
        initial_cols = len(working_df.columns)
        
        if op_type == "remove_duplicates":
            subset = params.get("columns")
            if subset and not isinstance(subset, list):
                subset = [subset]
            if subset:
                valid_subset = [c for c in subset if c in working_df.columns]
                if not valid_subset:
                    return working_df, {}, "Specified columns for duplicate removal do not exist."
                working_df = working_df.drop_duplicates(subset=valid_subset, keep="first").reset_index(drop=True)
                desc = f"Removed duplicate rows based on column(s): {', '.join(valid_subset)}"
            else:
                working_df = working_df.drop_duplicates(keep="first").reset_index(drop=True)
                desc = "Removed exact duplicate rows across all columns."
                
            rows_removed = initial_rows - len(working_df)
            return working_df, {
                "operation": "remove_duplicates",
                "description": desc,
                "rows_affected": rows_removed,
                "values_modified": 0
            }, None
            
        elif op_type == "remove_missing_rows":
            col = params.get("column")
            how = params.get("how", "any")  # 'any' or 'all'
            
            if col and col != "__all__":
                if col not in working_df.columns:
                    return working_df, {}, f"Column '{col}' does not exist."
                mask = working_df[col].isna() | (working_df[col].astype(str).str.strip().isin(["", "nan", "None", "null"]))
                working_df = working_df[~mask].reset_index(drop=True)
                desc = f"Removed rows with missing values in column '{col}'."
            else:
                # Replace whitespace / empty strings with NaN temporarily to dropna
                cleaned_mask = working_df.isna() | working_df.apply(lambda col_series: col_series.astype(str).str.strip().isin(["", "nan", "None", "null"]))
                if how == "all":
                    rows_to_drop = cleaned_mask.all(axis=1)
                else:
                    rows_to_drop = cleaned_mask.any(axis=1)
                working_df = working_df[~rows_to_drop].reset_index(drop=True)
                desc = f"Removed rows where {how} column(s) contained missing values."
                
            rows_removed = initial_rows - len(working_df)
            return working_df, {
                "operation": "remove_missing_rows",
                "description": desc,
                "rows_affected": rows_removed,
                "values_modified": 0
            }, None
            
        elif op_type == "fill_missing":
            col = params.get("column")
            strategy = params.get("strategy", "constant")  # 'constant', 'mean', 'median', 'mode'
            fill_value = params.get("value", "")
            
            if not col or col not in working_df.columns:
                return working_df, {}, f"Column '{col}' does not exist."
                
            s = working_df[col]
            missing_mask = s.isna() | (s.astype(str).str.strip().isin(["", "nan", "None", "null"]))
            missing_count = int(missing_mask.sum())
            
            if missing_count == 0:
                return working_df, {
                    "operation": "fill_missing",
                    "description": f"No missing values to fill in column '{col}'.",
                    "rows_affected": 0,
                    "values_modified": 0
                }, None
                
            computed_val = fill_value
            if strategy in ("mean", "median"):
                nums = pd.to_numeric(s[~missing_mask], errors="coerce").dropna()
                if nums.empty:
                    return working_df, {}, f"Cannot compute {strategy} for column '{col}' because it has no numeric values."
                if strategy == "mean":
                    computed_val = str(round(float(nums.mean()), 2))
                else:
                    computed_val = str(round(float(nums.median()), 2))
            elif strategy == "mode":
                valid_vals = s[~missing_mask]
                if valid_vals.empty:
                    return working_df, {}, f"Cannot compute mode for empty column '{col}'."
                computed_val = str(valid_vals.mode().iloc[0])
                
            working_df.loc[missing_mask, col] = str(computed_val)
            desc = f"Filled {missing_count} missing values in '{col}' using {strategy} (value: '{computed_val}')."
            
            return working_df, {
                "operation": "fill_missing",
                "description": desc,
                "rows_affected": 0,
                "values_modified": missing_count
            }, None
            
        elif op_type == "convert_type":
            col = params.get("column")
            target_type = params.get("target_type")  # 'integer', 'decimal', 'string', 'datetime', 'boolean'
            
            if not col or col not in working_df.columns:
                return working_df, {}, f"Column '{col}' does not exist."
                
            s = working_df[col]
            modified_count = 0
            
            try:
                if target_type == "integer":
                    # Convert to numeric, round/truncate, format as int or Int64
                    nums = pd.to_numeric(s, errors="coerce")
                    working_df[col] = nums.apply(lambda x: "" if pd.isna(x) else str(int(round(x))))
                    desc = f"Converted column '{col}' to Integer."
                elif target_type == "decimal":
                    nums = pd.to_numeric(s, errors="coerce")
                    working_df[col] = nums.apply(lambda x: "" if pd.isna(x) else str(float(x)))
                    desc = f"Converted column '{col}' to Decimal/Float."
                elif target_type == "string":
                    working_df[col] = s.astype(str).str.strip()
                    desc = f"Converted column '{col}' to clean String."
                elif target_type == "datetime":
                    dates = pd.to_datetime(s, errors="coerce")
                    working_df[col] = dates.apply(lambda d: "" if pd.isna(d) else d.strftime("%Y-%m-%d"))
                    desc = f"Converted column '{col}' to standard Date format (YYYY-MM-DD)."
                elif target_type == "boolean":
                    truthy = {"true", "1", "yes", "t", "y"}
                    falsy = {"false", "0", "no", "f", "n"}
                    def to_bool_str(val):
                        if pd.isna(val): return ""
                        v_lower = str(val).strip().lower()
                        if v_lower in truthy: return "True"
                        if v_lower in falsy: return "False"
                        return ""
                    working_df[col] = s.apply(to_bool_str)
                    desc = f"Converted column '{col}' to Boolean (True/False)."
                else:
                    return working_df, {}, f"Unsupported target type '{target_type}'."
            except Exception as e:
                return working_df, {}, f"Conversion failed: {str(e)}"
                
            return working_df, {
                "operation": "convert_type",
                "description": desc,
                "rows_affected": 0,
                "values_modified": len(working_df)
            }, None
            
        elif op_type == "strip_whitespace":
            col = params.get("column")
            if col and col != "__all__":
                if col not in working_df.columns:
                    return working_df, {}, f"Column '{col}' does not exist."
                working_df[col] = working_df[col].astype(str).str.strip()
                desc = f"Stripped leading and trailing whitespace in column '{col}'."
            else:
                for c in working_df.columns:
                    working_df[c] = working_df[c].astype(str).str.strip()
                desc = "Stripped leading and trailing whitespace across all columns."
                
            return working_df, {
                "operation": "strip_whitespace",
                "description": desc,
                "rows_affected": 0,
                "values_modified": len(working_df)
            }, None
            
        elif op_type == "drop_column":
            col = params.get("column")
            if not col or col not in working_df.columns:
                return working_df, {}, f"Column '{col}' does not exist."
            working_df = working_df.drop(columns=[col])
            desc = f"Dropped column '{col}'."
            return working_df, {
                "operation": "drop_column",
                "description": desc,
                "rows_affected": 0,
                "columns_affected": 1,
                "values_modified": 0
            }, None
            
        else:
            return working_df, {}, f"Unknown cleaning operation '{op_type}'."

    @classmethod
    def apply_pipeline(cls, original_df: pd.DataFrame, operations: List[Dict[str, Any]]) -> Tuple[pd.DataFrame, List[Dict[str, Any]], Optional[str]]:
        """
        Sequentially applies multiple cleaning operations to a fresh copy of original_df.
        """
        current_df = original_df.copy()
        audit_trail = []
        
        for op in operations:
            current_df, log_entry, err = cls.apply_operation(current_df, op)
            if err:
                return current_df, audit_trail, err
            audit_trail.append(log_entry)
            
        return current_df, audit_trail, None
