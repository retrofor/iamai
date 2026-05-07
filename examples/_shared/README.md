# iamai-example-utils

Shared helpers for the iamai LLM examples.

This package keeps the OpenAI-compatible client setup in one place so the
example runtimes stay focused on plugin and runtime patterns.

The helper package reads `examples/_shared/.env` on import and exposes the
OpenAI-compatible settings through `resolve_llm_settings`. Individual examples
only keep temperature and token limits in plugin config unless they need to
override the shared defaults.
