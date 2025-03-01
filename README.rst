iamai - Rule Engine Workspace
=============================

.. image:: https://img.shields.io/badge/Python-3.9%2B-blue?logo=python&logoColor=white
    :target: https://www.python.org/
.. image:: https://img.shields.io/badge/License-MIT-green
    :target: LICENSE

一个现代化的异步规则引擎工作空间，支持插件化扩展和AI模型集成。

Features
--------
* 🚀 **全异步架构** - 基于asyncio的高性能事件处理
* 🧩 **插件系统** - 支持Discord/Slack/Web等多平台接入
* 🧠 **AI集成** - 本地模型与API模型统一接口
* 📜 **规则DSL** - 声明式规则定义语法
* 🏗 **模块化设计** - 核心引擎/插件/模型解耦
* 📊 **状态管理** - 支持复杂状态机和工作流

目录结构
--------
::

    rule-engine-workspace/
    ├── pyproject.toml
    ├── config/
    │   └── settings.toml
    ├── src/
    │   └── rule_engine/
    │       ├── core/          # 引擎核心
    │       ├── plugins/       # 平台插件
    │       ├── models/        # 模型抽象
    │       ├── dsl/           # 规则语法
    │       └── utils/         # 工具模块
    ├── examples/             # 使用示例
    ├── tests/                # 单元测试
    └── docs/                 # 文档资源

快速开始
--------

安装依赖
^^^^^^^^
.. code:: bash

    pip install poetry
    poetry install

基本用法
^^^^^^^^
.. code:: python

    from rule_engine import AsyncRuleEngine, RuleBuilder

    engine = AsyncRuleEngine()

    # 定义业务规则
    ruleset = (
        RuleBuilder("fraud_detect")
        .when_all(
            lambda m: m.amount > 10000,
            lambda m: m.location != "CN"
        )
        .then(lambda ctx: print("Risk detected!"))
        .build()
    )

    engine.register_ruleset(ruleset)

    # 处理事件
    async def main():
        await engine.post_event({
            "amount": 15000,
            "location": "US"
        })

    asyncio.run(main())

核心特性
--------

插件系统
^^^^^^^^
.. code:: python

    from rule_engine.plugins import DiscordPlugin

    # 初始化插件
    discord_plugin = DiscordPlugin(
        token="BOT_TOKEN",
        channel="ALERT_CHANNEL"
    )

    # 注册消息处理
    @discord_plugin.on_message
    async def handle_message(msg):
        await engine.process(msg)

AI模型集成
^^^^^^^^^
.. code:: python

    from rule_engine.models import ModelFactory

    # 本地模型
    local_llm = ModelFactory.create({
        "type": "local",
        "path": "models/llm-v1.bin"
    })

    # API模型
    api_llm = ModelFactory.create({
        "type": "api",
        "endpoint": "https://api.llm.com/v1",
        "key": "API_KEY"
    })

高级功能
--------

状态机
^^^^^^
.. code:: python

    from rule_engine.core import StateMachine

    sm = StateMachine("order")

    @sm.state("created")
    async def created_state(ctx):
        if ctx.event.type == "payment":
            await ctx.transition("paid")

    @sm.state("paid")
    async def paid_state(ctx):
        if ctx.event.type == "ship":
            await ctx.transition("shipped")

定时任务
^^^^^^^^
.. code:: python

    from rule_engine.core import cron

    @cron("*/5 * * * *")
    async def health_check():
        print("System health check...")

贡献指南
--------
欢迎通过 issue 或 PR 参与贡献，请遵循以下步骤：

1. Fork 本仓库
2. 创建特性分支 (git checkout -b feature/amazing-feature)
3. 提交修改 (git commit -m 'Add amazing feature')
4. 推送分支 (git push origin feature/amazing-feature)
5. 发起 Pull Request

许可证
------
本项目采用 `MIT 许可证`_ 发布

.. _MIT 许可证: https://choosealicense.com/licenses/mit/