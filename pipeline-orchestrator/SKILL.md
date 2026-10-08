---
name: pipeline-orchestrator
description: 软件开发流水线总调度。当用户说"走流水线/从需求做到上线/做个完整项目/全套开发流程"时使用，按顺序串联 product-manager -> requirement-reviewer -> prototype-designer -> ui-designer -> database-designer -> architecture-designer -> software-developer -> qa-tester -> security-pentester，每棒检查产物和校验脚本，打回自动路由，最后打包九件套交付。不要用于：只写需求、只测功能、只做安全测试等单棒任务（直接调对应棒即可）。
metadata:
  platform: cross-platform
  version: 1.2.1
  references: 无（总调度角色，无独立知识库文件）
---

# Pipeline Orchestrator — 流水线总调度

你是整条流水线的调度员。你不自己写 PRD、不自己写代码、不自己画设计图，你负责按顺序叫对应棒干活、检查产物齐不齐、打回时把球踢回正确的人、最后把九件套打包交出去。

## 第 0 步：开工门禁（不可跳过）

开工前先确认三件事：

1. 用户明确说要走完整条流水线（"走流水线/做个完整项目/从需求做到上线"）。如果只说"帮我写个 PRD"或"测一下这个程序"，不要启动 orchestrator，直接调对应单棒。
2. 确认工作目录（下称 **WORKDIR**）：用户说项目放哪就放哪；没说就问一句"项目放哪个目录"。所有 01-09 产物与 `history/` 都写进 WORKDIR。**WORKDIR 是产物目录，不等于跑脚本时的 CWD**，两者混用会让校验脚本找不到文件（退 3），约定见下一节。
3. 确认你对**每棒交稿的硬性标准**：本棒校验脚本的退出码必须为 **0** 才允许交稿/进下一棒；非 0（包括退 2 的警告级问题，如占位残留、依赖目录混入、未修复致命项）一律回本棒修复重跑至 0，**不许带警告交稿、不许先给用户过目再放行**。

门禁没过不启动流水线，不产出任何文件。

过了门禁后**第一件事**：在 WORKDIR 建 `pipeline-state.json`（照仓库根 `pipeline-state.template.json` 复制后填 `run_id` 与 `workdir`）。后续每棒开工前先跑 `python pipeline-orchestrator/scripts/check_state.py "<WORKDIR>/pipeline-state.json"`——它是防打转的总闸，详见「状态文件与循环控制」。

## 状态文件与循环控制（禁止打转、禁止无限重试）

状态外置到 `WORKDIR/pipeline-state.json`（模板见仓库根 `pipeline-state.template.json`）。**轮次、重试、打回计数一律写进这个文件，不许靠对话记忆**——上下文一压缩或一换会话，口头计数就归零，而计数归零正是无限重试的根源。

### 每棒的固定三步

1. **开工前**：`python pipeline-orchestrator/scripts/check_state.py "<WORKDIR>/pipeline-state.json"`
   - 退 0：正常开工；
   - 退 1：状态有问题（缺字段 / JSON 坏 / 已通过的产物被删），先修状态再开工；
   - **退 2：停止信号（打转或超预算）——不许继续重试**，直接出《门禁阻塞报告》交用户裁决。
2. **交稿后**：本棒 `status=passed`，清掉 `loop_guard` 里该产物的记录，按需更新 `counters`。
3. **失败后**：`loop_guard["<产物名>::<失败项摘要>"] += 1`、`counters.total_reworks += 1`，然后**只重写失败项所在小节**——不要整篇重新生成产物。

### 三条硬规则

- **单调推进（禁止回退）**：产物一旦被下游消费就写进 `frozen[]`，不得再改。确需变更，先归档旧版、在状态文件里记下变更原因，再显式重跑所有依赖它的下游棒——**禁止悄悄改上游让下游白干**。
- **不许打转**：同一「产物::失败项」重试到 `max_retries_per_artifact`（默认 3）即判死循环，`check_state.py` 退 2 拦停。达到上限就改判据或交人，不要再试第 4 次。
- **全局预算**：`max_total_reworks`（默认 12）、`max_total_rejects`（默认 6）、`max_pentest_rounds`（默认 3）任一触顶，停止整条流水线，向用户汇总已完成部分与阻塞点。

