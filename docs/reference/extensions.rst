插件与适配器发布参考
======================

iamai 支持两种扩展加载方式：

显式引用
   在配置里写导入路径，例如 ``plugins = ["my_pkg:MyPlugin"]`` 或
   ``adapters = ["my_pkg:MyAdapter"]``。这适合本地项目和私有代码。

Entry points
   扩展包在 ``pyproject.toml`` 里声明 ``iamai.plugins`` 或 ``iamai.adapters`` entry point。
   用户 ``uv add`` 安装后，可以用 entry point 名加载，也可以开启自动发现。

社区商店
   可发布扩展可以提交到 :doc:`../community/store`。商店条目是静态 JSON registry，提交前运行
   ``uv run python scripts/validate_ecosystem_store.py``。

插件包
------

一个可发布插件包的最小结构：

.. code-block:: text

   iamai-plugin-echo/
   ├── pyproject.toml
   └── src/
       └── iamai_plugin_echo/
           └── __init__.py

``pyproject.toml``：

.. code-block:: toml

   [project]
   name = "iamai-plugin-echo"
   version = "0.1.0"
   dependencies = [
     "iamai>=0.3,<0.5",
   ]

   [project.entry-points."iamai.plugins"]
   echo = "iamai_plugin_echo:EchoPlugin"

插件代码：

.. code-block:: python

   from iamai import Context, Plugin, command


   class EchoPlugin(Plugin):
       name = "echo"
       description = "Echo command plugin."

       @command("echo")
       async def echo(self, ctx: Context) -> None:
           await ctx.reply(ctx.args or "empty")

插件依赖
--------

依赖分两层：

Python 包依赖
   写在插件包自己的 ``project.dependencies``。例如插件要调用 Redis，就由插件包声明
   ``redis>=5``，使用者通过 ``uv add iamai-plugin-xxx`` 安装时一起解析。

iamai 插件依赖
   写在插件类属性里，用于加载顺序和缺失检查：

.. code-block:: python

   class ReportPlugin(Plugin):
       name = "report"
       requires = ("auth",)
       optional_requires = ("metrics-extra",)
       load_after = ("database",)

``requires`` 缺失会启动失败。``optional_requires`` 和 ``load_after`` 只有目标插件存在时才影响顺序。

插件配置
--------

插件包可以声明 Pydantic 配置模型，使用者在主项目配置里填写：

.. code-block:: python

   from pydantic import BaseModel, Field


   class EchoConfig(BaseModel):
       prefix: str = Field(default="echo")


   class EchoPlugin(Plugin):
       name = "echo"
       config_model = EchoConfig

.. code-block:: toml

   [plugin.echo]
   prefix = "reply"

显式启用插件
------------

安装：

.. code-block:: console

   uv add iamai-plugin-echo

配置：

.. code-block:: toml

   [runtime]
   plugins = ["echo"]

``echo`` 是 entry point 名。也可以继续写导入路径：

.. code-block:: toml

   [runtime]
   plugins = ["iamai_plugin_echo:EchoPlugin"]

自动发现插件
------------

.. code-block:: toml

   [runtime]
   auto_discover_plugins = true

开启后，iamai 会加载环境中所有 ``iamai.plugins`` entry points。生产环境更建议显式列出插件；
自动发现适合开发、示例项目和受控的私有运行环境。发现结果先按 entry point 名排序，
再交给插件依赖排序器，因此相同安装环境会得到确定的加载结果。

适配器包
--------

适配器包的 entry point group 是 ``iamai.adapters``：

.. code-block:: toml

   [project]
   name = "iamai-adapter-acme"
   version = "0.1.0"
   dependencies = [
     "iamai>=0.3,<0.5",
     "httpx>=0.27",
   ]

   [project.entry-points."iamai.adapters"]
   acme = "iamai_adapter_acme:AcmeAdapter"

使用者安装并启用：

.. code-block:: console

   uv add iamai-adapter-acme

.. code-block:: toml

   [runtime]
   adapters = ["acme"]

   [adapter.acme]
   token = "replace-me"

自动发现适配器：

