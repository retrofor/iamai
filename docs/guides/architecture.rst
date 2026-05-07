架构概览
========

iamai 的核心设计是把协议边界和业务插件分开。Adapter 负责和外部世界打交道，
Plugin 只处理统一事件和上下文。这样做的价值不是“抽象更漂亮”，而是当平台、鉴权方式、
部署方式变化时，业务代码不必跟着重写。

运行时分层
----------

.. code-block:: text

   Plugin callbacks
       ↓
   Context / DI / Rule / Permission / Middleware
       ↓
   Runtime runtime
       ↓
   Adapter boundary
       ↓
   Rust core helpers (_core)

``Runtime``
   负责配置装配、插件发现、依赖注入、事件分发、适配器生命周期、热重载、状态存取和观测。

``Adapter``
   负责把外部协议转换成统一 ``Event``，并把 ``Message`` 发回目标平台。网络鉴权、验签、
   payload 归一化、出站回调限制都属于 Adapter 边界。

``Plugin``
   负责业务逻辑。插件用 decorator 声明 handler 和 middleware，通过 ``Context`` 获取配置、
   状态、事件、回复方法和运行时服务。

``Event`` / ``Message``
   是协议中间层。插件可以读取 ``event.raw``，但稳定业务逻辑应优先依赖统一字段。

一次事件的生命周期
------------------

下面这张 Mermaid 泳道图把启动、事件分发、回复、热重载和关闭放在同一条链路里。横向泳道表示
职责边界，纵向顺序表示主要生命周期阶段。

.. mermaid::
   :caption: iamai 工作流程、链路和生命周期泳道图

   flowchart TB
     classDef external fill:#ecfeff,stroke:#0891b2,color:#0f172a
     classDef adapter fill:#eef2ff,stroke:#4f46e5,color:#0f172a
     classDef runtime fill:#f0fdf4,stroke:#16a34a,color:#0f172a
     classDef plugin fill:#fff7ed,stroke:#ea580c,color:#0f172a
     classDef state fill:#f8fafc,stroke:#64748b,color:#0f172a
     classDef terminal fill:#fef2f2,stroke:#dc2626,color:#0f172a

     subgraph external_lane["外部协议 / 平台"]
       E1["Webhook / WebSocket / Long polling / Terminal input"]:::external
       E2["Platform API response"]:::external
     end

     subgraph adapter_lane["Adapter 生命周期"]
       A0["construct adapter from [adapter.*] config"]:::adapter
       A1["start(): connect / listen / poll"]:::adapter
       A2["validate auth, signature, content-type"]:::adapter
       A3["normalize payload -> Event"]:::adapter
       A4["send_message() / call_api()"]:::adapter
       A5["close network resources"]:::adapter
     end

     subgraph runtime_lane["Runtime 编排"]
       R0["load config and state backend"]:::runtime
       R1["discover plugins and adapters"]:::runtime
       R2["plugin startup()"]:::runtime
       R3["emit(Event)"]:::runtime
       R4["session waiters"]:::runtime
       R5["match command / message / event handlers"]:::runtime
       R6["Rule + Permission + DI"]:::runtime
       R7["schedule handler task"]:::runtime
       R8["reload_plugins() / reload_config()"]:::runtime
       R9["plugin shutdown() and adapter stop"]:::runtime
     end

     subgraph plugin_lane["Plugin 生命周期"]
       P0["declare handlers and middleware"]:::plugin
       P1["read config_obj and plugin state"]:::plugin
       P2["before / around middleware"]:::plugin
       P3["handler(ctx, injected deps)"]:::plugin
       P4["ctx.reply() / ctx.runtime services"]:::plugin
       P5["after / error middleware"]:::plugin
     end

     subgraph state_lane["状态 / 观测 / 管理"]
       S0["state store load/save"]:::state
       S1["metrics and audit trace"]:::state
       S2["management commands / HTTP API"]:::state
     end

     R0 --> R1 --> A0 --> A1
     R1 --> P0 --> R2 --> P1
     R0 <--> S0
     E1 --> A2 --> A3 --> R3 --> R4 --> R5 --> R6 --> R7
     R7 --> P2 --> P3 --> P4 --> A4 --> E2
     P3 --> P5 --> S1
     R3 --> S1
     S2 --> R8 --> R1
     R8 --> R9
     R9 --> A5

.. code-block:: text

   external protocol
     -> Adapter validates and normalizes payload
     -> Adapter.emit(Event)
     -> Runtime checks session waiters
     -> Runtime matches command/message/event handlers
     -> Rule and Permission run with DI
     -> Middleware phases wrap handler execution
     -> Context.reply() delegates back to Adapter

这个流程决定了调试顺序：先看适配器有没有收到事件，再看事件是否归一化正确，
然后看 handler 匹配、规则、权限和中间件。

Rust 核心的作用
---------------

Rust 扩展承担高频、结构稳定的底层能力：

- 消息链操作；
- OneBot11 事件归一化；
- JSON 配置深度合并。

Python 层保留插件开发体验、动态加载、依赖注入和运维能力。两层边界清晰后，性能和可扩展性
不需要互相牺牲。

热重载模型
----------

插件热重载会保存旧插件状态、重新导入插件模块、启动新插件，然后替换运行时插件集合。
配置热重载还会重建状态后端和适配器。失败时，运行时会回滚到旧配置和旧插件。

这意味着插件的 ``startup`` 和 ``shutdown`` 必须可重复执行，不要把不可恢复的副作用藏在
模块 import 顶层。
