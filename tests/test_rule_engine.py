import asyncio
from typing import Dict, Any
from iamai.engine import Engine
from iamai.plugin import Plugin
from iamai.lang import Condition
from iamai.rule import Rule
from iamai.mapper.utils import WSMapper

class WebSocketPlugin(Plugin):
    def register_rules(self, engine: Engine) -> None:
        condition = Condition(lambda context: context.get("type") == "greeting")

        def action(context: Dict[str, Any]) -> None:
            print(f"[W1]Received greeting: {context.get('message')}")

        rule = Rule("GreetingRule", condition, action, priority=1)
        engine.add_rule(rule)

class WebSocketPlugin2(Plugin):
    def register_rules(self, engine: Engine) -> None:
        condition = Condition(lambda context: context.get("type") == "greeting")

        def action(context: Dict[str, Any]) -> None:
            print(f"[W2]Received greeting: {context.get('name')}")

        rule = Rule("GreetingRule2", condition, action, priority=200)
        engine.add_rule(rule)

class WebSocketPlugin3(Plugin):
    def register_rules(self, engine: Engine) -> None:
        condition = Condition(lambda context: context.get("type") == "hi")

        def action(context: Dict[str, Any]) -> None:
            print(f"[W3]Received greeting: {context.get('name')}")

        rule = Rule("GreetingRule2", condition, action, priority=-200)
        engine.add_rule(rule)

async def main():
    engine = Engine()
    plugin = WebSocketPlugin()
    plugin.register_rules(engine)
    plugin2 = WebSocketPlugin2()
    plugin2.register_rules(engine)
    plugin3 = WebSocketPlugin3()
    plugin3.register_rules(engine)
    mapper = WSMapper(engine)

    # Start WebSocket server
    await mapper.start("localhost", 8765)

if __name__ == "__main__":
    asyncio.run(main())