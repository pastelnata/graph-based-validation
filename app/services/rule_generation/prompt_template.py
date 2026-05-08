TEMPLATE = """You are a system that extracts cross-field validation constraints between product attributes.

Given the following attributes:
{attributes}

Identify realistic cross-field dependencies involving two or more attributes.

Focus especially on:

1. Min/max consistency rules
2. Conditional required fields
3. Form factor and physical dimension relationships
4. Electrical compatibility (voltage, current, frequency, phases)
5. Connection count consistency
6. Rack-mount specific properties
7. Output values constrained by input values

Prefer meaningful domain rules over trivial rules.

Return ONLY valid JSON in this format:

[
  {{
    "source": "fieldA",
    "target": "fieldB",
    "rule_details": {{
      "condition": "fieldA == 'specific_value'",
      "constraint": "fieldB == expected_value",
      "message": "When fieldA is 'specific_value', fieldB must equal expected_value"
    }}
  }}
]

Rules:
- Use concise machine-readable expressions
- Use operators like <=, >=, ==, <, >, !=
- rule_details.constraint is required
- rule_details.condition is optional; omit if constraint always applies
- rule_details.message is optional; omit if no user-friendly message is needed
- Do not include explanations outside the JSON
- Do not include single-field constraints
- Do not include any text outside the JSON array
- Do not include any comments or formatting, only raw JSON
"""