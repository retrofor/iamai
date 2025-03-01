from iamai._core import RuleEngine, process_message
from iamai.typing import Message
from typing import List, Dict
import json


class HybridMessage(Message):
    """Python-Rust共享消息结构"""

    def to_json(self) -> str:
        return json.dumps(
            {
                "content": self.content,
                "platform": self.platform,
                "user_id": self.user_id,
            }
        )


class HybridRuleEngine:
    def __init__(self):
        self.rust_engine = RuleEngine()
        self.py_plugins: List[object] = []

    def add_regex_rule(self, pattern: str):
        """添加高性能正则规则到Rust引擎"""
        self.rust_engine.add_regex_rule(pattern)

    def add_py_plugin(self, plugin: object):
        """添加Python插件"""
        self.py_plugins.append(plugin)

    def process(self, msg: HybridMessage) -> List[str]:
        """混合处理流程"""
        responses = []

        # Rust侧处理
        rust_resp = process_message(msg)
        responses.append(rust_resp)

        # Rust正则匹配
        matched_rules = self.rust_engine.match_message(msg)
        for rule in matched_rules:
            responses.append(f"[Rust规则匹配] {rule}")

        # Python插件处理
        for plugin in self.py_plugins:
            if hasattr(plugin, "match_rule") and plugin.match_rule(msg):
                responses.append(plugin.execute_action(msg))

        return responses


# math_plugin.py
class MathPlugin:
    def match_rule(self, msg: Message) -> bool:
        return msg.content.startswith("计算")

    def execute_action(self, msg: Message) -> str:
        try:
            expr = msg.content.strip()
            return f"计算结果: {expr} = {eval(expr)}"
        except:
            return "计算失败"


import time

# 创建测试消息
msg = Message(content="2*10*1000000", platform="test", user_id="perf")

# 纯Python版本
start = time.time()
for _ in range(10_000):
    MathPlugin().execute_action(msg)
py_time = time.time() - start

# Rust混合版本
from iamai._core import process_message

start = time.time()
for _ in range(10_000):
    process_message(msg.content.strip())
rs_time = time.time() - start

print(f"Python耗时: {py_time:.4f}s")
print(f"Rust耗时: {rs_time:.4f}s")
print(f"性能提升: {(py_time/rs_time):.1f}x")
