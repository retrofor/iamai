FOSSA 治理基线
==============

状态
----

``BLOCKED_EXTERNAL``，最后验证时间为 2026-07-16。跟踪项为
`GitHub issue #436 <https://github.com/retrofor/iamai/issues/436>`_。

本页记录 FOSSA 变更前的可公开复现证据和凭据边界。它不是合规通过结论，也不枚举认证后才能读取的
issue 明细。

公开 FOSSA 快照
---------------

公开 project API 入口为：

.. code-block:: text

   https://app.fossa.com/api/projects/git%2Bgithub.com%2Fretrofor%2Fiamai?ref=dev&ref_type=branch

完整 project JSON 含有不应进入 issue、CI 日志或文档的 ``updateHook.secret_key``。不得直接输出或先保存
原始响应；查询时必须在管道中直接构造白名单投影，例如：

.. code-block:: bash

   curl -fsSL 'https://app.fossa.com/api/projects/git%2Bgithub.com%2Fretrofor%2Fiamai?ref=dev&ref_type=branch' \
       | jq '{locator, public, default_branch, tracking_branches,
              policy: {id: .policyId, title: .policy.title, type: .policy.type},
              last_analyzed_revision,
              head: {locator: .head.locator, updatedAt: .head.updatedAt,
                     integration_hook_status: .head.integration_hook_status,
                     dependency_count: .head.dependency_count,
                     license_count: .head.license_count,
                     todo_count: .head.todo_count,
                     unresolved_issue_count: .head.unresolved_issue_count},
              dev_reference: ([.references[]
                | select(.name == "dev")
                | {name, type, revision_id}][0])}'

2026-07-16 的白名单快照：

* locator：``git+github.com/retrofor/iamai``；project 为 public。
* default branch：``master``；tracking branches 包含 ``master``，不包含 ``dev``。
* policy：``Single-Binary Distribution``，policy id ``98653``，type ``LICENSING``。
* last analyzed project revision 仍是
  ``a59126dec42ebeb6dd55df9fd7382284fb4a7af0``，创建时间为 2026-05-06 06:16:49 UTC。
* 旧 ``master`` head 显示 119 dependencies、54 licenses、9 todos；公开摘要在 2026-07-16
  重新计算后显示 0 unresolved licensing issues，但它仍是旧 revision，不能证明当前 ``dev`` 合规。
  该旧 revision 的 source-license matches 仍包含 ``AGPL-3.0-or-later``（``docs/source/credits.md``）
  和 ``AGPL-3.0-only``（``Cargo.toml``、``DECLARED_LICENSE``、``COPYING``）；应分析当前 ``dev``
  并核对新匹配路径，不能改写历史 revision 来制造通过状态。
* ``dev`` reference 已前进到 ``1e34500e8357e36477536f5c76f5d9548aaae0d7``，但该 revision 的
  ``integration_hook_status`` 为 ``NONE``，依赖、许可证和 issue 计数均为空。当前 GitHub ``dev`` 为
  ``d2e5216b8c611c7f7e53e0027865919bd790f33f``，对应公开 revision API 返回 404。
* licensing issue scanning 和 status check 均启用；GitHub update hook active，last error 为 null。

最新可复现的 pull request revision ``71eb09e4f9b753caf1651429b2f58723cbcf13f6`` 已完成分析，
公开 revision 摘要显示 113 dependencies、37 licenses、8 todos、0 unresolved issues，并识别出
first-party ``MIT``。它的 GitHub ``License Compliance`` status 成功，但 target URL 仍错误地位于
``refs/branch/master/71eb09e...``；合并后的 ``dev`` SHA 没有 FOSSA status。

状态结果也会随 revision 改变：``1c49ebd`` 的 GitHub status 报告 3 issues，后续 ``c2321ac`` 和
``71eb09e`` 报告全部通过。未认证的 revision 摘要不能替代完整 finding 清单，也不能解释旧 status
中的 dependency、version、license、policy、locator 和 disposition。

认证边界
--------

当前终端没有 ``fossa`` CLI，``FOSSA_API_KEY``、``FOSSA_API_TOKEN``、``FOSSA_TOKEN`` 均未设置，
常见用户配置目录中也没有 FOSSA 凭据。公开 project、revision、dependencies 和 licenses API 可读；
issue、issue export 和 policy rule API 返回 HTTP 302 到登录页，revision 页面显示
``window.logged_in = false``。

FOSSA 官方权限模型将所需能力拆分如下：

* 导出完整 finding 清单需要 Full credential 或 UI session 以及项目 View 权限；
* 修改 default/tracked branch 需要项目 Edit 权限；
* 应用 licensing policy 还需要 ``SetPolicy``；
* 纠正跨项目 dependency license metadata 需要 organization Admin 或 Editor。

因此 project-admin 不是唯一可行角色，但 Push-Only token 不足以读取或管理这些数据。GitHub App、
``.fossa.yml`` 和带 Push-Only token 的 GitHub Actions 也不会向执行者授予上述 FOSSA 权限。

因此下列操作不能在当前凭据边界内完成：

