"""
规则引擎模块
"""
from typing import Any, Dict, List, Optional, Callable, Union, Set
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import asyncio
import re
from functools import wraps
from .typing import RuleCondition, RuleAction, RuleContext, EventType, LogLevel
from .event import Event
from .logger import get_logger

logger = get_logger(__name__)

@dataclass
class RuleDefinition:
    """规则定义"""
    name: str
    condition: RuleCondition
    action: RuleAction
    priority: int = 0
    enabled: bool = True
    plugin: Optional[str] = None
    event_types: Set[EventType] = field(default_factory=set)
    
    def __post_init__(self):
        if not self.event_types:
            self.event_types = {'message'}

class RuleEngine:
    """规则引擎"""
    
    def __init__(self):
        self.rules: List[RuleDefinition] = []
        self.facts: Dict[str, Any] = {}
        self.contexts: List[RuleContext] = []
        
    def add_rule(self, rule: RuleDefinition) -> None:
        """添加规则"""
        self.rules.append(rule)
        # 按优先级排序
        self.rules.sort(key=lambda r: r.priority, reverse=True)
        logger.debug(f"添加规则: {rule.name}")
    
    def remove_rule(self, name: str) -> bool:
        """移除规则"""
        for i, rule in enumerate(self.rules):
            if rule.name == name:
                self.rules.pop(i)
                logger.debug(f"移除规则: {name}")
                return True
        return False
    
    def get_rules(self, plugin: Optional[str] = None) -> List[RuleDefinition]:
        """获取规则列表"""
        if plugin:
            return [rule for rule in self.rules if rule.plugin == plugin]
        return self.rules
    
    async def process_event(self, event: Event, bot: 'Bot', middleware: Optional['Middleware'] = None, plugin: Optional['Plugin'] = None) -> List[Any]:
        """处理事件"""
        results = []
        context = RuleContext(event=event, bot=bot, middleware=middleware, plugin=plugin, facts=self.facts)
        
        logger.debug(f"处理事件: {event.type}, 平台: {event.platform}")
        
        # 筛选匹配的规则
        matching_rules = []
        for rule in self.rules:
            if not rule.enabled:
                continue
            if event.type not in rule.event_types:
                continue
            if self._evaluate_condition(rule.condition, context):
                matching_rules.append(rule)
        
        logger.debug(f"匹配到 {len(matching_rules)} 个规则")
        
        # 执行匹配的规则
        for rule in matching_rules:
            try:
                result = await self._execute_action(rule.action, context)
                if result is not None:
                    results.append(result)
                logger.debug(f"执行规则: {rule.name}")
            except Exception as e:
                logger.error(f"执行规则 {rule.name} 时出错: {e}")
        
        return results
    
    def _evaluate_condition(self, condition: RuleCondition, context: RuleContext) -> bool:
        """评估条件"""
        if isinstance(condition, str):
            return self._evaluate_string_condition(condition, context)
        elif callable(condition):
            try:
                return condition(context)
            except Exception as e:
                logger.error(f"条件评估错误: {e}")
                return False
        return False
    
    def _evaluate_string_condition(self, condition: str, context: RuleContext) -> bool:
        """评估字符串条件"""
        try:
            # 简单的条件表达式解析
            # 支持: event.type == "message", event.fields.get("content", "").startswith("help")
            
            # 替换变量
            condition = condition.replace("event.type", f"'{context.event.type}'")
            condition = condition.replace("event.platform", f"'{context.event.platform}'")
            
            # 处理 event.fields.get() 调用
            pattern = r'event\.fields\.get\(["\']([^"\']+)["\'][^)]*\)'
            def replace_fields(match):
                field_name = match.group(1)
                value = context.event.get_field(field_name, "")
                if isinstance(value, str):
                    return f"'{value}'"
                return str(value)
            
            condition = re.sub(pattern, replace_fields, condition)
            
            # 安全评估
            return eval(condition, {"__builtins__": {}}, {})
        except Exception as e:
            logger.error(f"字符串条件评估错误: {condition}, {e}")
            return False
    
    async def _execute_action(self, action: RuleAction, context: RuleContext) -> Any:
        """执行动作"""
        if asyncio.iscoroutinefunction(action):
            return await action(context)
        else:
            return action(context)
    
    def add_fact(self, key: str, value: Any) -> None:
        """添加事实"""
        self.facts[key] = value
        logger.debug(f"添加事实: {key} = {value}")
    
    def get_fact(self, key: str, default: Any = None) -> Any:
        """获取事实"""
        return self.facts.get(key, default)
    
    def remove_fact(self, key: str) -> bool:
        """移除事实"""
        if key in self.facts:
            del self.facts[key]
            logger.debug(f"移除事实: {key}")
            return True
        return False

# 规则装饰器
def rule(
    condition: Union[str, Callable] = "event.type == 'message'",
    priority: int = 0,
    event_types: Optional[List[EventType]] = None,
    name: Optional[str] = None,
    enabled: bool = True
):
    """规则装饰器"""
    def decorator(func):
        rule_name = name or func.__name__
        rule_event_types = set(event_types) if event_types else {'message'}
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        
        # 添加规则元数据
        wrapper._rule_metadata = {
            'name': rule_name,
            'condition': condition,
            'priority': priority,
            'event_types': rule_event_types,
            'enabled': enabled,
            'action': func
        }
        
        return wrapper
    return decorator

def when_all(*conditions):
    """所有条件都满足"""
    def combined_condition(context: RuleContext) -> bool:
        for condition in conditions:
            if isinstance(condition, str):
                # 这里需要实现字符串条件的评估
                # 简化版本，实际应该更复杂
                if not eval(condition.replace("event", "context.event")):
                    return False
            elif callable(condition):
                if not condition(context):
                    return False
        return True
    return combined_condition

def when_any(*conditions):
    """任一条件满足"""
    def combined_condition(context: RuleContext) -> bool:
        for condition in conditions:
            if isinstance(condition, str):
                if eval(condition.replace("event", "context.event")):
                    return True
            elif callable(condition):
                if condition(context):
                    return True
        return False
    return combined_condition

# 预定义条件
class Conditions:
    """预定义条件"""
    
    @staticmethod
    def is_message(context: RuleContext) -> bool:
        """是消息事件"""
        return context.event.type == 'message'
    
    @staticmethod
    def is_join(context: RuleContext) -> bool:
        """是加入事件"""
        return context.event.type == 'join'
    
    @staticmethod
    def is_leave(context: RuleContext) -> bool:
        """是离开事件"""
        return context.event.type == 'leave'
    
    @staticmethod
    def content_starts_with(prefix: str):
        """内容以指定前缀开始"""
        def condition(context: RuleContext) -> bool:
            if context.event.type != 'message':
                return False
            content = context.event.get_field('content', '')
            return content.startswith(prefix)
        return condition
    
    @staticmethod
    def content_contains(text: str):
        """内容包含指定文本"""
        def condition(context: RuleContext) -> bool:
            if context.event.type != 'message':
                return False
            content = context.event.get_field('content', '')
            return text in content
        return condition
    
    @staticmethod
    def user_id_equals(user_id: str):
        """用户ID等于指定值"""
        def condition(context: RuleContext) -> bool:
            return context.event.get_field('user_id', '') == user_id
        return condition
    
    @staticmethod
    def platform_equals(platform: str):
        """平台等于指定值"""
        def condition(context: RuleContext) -> bool:
            return context.event.platform == platform
        return condition
