import json
from typing import Optional, List

with open('dataset/definitions.json') as json_definitions:
        rules = json.load(json_definitions)
        #print(1, rules)
        assert rules["16c3027744ff5a086a69c91ab8022086"] == "most-recent"


def get_rules(to_use: Optional[List[str]] = []):
        if len(to_use) == 0:
                return rules
        return {k: v for (k, v) in rules.items() if v in to_use}


RULES = get_rules()