弃用与兼容性政策
==================

本政策适用于在 :doc:`public-api-conformance` 中声明为稳定的 Python symbol、配置 key、entry-point
group 和序列化字段。该政策已通过 ``1.0.0rc1`` 验证；对外兼容承诺从 ``1.0.0`` 正式发布起生效。

.. _dep-warning-001:

DEP-WARNING-001：结构化警告
----------------------------

弃用稳定接口时，iamai 必须在旧接口仍可用时发出 ``iamai.IamaiDeprecationWarning``。该类型继承
``FutureWarning``，使应用作者在默认警告设置下也能看到迁移信号。警告必须提供稳定的 ``code``、
``kind``、``subject``、``since``、``remove_in`` 和 ``replacement`` 字段；``kind`` 只能是
``symbol``、``config_key``、``entry_point`` 或 ``serialized_field``。调用方只能依赖这些字段，
不应解析完整英文消息。

每个弃用项必须同时写入 changelog 和迁移文档。``since`` 是首次发出警告的稳定包版本；
``remove_in`` 是最早允许删除的 major 版本；存在替代接口时 ``replacement`` 不得为空。

.. _dep-window-001:

DEP-WINDOW-001：最短支持窗口
----------------------------

稳定 Python symbol、配置 key 和 entry-point group 在首次稳定版本发出警告后，必须至少继续支持
**两个后续 minor release 且满 180 天**。两个条件必须同时满足；时间先到或版本先到都不能提前删除。
例如在 ``1.1.0`` 首次警告的接口，最早也要经过 ``1.2.0``、``1.3.0`` 且满 180 天，才能进入满足
删除条件的下一个 major。

同一支持窗口内，旧名称和新名称必须产生相同规范化结果。配置同时提供旧 key 和新 key 且值冲突时
必须报错，不能静默任选其一。entry point 的旧名和新名同时安装造成歧义时也必须确定性报错。

.. _dep-removal-001:

DEP-REMOVAL-001：删除与 wire format
------------------------------------

满足最短窗口只代表可以计划删除；稳定 Python symbol、配置 key 和 entry-point group 只能在下一个
包 major 中删除。序列化 reader 必须在当前 ``SERIALIZATION_CONTRACT_VERSION`` major 内继续接受
已发布字段；字段删除、重命名、类型或含义变化只能进入新的序列化 contract major，并提供显式迁移。
包版本、Python 公共 API、配置 Schema 与序列化格式是独立版本轴，任一轴升级不得自动授权另一轴
删除兼容行为。

.. _dep-exception-001:

DEP-EXCEPTION-001：安全与法律例外
---------------------------------

只有正在被利用的安全漏洞、可导致数据损坏的严重缺陷，或继续分发会违反法律及许可证义务时，才可
缩短上述窗口。维护便利、实现复杂、依赖升级或使用量低不构成例外。

例外必须由维护者在公开 security advisory、release note 或法律可公开的决策记录中说明影响范围、
受影响版本、停止支持日期和恢复方案；能够提供兼容替代时必须同时提供。涉及未公开漏洞时可以暂缓
技术细节，但发布时必须给出可审计的 advisory 标识。
