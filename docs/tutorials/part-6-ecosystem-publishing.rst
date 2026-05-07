第六章：发布到社区商店
========================

这一章把前面写好的插件或适配器提交到 iamai 社区商店。商店不是运行时后端，而是随文档构建生成的
静态 registry；提交入口使用 GitHub issue，维护者审核后再把条目合入 ``docs/ecosystem/entries``。

准备扩展元数据
--------------

先确认扩展已经可以通过 ``uv add`` 安装，或者至少有一个公开仓库。可发布扩展至少需要这些信息：

- ``id``：全局唯一，例如 ``plugin.echo`` 或 ``adapter.acme``。
- ``type``：``plugin``、``adapter``、``ruleset``、``agent_tool`` 等。
- ``name`` 和 ``summary``：用于商店卡片展示，``summary`` 保持一句话。
- ``package`` 或 ``repository``：至少填写一个。
- ``license``：例如 ``MIT``、``Apache-2.0``。
- ``entry_points``：插件使用 ``iamai.plugins``，适配器使用 ``iamai.adapters``。
- ``runtime_capabilities``：例如 ``network:http``、``storage:sqlite``、``agent:tool``。
- ``security_notes``：声明网络访问、凭据需求、危险动作和可选依赖。
- ``permission_notes``：Agent 工具需要说明权限名、输入 schema、审计字段和审批要求。

使用文档表单提交
----------------

打开 :doc:`../community/store`，点击“提交扩展”并填写这些字段。表单会实时生成候选
registry JSON，并在点击提交后打开 GitHub issue 页面。

Entry point 的填写格式是每行一个：

.. code-block:: text

   plugin:echo=iamai_plugin_echo:EchoPlugin
   adapter:acme=iamai_adapter_acme:AcmeAdapter

表单不会让你声明 ``official``、``security_reviewed`` 这类认证徽章。它们代表维护者审核结论，
不是扩展作者的自我声明。

使用 GitHub Issue Form 提交
---------------------------

你也可以直接在 GitHub 新建 issue，选择 ``Ecosystem submission`` 模板。这个模板和文档页表单使用同一组核心字段。
如果你已经从文档页表单生成了 JSON，可以把它粘贴到 ``Candidate registry JSON`` 字段。

维护者审核
----------

维护者会检查包或仓库是否可访问、entry point 是否和包元数据一致、安装说明是否安全、是否含有密钥或私有地址，
以及安全声明是否覆盖实际运行时能力。
通过后，维护者把 JSON 合入 ``docs/ecosystem/entries/<id>.json`` 并运行：

.. code-block:: console

   uv run python scripts/validate_ecosystem_store.py

Checkpoint
----------

完成后你应该得到一个带有 ``ecosystem-submission`` label 的 GitHub issue。issue 里包含一段 ``json`` 代码块，
它可以直接作为 registry 条目的初稿。
