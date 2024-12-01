from typing import Any, Dict, List
from iamai.log import logger
from iamai.rule import Rule
    
class Engine:
    def __init__(self):
        self.rules: List[Rule] = []

    def add_rule(self, rule: Rule) -> None:
        self.rules.append(rule)
        self.rules.sort(key=lambda r: r.priority, reverse=True)

    def run(self, context: Dict[str, Any]) -> None:
        for rule in self.rules:
            if rule.evaluate(context):
                logger.info(f"Executing rule: {rule.name}")
                rule.execute(context)