.. code-block:: toml

   [runtime]
   auto_discover_adapters = true

自动发现会把所有 ``iamai.adapters`` entry points 当作启用适配器。适配器通常涉及网络凭据和公网边界，
生产环境应优先显式配置。

命名约定
--------

- 申请进入社区 registry 的插件包必须命名为 ``iamai-plugin-<name>``，适配器包必须命名为
  ``iamai-adapter-<platform>``；私有 distribution 可以使用自己的命名规则。
- Distribution 必须通过标准 ``Requires-Dist: iamai...`` 声明所支持的 iamai 版本范围；
  安装器负责在运行前拒绝不兼容组合，运行时不维护第二套版本字段。
- 插件和适配器必须分别发布到 ``iamai.plugins`` 和 ``iamai.adapters`` group。
- Entry point 名必须和 ``Plugin.name`` 或 ``Adapter.name`` 保持一致。
- 配置表应分别使用 ``[plugin.<name>]`` 和 ``[adapter.<name>]``。
- 包依赖交给 Python packaging，运行时加载顺序交给 ``requires`` / ``load_after``。

发现与错误契约
--------------

配置中的 ``plugins`` / ``adapters`` 是显式启用清单。启用
``auto_discover_plugins`` / ``auto_discover_adapters`` 后，运行时才会把对应 group 中其余已安装的
entry points 按名称排序并追加到清单。自动发现是 opt-in，不改变显式引用的顺序。

``management``、``management_api``、``terminal``、``onebot11``、``telegram`` 和 ``webhook``
是内置保留名。已安装 distribution 不得在对应 group 中发布这些名称。一个 group 内也不得由多个
distribution 发布同名 entry point；运行时不会选择 last-wins 结果。

已安装 entry point 的发现失败会抛出公开的 ``iamai.ExtensionDiscoveryError``。异常提供稳定字段
``code``、``group``、``entry_point``、``distributions`` 和 ``reason``，其中 ``code`` 是以下之一：

- ``duplicate_entry_point``：多个 distribution 发布同组同名入口。
- ``reserved_entry_point``：入口名与内置别名冲突。
- ``load_failed``：入口模块或属性无法加载。
- ``invalid_object``：入口没有返回对应的 ``Plugin`` / ``Adapter`` 子类。
- ``name_mismatch``：入口名和类的 ``name`` 不一致。

错误字符串固定包含 code、group、entry point、排序后的 distribution 标识和原因，便于 CI 及运维系统
稳定断言。显式加载只检查被请求的入口；自动发现按入口名排序后报告第一个错误。

适配器兼容性规范草案
--------------------

第三方适配器包推荐命名 ``iamai-adapter-<platform>``，并通过
``[project.entry-points."iamai.adapters"]`` 暴露入口。当前不要求强改运行时 API，但适配器必须保持这些契约：

- ``Adapter.start`` 负责启动连接、轮询或 HTTP/WebSocket 服务，并在取消时正常退出。
- ``Adapter.send_message`` 接收 iamai ``Message`` 或文本，并把它编码成目标平台的出站消息。
- ``Adapter.call_api`` 暴露平台 API 调用，成功时返回平台响应，失败时抛出可诊断异常或返回明确错误结构。
- ``Adapter.name``、entry point 名和配置表 ``[adapter.<name>]`` 保持一致。

适配器可以像插件一样声明类级 ``config_model``。支持 Pydantic 模型和 dataclass；Runtime 会在
构造适配器时验证并归一化 ``[adapter.<name>]``，同时把同一模型纳入根配置 Schema。凭据字段必须
通过字段元数据显式声明 ``json_schema_extra={"writeOnly": True}``，不得依赖字段名猜测。

最小 conformance tests 应覆盖：

- inbound event normalize：平台事件必须归一化成稳定的 ``Event`` 字段。
- outbound message encode：文本、基础消息段和目标对象必须编码正确。
- API call response：成功响应、平台错误和超时都要有测试。
- 错误处理：鉴权失败、非法 payload、网络失败不能静默吞掉。

适配器包可以直接依赖 ``iamai.testing.adapters`` 中的 helper 来表达这些最低契约。

