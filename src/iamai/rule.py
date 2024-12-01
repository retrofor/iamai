from typing import Any, Callable, Dict
from iamai.log import logger
from iamai.lang import Condition

class Rule:
    def __init__(self, name: str, condition: Condition, action: Callable[[Dict[str, Any]], None], priority: int = 0):
        self.name = name
        self.condition = condition
        self.action = action
        self.priority = priority

    def evaluate(self, context: Dict[str, Any]) -> bool:
        try:
            return self.condition.evaluate(context)
        except Exception as e:
            logger.error(f"Error evaluating rule {self.name}: {e}")
            return False

    def execute(self, context: Dict[str, Any]) -> None:
        try:
            self.action(context)
        except Exception as e:
            logger.error(f"Error executing rule {self.name}: {e}")