通用 Agent 研究 Harness
========================

iamai 正在稳定消息 Runtime 之外建立一条 headless、record-first 的研究执行面：

``Task → Agent → Environment → Trajectory → Evaluation``

第一条垂直切片位于 provisional 的 ``iamai.harness``。它的执行模型不构造或使用 Adapter、Plugin、
Event、SessionManager 或任何 LLM provider，也不会从顶层 ``iamai`` 重新导出。``1.x`` 消息 API
的含义保持不变；AGI 是长期研究方向，不是当前版本声明。

运行一个确定性 Trial
--------------------

下面的 Trial 先查询一个非聊天 Environment，再提交最终答案。最终 Action 仍然必须经过
``Environment.step()``；只有 Environment 返回 terminating Transition，Trial 才正常完成。

.. code-block:: python

   import asyncio

   from iamai.harness import (
       Action,
       ExactEvaluator,
       LookupEnvironment,
       ScriptedAgent,
       Task,
       Trial,
       TrialConfig,
   )


   async def main() -> None:
       result = await Trial(
           task=Task(
               id="capital-of-france",
               input={"question": "What is the capital of France?"},
           ),
           agent=ScriptedAgent(
               [
                   Action.invoke("lookup", {"key": "france"}),
                   Action.finish("Paris"),
               ],
               name="scripted-capital-agent",
               version="1",
           ),
           environment=LookupEnvironment(
               {"france": "Paris"},
               name="country-capitals",
               version="1",
           ),
           evaluator=ExactEvaluator("Paris", version="1"),
           config=TrialConfig(
               trial_id="trial-capital-france",
               seed=7,
               max_actions=2,
           ),
       ).run()

       assert result.status.value == "completed"
       assert result.evaluation is not None
       assert result.evaluation.passed


   asyncio.run(main())

终态语义
--------

``completed``
   Environment 已提交 terminating Transition，Evaluator 也已记录判断。错误答案仍是 completed，
   但 Evaluation 可以是 ``passed=False``。

``budget_exhausted``
   Action 预算用尽但 Environment 尚未终止。Trial 仍会接受 Evaluation，因此预算失败也能进入比较数据。

``failed``
   Agent、Environment 或 Evaluator 抛出普通异常。结果包含 ``TrialFailure``，Trajectory 会记录阶段、
   错误码、异常类型和消息，然后只写入一个终止记录。

``cancelled``
   调用方取消了正在执行的 Trial。Trajectory 记录取消阶段与终态，``CancelledError`` 继续向调用方传播。

Trajectory 与 Replay
--------------------

Trajectory 是不可变、从零连续编号的因果记录。配置哈希覆盖 Harness 配置版本、Agent、Environment、
Evaluator 的声明身份与配置以及 Action 预算；Trial ID、Task、seed 和时间戳不属于配置哈希。
记录的是决策所见输入与已提交结果，不声称保存模型的隐藏推理。

``replay(trajectory)`` 是纯 Replay：它校验格式、配置哈希、序号和状态专属记录，再重建
``TrialResult``，不会重新调用 Agent、Environment 或 Evaluator。Re-execution 则是使用同一规范开始
一个新的 Trial；只有所有参与组件和依赖都确定时，Re-execution 才应产生相同结果。

持久化 Experiment
------------------

``Experiment`` 把一组显式命名的 variant、baseline 和调用方 provenance 冻结为不可变
``ExperimentPlan``。``JsonlTrajectoryStore`` 使用“一文件一个 Experiment”的 JSONL：先在任何
Trial 副作用前 fsync plan，再为每个 Trial 写入 start marker 和完整终态 Trajectory。Store 只保存
Trajectory；status、Evaluation 与 failure 都由 :func:`~iamai.harness.replay` 重建，不维护第二份真相。

.. code-block:: python

   import asyncio

   from iamai.harness import (
       Action,
       ExactEvaluator,
       Experiment,
       JsonlTrajectoryStore,
       LookupEnvironment,
       ScriptedAgent,
       Task,
       Trial,
       TrialConfig,
   )


   def candidate(trial_id: str, answer: str) -> Trial:
       return Trial(
           task=Task(id="capital-of-france", input={"question": "Capital?"}),
           agent=ScriptedAgent(
               [Action.finish(answer)],
               name=f"{trial_id}-agent",
               version="1",
           ),
           environment=LookupEnvironment(
               {},
               name="country-capitals",
               version="1",
           ),
           evaluator=ExactEvaluator("Paris", version="1"),
           config=TrialConfig(trial_id=trial_id, seed=7, max_actions=1),
       )


   async def compare() -> None:
       store = JsonlTrajectoryStore("runs/capitals.jsonl")
       result = await Experiment(
           experiment_id="capitals",
           version="1",
           baseline="baseline",
           provenance={"source_revision": "abc123"},
           trials={
               "baseline": (candidate("baseline-7", "Lyon"),),
               "candidate": (candidate("candidate-7", "Paris"),),
           },
       ).run(store)

       assert result.complete
       assert not result.results["baseline"][0].evaluation.passed
       assert result.results["candidate"][0].evaluation.passed
       assert JsonlTrajectoryStore("runs/capitals.jsonl").load() == result


   asyncio.run(compare())

