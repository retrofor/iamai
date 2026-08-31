API 参考
========

本页列出插件作者和应用代码可直接从 ``iamai`` 导入的公共接口。1.0 的 stable/provisional 边界、
独立 contract version 和机器可读 symbol manifest 见 :doc:`../reference/public-api-conformance`；
删除窗口见 :doc:`../reference/deprecation-policy`。仅仅能从子模块导入不代表获得公共兼容承诺。

.. automodule:: iamai
   :members:
   :imported-members:
   :undoc-members:
   :show-inheritance:

Provisional research Harness
----------------------------

``iamai.harness`` 是独立的 provisional interface，不从顶层 ``iamai`` 重新导出，也不属于稳定的
``1.x`` 消息合同。它当前提供 headless Trial、Replay、版本化 Experiment、JSONL Trajectory Store，
以及受控 Tool interface：``ToolSpec``、``Tool``、``ToolResult``、``ExecutionPolicy``、
``ExecutionBudget``、``ApprovalRequest``、``ApprovalDecision``、``Approver``、``ToolCallStatus`` 和
``ControlledToolEnvironment``。Harness ``ExecutionPolicy`` 不复用稳定消息 Runtime 的
``Permission`` 或 ``ToolRegistry``，``ControlledToolEnvironment`` 也不是隔离沙箱。

配对实验评证接口包括 ``TaskDistributionManifest``、``TrialComparison``、
``ExperimentComparison`` 与 ``compare_experiment``。manifest 预登记 exactly one baseline and one
candidate 的固定 case 分布；manifest 字段是调用方声明，Harness 不执行 sampling rule。
``compare_experiment`` 只接受 complete、经 ``JsonlTrajectoryStore``
校验且 ``jsonl_verified=True`` 的结果；``dataclasses.replace`` 或公开重建的结果不会继承该资格。两个 Comparison 类是
返回值类型，没有受支持的公共构造器。它们提供描述性聚合与完整性
hash；``ExperimentComparison.comparison_format_version`` 版本化其 hash 与聚合语义。它们不提供签名、
可信时间、统计显著性或分布外泛化证明。

.. automodule:: iamai.harness
   :members:
   :imported-members:
   :undoc-members:
   :show-inheritance:
