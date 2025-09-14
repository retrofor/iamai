# iamai

> 高级异步Python跨平台规则驱动机器人框架

[![Python Version](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![AsyncIO](https://img.shields.io/badge/async-await-orange.svg)](https://docs.python.org/3/library/asyncio.html)

iamai是一个强大的异步Python跨平台规则驱动机器人框架，支持复杂的规则引擎、多平台适配器、插件系统和会话管理。它结合了现代异步编程的最佳实践和高级规则引擎功能，可以满足复杂机器人的需求。

## ✨ 特性

- 🚀 **异步优先**: 基于Python asyncio，支持高并发处理
- 🧠 **智能规则引擎**: 支持复杂规则定义、条件评估和动作执行
- 🔌 **多平台支持**: Discord、Telegram、Slack、Webhook等平台适配器
- 🎯 **插件系统**: 可扩展的插件架构，支持钩子和生命周期管理
- 💾 **会话管理**: 智能会话状态管理和持久化存储
- 📊 **分析监控**: 内置性能监控、日志记录和通知系统
- ⚙️ **配置管理**: 灵活的YAML配置和热重载支持
- 🛡️ **安全可靠**: 内置安全机制和错误处理

## 🏗️ 架构设计

```
┌─────────────────────────────────────────┐
│               应用层                    │
│  (机器人实例、插件、业务逻辑)           │
└─────────────────────────────────────────┘
┌─────────────────────────────────────────┐
│               规则引擎层                │
│  (规则评估、事实管理、事件处理)         │
└─────────────────────────────────────────┐
┌─────────────────────────────────────────┐
│              平台适配层                 │
│  (Discord/Telegram/Slack/Web等适配器)   │
└─────────────────────────────────────────┘
┌─────────────────────────────────────────┐
│              异步核心层                 │
│  (事件循环、异步IO、并发管理)           │
└─────────────────────────────────────────┘
```

## 🚀 快速开始

### 安装

```bash
pip install iamai
```

### 基本使用

1. **创建配置文件**

```bash
iamai init
```

2. **运行机器人**

```bash
iamai run
```

3. **在控制台中测试**

```
iamai> help
🤖 iamai 帮助信息

可用命令:
• help/帮助 - 显示此帮助信息
• echo <文本> - 回显文本
• time/时间 - 显示当前时间
• stats/统计 - 显示机器人统计信息
• ping - 测试机器人响应
```

## 📝 规则定义

### 基础规则

```python
from iamai.core.rule_engine import rule, when_all

@rule(
    name="welcome_new_user",
    description="欢迎新用户加入",
    priority=100,
    tags=["welcome", "user_management"]
)
async def welcome_new_user_rule(ctx):
    if ctx.event.type == "member_join":
        user = ctx.event.user
        channel = ctx.event.channel
        
        await ctx.post(
            channel=channel,
            message=f"🎉 欢迎 {user.display_name or user.name} 加入我们的社区！"
        )
        
        await ctx.log_action("welcome_user", user_id=user.id)
```

### 高级规则

```python
@rule(
    name="spam_detection",
    description="检测并处理垃圾信息",
    priority=200,
    tags=["moderation", "spam", "security"]
)
async def spam_detection_rule(ctx):
    if ctx.event.type == "message" and ctx.event.message:
        message = ctx.event.message
        user = message.author
        
        # 检查用户是否在短时间内发送了多条消息
        recent_messages = await ctx.find_facts(
            type="message",
            user_id=user.id,
            timestamp__gte=datetime.now() - timedelta(seconds=10)
        )
        
        if len(recent_messages) >= 5:
            await ctx.post(
                channel=message.channel,
                message=f"⚠️ {user.mention or user.name}，请勿发送垃圾信息！"
            )
            
            await ctx.log_action("spam_detection", user_id=user.id)
```

### 工作流规则

```python
@rule(
    name="customer_support_workflow",
    description="客户支持工作流，自动处理支持请求",
    priority=300,
    tags=["workflow", "customer_support", "automation"]
)
async def customer_support_workflow(ctx):
    if ctx.event.type == "support_request":
        request = ctx.event
        user = request.user
        priority = request.get('priority', 'normal')
        
        # 创建支持工单
        ticket_id = f"TICKET-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        await ctx.assert_fact({
            'type': 'support_ticket',
            'ticket_id': ticket_id,
            'user_id': user.id,
            'priority': priority,
            'status': 'open',
            'created_at': datetime.now()
        })
        
        # 启动监控工作流
        workflow_id = await ctx.start_workflow(
            "monitor_support_ticket",
            ticket_id=ticket_id,
            timeout=3600
        )
```

## 🔌 插件系统

### 创建自定义插件

```python
from iamai.core.plugin import Plugin, PluginInfo, plugin_hook

class MyPlugin(Plugin):
    @property
    def info(self) -> PluginInfo:
        return PluginInfo(
            name="my_plugin",
            version="1.0.0",
            description="我的自定义插件",
            author="Your Name",
            hooks=['before_event', 'after_event']
        )
    
    @plugin_hook('before_event', priority=100)
    async def before_event(self, event):
        print(f"处理事件: {event.type}")
    
    @plugin_hook('after_event', priority=100)
    async def after_event(self, event, results):
        print(f"事件处理完成: {len(results)} 个结果")
```

### 内置插件

- **AnalyticsPlugin**: 用户行为分析和性能监控
- **LoggingPlugin**: 详细的日志记录和管理
- **NotificationPlugin**: 多渠道通知（邮件、Webhook、Slack等）
- **CachePlugin**: 智能缓存功能

## 🌐 平台适配器

### Discord适配器

```yaml
adapters:
  - name: "discord"
    class_path: "iamai.adapters.discord.DiscordAdapter"
    enabled: true
    config:
      token: "${DISCORD_TOKEN}"
      intents:
        - "messages"
        - "reactions"
        - "members"
```

### Telegram适配器

```yaml
adapters:
  - name: "telegram"
    class_path: "iamai.adapters.telegram.TelegramAdapter"
    enabled: true
    config:
      token: "${TELEGRAM_TOKEN}"
```

### Webhook适配器

```yaml
adapters:
  - name: "webhook"
    class_path: "iamai.adapters.webhook.WebhookAdapter"
    enabled: true
    config:
      host: "0.0.0.0"
      port: 8080
      path: "/webhook"
      secret: "${WEBHOOK_SECRET}"
```

## ⚙️ 配置管理

### 完整配置示例

```yaml
# 基本信息
name: "Myiamai"
version: "0.1.0"
description: "基于iamai的智能机器人"

# 日志配置
log_level: "INFO"
log_file: "logs/iamai.log"

# 会话配置
session_timeout: 86400  # 24小时
session_cleanup_interval: 1800  # 30分钟

# 规则配置
rules:
  - module: "iamai.examples.rules.basic_rules"
    enabled: true
  - module: "iamai.examples.rules.advanced_rules"
    enabled: true

# 插件配置
plugins:
  - name: "analytics"
    class_path: "iamai.examples.plugins.analytics.AnalyticsPlugin"
    enabled: true
    config:
      database_url: "sqlite:///analytics.db"

# 平台适配器配置
adapters:
  - name: "console"
    class_path: "iamai.adapters.console.ConsoleAdapter"
    enabled: true
    config:
      prompt: "iamai> "
```

## 📊 监控和分析

### 获取统计信息

```python
# 获取机器人统计
stats = await bot.get_stats()
print(f"运行时间: {stats['uptime_seconds']} 秒")
print(f"活跃会话: {stats['sessions']['active_sessions']} 个")
print(f"规则评估: {stats['rules']['total_evaluations']} 次")

# 健康检查
health = await bot.health_check()
print(f"系统状态: {health['status']}")
```

### 性能监控

```python
# 获取规则引擎性能统计
rule_stats = bot.rule_engine.get_performance_stats()
print(f"平均执行时间: {rule_stats['average_execution_time']:.3f} 秒")
print(f"总评估次数: {rule_stats['total_evaluations']}")

# 获取事实库统计
fact_stats = await bot.fact_base.get_stats()
print(f"活跃事实: {fact_stats['active_facts']} 个")
```

## 🛠️ 命令行工具

```bash
# 运行机器人
iamai run

# 使用指定配置文件
iamai run -c config.yaml

# 创建默认配置
iamai init

# 验证配置文件
iamai validate -c config.yaml

# 检查状态
iamai status -c config.yaml
```

## 🔧 开发指南

### 项目结构

```
iamai/
├── core/                 # 核心模块
│   ├── bot.py           # 主机器人类
│   ├── rule_engine.py   # 规则引擎
│   ├── facts.py         # 事实和事件系统
│   ├── session.py       # 会话管理
│   └── plugin.py        # 插件系统
├── adapters/            # 平台适配器
│   ├── base.py         # 适配器基类
│   ├── console.py      # 控制台适配器
│   ├── discord.py      # Discord适配器
│   ├── telegram.py     # Telegram适配器
│   ├── slack.py        # Slack适配器
│   └── webhook.py      # Webhook适配器
├── config/              # 配置管理
│   └── config.py       # 配置类
├── examples/            # 示例代码
│   ├── rules/          # 示例规则
│   └── plugins/        # 示例插件
└── utils/               # 工具函数
```

### 扩展开发

1. **创建自定义适配器**

```python
from iamai.adapters.base import PlatformAdapter

class MyAdapter(PlatformAdapter):
    async def connect(self):
        # 连接逻辑
        pass
    
    async def send_message(self, channel, content, **kwargs):
        # 发送消息逻辑
        pass
```

2. **创建自定义规则**

```python
from iamai.core.rule_engine import Rule, RuleCondition, RuleAction

def my_rule_handler(ctx):
    # 规则处理逻辑
    pass

my_rule = Rule(
    name="my_rule",
    description="我的自定义规则",
    conditions=[RuleCondition("event.type == 'message'")],
    actions=[RuleAction(my_rule_handler, "handle_message")],
    priority=100
)
```

## 📚 文档

- [快速开始指南](docs/quickstart.md)
- [规则引擎详解](docs/rule-engine.md)
- [插件开发指南](docs/plugin-development.md)
- [平台适配器开发](docs/adapter-development.md)
- [API参考](docs/api-reference.md)
- [配置参考](docs/configuration.md)

## 🤝 贡献

我们欢迎各种形式的贡献！

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- 感谢所有贡献者的支持
- 感谢开源社区提供的优秀库和工具
- 特别感谢 Python asyncio 团队提供的异步编程支持

## 📞 支持

- 📧 邮箱: i@jyunko.cn
- 🐛 问题反馈: [GitHub Issues](https://github.com/retrofor/iamai/issues)
- 💬 讨论: [GitHub Discussions](https://github.com/retrofor/iamai/discussions)

---

**iamai** - 让机器人开发更简单、更强大！ 🚀