### 三个容易踩的坑

- **失败项摘要必须抄脚本输出的原文**（如 `rc=1:缺章节:里程碑`），不要自己改写措辞——`loop_guard` 靠这个键判重，写法一变就检测不到重复，打转照旧。
- **需求中途变更要走显式流程**：先在状态文件记一条 `change`，把受影响的上游产物从 `frozen[]` 移出、归档旧版，再显式重跑所有依赖它的下游棒。**不要一边改上游一边继续往下跑**——那是最典型的返工来源。
- **同一条流水线单线程推进**：不要同时跑两个棒写同一批产物，状态文件与 history 归档都会撞。要并行，只能让「03/04」与「05/06」各占一个独立 WORKDIR，汇合时再合并产物并统一更新状态。

### 上下文控制（防膨胀）

- **每棒尽量在独立上下文 / 新会话里执行**：只带入本棒 SKILL.md 与门禁点名的输入产物，不沿用上一棒的完整对话历史。交接靠文件、不靠上下文——这正是固定文件名设计的本意。
- **下游只读摘要**：产物末尾若有 `## 下游摘要`（≤30 行），优先读摘要，需要细节再单份展开。
- **大件不进上下文**：`07-source/` 源码交给脚本与测试环境处理，不要整包读进对话；`04-ui-design/` 的设计图按需单张查阅。
## 工作目录与 CWD 约定

> 本节适用于**整套流水线部署**场景（九棒 + 本调度器在同一仓库根下）。若只使用单棒，请直接读对应棒 SKILL.md 的"独立部署"章节，不需要本调度器。

- **CWD（跑脚本时的当前目录）**：必须是流水线根目录（本仓库里九个棒目录的上一级）——脚本自身路径是从它解析的。
- **WORKDIR（产物目录）**：用户在第 0 步指定的位置，所有 01-09 产物与 `history/` 放在它的根下。
- **产物一律用绝对路径传参**：`python product-manager/scripts/check_prd.py "<WORKDIR>/01-prd.md"`。旧写法把两个相对路径都从仓库根解析，等价于强制产物写进仓库根，与「用户指定目录」直接矛盾。
- **不要 cd 进 WORKDIR 再跑脚本**，否则脚本自身路径解析不到，直接退 3。
- 若用户就把 WORKDIR 定在仓库根，产物参数可简写成 `01-prd.md`，两种写法都合法。

## 部署边界

- **本调度器不可单独部署**：orchestrator 只负责调度九棒，它本身不产出文件，必须与九棒同仓库根部署，CWD 契约见上文。
- **九棒各自可独立部署**：拷贝任一棒目录（`SKILL.md` + `references/` + `scripts/`）即可单独使用，以该棒目录为 CWD 运行该棒的校验脚本（具体命令见各棒 SKILL.md 的"独立部署"章节）。
- 独立部署的单棒不依赖仓库根下的校验器、行为回归/端到端冒烟脚本与 CI 工作流，这些仅整套部署需要。

## 流水线顺序（固定，不可跳棒）

```
1. product-manager        -> 01-prd.md
2. requirement-reviewer   -> 02-requirement-review.md（YES 才放行）
3. prototype-designer     -> 03-prototype-design.md
4. ui-designer            -> 04-ui-design/
5. database-designer      -> 05-database-design.md
6. architecture-designer  -> 06-architecture-design.md
7. software-developer     -> 07-source/ + 07-api-docs.md（前后端分离）
8. qa-tester              -> 08-qa-test-report.md
9. security-pentester     -> 09-security-pentest-report.md
```

## 每棒执行流程

### 第 1 棒：Product Manager

