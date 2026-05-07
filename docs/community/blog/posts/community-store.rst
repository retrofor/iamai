---
id: community.store
title: 社区商店如何承载插件、适配器与 Agent 工具
summary: 社区商店把扩展元数据、安全声明、运行时能力和 entry point 统一成可审核的静态 registry。
author: iamai maintainers
published_at: 2026-04-25
category: 社区建设
tags: [community, store, extensions]
---

:orphan:

社区商店如何承载插件、适配器与 Agent 工具
=========================================

社区商店不是运行时依赖源，而是一个可审核、可版本化的扩展索引。每个条目都应该说明
包名、仓库、entry point、安全声明、运行时能力和需要的权限。

提交入口现在放在商店页面标题区域，维护者可以继续通过 GitHub issue 审核字段，再把
合格条目合入 ``docs/ecosystem/entries/*.json``。
