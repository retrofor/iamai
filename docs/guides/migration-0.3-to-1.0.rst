从 0.3.0 迁移到 1.0
====================

本指南以 ``v0.3.0`` 和 ``1.0.0rc1`` 的公开代码、配置与测试为基线。``1.0.0rc1`` 是候选版本；
稳定承诺从 ``1.0.0`` 正式发布起生效。升级前先固定 RC、运行完整测试，再逐项处理下列已确认的
变化或非变化结论。

.. _mig-coverage-001:

MIG-COVERAGE-001：有意变化必须可迁移
--------------------------------------

#. **顶层 API 没有删除 0.3 symbol。** ``v0.3.0`` 的 ``iamai.__all__`` 名称在 1.0 候选中仍可导入，
   ``on_command``、``on_message``、``on_event`` 仍是原有别名。新增 symbol 由
   ``PUBLIC_API_CONTRACT_VERSION`` 和 golden manifest 管理。Agent Runtime 的 ``AgentError``、
   ``AgentTrace``、``Guardrail``、``LLMClient``、``LLMConfig``、``ToolRegistry`` 仍是 provisional，
   不能把“可导入”误当成 1.x 兼容保证。

#. **持久化和跨进程消息必须改用 versioned API。** 新代码使用 ``Event.to_payload()`` /
   ``from_payload()``、``Message.to_payload()`` / ``from_payload()`` 或对应 JSON 方法。
   ``Event.to_dict()``、``Event.from_dict()``、``Message(...)`` 和 ``Message.segments`` 继续可用作
   adapter normalization 与便捷接口，但不是稳定 wire format；不要继续用它们写数据库或队列。

#. **稳定 payload 保留标准 JSON 类型。** segment ``data`` 与 Event ``raw`` 中的 string、number、
   boolean、null、array、object 不再为跨进程格式统一字符串化。检查消费者是否错误假定所有值都是
   ``str``。OneBot adapter 边界仍按协议做字符串 normalization，这一点没有改变。

#. **第三方扩展必须使用标准 packaging metadata。** 发布 ``iamai-plugin-<name>`` 或
   ``iamai-adapter-<platform>``，声明 ``iamai>=1,<2``，并分别使用 ``iamai.plugins`` 或
   ``iamai.adapters`` entry-point group。entry point 名必须与类 ``name`` 一致；兼容范围只放在
   ``Requires-Dist``，不要再维护自定义 runtime 版本字段。

#. **扩展发现从宽松选择改为确定性拒绝。** 重复名、内建保留名、加载失败、非 ``Plugin`` /
   ``Adapter`` 子类、entry point 与类名不一致，以及不兼容的 iamai requirement 都会失败，而不是
   last-wins 或继续启动。先在隔离环境安装 wheel，修正 ``ExtensionDiscoveryError.code`` 指出的
   metadata，再开启 auto-discovery。

#. **配置验证更严格，但 OneBot alias 保留。** 带 ``extra="forbid"`` 的核心或扩展模型会拒绝未知
   key；用 ``iamai config-schema`` 查出拼写错误或已移动字段。``event_path``、``api_path``、
   ``api_url`` 的兼容 alias 仍会 normalization，不需要为 1.0 强制改名。配置工具应读取独立的
   ``CONFIG_SCHEMA_CONTRACT_VERSION``，不要从包版本猜测 Schema。

#. **无参 Schema 出口改为统一根 Schema。** ``iamai config-schema`` 和 management ``GET /schema``
   从 0.3 的 ``{plugin_name: schema}`` 映射改为包含 runtime、logging、state、adapter 和 plugin 的
   Draft 2020-12 根 Schema。读取旧映射的工具必须改从 ``properties.plugin.properties[name]`` 取
   插件 Schema，或者继续使用保留的 ``iamai config-schema <plugin>`` selector。Pydantic model 与
   dataclass 统一通过 validation-mode Schema 生成，依赖手写 shape 或旧 golden 的工具必须重生成。

#. **冷启动和运行失败现在保证全量清理。** Plugin 启动失败会逆序回滚已启动 Plugin 并关闭已构造
   Adapter；Adapter 运行失败进入统一 shutdown，清理错误不替换原始异常。扩展的 ``startup()``、
   ``shutdown()`` 和 ``close()`` 必须让 ``CancelledError`` 继续传播，但三者并不共享同一个幂等承诺：
   成功后的 ``Runtime.bootstrap()`` 是空操作，完成后的 ``Runtime.shutdown()`` 幂等，Adapter
   ``close()`` 必须可重复调用；Plugin ``startup()`` 不要求由扩展作者自行幂等。Plugin cleanup 必须
   在 Runtime 调用时释放资源，并能在先前清理被取消时接受 recovery cleanup；成功完成的 Runtime
   shutdown 不会再次调用该 Plugin cleanup。

#. **reload 是事务，handler admission 有明确边界。** reload 会暂停新 handler、drain 当前完整
   pipeline、推进 generation，再 staging 和原子提交 Plugin/Adapter/配置；失败恢复旧集合。不要在
   reload 中依赖半更新 registry，也不要假定容量不足时会执行部分匹配 handler。

#. **Context 只在创建它的 generation 内有效。** reload 或 shutdown 后，旧 Context 的状态、DI、
   reply/send/API、等待消息和 reload 请求会抛出 ``ContextInvalidatedError``。每个 handler 有独立
   Context；middleware 共享该 handler 的 Context。``Depends`` cache 不跨 handler、Event 或
   generation；session waiter 和 backlog 也不会投递旧 Context。后台任务只保存纯数据或 Plugin
   state，不要长期持有 Context。

#. **公开 conformance kit 成为扩展发布门，但 Python 基线不变。** adapter 必须验证 config、inbound
   normalization、outbound send/API、错误、启动、取消和清理；plugin 必须验证 metadata、config、
   dependency、handler、permission、lifecycle 和失败清理。``iamai.testing`` helper 可直接用于
   第三方 CI。Python 要求在 ``v0.3.0`` 已是 ``>=3.11``，因此 1.0 没有新增 Python major break；
   没有使用新扩展发布面或稳定 wire format 的普通 0.3 应用，通常只需修正严格配置检查。

#. **社区录入新增可审计证据。** 新增或更新 plugin/adapter store 条目时，除了标准包名和
   ``Requires-Dist``，还必须提交 ``iamai_requires``、无需凭据即可访问的公开 conformance evidence
   以及网络、凭据和危险动作安全声明。已有条目可以渐进补齐，但缺少这些字段的新提交不会进入
   registry；私有扩展不受 store 录入流程约束。

升级检查
--------

#. 将测试环境升级到 ``iamai==1.0.0rc1``，但生产依赖暂时保留回滚锁定。
#. 把持久化/队列边界迁移到 versioned payload，并用真实历史样本做 round-trip。
#. 在隔离环境构建并安装每个第三方 extension wheel，运行 ``iamai.testing`` conformance helper。
#. 运行 ``iamai config-schema``，清理未知配置 key，并确认 secret 只通过 ``writeOnly`` metadata 暴露。
#. 测试 startup failure、Adapter failure、reload、shutdown 与持有旧 Context 的后台任务。
#. 完整 CI 通过后再切到 ``iamai>=1,<2``；正式版发布后从 RC 切换到 ``1.0.0``。

兼容与弃用
----------

三个契约版本轴及 stable/provisional 边界见 :doc:`../reference/public-api-conformance`；警告窗口、删除
规则和安全/法律例外见 :doc:`../reference/deprecation-policy`。发现本文遗漏有意 breaking change 时，
必须先补迁移步骤和 conformance evidence，再发布 ``1.0.0``。
