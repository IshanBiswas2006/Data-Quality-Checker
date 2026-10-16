import re
from typing import Dict, Any, List, Optional
import pandas as pd

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")

class ValidationRuleEngine:
    """
    Evaluates configurable validation rules on a DataFrame and collects violations.
    """
    
    @staticmethod
    def validate_rules(df: pd.DataFrame, rules: List[Dict[str, Any]], max_samples: int = 20) -> Dict[str, Any]:
        """
        Executes a list of rules against the dataframe.
        
        Rule structure:
        {
            "id": "rule_1",
            "column": "Age",
            "type": "min_value" | "max_value" | "required" | "email" | "date",
            "params": {"min": 0}
        }
        
        Returns:
            {
                "total_violations": int,
                "rules_evaluated": int,
                "results": [ ... ]
            }
        """
        results = []
        total_violations = 0
        
        for rule in rules:
            col = rule.get("column")
            rule_type = rule.get("type")
            params = rule.get("params", {})
            rule_id = rule.get("id", f"{col}_{rule_type}")
            
            if col not in df.columns:
                results.append({
                    "rule_id": rule_id,
                    "column": col,
                    "type": rule_type,
                    "status": "error",
                    "error_message": f"Column '{col}' not found in dataset.",
                    "violations_count": 0,
                    "samples": []
                })
                continue
                
            series = df[col]
            violations = []
            
            if rule_type == "required":
                # Check for null, NaN, or empty/whitespace string
                for idx, val in series.items():
                    if pd.isna(val) or str(val).strip() in ("", "nan", "None", "null"):
                        violations.append({
                            "row_index": int(idx) + 1,
                            "value": "(empty)",
                            "reason": f"Required field '{col}' is missing or blank."
                        })
                        
            elif rule_type in ("min_value", "max_value", "numeric_range"):
                min_val = params.get("min")
                max_val = params.get("max")
                inclusive_min = params.get("inclusive_min", True)
                inclusive_max = params.get("inclusive_max", True)
                
                for idx, val in series.items():
                    if pd.isna(val) or str(val).strip() == "":
                        continue  # Missing values handled by required check
                    val_str = str(val).strip()
                    try:
                        num = float(val_str)
                        if min_val is not None:
                            min_f = float(min_val)
                            if inclusive_min and num < min_f:
                                violations.append({
                                    "row_index": int(idx) + 1,
                                    "value": val_str,
                                    "reason": f"Value {num} is below minimum allowed value ({min_f})."
                                })
                            elif not inclusive_min and num <= min_f:
                                violations.append({
                                    "row_index": int(idx) + 1,
                                    "value": val_str,
                                    "reason": f"Value {num} must be strictly greater than {min_f}."
                                })
                        if max_val is not None:
                            max_f = float(max_val)
                            if inclusive_max and num > max_f:
                                violations.append({
                                    "row_index": int(idx) + 1,
                                    "value": val_str,
                                    "reason": f"Value {num} is above maximum allowed value ({max_f})."
                                })
                            elif not inclusive_max and num >= max_f:
                                violations.append({
                                    "row_index": int(idx) + 1,
                                    "value": val_str,
                                    "reason": f"Value {num} must be strictly less than {max_f}."
                                })
                    except ValueError:
                        violations.append({
                            "row_index": int(idx) + 1,
                            "value": val_str,
                            "reason": f"Expected numeric value for range check, found non-number '{val_str}'."
                        })
                        
            elif rule_type == "email":
                for idx, val in series.items():
                    if pd.isna(val) or str(val).strip() == "":
                        continue
                    val_str = str(val).strip()
                    if not EMAIL_REGEX.match(val_str):
                        violations.append({
                            "row_index": int(idx) + 1,
                            "value": val_str,
                            "reason": "Value does not match standard email address format (e.g., user@domain.com)."
                        })
                        
            elif rule_type == "date":
                for idx, val in series.items():
                    if pd.isna(val) or str(val).strip() == "":
                        continue
                    val_str = str(val).strip()
                    try:
                        parsed = pd.to_datetime(val_str, errors="coerce")
                        if pd.isna(parsed):
                            violations.append({
                                "row_index": int(idx) + 1,
                                "value": val_str,
                                "reason": "Value is not a valid recognized date."
                            })
                    except Exception:
                        violations.append({
                            "row_index": int(idx) + 1,
                            "value": val_str,
                            "reason": "Value is not a valid date format."
                        })
                        
            total_violations += len(violations)
            results.append({
                "rule_id": rule_id,
                "column": col,
                "type": rule_type,
                "params": params,
                "status": "passed" if len(violations) == 0 else "failed",
                "violations_count": len(violations),
                "samples": violations[:max_samples]
            })
            
        return {
            "total_violations": total_violations,
            "rules_evaluated": len(rules),
            "results": results
        }

    @staticmethod
    def suggest_default_rules(df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Analyzes column names and contents to suggest relevant validation rules automatically.
        Users can enable, tweak, or disable these.
        """
        suggested = []
        for col in df.columns:
            col_lower = str(col).lower()
            
            # Age rule
            if "age" in col_lower:
                suggested.append({
                    "id": f"rule_age_{col}",
                    "column": col,
                    "type": "min_value",
                    "params": {"min": 0, "inclusive_min": True},
                    "description": f"Age in '{col}' must be non-negative (>= 0)"
                })
                
            # Price / Amount / Cost rule
            elif any(k in col_lower for k in ["price", "cost", "salary", "amount", "revenue"]):
                suggested.append({
                    "id": f"rule_pos_{col}",
                    "column": col,
                    "type": "min_value",
                    "params": {"min": 0, "inclusive_min": False},
                    "description": f"'{col}' must be strictly positive (> 0)"
                })
                
            # Email rule
            elif "email" in col_lower:
                suggested.append({
                    "id": f"rule_email_{col}",
                    "column": col,
                    "type": "email",
                    "params": {},
                    "description": f"'{col}' must be a valid email format"
                })
                
            # Date rule
            elif any(k in col_lower for k in ["date", "time", "created_at", "updated_at", "dob", "birthday"]):
                suggested.append({
                    "id": f"rule_date_{col}",
                    "column": col,
                    "type": "date",
                    "params": {},
                    "description": f"'{col}' must be a valid date format"
                })
                
        return suggested
