Runtime 生命周期与 Context 契约
================================

本页定义 iamai 1.0 的 ``Runtime``、``Adapter``、``Plugin`` 和 ``Context``
公共行为。条款中的“必须”“不得”和“仅”是规范性要求；每条要求使用稳定 ID，供
conformance matrix、自动测试和发布检查引用。

生命周期状态由 ``Runtime`` 统一管理。扩展可以实现启动、关闭和消息处理钩子，但不得绕过
Runtime 的 admission、排序、回滚或失效边界。

冷启动与失败清理
----------------

.. _lif-start-001:

LIF-START-001：冷启动顺序
~~~~~~~~~~~~~~~~~~~~~~~~~

冷启动必须按以下顺序执行：配置 logging 和内建依赖，发现并实例化 Plugin，按依赖关系解析
Plugin 顺序，发现并实例化 Adapter，依次执行 Plugin ``startup()``，最后才允许 Adapter
``start()`` 接收事件。所有 Plugin 启动成功之前，Adapter 不得开始对外服务。

重复调用已成功完成的 ``bootstrap()`` 必须是空操作，不得重复创建扩展实例或重复执行
``startup()``。

.. _lif-start-002:

LIF-START-002：冷启动回滚与原始异常
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

任一 Plugin ``startup()`` 失败或被取消时，Runtime 必须关闭已经构造的 Adapter，并按启动顺序的
逆序对已成功启动的 Plugin 执行 ``shutdown()``。清理是 best-effort：单个清理错误不得阻止后续
清理，也不得替换触发回滚的原始异常。清理完成后，调用方必须收到同一个原始异常或取消信号，
失败的 Runtime 不得被标记为已启动。

.. _lif-adapter-001:

LIF-ADAPTER-001：Adapter 运行失败
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Adapter ``start()`` 在运行期抛出的非取消异常必须结束 ``serve()``，并把原始 Adapter 异常交还
调用方。Runtime 必须先进入统一 ``shutdown()`` 路径；其他 Adapter、handler 和 Plugin 的清理
错误不得替换该原始异常。Runtime 主动停止或替换 Adapter 造成的 ``CancelledError`` 不属于
Adapter 运行失败。

正常关闭
--------

.. _lif-shutdown-001:

LIF-SHUTDOWN-001：best-effort 幂等关闭
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``shutdown()`` 必须先停止接收新 handler，取消仍在评估或等待的工作，再关闭 Adapter，最后按
Plugin 启动顺序的逆序保存状态并执行 ``shutdown()``。每个 Adapter 和 Plugin 都必须获得一次
清理机会；一个扩展的保存或关闭错误不得跳过其后的扩展。

一次关闭完成后，后续 ``shutdown()`` 调用必须是空操作，不得再次调用 Adapter ``close()``、
Plugin 状态保存或 Plugin ``shutdown()``。关闭期间收到的重复调用必须由同一 lifecycle lock
串行化。

Reload 与 handler admission
---------------------------

.. _lif-reload-001:

LIF-RELOAD-001：暂停 admission 与 generation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Plugin reload、配置 reload 和 shutdown 必须先暂停 handler admission，并推进 Runtime handler
generation。reload 必须先让已执行的 handler pipeline drain 或取消，再在 staging 之前推进
generation；shutdown 必须在取消 active handler 前推进 generation。暂停后到恢复前的新事件必须返回
未接纳；旧 generation 的规则评估结果和 handler job 不得进入执行队列。一次事件匹配出的完整
handler 集合必须原子接纳：容量不足或 generation 已变化时，不得只调度其中一部分。

.. _lif-reload-002:

LIF-RELOAD-002：drain、cancel 与 drop
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

进入 lifecycle 过渡时，Runtime 必须取消尚未完成的事件评估，并丢弃排队但未开始的 handler。
reload 必须允许正在执行的 handler 在 ``handler_shutdown_timeout_seconds`` 内 drain；超时后取消
剩余 handler。shutdown 可以立即取消正在执行的 handler。被 lifecycle 丢弃的工作必须以
``lifecycle`` 或 ``stale_generation`` 原因计入 drop metric，不得在过渡完成后复活。

.. _lif-reload-003:

LIF-RELOAD-003：事务化 Plugin reload
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Plugin reload 必须先保留旧 Plugin 集合，再构造新集合并按解析后的顺序执行新 Plugin
``startup()``。只有全部新 Plugin 启动成功后，reload 才能提交新集合并逆序关闭旧集合。

若构造、启动或 watch snapshot 失败，Runtime 必须逆序关闭本次已启动的新 Plugin、恢复旧 Plugin
集合，并重新抛出原始异常。回滚清理错误不得替换原始异常。无论成功或失败，lifecycle 过渡结束后
只要 Runtime 尚未停止，就必须恢复 handler admission。

.. _lif-reload-004:

LIF-RELOAD-004：事务化配置 reload
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

