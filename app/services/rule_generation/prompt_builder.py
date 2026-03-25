from __future__ import annotations

class PromptBuilder:
    def __init__(self, template: str):
        self.template = template

    def build_prompt(self, attributes: list[str]) -> str:
        attributes_str = "\n".join(f"- {item}" for item in attributes)
        
        return self.template.format(attributes=attributes_str)
    