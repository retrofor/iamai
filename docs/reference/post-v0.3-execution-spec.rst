v0.3 之后的执行规范
=====================

状态
----

本规范定义 ``v0.3.0`` 发布后的六个连续执行工作流，编号为 1 到 6。仓库根目录
``TODO.md`` 另外使用工作流 0 记录本规范和台账自身的发布门；工作流 0 不属于这六个产品工作流。
GitHub issue、pull request、CI run 和外部合规系统保存完成证据。

规范中的“必须”是验收要求，“建议”是默认工程选择。除非工作流被标记为
``BLOCKED_EXTERNAL``，后一个工作流只能在前一个工作流满足完成定义后开始。工作流 6 是唯一例外：
它由 2026-07-29 截止时间触发，必须按期执行，不能等待 0.4 或 1.0 工作结束。
``BLOCKED_EXTERNAL`` 必须同时记录阻塞方、所需权限或事件、最后验证时间和恢复条件，
不能用来代替可以在仓库内完成的工作。

共同质量门
----------

每个代码变更必须满足：

* 基于最新 ``dev`` 创建独立分支和 pull request。
* 先运行与改动直接相关的测试，再运行 Ruff、Mypy、Pytest、Rust tests、配置验证和
  Sphinx ``-W`` 中适用的完整门禁。
* 所有受保护检查使用变更后的最新提交重新运行，不接受旧提交上的绿灯。
* pull request 的可执行 review thread 全部解决；合并后再次确认 ``dev`` CI。
* 不通过移动已发布 tag、改写公共历史或人工删除安全告警来制造完成状态。

工作流 1：FOSSA 与发布治理
---------------------------

目标
~~~~

让 FOSSA 分析真实默认分支 ``dev``、读取项目 MIT 许可证，并产生可以逐项审计的
当前 revision 结果。跟踪项为 `GitHub issue #436 <https://github.com/retrofor/iamai/issues/436>`_。

必须完成
~~~~~~~~

* FOSSA 项目 source revision 从旧 ``master`` 改为 ``dev``。
* 项目许可证识别为 SPDX ``MIT``，不再出现无法由当前 manifest、lockfile 或源码解释的
  phantom AGPL 结论。
* 项目策略从旧 ``Single-Binary Distribution`` 调整为适合本项目发布形态的 ``Standard Bundle``。
* 导出当前 revision 的全部 issue 清单，至少包含 dependency、version、license、policy、
  locator 和处置结论。
* 对真实问题执行升级、移除、策略允许或具名书面豁免；任何豁免必须有范围和失效日期。
* 在一个 ``dev`` revision 和一个 pull request revision 上取得可复现结果。
* 在结果稳定前，``License Compliance`` 不得加入 ``dev`` 的 required checks。

完成定义
~~~~~~~~

FOSSA revision、清单和 GitHub status URL 均指向 ``dev``；所有 findings 已清零或逐项处置；
证据链接写入 `#436 <https://github.com/retrofor/iamai/issues/436>`_，现有 ``v0.3.0`` 豁免在
2026-08-15 前关闭或被新的具名决策替代。

外部阻塞
~~~~~~~~

修改 FOSSA 项目和读取 issue 明细需要项目管理员登录或 API token。没有这些权限时，执行者必须
记录公开可验证的 project/status 信息、凭据探测结果和恢复条件，然后将本工作流标记为
``BLOCKED_EXTERNAL``，不能猜测 11 条 issue 的内容。

工作流 2：低风险依赖升级
-------------------------

目标
~~~~

逐个处理已通过针对性门禁的 Dependabot pull request：``#437``、``#439``、``#441``、
``#442`` 和 ``#443``。

执行规则
~~~~~~~~

* 每个分支必须先更新到最新 ``dev``，再取得 fresh green。
* ``#437`` 只改变 Cargo lock 中的 serde_json patch，可独立处理。
* ``#439``、``#441``、``#442``、``#443`` 共享 ``uv.lock``，必须一次只更新和合并一个；
  下一项必须在前一项进入 ``dev`` 后重新 rebase。
* Mypy、Pytest 和 Sphinx 的 major 更新只针对当前具体 PR 放行，不建立未来 major 自动合并策略。
* FOSSA 的旧 ``master`` 状态不作为依赖兼容性证据；真实 required checks、CodeQL 和
  pre-commit 才是 GitHub 合并门。

