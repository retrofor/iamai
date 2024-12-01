from typing import Any, Callable, Dict


class Condition:
    def __init__(self, func: Callable[[Dict[str, Any]], bool]):
        self.func = func

    def evaluate(self, context: Dict[str, Any]) -> bool:
        return self.func(context)

    def __and__(self, other: 'Condition') -> 'Condition':
        return Condition(lambda context: self.evaluate(context) and other.evaluate(context))

    def __or__(self, other: 'Condition') -> 'Condition':
        return Condition(lambda context: self.evaluate(context) or other.evaluate(context))

    def __invert__(self) -> 'Condition':
        return Condition(lambda context: not self.evaluate(context))