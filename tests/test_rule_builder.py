import json

import pytest

from app.schemas.rule import Rule
from app.services.rule_generation.rule_builder import (
    InvalidRuleDataError,
    RuleBuilder,
    RuleParsingError,
    RuleValidationError,
)


rule_1 = {
    "source": "field_a",
    "target": "field_b",
    "rule_details": {
        "constraint": "must_equal",
        "condition": "field_a == 'specific_value'",
    },
}

rule_2 = {
    "source": "field_x",
    "target": "field_y",
    "rule_details": {
        "constraint": "must_not_equal",
        "condition": "field_x != field_y",
        "message": "field_x and field_y cannot be the same",
    },
}


def test_convert_to_rule_success():
    builder = RuleBuilder()
    rule = builder.convert_to_rule(rule_1)

    assert isinstance(rule, Rule)
    assert rule.source == "field_a"
    assert rule.target == "field_b"
    assert rule.rule_details.constraint == "must_equal"


def test_convert_to_rule_invalid_data():
    builder = RuleBuilder()

    with pytest.raises(RuleValidationError) as excinfo:
        builder.convert_to_rule({"source": "field_a"})

    assert "Rule validation failed" in str(excinfo.value)
    assert excinfo.value.original_error is not None


def test_convert_to_rule_non_mapping_input():
    builder = RuleBuilder()

    with pytest.raises(RuleValidationError) as excinfo:
        builder.convert_to_rule("not a dict")

    assert "Rule validation failed" in str(excinfo.value)
    assert excinfo.value.original_error is not None
    assert isinstance(excinfo.value.original_error, TypeError)


def test_parse_rules_success():
    builder = RuleBuilder()

    ai_response = json.dumps(
        [
            rule_1,
            rule_2,
        ]
    )
    rules = builder.parse_rules(ai_response)

    assert len(rules) == 2
    assert all(isinstance(r, Rule) for r in rules)
    assert [r.source for r in rules] == ["field_a", "field_x"]


def test_parse_rules_invalid_json():
    builder = RuleBuilder()

    with pytest.raises(RuleParsingError) as excinfo:
        builder.parse_rules("{not valid json")

    assert "Invalid JSON" in str(excinfo.value)
    assert excinfo.value.original_error is not None


def test_parse_rules_json_but_not_list():
    builder = RuleBuilder()

    ai_response = json.dumps({"rules": [rule_1]})

    with pytest.raises(RuleParsingError) as excinfo:
        builder.parse_rules(ai_response)

    assert "expected a list" in str(excinfo.value)


def test_parse_rules_list_with_non_dict_item():
    builder = RuleBuilder()

    ai_response = json.dumps([rule_1, "not an object"])

    with pytest.raises(RuleParsingError) as excinfo:
        builder.parse_rules(ai_response)

    assert "expected an object" in str(excinfo.value)


def test_parse_rules_wraps_rule_validation_error():
    builder = RuleBuilder()

    ai_response = json.dumps(
        [
            rule_1,
            {"source": "only_source"},
        ]
    )

    with pytest.raises(RuleValidationError) as excinfo:
        builder.parse_rules(ai_response)

    assert "Failed to parse rule" in str(excinfo.value)
    assert isinstance(excinfo.value.original_error, RuleValidationError)


def test_parse_rules_wraps_invalid_rule_data_error(monkeypatch):
    builder = RuleBuilder()

    def _raise_business_error(_data):
        raise InvalidRuleDataError("business rule violated")

    monkeypatch.setattr(builder, "convert_to_rule", _raise_business_error)

    with pytest.raises(RuleValidationError) as excinfo:
        builder.parse_rules(json.dumps([rule_1]))

    assert "Failed to parse rule" in str(excinfo.value)
    assert isinstance(excinfo.value.original_error, InvalidRuleDataError)