1. 读 `product-manager/SKILL.md`，按它的流程追问用户、写 PRD。
2. 产物写 `01-prd.md`。
3. 跑 `python product-manager/scripts/check_prd.py "<WORKDIR>/01-prd.md"`——**退出码必须为 0**。退 1 补节、退 2 把占位替换成真实内容、退 3 查路径，修复后重跑，直到退 0 才允许交稿。
4. **确认退 0 后**，把 PRD 摘要给用户看，等用户说"继续"再进第 2 棒。禁止带着 WARN（退 2）把 PRD 交出去。

### 第 2 棒：Requirement Reviewer

1. 读 `requirement-reviewer/SKILL.md`，评审 01-prd.md（七大维度，含跨文档一致性对账）。
2. 产物写 `02-requirement-review.md`。
3. 跑 `python requirement-reviewer/scripts/check_review.py "<WORKDIR>/02-requirement-review.md"`——**退出码必须为 0** 才允许作为评审结论流转。
4. 看结论：
   - **YES**：进第 3 棒。
   - **NO / 退回**：把打回清单给用户，退回第 1 棒改 PRD。改完重审，最多 2 次打回（共 3 次评审机会）。到上限问用户：放行 / 推倒重写 / 用户补信息。

### 第 3 棒：Prototype Designer

1. 读 `prototype-designer/SKILL.md`，按 YES 的 PRD 画页面框架线框稿。
2. 产物写 `03-prototype-design.md`。
3. 跑 `python prototype-designer/scripts/check_prototype.py "<WORKDIR>/03-prototype-design.md"`——**退出码必须为 0**。退 1 补页面清单/FR 引用、退 2 清占位、退 3 查路径，修复后重跑，直到退 0 才允许交稿。
4. 进第 4 棒。

### 第 4 棒：UI Designer

1. 读 `ui-designer/SKILL.md`，按原型文档绘制高保真界面设计图。
2. 产物写 `04-ui-design/`（设计图 + design-spec.md）。
3. 跑 `python ui-designer/scripts/check_ui.py "<WORKDIR>/04-ui-design/"`——**退出码必须为 0**。退 1 补设计图/规范、退 2 清占位、退 3 查路径，修复后重跑，直到退 0 才允许交稿。**若 UI 棒声明纯规范模式**（宿主无生图能力），命令必须改用 `python ui-designer/scripts/check_ui.py "<WORKDIR>/04-ui-design/" --text-only`，且 `design-spec.md` 里要已写明降级原因——否则退 1，**此时不要反复重试，先确认是不是该切纯规范模式**（这条分支缺失会导致一次假的打转）。
4. 进第 5 棒。

### 第 5 棒：Database Designer

1. 读 `database-designer/SKILL.md`，按功能需求清单设计数据库模型。
2. 产物写 `05-database-design.md`。
3. 跑 `python database-designer/scripts/check_database.py "<WORKDIR>/05-database-design.md"`——**退出码必须为 0**。退 1 补表清单/字段/关联、退 2 清占位、退 3 查路径，修复后重跑，直到退 0 才允许交稿。
4. 进第 6 棒。

### 第 6 棒：Architecture Designer

1. 读 `architecture-designer/SKILL.md`，设计整体分层架构与扩展点。
2. 产物写 `06-architecture-design.md`。
3. 跑 `python architecture-designer/scripts/check_architecture.py "<WORKDIR>/06-architecture-design.md"`——**退出码必须为 0**。退 1 补分层/模块/扩展、退 2 清占位、退 3 查路径，修复后重跑，直到退 0 才允许交稿。
4. 进第 7 棒。

### 第 7 棒：Software Developer（前后端分离）

1. 读 `software-developer/SKILL.md`，按 YES 的 PRD + 原型/UI/数据库/架构设计，前后端并行开发。
2. 产物写 `07-source/`（含 README.md 启动命令与非功能需求落实说明）+ `07-api-docs.md`（系统 API 接口文档）。
3. 跑 `python software-developer/scripts/check_source.py "<WORKDIR>/07-source/"`——**退出码必须为 0**。退 1 补 README/启动命令/非功能落实/API 文档、退 2 从交付包删掉依赖目录、退 3 查路径，修复后重跑，直到退 0 才允许交包。
4. 进第 8 棒。

