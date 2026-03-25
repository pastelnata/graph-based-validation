TEMPLATE = """You are a system that extracts cross-field validation constraints between attributes.

Given the following attributes:
{attributes}

Identify ONLY cross-field constraints (involving 2 or more attributes).

Return ONLY valid JSON in this format:

[
  {{
    "inputs": ["fieldA", "fieldB"],
    "expression": "..."
  }}
]

Rules:
- Expressions must be concise and machine-readable
- Use operators like <=, >=, ==, <, >
- Use "->" for conditional logic (e.g. A == 3 -> B == 400)
- Do not include explanations
- Do not include single-field constraints
- Do not include any text outside the JSON array
- Do not include any comments
- Do not include any formatting or markdown, only raw JSON
"""