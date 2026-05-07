第四步：Webhook 与生产化约束
=============================

前几章解决的是功能建模。这一章把入口暴露到 HTTP 网络上，因此要同时处理鉴权、验签、
请求体校验、出站回调限制和观测能力。

更接近生产的配置
----------------

.. code-block:: toml

   [runtime]
   adapters = ["webhook"]
   plugins = ["src/echo_runtime/plugins/echo.py:EchoPlugin"]
   superusers = ["webhook-admin"]

   [adapter.webhook]
   host = "0.0.0.0"
   port = 8090
   path = "/events"
   access_token = "change-me"
   signature_provider = "github"
   signature_secret = "change-me-too"
   reply_url_allowlist = ["hooks.example.com"]

   [plugin.management]
   allow_reload = true
   allow_introspection = true
   reload_requires_superuser = true
   introspection_requires_superuser = true

这个配置刻意显式写出安全边界：入口需要 token 和签名，管理能力需要 superuser，
出站回调只允许明确域名。

请求进入时发生什么
------------------

Webhook 请求进入后会经过以下步骤：

.. code-block:: text

   HTTP request
     -> access token check
     -> signature verification
     -> JSON/content-type validation
     -> payload normalization
     -> Event dispatch
     -> optional reply_url delivery

任何一步失败，适配器都会记录指标和审计事件，便于排查是鉴权失败、签名失败还是 payload
不符合预期。

验签 provider
-------------

``WebhookAdapter`` 支持三类签名策略：

``generic``
   自定义 HMAC-SHA256 请求头，适合内部系统或没有标准 provider 的平台。

``github``
   兼容 GitHub 的 ``X-Hub-Signature-256``。

``stripe``
   兼容 Stripe 的 ``Stripe-Signature``，包含时间戳窗口和防重放检查。

如果平台本身已有标准签名格式，优先使用 provider；如果没有，再使用 ``generic``。

出站回复
--------

Webhook 事件可以携带 ``reply_url``，但它本质上是外部输入，不能默认信任。iamai 的默认策略
会拒绝 private/loopback 地址、非 HTTPS 地址和重定向。生产环境应使用最小范围的
``reply_url_allowlist``。

上线前检查
----------

运行：

.. code-block:: bash

   uv run python -m iamai --config config.toml config-check

确认以下项都成立：

- 非 loopback 监听配置了 ``access_token``；
- 对公网 webhook 配置了 ``signature_secret``；
- ``reply_url_allowlist`` 只包含可信域名；
- 管理插件命令只允许 superuser 执行；
- ``/metrics`` 能看到请求、拒绝、handler 执行和错误指标；
- 日志里能看到结构化 audit 事件。

Checkpoint
----------

到这里你已经把一个本地 Runtime 推进到可暴露网络的形态。后续新增平台时，优先把协议差异放进
Adapter，把业务逻辑留在 Plugin。
