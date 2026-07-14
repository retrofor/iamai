配置参考
========

``[runtime]``
-------------

``log_level``
   日志级别。默认 ``INFO``。

``command_prefixes``
   命令前缀列表。默认 ``["/"]``。

``adapters``
   要加载的适配器名、entry point 名或导入路径。

``plugins`` / ``plugin_dirs``
   显式插件 entry point、导入路径和插件目录。

``auto_discover_plugins``
   是否自动加载已安装包声明的 ``iamai.plugins`` entry points。默认 ``false``。

``auto_discover_adapters``
   是否自动加载已安装包声明的 ``iamai.adapters`` entry points。默认 ``false``。

``python_paths``
   额外导入路径。默认必须位于配置根目录内。

``allow_external_paths``
   是否允许引用配置根目录外的路径。生产环境应保持 ``false``。

``superusers``
   管理命令和敏感操作的特权用户 ID。

``max_concurrent_handlers``
   同时执行的 handler 上限。达到上限时，事件分发会等待空位，默认 ``64``。

``session_backlog_max_keys`` / ``session_backlog_per_key``
   等待会话建立前可暂存的会话 key 总数和每个 key 的消息数，默认分别为 ``1024`` 和 ``3``。

``session_backlog_ttl_seconds``
   等待会话 backlog 的保留秒数，默认 ``300``。过期消息不会交给新 waiter。

``[logging]``
-------------

``level``
   Loguru 和标准库日志接入的级别。默认继承 ``[runtime].log_level``。

``stderr``
   是否输出到 stderr。默认 ``true``。

``file``
   可选日志文件路径。相对路径按配置文件目录解析。

``rotation`` / ``retention`` / ``compression``
   文件 sink 的轮转、保留和压缩策略，直接传给 Loguru。

``serialize``
   是否输出 JSON 日志。默认 ``false``。

``backtrace`` / ``diagnose``
   Loguru 异常诊断选项。生产环境建议保持 ``diagnose = false``，避免泄露上下文敏感值。

``intercept_stdlib`` / ``capture_warnings``
   是否把标准库 ``logging`` 和 Python warnings 汇入 Loguru 链路。默认都启用。

``[adapter.onebot11]``
-----------------------

``mode``
   ``ws``、``ws-reverse`` 或 ``http``。

``access_token``
   反向连接和 HTTP 模式的鉴权 token。非 loopback 监听默认必须配置。

``allow_query_token``
   是否允许通过 query string 传 token。默认 ``false``。

``open_timeout`` / ``max_size`` / ``read_timeout`` / ``max_body_bytes``
   websocket 和 HTTP 边界限制。

``[adapter.webhook]``
----------------------

``access_token``
   Bearer token。对公网部署建议始终配置。

``signature_provider``
   ``generic``、``github`` 或 ``stripe``。

``signature_secret``
   HMAC 签名密钥。

``timestamp_tolerance_seconds``
   签名时间窗。默认 ``300``。

``allow_event_reply_url``
   是否信任事件 payload 中提供的 ``reply_url``。默认 ``false``。

``reply_url_allowlist``
   允许回调的 hostname 列表。

``[adapter.telegram]``
----------------------

``token``
   Telegram Runtime token。生产环境不要提交到仓库。

``api_base_url``
   Bot API 地址。默认 ``https://api.telegram.org``，私有 Bot API Server 可覆盖。

``poll_timeout``
   ``getUpdates`` 长轮询等待秒数。默认 ``30``。

``request_timeout``
   单次 HTTP 请求超时秒数。默认 ``40``。

``reconnect_interval``
   轮询失败后的重试间隔。默认 ``3``。

``limit``
   每次最多拉取的 update 数量。默认 ``100``。

``offset``
   初始 update offset。一般不需要配置，适合迁移或跳过旧消息。

``allowed_updates``
   Telegram update 类型列表。默认只拉取 ``["message"]``。

``[state]``
-----------

``backend``
   ``memory``、``json`` 或 ``sqlite``。

``path``
   JSON 或 SQLite 后端的存储路径。