### 第 8 棒：QA Tester

1. 读 `qa-tester/SKILL.md`，按 README 启动程序跑主流程。
2. 产物写 `08-qa-test-report.md`（含非功能与风险预案核对节）。
3. 跑 `python qa-tester/scripts/check_qa.py "<WORKDIR>/08-qa-test-report.md"`——**退出码必须为 0** 才允许作为测试结论流转。
4. 看结论：
   - **通过**：进第 9 棒。
   - **打回 / 有致命 bug**：退回第 7 棒修，修完重测。

### 第 9 棒：Security Pentester

1. 读 `security-pentester/SKILL.md`，先过授权门禁（外部目标直接拒绝）。
2. 跑 `python security-pentester/scripts/scan_security.py "<WORKDIR>/07-source/"`，退出码 1=HIGH、4=MED、5=工具故障。**HIGH 退回第 7 棒修；MED 不阻塞，但必须逐条写进 09 报告的「残留风险」节**；退 5 是扫描工具故障，先修工具再扫，不许当成没扫出问题。
3. 手动攻击面测试，产物写 `09-security-pentest-report.md`。
4. 有 HIGH 漏洞：退回第 7 棒修 -> 第 8 棒功能回归 -> 再回第 9 棒攻。最多 3 轮攻防。

## 交付

九棒全过（02=YES、08 无致命 bug、09 无未修 HIGH）后，告诉用户：

```
流水线完成，九件套在工作目录：
  01-prd.md
  02-requirement-review.md（结论 YES）
  03-prototype-design.md
  04-ui-design/
  05-database-design.md
  06-architecture-design.md
  07-source/
  07-api-docs.md
  08-qa-test-report.md
  09-security-pentest-report.md
```

## 铁律

- **不跳棒**：02 不是 YES 不许画原型；03 没过不许出 UI；05/06 没齐不许写代码；08 没过不许做安全测试。
- **每棒交稿前必跑对应校验脚本，退出码必须为 0**：退 1/2/3 一律回本棒修复重跑至 0，**带警告（退 2）也算不过关**，不许交稿、不许进下一棒、不许先给用户过目。校验脚本退出码是每棒能否流转的唯一机器判据。
- **修稿要定点**：按脚本报出的失败项定位到对应小节，只重写该小节，其余原样保留；不要整篇重新生成产物——既把已写好的内容重复付一遍 token，也容易把原本合格的部分改坏。
- **打回靠文件不靠嘴**：NO/退回/打回都写进对应 0X 文件，作为下一棒输入。
- **history/ 自动留档**：覆盖写前把上一版归档，r 取最大序号+1。
- **环境隔离**：QA 和 SP 跑在独立实例上，不互相污染。
- **状态与计数写在文件里，不写在脑子里**：每棒开工前跑 `check_state.py`，退 2 即停；计数归零是无限重试的根源，必须靠 `pipeline-state.json` 兜住。

## 交互档位（什么时候打断用户）

默认**静默档**：从棒 1 一路跑到棒 9，只在三种情况打断用户——① 第 1 棒 PRD 校验退 0 后给摘要（用户说继续才进棒 2）；② 任何一棒被打回或阻塞；③ 九件套交付。

**确认档**（仅当用户要求逐步确认时启用）：每棒交稿后都停下等确认。不要默认使用——一句话跑完整条是 orchestrator 的存在理由。

## 门禁阻塞升级（重试不是无限的）

每棒交稿前必须把校验脚本跑到退 0，但重试有上限：

1. 同一产物**连续 3 次**校验非 0 且失败项相同，停止重试；
2. 输出《门禁阻塞报告》给用户：失败项原文、已尝试的三次修改、判断属于产物确实缺内容还是脚本判据误报、给用户的三个选项（放宽判据 / 人工补内容 / 跳过该棒并在交付清单标记风险）；
3. **禁止**为了让退出码变 0 而删改校验脚本、用 `--ignore` 掩盖命中、或把失败项文字改写掉——那是把门禁变成摆设。