恢复与完整性语义
~~~~~~~~~~~~~~~~

- 相同 plan 再次运行时，已提交 Trial 通过 Replay 恢复，不再次调用 Agent、Environment 或 Evaluator；
  同一文件出现不同 plan hash 时，会在新 Trial 副作用之前报冲突。
- Store 为 full Trajectory、Trial spec 和每一行维护独立 digest/chain。digest 用于发现意外损坏，
  不是签名或真实性证明；JSON reader 只接受 canonical JSON，并拒绝重复 key、NaN/Infinity、
  错误版本和超限记录。
- 非空文件必须以 LF 结束。未终止的最后一行不会被视为已提交；调用方可以显式调用
  ``store.repair_tail()`` 截掉它。完整但损坏的中间行、坏 digest 或重排行会 fail closed。
- Trial 执行前先持久化 start marker。载入时，只有 start、没有终态 Trajectory 的 Trial 出现在
  ``started_trial_ids``；在没有活跃 writer 的载入 snapshot 中，它表示 interrupted Trial。
  ``Experiment.run()`` 不会自动 Re-execution，以免重复外部 Action，但会继续执行同一 plan 中从未
  开始的 Trial，并返回 ``complete=False`` 的结果。若终态写入失败而同一个 ``Experiment`` 对象仍
  保有 replay-valid Trajectory，且该对象曾向同一路径持久化对应 start marker 并在终态复检组件声明，
  再次运行只补交这次内存尝试，不重复 Agent 或 Environment 调用。artifact 被替换或回滚不在此保证内。
- 当前实现顺序执行并强制 ``single writer``；第二个 writer 和并发尾修复会在任何新副作用前失败。
  取消中的 Trial 会尝试先提交 cancelled Trajectory，再继续传播 ``CancelledError``；若提交本身失败，
  取消仍是主异常，持久化错误会附在 exception note 中。
- ``load()`` 通过 reader lock 取得一致 snapshot，并可读取不带可写 lock sidecar 的只读 artifact 副本。
  POSIX 支持跨进程共享 reader lock；Windows CRT 路径会把跨进程 reader 串行化，busy 时 fail fast。
- 行链可以发现可见前缀内部的修改、插入和重排，但单个 append-only 文件无法自行证明完整后缀未被
  删除或回滚；若完整 start/commit 后缀被删除，fresh resume 可能把对应 slot 当作从未开始并再次执行。
  它不提供真实性、抗回滚或外部 Action exactly-once；应保护 artifact 路径并保留独立备份。

.. warning::

   Harness JSONL 可能包含 Task 输入或 prompt、Observation、Action、错误消息、组件配置和调用方
   provenance。调用方必须在写入前清理 secret，并保护目录、备份和传输路径。POSIX 上新建 artifact
   使用私有文件权限，但 digest 只提供完整性检查，不提供机密性或真实性。

Harness JSONL 使用独立的 provisional 格式版本，不读取稳定消息合同的
``iamai.SERIALIZATION_CONTRACT_VERSION``。这两个格式可以独立演进；Harness plan hash 还覆盖
variant 顺序、baseline、Task、seed、预算、组件声明和调用方 provenance。

当前边界
--------

- ``ScriptedAgent``、``LookupEnvironment`` 与 ``ExactEvaluator`` 是确定性基线，不是完整 Agent 产品。
- 一个 ``Trial`` 只能运行一次；当前预算只限制 Action 数量。
- 当前 Store 是单文件本地 JSONL；跨 Experiment 查询、artifact manifest、统计汇总、schema migration、
  mid-Trial resume、沙箱、模型 provider、学习器和消息桥接尚未加入。
- 恢复合同面向预先存在父目录上的本地文件系统与进程中断/末行撕裂；不声明断电、NFS、共享挂载或
  多主机 writer 的持久性保证。
- Store 恢复不等于外部 Action exactly-once；start marker 只阻止不明确的 interrupted Trial 被自动重跑。
- provisional namespace 可以在 ``1.x`` 内迭代；稳定消息 Runtime 的公共合同不随它改变。
- 关于能力或通用性的结论必须同时报告 Task/Environment 分布、seed、预算、组件版本和基线。

工程顺序见 :doc:`roadmap`；稳定消息执行面与旧有模型助手的区别见 :doc:`agent-runtime`。
