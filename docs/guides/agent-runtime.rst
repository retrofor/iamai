Agent Runtime
=============

iamai 内置的 agent runtime 是一组轻量工具，不是完整 agent 平台。它主要服务 examples 中的
ReAct、Planner/Executor、Supervisor 等模式，让示例能共享模型配置、工具注册、trace 和简单
guardrail。

核心对象
--------

``LLMConfig``
   从显式配置或环境变量读取模型参数。支持 ``OPENAI_API_KEY``、``OPENAI_BASE_URL`` 和
   ``OPENAI_MODEL``。

``LLMClient``
   提供 ``chat_text`` 和 ``chat_json``。测试时可以设置 ``iamai_LLM_MOCK=1``，避免真实模型调用。

``ToolRegistry``
   注册、枚举和调用工具。工具名会标准化为小写。发布到社区商店的工具应声明
   ``permission_name``、``input_schema``、``audit_fields``、``requires_approval`` 和
   ``runtime_capabilities``。

``AgentTrace``
   记录模型调用、工具调用和中间观察结果。插件可以把 trace 放进状态或管理命令输出。

``Guardrail``
   对输出做轻量 token 阻断。它不是安全系统，只适合作为示例级保护。

使用方式
--------

.. code-block:: python

   from iamai import AgentTrace, LLMClient, ToolRegistry


   tools = ToolRegistry()
   tools.register(
       "lookup",
       "Look up a value by key.",
       lambda key: {"key": key},
       permission_name="demo.lookup",
       input_schema={"type": "string"},
       audit_fields=(),
       requires_approval=False,
   )

   trace = AgentTrace("demo")
   client = LLMClient({"model": "gpt-4.1-mini"})
   result = await client.chat_text(
       [{"role": "user", "content": "Say hello briefly."}],
       trace=trace,
   )

设计边界
--------

- 把业务逻辑放回插件，把 agent runtime 当作能力模块。
- 工具保持窄权限、显式输入和可枚举描述。
- 保留 trace，不要让模型调用成为纯黑盒。
- 工具涉及写文件、执行命令、调用外部 API 或批量发送消息时，设置 ``requires_approval=True``。
- 对外部工具调用做自己的权限和速率控制。
