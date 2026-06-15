TEMPLATE = """You are a system that extracts cross-field validation dependencies between product attributes.

Given the following attributes:
{attributes}

Identify realistic cross-field validation rules involving logical relationships between TWO OR MORE DISTINCT attributes.

Focus especially on:

1. Min/max consistency relationships
2. Conditional required fields
3. Electrical compatibility (voltage, current, phases, frequency)
4. Physical and dimensional relationships
5. Rack-mount specific constraints
6. Connection and outlet consistency
7. Configuration compatibility rules
8. Output values constrained by input values
9. Product-type dependent behavior

Only generate rules that express REAL dependency logic between attributes. Generate a maximum of 40 rules. Prioritise the most critical and unambiguous dependencies only.

DON'T generate:
- single-field validation rules
- trivial positivity checks (e.g. FIELD > 0)
- existence-only checks (e.g. FIELD != null)
- duplicate or redundant rules
- rules comparing incompatible units
- vague or probabilistic rules using words like "typically", "usually", or "may"

Only use attributes explicitly provided in the attribute list.

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
- Use logical operators: "and", "or", "not" (lowercase, Python-style, NOT AND/OR/NOT)
- Use Python boolean literals: True, False (NOT 'true'/'false' strings)
- Use None for null values (NOT 'null' or null strings)
- Available functions: abs(), min(), max(), pow(), round(), len()
- rule_details.constraint is required
- rule_details.condition is optional; omit if constraint always applies
- rule_details.message is optional; omit if no user-friendly message is needed
- Conditions and constraints must use valid attribute names
- Every rule must involve at least TWO DISTINCT attributes
- Do not include explanations outside the JSON
- Do not include single-field constraints
- Do not include any text outside the JSON array
- Do not include any comments or formatting, only raw JSON
"""