# rule_engine.py

from functools import wraps
from contextlib import contextmanager
import importlib
import logging

# 配置日志记录
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RuleEngine:
    def __init__(self):
        self.rulesets = {}
        self.transitions = {}
        self.current_ruleset = None

    def ruleset(self, name):
        @contextmanager
        def _ruleset():
            previous_ruleset = self.current_ruleset
            self.current_ruleset = name
            if name not in self.rulesets:
                self.rulesets[name] = []
            try:
                yield
            finally:
                self.current_ruleset = previous_ruleset
        return _ruleset

    def rule(self, ruleset_name):
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)
            if ruleset_name not in self.rulesets:
                self.rulesets[ruleset_name] = []
            self.rulesets[ruleset_name].append(wrapper)
            return wrapper
        return decorator

    def when_all(self, condition):
        def decorator(func):
            @wraps(func)
            def wrapper(c):
                if condition(c.m):
                    return func(c)
            if self.current_ruleset:
                self.rulesets[self.current_ruleset].append(wrapper)
            return wrapper
        return decorator

    def execute(self, ruleset_name, message):
        if ruleset_name in self.rulesets:
            for rule in self.rulesets[ruleset_name]:
                rule(Context(message))

    def add_transition(self, from_ruleset, to_ruleset):
        self.transitions[from_ruleset] = to_ruleset

    def __rshift__(self, other):
        if isinstance(other, str):
            self.add_transition(self.current_ruleset, other)
        return self

    def set_current_ruleset(self, ruleset_name):
        self.current_ruleset = ruleset_name

    def load_plugin(self, plugin_name):
        try:
            module = importlib.import_module(plugin_name)
            if hasattr(module, 'register'):
                module.register(self)
                logger.info(f"Plugin '{plugin_name}' loaded successfully.")
            else:
                logger.warning(f"Plugin '{plugin_name}' does not have a 'register' function.")
        except ImportError as e:
            logger.error(f"Error loading plugin '{plugin_name}': {e}")

class Context:
    def __init__(self, message):
        self.m = message

class Message:
    def __init__(self, content, platform, user_id):
        self.content = content
        self.platform = platform
        self.user_id = user_id