Event 与 Message 序列化契约
============================

本页定义 iamai 1.x 稳定的跨进程序列化格式。它适用于持久化、队列、审计日志和第三方扩展之间的
兼容交换。该契约已随 ``1.0.0rc1`` 完成验证，并在 ``1.0.0`` 正式发布时生效。当前契约由顶层常量
``iamai.SERIALIZATION_CONTRACT_VERSION`` 标识。条款中的“必须”“不得”和“仅”是规范性要求；
每条要求使用稳定 ID，验证映射见 :doc:`public-api-conformance`。

.. note::

   Provisional ``iamai.harness`` 使用独立版本的 Harness JSONL 来保存 Experiment 与 Trajectory。
   它不读取或写入 ``SERIALIZATION_CONTRACT_VERSION``，也不属于本契约；Harness artifact 格式可以
   在 ``1.x`` 内独立迭代，而不会改变稳定 Event/Message wire format。

.. _ser-version-001:

SER-VERSION-001：稳定入口与版本
-------------------------------

``Event.to_payload()``、``Event.from_payload()``、``Message.to_payload()`` 和
``Message.from_payload()`` 是 1.x 稳定序列化 API；对应的 ``to_json()`` 和 ``from_json()``
在同一契约上编码和解码 JSON 文本。

``Event.to_dict()``、``Event.from_dict()``、``Message(...)``、``Message.segments`` 和 OneBot
转换接口仍是 adapter 使用的 legacy normalization 或便捷接口。它们可以接受协议特定输入，
不声明版本，也不属于本页的稳定 wire format。稳定 reader 不会猜测无版本 payload；调用方必须
显式选择正确接口。

.. _ser-message-001:

SER-MESSAGE-001：Message payload
--------------------------------

Message 的 canonical payload 是一个对象：

.. code-block:: json

   {
     "contract_version": "1.0",
     "segments": [
       {
         "kind": "text",
         "data": {"text": "hello"}
       }
     ]
   }

``contract_version`` 和 ``segments`` 都是必需字段。``contract_version`` 必须是 ``"1.0"``
或 reader 支持的同一 major 版本；``segments`` 必须是数组。每个 segment 必须是对象，包含非空
字符串 ``kind`` 和对象 ``data``。未知 ``kind`` 合法，``data`` 中的未知 key 以及 string、number、
boolean、null、array、object 等标准 JSON 类型必须按下述数值域原样保留。整数支持最多 4096 位十进制
数字；带小数点或指数的 number 使用有限 IEEE-754 binary64，文本最长 128 个字符、最多 17 位有效
十进制数字，且不得上溢或下溢。超出该数值域或文本上限的输入以 ``invalid_number`` 拒绝，不会静默
量化，也不会先构造无界大数。segment 的顺序属于契约，对象 key 顺序不属于契约。

.. _ser-event-001:

SER-EVENT-001：Event payload
----------------------------

Event 的 canonical payload 是一个对象：

.. code-block:: json

   {
     "contract_version": "1.0",
     "id": "evt-1",
     "adapter": "demo",
     "platform": "test",
     "type": "message",
     "detail_type": null,
     "sub_type": null,
     "user_id": null,
     "channel_id": null,
     "guild_id": null,
     "self_id": null,
     "message": {
       "contract_version": "1.0",
       "segments": []
     },
     "raw": {}
   }

必需字段是 ``contract_version``、``id``、``adapter``、``platform``、``type`` 和 ``message``。
四个必需标识字段必须是非空字符串；``message`` 必须是上述 versioned Message payload。
``detail_type``、``sub_type``、``user_id``、``channel_id``、``guild_id`` 和 ``self_id`` 是可选的
字符串或 null，缺失时 canonical writer 补 null。``raw`` 是可选对象，缺失时补空对象，其中的标准
JSON 值必须原样保留。

.. _ser-unknown-001:

SER-UNKNOWN-001：未知字段
--------------------------

同一 major 的 reader 忽略 Event、Message 和 segment 对象中的未知结构字段；canonical writer
不会重新输出这些未知结构字段。因此稳定 API 不是未知 envelope 字段的无损透明代理。唯一例外是
segment ``data`` 和 Event ``raw``：它们是明确的扩展容器，内部未知字段和值必须保留。

.. _ser-canonical-001:

SER-CANONICAL-001：canonical writer
-----------------------------------

writer 总是输出当前 ``SERIALIZATION_CONTRACT_VERSION``，补齐上述默认字段，并拒绝 NaN、
Infinity、bytes、非字符串对象 key 和其他非 JSON 值。字符串字段不会隐式调用 ``str()``。

.. _ser-error-001:

SER-ERROR-001：错误与资源边界
-----------------------------

稳定 reader 和 writer 以 ``SerializationContractError`` 报告错误。调用方可以依赖 ``code`` 和
``path``，不应依赖完整英文消息。公开错误码为 ``invalid_json``、``duplicate_key``、
``expected_object``、``expected_array``、``missing_field``、``expected_string``、
``empty_string``、``invalid_contract_version``、``unsupported_contract_version``、
``invalid_number``、``invalid_json_key``、``invalid_json_value``、``cyclic_value``、
``nesting_too_deep`` 和 ``invalid_message``。为避免资源耗尽，payload 的 JSON 容器嵌套不得超过
100 层。

.. _ser-evolution-001:

SER-EVOLUTION-001：版本演进
---------------------------

版本字符串使用 ``MAJOR.MINOR``。reader 接受同一 major 的任意 minor，拒绝缺失、格式错误和不同
major。1.x 的同一 major 内只允许新增可选字段、放宽枚举或新增未知 segment kind；不得新增必需
字段、重命名字段、改变字段类型、含义或默认值、收窄枚举，也不得改变未知字段处理规则。

新 reader 读取旧 minor 时补当前默认值；旧 reader 读取新 minor 时忽略新增可选字段。writer 始终
输出当前版本。不同 major 之间必须通过显式迁移，不允许 stable loader 猜测或静默升级。

验证证据
--------

``tests/golden/serialization/v1/message-valid.json``、``event-valid.json``、
``event-minimal-valid.json`` 和 ``invalid-cases.json`` 是规范示例的机器可读来源；
``tests/test_serialization_contract.py`` 验证 payload 与 JSON round-trip、future-minor reader、
canonical 输出、未知字段规则、JSON 类型保真以及每个稳定错误码。
