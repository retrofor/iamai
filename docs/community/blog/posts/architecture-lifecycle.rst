---
id: architecture.lifecycle
title: 用泳道图理解 iamai 的运行时生命周期
summary: 从事件进入适配器到插件处理、Agent 工具调用、审计记录和响应返回，梳理运行时链路的职责边界。
author: iamai maintainers
published_at: 2026-04-26
category: 架构笔记
tags: [architecture, runtime, mermaid]
featured: true
---

:orphan:

用泳道图理解 iamai 的运行时生命周期
=======================================

iamai 的核心目标不是把所有能力放进一个平台，而是把协议边界、插件生命周期、
Agent 工具权限和审计链路固定成可测试、可嵌入的运行时约束。

.. mermaid::
   :caption: 运行时生命周期与责任链路

   sequenceDiagram
     participant Platform as 外部平台
     participant Adapter as 协议适配器
     participant Runtime as iamai Runtime
     participant Plugin as 插件/Handler
     participant Agent as Agent Tool
     participant Audit as 审计与日志

     Platform->>Adapter: 原始事件
     Adapter->>Runtime: 归一化 Event
     Runtime->>Audit: 记录 inbound trace
     Runtime->>Plugin: 匹配规则并执行 handler
     Plugin->>Runtime: 读取配置、状态和已注册 handler
     Plugin->>Agent: 请求工具调用
     Agent->>Runtime: 权限声明与审批结果
     Runtime->>Audit: 记录工具输入、输出和审批状态
     Runtime->>Adapter: 编码 Message / API call
     Adapter->>Platform: 发送响应

后续的管理 API、权限注册表和运行时检查都会沿着这条链路落地，避免把 WebUI 或沙箱
提前塞进核心。
