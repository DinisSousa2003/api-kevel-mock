import json
from typing import Optional, List, Dict

class Rules:
    def __init__(self, file_path: str = "dataset/definitions.json"):
        self.file_path = file_path
        self._rules = self._load_rules()
    
    def _load_rules(self) -> Dict[str, str]:
        with open(self.file_path) as json_definitions:
            return json.load(json_definitions)
    
    def get_all_rules(self) -> Dict[str, str]:
        return self._rules

    def get_all_rules_name(self) -> List[str]:
        return self._rules.keys()
    
    def get_rules_by_type(self, rule_types: Optional[tuple] = ()) -> Dict[str, str]:
        if not rule_types:
            return self._rules
        return {k: v for k, v in self._rules.items() if v in rule_types}
    
    def get_rule_by_atrr(self, attr: str) -> str:
        return self._rules[attr]

    def mock_attributes(self):
        update = dict()
        for name, rule in self._rules.items():
            if "bounded-last-unique-concatenation" in rule:
                update[name] = [1.0]
            elif rule == "or":
                update[name] = True
            else:
                update[name] = 1.0

        return update