插件与 Agent 工具安全声明
-------------------------

进入社区商店的插件包必须声明：

- 网络访问：是否访问公网、内网、Webhook、WebSocket 或本地服务。
- 凭据需求：需要哪些 token、secret、cookie、数据库凭据或云服务权限。
- 危险动作：是否会写文件、执行命令、调用外部 API、修改远端状态或发送批量消息。
- 可选依赖：哪些 extra 或服务不是默认必需，但启用后会扩大运行时权限。

Agent tool 必须额外声明：

- 权限名，例如 ``web.search``、``repo.write``、``shell.execute``。
- 输入 schema，用于运行前校验和审计。
- 审计字段，例如 ``query``、``target``、``repository``、``approval_id``。
- 是否需要人工审批。危险工具应默认需要审批，除非部署方显式降级。

本阶段先要求规范、社区商店字段和审计 trace，不提供完整隔离沙箱承诺。

管理 API 候选能力
-----------------

管理面先稳定 API，再决定是否做 WebUI。候选端点包括：

- ``/health``：进程和依赖健康状态。
- ``/metrics``：运行时指标，格式可对接 Prometheus 或 JSON。
- ``/adapters``：已加载适配器、配置摘要和连接状态。
- ``/plugins``：已加载插件、依赖、启用状态和版本。
- ``/handlers``：已注册 handler、匹配条件、优先级和所属插件。
- ``/sessions``：活跃 session 摘要和清理入口。
- ``/state``：状态后端检查和安全的只读诊断。
- ``/schema``：与无参 CLI ``config-schema`` 完全一致的版本化根配置 Schema。

WebUI 后续作为独立插件或独立项目，不进入核心 runtime。

提交到社区商店
--------------

社区开发者有两种提交方式：

- 在 :doc:`../community/store` 点击“提交扩展”并填写可视化表单，跳转到预填好的 GitHub issue。
- 在 GitHub 直接选择 ``Ecosystem submission`` issue 模板并填写字段。

维护者审核后新增或更新 ``docs/ecosystem/entries/<id>.json``。字段至少包括：

- ``id``：全局唯一，例如 ``plugin.echo``、``adapter.acme``、``agent_tool.web_search``。
- ``type``：扩展类型，例如 ``plugin``、``adapter``、``ruleset``、``agent_tool``、``template``。
- ``name``：展示名称。
- ``summary``：不超过 180 字符的一句话简介。
- ``license``：许可证标识。
- ``package`` 或 ``repository``：至少填写一个。
- ``entry_points``：如果是可安装插件或适配器，填写 ``iamai.plugins`` 或 ``iamai.adapters``。
- ``runtime_capabilities``：声明运行时能力，例如 ``network:http``、``storage:sqlite``、``agent:tool``。
- ``security_notes``：声明网络访问、凭据需求、危险动作和可选依赖。
- ``permission_notes``：Agent 工具的权限名、输入 schema、审计字段和审批要求。
- ``verification``：普通提交使用 ``community``；更高等级由维护者审核后添加。

商店支持的类型包括：

- ``plugin``：可加载业务插件。
- ``adapter``：协议适配器。
- ``ruleset``：可复用规则集。
- ``permission``：权限谓词或权限策略包。
- ``state_backend``：状态和会话存储后端。
- ``agent_tool``：Agent 可直接调用的工具。
- ``agent_skill``：Agent 技能或 workflow 模板。
- ``middleware``：适配器或运行时中间件。
- ``template``：项目模板。
- ``example``：示例项目或教学代码。

``provider`` 和 ``theme`` 保留给未来 UI 或模型供应商集成。不要把认证等级当作营销字段；
它们代表可验证的包元数据、作者身份或安全审核状态。

文档页表单默认使用 GitHub 预填 issue 链接，不在浏览器里保存 GitHub token。若未来要启用“登录后直接提交”，
需要单独部署服务端代理负责 GitHub App 或 OAuth App 的 callback、CSRF ``state`` 校验、token 交换、创建 issue、
速率限制和审计日志。静态 Sphinx 站点不能持有 ``client_secret``。