* 导出包含 issue id、dependency、version、license、policy、locator 和状态的完整 finding 清单；
* 备份或修改 FOSSA project settings 和 policy；
* 把 default/tracked branch 改为 ``dev``；
* 把 policy 改为 ``Standard Bundle Distribution``；
* 对精确 ``dev`` SHA 发起新分析，处理或逐项豁免 findings；
* 证明精确 ``dev`` revision 的 first-party license 为 MIT 且没有未处置的 AGPL 匹配。

仓库与 GitHub 基线
------------------

GitHub 默认分支是 ``dev``，repository license API 返回 ``MIT``。``dev`` 的 required checks 只有：

* ``Lint / Rust / Config``；
* ``Pytest (Python 3.11)``；
* ``Pytest (Python 3.12)``；
* ``Pytest (Python 3.13)``；
* ``Docs``。

FOSSA 不在 required checks 中；在认证后的 ``dev`` 重分析通过前必须保持这一状态。

仓库中没有 ``.fossa.yml`` 或 FOSSA workflow。全部 13 个受版本控制的 Python project metadata 都声明
MIT，``Cargo.toml`` 也声明 MIT。发布输入的基线 digest 为：

.. code-block:: text

   uv.lock     b31f2c8cb9702ab7452c1e377ce6638ebfe36e8a99ae676b9d020f11ec79acb1
   Cargo.lock  ea8cda5d4e4aa258b2716241315948a093615faa569c27a34326159a6f951860

官方权限与 API 参考
-------------------

权限和恢复步骤以 FOSSA 官方文档为准：

* `API tokens <https://docs.fossa.com/docs/organization-management/api-tokens>`_；
* `roles and permissions <https://docs.fossa.com/docs/organization-management/role-based-access-control>`_；
* `project settings <https://docs.fossa.com/docs/project-setup/project-settings>`_；
* `Update Project API <https://docs.fossa.com/docs/api/reference/projects/updateProject>`_；
* `Project Issue JSON Export API
  <https://docs.fossa.com/docs/api/reference/projects/getProjectJSONExportIssues>`_；
* `FOSSA configuration file <https://docs.fossa.com/docs/cli/references/files/fossa-yml>`_；
* `GitHub App <https://docs.fossa.com/docs/integrations/github-app>`_ 和
  `GitHub Actions <https://docs.fossa.com/docs/integrations/github-actions>`_；
* `license corrections <https://docs.fossa.com/docs/licenses/license-corrections>`_ 和
  `license disputes <https://docs.fossa.com/docs/licenses/license-disputes>`_。

恢复步骤
--------

1. 取得带最小充分权限的 FOSSA Full credential 或 UI session：issue export 需要 View，branch 设置需要
   Edit，policy 应用需要 ``SetPolicy``；不得把 token 写入 issue 或日志。
2. 在变更前导出 project settings、旧 policy，并对精确 revision 分别使用 ``status=active`` 和
   ``status=ignored`` 导出 issues；也可用 ``/api/v2/issues`` 做等价的完整分页导出。清单必须保留 issue
   状态、policy rule、豁免或忽略理由，不能只保存默认的 active 结果。
3. 把 default/tracked branch 改为 ``dev``，policy 改为 ``Standard Bundle Distribution``；此时不改
   GitHub branch protection。FOSSA 没有可直接设置的 project source-license 字段。
4. 对执行时最新 ``dev`` SHA 和一个基于该 SHA 的 pull request revision 分别发起分析，核对 BOM 与
   ``uv.lock``、``Cargo.lock`` 和发布 artifacts，并确认 first-party license 结果包含 MIT、不包含
   无法解释的 AGPL。只有证明匹配路径不属于发布物或 first-party source，并记录 owner、理由且保留
   过滤前后的 match inventory 时，才能使用 scan path filter。FOSSA dependency correction/conclusion 不能
   充当 project source-license 设置。Dependency license correction 必须限定在 FOSSA 支持的对应 scope，
   记录审计证据，并取得所需的 organization Admin 或 Editor 权限；license dispute 按项目 issue 的访问
   权限提交，并同样保留证据和审计记录，不能把 correction 的组织级权限要求套用到 dispute。
5. 修复真实 finding；无法立即修复的项目必须逐项记录 owner、理由、批准日和到期日。
6. 同时验证两个 revision 的 FOSSA 页面/API 与 GitHub commit status，再把 revision、policy 或 waiver
   决策、package license metadata 证据链接到 #436 和 release checklist。
7. unresolved findings 清零或逐项处置，并在 2026-08-15 前关闭现有 ``v0.3.0`` waiver 或用新的具名、
   限时决策替代后，才能关闭 #436；是否将 FOSSA 设为 required check 另行决策。

完成门槛
--------

FOSSA 的 default/tracked branch 和 last analyzed revision 必须指向同一个已记录的 ``dev`` SHA；policy 为
``Standard Bundle Distribution``，该 revision 的 first-party license 为 MIT，没有未处置的 AGPL 匹配；
完整 issue inventory 可追溯到该 SHA 和 lockfile digest；未解决项为零或都有具名、限时豁免；
一个 ``dev`` revision 和一个 pull request revision
的 ``License Compliance`` status 都成功；#436 与 release checklist 含 revision、policy/waiver 和 package
license metadata 证据；现有 ``v0.3.0`` waiver 已关闭或被新的具名决策替代。
