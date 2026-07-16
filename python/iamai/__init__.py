"""Public package exports for iamai plugin authors and application code."""

from .adapter import Adapter
from .agent import AgentError, AgentTrace, Guardrail, LLMClient, LLMConfig, ToolRegistry
from .config import ConfigValidationError
from .config_schema import (
    CONFIG_SCHEMA_CONTRACT_VERSION,
    CONFIG_SCHEMA_ID,
    build_config_schema,
)
from .context import Context, ContextInvalidatedError
from .di import Depends, depends
from .event import Event
from .message import Message
from .middleware import middleware
from .observability import AuditLogger, RuntimeMetrics
from .permissions import (
    Permission,
    adapter_in,
    allow_all,
    channel_in,
    deny_all,
    group_in,
    permission,
)
from .permissions import predicate as permission_predicate
from .permissions import superusers, user_in
from .plugin import Plugin, command, event_handler, message_handler
from .rules import FieldCondition, FieldOp, Rule, RuleCase, RuleMatch, Ruleset, adapter_is
from .rules import all_of as all_rules
from .rules import allow as allow_rule
from .rules import any_of as any_rules
from .rules import channel_id_is, contains
from .rules import deny as deny_rule
from .rules import (
    detail_type_is,
    endswith,
    event_type_is,
    field,
    fullmatch,
    group_message,
    guild_id_is,
    match_fields,
    none_of,
    platform_is,
)
from .rules import predicate as rule_predicate
from .rules import (
    private_message,
    raw_field,
    regex,
    rule,
    ruleset,
    startswith,
    state_field,
    text_equals,
    user_id_is,
    when_all,
    when_any,
    word_in,
)
from .runtime import ExtensionDiscoveryError, Runtime
from .serialization import SERIALIZATION_CONTRACT_VERSION, SerializationContractError
from .session import SessionManager
from .state import JsonStateStore, NullStateStore, SqliteStateStore, StateStore

__all__ = [
    "AgentError",
    "AgentTrace",
    "Adapter",
    "AuditLogger",
    "Guardrail",
    "JsonStateStore",
    "LLMClient",
    "LLMConfig",
    "NullStateStore",
    "Permission",
    "Rule",
    "RuntimeMetrics",
    "SessionManager",
    "SqliteStateStore",
    "StateStore",
    "ToolRegistry",
    "Runtime",
    "SERIALIZATION_CONTRACT_VERSION",
    "SerializationContractError",
    "ConfigValidationError",
    "CONFIG_SCHEMA_CONTRACT_VERSION",
    "CONFIG_SCHEMA_ID",
    "Context",
    "ContextInvalidatedError",
    "Depends",
    "Event",
    "ExtensionDiscoveryError",
    "Message",
    "FieldCondition",
    "FieldOp",
    "adapter_in",
    "adapter_is",
    "allow_all",
    "allow_rule",
    "all_rules",
    "any_rules",
    "channel_in",
    "Plugin",
    "command",
    "channel_id_is",
    "contains",
    "deny_all",
    "deny_rule",
    "detail_type_is",
    "depends",
    "endswith",
    "event_handler",
    "event_type_is",
    "field",
    "fullmatch",
    "group_in",
    "group_message",
    "guild_id_is",
    "match_fields",
    "middleware",
    "message_handler",
    "none_of",
    "permission",
    "permission_predicate",
    "platform_is",
    "private_message",
    "raw_field",
    "regex",
    "rule",
    "rule_predicate",
    "RuleCase",
    "RuleMatch",
    "Ruleset",
    "ruleset",
    "startswith",
    "state_field",
    "superusers",
    "text_equals",
    "user_id_is",
    "user_in",
    "when_all",
    "when_any",
    "word_in",
    "build_config_schema",
]

on_command = command
on_message = message_handler
on_event = event_handler

__all__.extend(["on_command", "on_message", "on_event"])
