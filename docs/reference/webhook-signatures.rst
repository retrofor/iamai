Webhook 签名参考
================

Generic
-------

默认 provider 是 ``generic``。签名载荷为：

.. code-block:: text

   <timestamp>.<raw_body>

签名算法为 HMAC-SHA256。默认请求头：

.. code-block:: text

   X-iamai-Signature: sha256=<hex>
   X-iamai-Timestamp: <unix timestamp>

GitHub
------

``signature_provider = "github"`` 使用 GitHub 风格的请求头：

.. code-block:: text

   X-Hub-Signature-256: sha256=<hex>

签名载荷为原始请求体。

Stripe
------

``signature_provider = "stripe"`` 使用 Stripe 风格的请求头：

.. code-block:: text

   Stripe-Signature: t=<timestamp>,v1=<hex>

签名载荷为：

.. code-block:: text

   <timestamp>.<raw_body>

安全行为
--------

所有 provider 都使用常量时间比较。带时间戳的 provider 会检查时间窗，并在进程内记录
已见过的签名以拒绝重放。