完成定义
~~~~~~~~

五个 pull request 均已合并或被一个有等价版本和更完整验证的新 PR 取代；最终 ``dev`` lockfile
一致，完整 CI 通过，未留下并行旧 lock 分支造成的冲突。

工作流 3：带专项门禁的依赖升级
-------------------------------

GitHub Actions major 更新
~~~~~~~~~~~~~~~~~~~~~~~~~

``#438`` 必须在精确最新 head 上触发一次非 tag ``workflow_dispatch`` release rehearsal。
该 run 不得发布 PyPI 或 GitHub Release，但必须完成 validate、sdist、所有 Linux、musllinux、
Windows、macOS wheels、artifact download 和 provenance attestation。只有 rehearsal 全绿且普通
PR CI fresh green 后才能合并。

WebSocket runtime major 更新
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``#440`` 改变生产依赖，必须先增加真实 loopback tests，而不是只依赖 fake transport。测试至少覆盖：

* client connect 和鉴权 header；
* server handler 的 path/role 解析；
* JSON 双向 send/echo；
* 正常 close；
* 断线后的 reconnect 或明确终止语义；
* Python 3.11 和 3.13。

完成定义
~~~~~~~~

``#438`` 的 rehearsal 证据和 ``#440`` 的 loopback tests 链接到对应 PR；两个 PR 在最新 ``dev``
上取得 fresh green 并按顺序合并，合并后 ``dev`` CI 通过。

工作流 4：0.4 扩展契约
----------------------

目标
~~~~

完成 `GitHub issue #435 <https://github.com/retrofor/iamai/issues/435>`_，让第三方 adapter 和
plugin 可以被独立打包、发现、配置和验证。

0.4-A：打包与发现
~~~~~~~~~~~~~~~~~~

* 发布 distribution 命名、``iamai`` 兼容范围 metadata 和 entry-point group 规范。
* 提供一个可安装 reference adapter fixture 和一个 reference plugin fixture。
* 在隔离安装环境验证显式加载与 opt-in auto-discovery，不使用仓库本地 import path。
* 对重复 entry-point 名、entry-point 与 ``Plugin.name`` / ``Adapter.name`` 不一致以及错误对象类型
  给出稳定、可断言的 runtime 错误。
* 兼容范围使用标准 ``Requires-Dist`` 声明，不发明第二套 runtime version metadata；隔离安装测试必须
  证明 package resolver 会拒绝与当前 ``iamai`` 版本不兼容的扩展。
* discovery 顺序必须确定，失败信息必须包含 group、entry-point、distribution 和原因。

0.4-B：统一 Schema 导出
~~~~~~~~~~~~~~~~~~~~~~~

* 单一生成器导出 root/runtime、adapter 和 plugin 配置 JSON Schema。
* payload 必须包含稳定 ``$id``、contract version、默认值；secret 字段在对应 property schema 上使用
  JSON Schema ``writeOnly: true``，且不得导出 secret 的运行时值。
* CLI ``config-schema`` 和 management API ``/schema`` 对同一扩展集合输出语义等价 payload。
* 输出顺序稳定，并有 golden/equivalence tests。

Schema contract v1
^^^^^^^^^^^^^^^^^^

* 公开 ``CONFIG_SCHEMA_CONTRACT_VERSION = "1"``、
  ``CONFIG_SCHEMA_ID = "urn:iamai:config-schema:v1:root"`` 和纯函数
  ``build_config_schema(*, adapters=..., plugins=...)``。
* 根属性固定按 ``runtime``、``logging``、``state``、``adapter``、``plugin`` 排列；对应
  ``$id`` 使用 ``urn:iamai:config-schema:v1:<section>``。扩展子 Schema 使用
  ``urn:iamai:config-schema:v1:<kind>:<percent-encoded-name>``。
* adapter 和 plugin 名按字典序输出；未知扩展表和没有 ``config_model`` 的扩展保持开放对象，
  以兼容外部工具和渐进迁移。
* ``state`` 同时接受配置表和 ``false``，其根默认值是空表。Pydantic 与 dataclass
  ``config_model`` 使用同一 validation-mode 生成路径。
