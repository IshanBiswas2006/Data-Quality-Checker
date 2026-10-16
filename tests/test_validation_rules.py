import pytest
import pandas as pd
from app.services.validation_rules import ValidationRuleEngine

def test_validation_required():
    df = pd.DataFrame({"name": ["Alice", "", None, "Bob"]})
    rules = [{"id": "r1", "column": "name", "type": "required"}]
    res = ValidationRuleEngine.validate_rules(df, rules)
    assert res["total_violations"] == 2
    assert res["results"][0]["status"] == "failed"

def test_validation_min_value_inclusive():
    df = pd.DataFrame({"age": [25, 0, -5, 40]})
    rules = [{"id": "r2", "column": "age", "type": "min_value", "params": {"min": 0, "inclusive_min": True}}]
    res = ValidationRuleEngine.validate_rules(df, rules)
    assert res["total_violations"] == 1
    assert res["results"][0]["samples"][0]["value"] == "-5"

def test_validation_strictly_positive():
    df = pd.DataFrame({"price": [10.5, 0, -2.0, 50]})
    rules = [{"id": "r3", "column": "price", "type": "min_value", "params": {"min": 0, "inclusive_min": False}}]
    res = ValidationRuleEngine.validate_rules(df, rules)
    assert res["total_violations"] == 2  # 0 and -2.0 are violations

def test_validation_email():
    df = pd.DataFrame({"email": ["valid@test.com", "not-an-email", "user@sub.domain.org", "bad@"]})
    rules = [{"id": "r4", "column": "email", "type": "email"}]
    res = ValidationRuleEngine.validate_rules(df, rules)
    assert res["total_violations"] == 2

def test_suggested_rules():
    df = pd.DataFrame({
        "User_Age": [20, 25],
        "Product_Price": [10.0, 20.0],
        "Customer_Email": ["a@b.com", "c@d.com"]
    })
    suggested = ValidationRuleEngine.suggest_default_rules(df)
    assert len(suggested) == 3
    rule_types = {r["type"] for r in suggested}
    assert "min_value" in rule_types
    assert "email" in rule_types
