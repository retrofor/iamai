运维与安全
==========

iamai 的生产化原则是默认保守：开发便利不能自动变成生产默认。上线前应把入口鉴权、
管理命令、出站回调、日志和指标都写进配置和检查流程。

管理命令
--------

内置管理插件默认关闭 reload 和 introspection。即使显式打开，也建议：

- 配置 ``runtime.superusers``；
- 保持 ``reload_requires_superuser = true``；
- 保持 ``introspection_requires_superuser = true``；
- 在审计日志中跟踪 reload 和 config reload。

Webhook 暴露面
--------------

对公网 ``WebhookAdapter`` 至少配置：

.. code-block:: toml

   [adapter.webhook]
   access_token = "change-me"
   signature_secret = "change-me-too"
   reply_url_allowlist = ["hooks.example.com"]

除非上游协议强依赖事件自带回调地址，否则保持 ``allow_event_reply_url = false``。

OneBot11 暴露面
---------------

对外监听的 ``ws-reverse`` 和 ``http`` 模式应配置 ``access_token``。同时建议：

- 不启用 ``allow_query_token``，除非上游无法发送 ``Authorization`` 头；
- HTTP 模式保留 JSON content-type 约束；
- 监听地址放在反向代理或内网边界后；
- 不把协议 API token 写进日志或管理命令输出。

审计和指标
----------

运行时内置：

``RuntimeMetrics``
   进程内计数器，适合健康检查和轻量观测。

``AuditLogger``
   结构化 JSON 日志，适合记录安全相关运行时事件。

默认重点记录：

- webhook / onebot HTTP 请求接受与拒绝；
- token、签名、content-type 失败；
- 适配器启动失败；
- 插件和配置重载结果；
- webhook 回复发送、丢弃和错误。
- handler 队列满、生命周期切换造成的任务丢弃。

可以通过管理命令查看：

.. code-block:: text

   /health
   /metrics

日志链路
--------

iamai 使用 Loguru 配置运行时日志，并把标准库 ``logging``、适配器日志、审计日志和运行时调度日志
汇入同一条链路。最小配置可以继续使用 ``[runtime].log_level``；更完整的配置使用 ``[logging]``：

.. code-block:: toml

   [logging]
   level = "INFO"
   stderr = true
   file = "logs/iamai.log"
   rotation = "10 MB"
   retention = "14 days"
   serialize = false
   backtrace = false
   diagnose = false
   intercept_stdlib = true
   capture_warnings = true

``file`` 使用相对路径时会相对配置文件目录解析。生产环境建议关闭 ``diagnose``，避免异常上下文里出现
敏感值；需要 JSON 日志时设置 ``serialize = true``。调试 handler 匹配和 management 权限时，把
``level`` 临时调到 ``DEBUG``，日志会显示匹配到的 handler 和被权限拒绝的 handler。

管理 HTTP API
-------------

需要让外部运维系统读取状态时，可以启用可选 ``management_api`` 插件。它只提供 JSON 诊断端点，
不提供 WebUI，默认应绑定在本机或受信任网络内：

.. code-block:: toml

   [runtime]
   builtin_plugins = ["management", "management_api"]

   [plugin.management_api]
   host = "127.0.0.1"
   port = 8765
   token = "change-me"

请求必须携带 ``Authorization: Bearer <token>``。初版端点包括 ``/health``、``/metrics``、
``/adapters``、``/plugins``、``/sessions``、``/schema`` 和只读摘要 ``/state``。

SSRF 与回调地址
---------------

Webhook 出站回复默认启用 URL 约束：

- scheme allowlist；
- hostname allowlist；
- private / loopback 地址拒绝；
- 禁止跟随重定向。

这主要是为了避免把上游事件当作任意内网跳板。

上线检查清单
------------

- ``config-check`` 在 CI 中通过。
- 所有对公网 adapter 都有鉴权。
- Webhook 有签名校验和最小出站 allowlist。
- 管理插件只对 superuser 开放。
- 日志和指标能定位拒绝原因。
- ``max_concurrent_handlers`` 和 ``max_pending_handlers`` 已按流量峰值设置。
- 插件 reload 后不会泄漏后台任务或连接。