* 默认工厂不得在 Schema 生成期间执行；需要公开的 factory 默认值必须由字段 metadata 显式提供。
* ``writeOnly`` 只接受字段 metadata 的显式标注，不根据 ``token`` 等字段名推断。生成器只读取类
  metadata，禁止读取或嵌入当前 Runtime 的配置值。
* 无参 ``config-schema`` 和认证后的 management API ``GET /schema`` 必须与
  ``Runtime.config_schema()`` 完全相等；``config-schema <plugin>`` 保留单插件兼容行为。

0.4-C：公开 conformance kit
~~~~~~~~~~~~~~~~~~~~~~~~~~~

* adapter helper 覆盖配置、inbound normalize、outbound encode/API、启动、取消、失败清理和错误语义。
* plugin helper 覆盖 metadata、配置、依赖、handler 注册、权限、生命周期和清理。
* reference adapter/plugin 在独立安装环境运行公开 helper。
* ecosystem admission 文档列出 metadata、安全声明、兼容范围和 conformance 证据。

完成定义
~~~~~~~~

`#435 <https://github.com/retrofor/iamai/issues/435>`_ 的全部 acceptance criteria 有自动测试或
明确的人工证据；三个切片各自以小型 PR 合并，
公开文档和第三方可导入的测试 helper 与实现同步。

工作流 5：1.0 公共 API 契约
---------------------------

目标
~~~~

完成 `GitHub issue #434 <https://github.com/retrofor/iamai/issues/434>`_，在 1.0 RC 前发布可测试的
兼容性规范。该工作流依赖工作流 4 完成。

必须完成
~~~~~~~~

* 定义 ``Event`` 和 ``Message`` 的版本化序列化形式、必需/可选字段、未知字段和 round-trip 规则。
* 定义 ``Runtime``、``Adapter`` 和 ``Plugin`` 的启动、正常关闭、取消、失败清理、reload 和
  handler admission 顺序。
* 单独定义 ``Context`` 的事件作用域、回复路由、依赖注入和失效语义；``Context`` 不拥有 runtime
  lifecycle。
* 公开 schema/contract version，并用兼容性测试证明已支持的演进规则。
* 建立规范条款到自动测试或人工检查的一一对应 conformance matrix。
* 定义 public symbol、配置 key、entry point 和序列化字段的弃用警告机制、最短支持窗口和删除规则。
* 发布最后一个 ``0.x`` 到 ``1.0`` 的迁移指南，列出所有有意 breaking changes。

完成定义
~~~~~~~~

版本化规范、golden tests、生命周期 contract tests、conformance matrix、弃用政策和迁移指南全部进入
``dev``，并在 1.0 RC 构建上通过。

工作流 6：needs-info issue 收敛
--------------------------------

目标
~~~~

在 2026-07-29 截止日后收敛 ``#294``、``#295``、``#297`` 和 ``#306``，避免没有维护者和真实
使用场景的请求长期占用路线图。

处理规则
~~~~~~~~

* 截止日前保留 issue，并只接受能说明当前行为、期望行为、使用场景、归属仓库和验收示例的回复。
* ``#294``、``#295``、``#297`` 若证明是同一 i18n 缺口，合并成一个新的、可执行的 issue；若只是
  文档本地化而当前版本已支持，则关闭并链接现有文档。
* ``#306`` 默认迁移到独立 scheduler plugin、service integration 或对应外部包；只有能证明是多个
  扩展共同需要的通用 scheduling contract 时才保留在核心仓库，不把 scheduler 错归类为传输 adapter。
* 2026-07-29 23:59 UTC 后仍无有效回复的 issue 关闭，并引用原 clarification 请求。

完成定义
~~~~~~~~

四个 issue 均被关闭、迁移，或被有 owner、范围、验收标准和里程碑的新 issue 取代；核心路线图不保留
无归属的 wishlist。

跨工作流安全告警基线
--------------------

Dependabot API 的告警状态可能晚于 lockfile 和 dependency graph。执行者必须等待默认分支扫描完成，
再用 manifest/lockfile 和 GitHub dependency graph 复核。只有误报、撤回 advisory 或不准确规则才可
人工 dismiss；已通过升级或移除解决的告警应由 GitHub 自动关闭。
