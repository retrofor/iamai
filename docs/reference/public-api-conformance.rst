1.0 公共 API 与 Conformance Matrix
===================================

本页定义 iamai 1.0 的公共兼容边界，并把所有规范条款映射到验证证据。当前 ``1.0.0rc1`` 是
**1.0 候选契约**；表中的稳定承诺在 ``1.0.0`` 正式发布时生效。RC 期间如需修订，必须同步更新
规范、迁移指南、golden manifest 和矩阵，不能把未说明的变化带入正式版。

.. _api-version-001:

API-VERSION-001：独立版本轴
---------------------------

调用方必须分别读取对应的公开常量，不能从包版本推导任一数据契约版本。

.. list-table:: 版本轴
   :header-rows: 1
   :widths: 28 28 44

   * - 版本轴
     - 公开标识
     - 兼容边界
   * - Python 公共 API
     - ``PUBLIC_API_CONTRACT_VERSION = "1"``
     - 顶层稳定 symbol、entry-point group、生命周期和弃用政策
   * - 配置 Schema
     - ``CONFIG_SCHEMA_CONTRACT_VERSION = "1"``
     - JSON Schema 的字段、默认值、开放表、secret 标注和 ``$id``
   * - 序列化 wire format
     - ``SERIALIZATION_CONTRACT_VERSION = "1.0"``
     - ``Event`` / ``Message`` payload 及同 major 演进规则
   * - Python distribution
     - package metadata（``importlib.metadata.version("iamai")``）
     - 安装和发布版本；不替代以上任一 contract version

.. _api-surface-001:

API-SURFACE-001：稳定与 provisional symbol
-------------------------------------------

``tests/golden/public_api_v1.json`` 是 1.0 顶层 public symbol 的机器可读快照。``iamai.__all__`` 中
除下表 provisional 项之外的 symbol 是 1.0 稳定候选；``on_command``、``on_message`` 和
``on_event`` 别名也属于稳定候选。未进入 ``iamai.__all__`` 的模块内部名称不构成兼容承诺。

.. list-table:: 顶层公共状态
   :header-rows: 1
   :widths: 24 34 42

   * - 状态
     - symbol
     - 承诺
   * - Stable at 1.0.0
     - golden manifest 中除下一行外的全部 symbol
     - 遵守 :doc:`deprecation-policy`，不得在 1.x 无警告删除或改变语义
   * - Provisional
     - ``AgentError``、``AgentTrace``、``Guardrail``、``LLMClient``、
       ``LLMConfig``、``ToolRegistry``
     - 可以从 ``iamai`` 导入，但 1.x 不保证名称、签名或行为兼容；变更仍必须写入 changelog

provisional 不等于私有，也不代表生产就绪。依赖这些 symbol 的应用应固定 iamai minor 版本并运行
自己的集成测试。将 provisional 项提升为稳定项必须更新 manifest、文档和本矩阵。

矩阵格式
--------

``public-api-conformance.csv`` 是规范条款到证据的一一对应清单。每行 ``requirement_id`` 唯一；
``automated`` 行给出可直接传给 Pytest 的完整 node id，``manual`` 行给出发布检查及必须保存的证据。
``verified`` 表示仓库已有自动证据；``external-required`` 表示该发布门必须在最终树之外保存证据。
RC run URL 不能写回它验证的 git tree，否则新 commit 会改变被验证的 SHA 并形成自引用循环。

.. csv-table:: 1.0 conformance matrix
   :file: public-api-conformance.csv
   :header-rows: 1
   :widths: 15, 14, 20, 33, 10, 8

.. _rc-validate-001:

RC-VALIDATE-001：非发布 RC rehearsal
------------------------------------

``1.0.0rc1`` 的精确 head 必须通过 ``release.yml`` 的非 tag ``workflow_dispatch``：validate、sdist、
全部 Linux、musllinux、Windows 和 macOS wheel、artifact download 与 provenance attestation 必须
全部成功。该 run 不得发布 PyPI 包或创建 GitHub Release。发布负责人必须把 GitHub Actions run URL
记录到 #434、PR comment 或 release checklist，并同时记录 ``headSha``；失败、URL 缺失或
``headSha`` 不等于合并后的 ``dev`` SHA 时，不得标记 1.0 契约完成。
