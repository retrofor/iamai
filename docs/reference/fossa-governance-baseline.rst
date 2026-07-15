FOSSA 治理基线
==============

状态
----

``BLOCKED_EXTERNAL``，最后验证时间为 2026-07-15。跟踪项为
`GitHub issue #436 <https://github.com/retrofor/iamai/issues/436>`_。

本页记录 FOSSA 变更前的可公开复现证据和凭据边界。它不是合规通过结论，也不枚举认证后才能读取的
issue 明细。

公开 FOSSA 快照
---------------

安全查询入口为：

.. code-block:: text

   https://app.fossa.com/api/projects/git%2Bgithub.com%2Fretrofor%2Fiamai?ref_type=branch

完整 project JSON 含有不应进入 issue、CI 日志或文档的 ``updateHook.secret_key``。只能保存明确白名单
投影，不得复制原始响应。

2026-07-15 的白名单快照：

* locator：``git+github.com/retrofor/iamai``；project 为 public。
* default branch：``master``；tracking branches 包含 ``master``，不包含 ``dev``。
* policy：``Single-Binary Distribution``，policy id ``98653``，type ``LICENSING``。
* last analyzed revision：``a59126dec42ebeb6dd55df9fd7382284fb4a7af0``，时间为
  2026-05-06 06:16:47 UTC。
* 旧 head 显示 119 dependencies、54 licenses、9 todos、24 unresolved licensing issues。
* ``dev`` reference 仍停在 ``935c8afe347bc1af7a8db10525a444cf183ec0de``；当前 GitHub ``dev``
  已前进到 ``23b7cb90ba3481c2f98b1df538240f1a227f9a8f``。
* licensing issue scanning 和 status check 均启用；GitHub update hook active，last error 为 null。

旧 pull request status 曾显示 11 issues，但当前公开旧 head 显示 24 个 unresolved licensing issues。
未认证前不能假定两个数字代表同一 revision 或同一组 finding。

认证边界
--------

当前终端没有 ``fossa`` CLI，``FOSSA_API_KEY``、``FOSSA_API_TOKEN``、``FOSSA_TOKEN`` 均未设置，
常见用户配置目录中也没有 FOSSA 凭据。issues API 返回 HTTP 302 到登录页，当前 revision 页面显示
``window.logged_in = false``。

因此下列操作不能在当前凭据边界内完成：

* 导出包含 issue id、dependency、version、license、policy、locator 和状态的完整 finding 清单；
* 备份或修改 FOSSA project settings 和 policy；
* 把 default/tracked branch 改为 ``dev``；
* 把 source license 确认为 MIT 并把 policy 改为 ``Standard Bundle``；
* 对精确 ``dev`` SHA 发起新分析，处理或逐项豁免 findings；
* 让精确 SHA 的 ``License Compliance`` status 成功。

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

恢复步骤
--------

1. 取得最小权限的 FOSSA project administrator 登录或 API key；不得把 token 写入 issue 或日志。
2. 在变更前导出 project settings、旧 policy 和完整 issues 清单。
3. 把 default/tracked branch 改为 ``dev``，source license 改为 MIT，policy 改为
   ``Standard Bundle``；此时不改 GitHub branch protection。
4. 对执行时最新 ``dev`` SHA 和一个基于该 SHA 的 pull request revision 分别发起分析，核对 BOM 与
   ``uv.lock``、``Cargo.lock`` 和发布 artifacts。
5. 修复真实 finding；无法立即修复的项目必须逐项记录 owner、理由、批准日和到期日。
6. 同时验证两个 revision 的 FOSSA 页面/API 与 GitHub commit status，再把 revision、policy 或 waiver
   决策、package license metadata 证据链接到 #436 和 release checklist。
7. unresolved findings 清零或逐项处置，并在 2026-08-15 前关闭现有 ``v0.3.0`` waiver 或用新的具名、
   限时决策替代后，才能关闭 #436；是否将 FOSSA 设为 required check 另行决策。

完成门槛
--------

FOSSA 的 default/tracked branch 和 last analyzed revision 必须指向同一个已记录的 ``dev`` SHA；policy 为
``Standard Bundle``，source license 为 MIT，没有 phantom AGPL；完整 issue inventory 可追溯到该 SHA 和
lockfile digest；未解决项为零或都有具名、限时豁免；一个 ``dev`` revision 和一个 pull request revision
的 ``License Compliance`` status 都成功；#436 与 release checklist 含 revision、policy/waiver 和 package
license metadata 证据；现有 ``v0.3.0`` waiver 已关闭或被新的具名决策替代。
