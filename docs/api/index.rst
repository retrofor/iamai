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
``1.x`` 消息合同。它当前提供 headless Trial、Replay、版本化 Experiment 和 JSONL Trajectory Store。

.. automodule:: iamai.harness
   :members:
   :imported-members:
   :undoc-members:
   :show-inheritance:
