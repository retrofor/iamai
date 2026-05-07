---
id: adapter.conformance
title: 适配器兼容性测试会先固定哪些边界
summary: 适配器 SDK 会优先固定事件归一化、消息编码、API 调用响应和错误处理四类 conformance tests。
author: iamai maintainers
published_at: 2026-04-24
category: 路线图
tags: [adapter, conformance, sdk]
---

:orphan:

适配器兼容性测试会先固定哪些边界
================================

适配器生态需要先稳定行为契约，再追求平台覆盖。短期规范会围绕四类测试展开：
inbound event normalize、outbound message encode、API call response 和错误处理。

第三方适配器包继续使用 ``iamai-adapter-<platform>`` 命名，并通过
``[project.entry-points."iamai.adapters"]`` 暴露实现。
