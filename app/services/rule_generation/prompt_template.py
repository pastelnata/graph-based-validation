TEMPLATE = """You are a system that extracts cross-field validation constraints between attributes.

Given the following attributes:
{attributes}

Identify ONLY cross-field constraints (involving 2 or more attributes).

Return ONLY valid JSON in this format:

[
  {{
    "source": "fieldA",
    "target": "fieldB",
    "condition": "fieldA == 'specific_value'",
    "constraint": "fieldB == expected_value",
    "message": "When fieldA is 'specific_value', fieldB must equal expected_value"
  }}
]

Rules:
- Constraints must be concise and machine-readable
- Use operators like <=, >=, ==, <, >, !=
- Condition is optional; omit if constraint always applies
- Message should be user-friendly and explain the constraint
- Do not include explanations outside the JSON
- Do not include single-field constraints
- Do not include any text outside the JSON array
- Do not include any comments or formatting, only raw JSON
"""