配置 reload 必须把新配置、state backend、依赖表、Plugin 和 Adapter 作为一个 staging 集合。
提交前失败时，Runtime 必须关闭 staging Adapter、逆序关闭已启动的 staging Plugin，并恢复旧配置、
路径、state backend、依赖表和扩展映射。旧 Adapter 和旧 Plugin 在失败路径上必须继续保持当前集合。

staging 全部成功后，Runtime 才能提交新集合；正在 ``serve()`` 时必须关闭旧 Adapter 后启动新
Adapter，随后逆序关闭旧 Plugin。提交前的异常必须保持为原始异常，不能被回滚清理错误覆盖。

.. _lif-order-001:

LIF-ORDER-001：扩展顺序
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Plugin 启动顺序必须满足 ``requires``、已安装的 ``optional_requires``、``load_before`` 和
``load_after`` 形成的拓扑约束；无约束节点按配置来源顺序、``priority`` 和名称稳定排序。依赖缺失
或成环必须在任何 Plugin 启动前失败。Plugin 关闭与回滚清理使用实际启动顺序的逆序。

Adapter 在 Plugin 全部启动后才开始服务，并在 Plugin 关闭前完成关闭。middleware 在 phase 内按
``priority`` 和 Plugin load index 稳定排序。

Context 公共契约
----------------

.. _ctx-scope-001:

CTX-SCOPE-001：事件作用域
~~~~~~~~~~~~~~~~~~~~~~~~~

Runtime 必须为每个匹配并获准执行的 handler 创建独立 ``Context``。该对象绑定一个 Runtime、
Adapter、Plugin、Event、handler 和本次匹配结果；不得作为另一个事件或 handler 的 Context
复用。handler 与围绕它执行的 middleware 共享同一个 Context。``wait_for_message()`` 成功时返回
收到的新 Event 对应的新 Context，而不是改写原对象。

事件作用域是所有权边界，不代表可以把 Context 作为长期后台任务句柄。需要跨事件保存的数据必须
复制到 Plugin state、Runtime shared state 或调用方自有结构中。

.. _ctx-route-001:

CTX-ROUTE-001：回复与 API 路由
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``reply(message)`` 必须通过当前 Context 的 Adapter 发送，并携带当前 Event 作为默认回复目标。
``send(message, target=...)`` 必须通过同一 Adapter 向显式目标发送；它不得隐式继承当前 Event。
``call_api(action, **params)`` 必须原样委托给同一 Adapter。字符串消息在发送前必须经
``Message.ensure()`` 规范化。

.. _ctx-di-001:

CTX-DI-001：依赖解析优先级
~~~~~~~~~~~~~~~~~~~~~~~~~~

handler、middleware、rule 和 permission 的参数必须按以下优先级解析，命中后立即停止：

#. 当前调用注入的额外参数，例如 ``call_next``、``result`` 或 ``error``；
#. 参数默认值中的显式 ``Depends``；
#. 按标准参数名或精确类型注解识别的 Context 内建对象；
#. ``Context.matches`` 中的同名匹配值；
#. Runtime 注册的同名依赖；
#. Python 参数默认值。

没有任何来源的必需参数必须抛出 ``TypeError``。``Depends`` provider 可以是值、同步 callable 或
异步 callable；嵌套 provider 必须沿用当前 Context 和同一依赖缓存。

.. _ctx-di-002:

CTX-DI-002：依赖缓存边界
~~~~~~~~~~~~~~~~~~~~~~~~

rule 与 permission 在一次 handler 匹配评估中共享一个依赖缓存。被接纳后的 handler 及其
``before``、``around``、``after``、``error`` middleware 链共享另一个依赖缓存。缓存不得跨
handler、Context、Event 或 Runtime generation 复用；``Depends(use_cache=False)`` 每次解析都
必须重新执行 provider。

.. _ctx-invalid-001:

CTX-INVALID-001：generation 失效
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Context 必须记录创建时的 Runtime handler generation。reload 或 shutdown 推进 generation，或
Runtime 已收到停止信号后，旧 Context 的 ``is_valid`` 必须为 false。旧 Context 上的 Runtime 绑定
操作，包括配置/状态访问、reply/send/API、等待消息、请求 reload 和 DI 解析，必须抛出
``ContextInvalidatedError``，不得向新 generation 产生副作用。session backlog 中的旧 Context
必须被丢弃。

Event、匹配值等纯快照可以由调用方复制后检查，但这不恢复 Context 的有效性。

.. _ctx-lifecycle-001:

CTX-LIFECYCLE-001：Context 不拥有生命周期
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``Context`` 不得直接执行、提交或解锁 Runtime lifecycle 过渡。``reload_plugins()`` 只向 Runtime
提交一个 lifecycle request，使真正的 reload 在当前 handler 任务之外由 Runtime 串行执行；该
方法不得让调用中的 handler 与 reload 相互等待。配置 reload、shutdown、admission 恢复和回滚
仍完全由 Runtime 负责。

版本与兼容性
------------

本契约属于 1.0 公共 API。修订说明可以澄清措辞或增加测试映射，但不得在同一 major 内改变上述
顺序、异常身份、路由目标、缓存边界或失效条件。条款与验证证据的最终映射由 1.0 conformance
matrix 维护。
