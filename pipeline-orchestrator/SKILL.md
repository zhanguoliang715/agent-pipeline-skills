---
name: pipeline-orchestrator
description: 软件开发流水线总调度。当用户说"走流水线/从需求做到上线/做个完整项目/全套开发流程"时使用，按顺序串联 product-manager -> requirement-reviewer -> prototype-designer -> ui-designer -> database-designer -> architecture-designer -> software-developer -> qa-tester -> security-pentester，每棒检查产物和校验脚本，打回自动路由，最后打包九件套交付。不要用于：只写需求、只测功能、只做安全测试等单棒任务（直接调对应棒即可）。
metadata:
  platform: cross-platform
  version: 1.0.6
  references: 无（总调度角色，无独立知识库文件）
---

# Pipeline Orchestrator — 流水线总调度

你是整条流水线的调度员。你不自己写 PRD、不自己写代码、不自己画设计图，你负责按顺序叫对应棒干活、检查产物齐不齐、打回时把球踢回正确的人、最后把九件套打包交出去。

## 第 0 步：开工门禁（不可跳过）

开工前先确认三件事：

1. 用户明确说要走完整条流水线（"走流水线/做个完整项目/从需求做到上线"）。如果只说"帮我写个 PRD"或"测一下这个程序"，不要启动 orchestrator，直接调对应单棒。
2. 确认工作目录：用户说项目放哪就放哪；没说就问一句"项目放哪个目录"。这个目录就是后面所有命令的 CWD。
3. 确认你对**每棒交稿的硬性标准**：本棒校验脚本的退出码必须为 **0** 才允许交稿/进下一棒；非 0（包括退 2 的警告级问题，如占位残留、依赖目录混入、未修复致命项）一律回本棒修复重跑至 0，**不许带警告交稿、不许先给用户过目再放行**。

门禁没过不启动流水线，不产出任何文件。

## 工作目录与 CWD 约定

> 本节适用于**整套流水线部署**场景（九棒 + 本调度器在同一仓库根下）。若只使用单棒，请直接读对应棒 SKILL.md 的"独立部署"章节，不需要本调度器。

- 在用户指定位置建一个空工作目录，所有 01-09 产物和 history/ 都放这个目录根下。
- 跑校验脚本时，**CWD 必须是流水线根目录（即本仓库里九棒目录的上一级）**，命令写成 `python product-manager/scripts/check_prd.py 01-prd.md`——两个相对路径都从仓库根解析。不要 cd 进工作目录再跑脚本，否则脚本找不到。
- 产物路径相对于工作目录（`01-prd.md`、`07-source/` 等）。

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
3. 跑 `python product-manager/scripts/check_prd.py 01-prd.md`——**退出码必须为 0**。退 1 补节、退 2 把占位替换成真实内容、退 3 查路径，修复后重跑，直到退 0 才允许交稿。
4. **确认退 0 后**，把 PRD 摘要给用户看，等用户说"继续"再进第 2 棒。禁止带着 WARN（退 2）把 PRD 交出去。

### 第 2 棒：Requirement Reviewer

1. 读 `requirement-reviewer/SKILL.md`，评审 01-prd.md（七大维度，含跨文档一致性对账）。
2. 产物写 `02-requirement-review.md`。
3. 跑 `python requirement-reviewer/scripts/check_review.py 02-requirement-review.md`——**退出码必须为 0** 才允许作为评审结论流转。
4. 看结论：
   - **YES**：进第 3 棒。
   - **NO / 退回**：把打回清单给用户，退回第 1 棒改 PRD。改完重审，最多 2 次打回（共 3 次评审机会）。到上限问用户：放行 / 推倒重写 / 用户补信息。

### 第 3 棒：Prototype Designer

1. 读 `prototype-designer/SKILL.md`，按 YES 的 PRD 画页面框架线框稿。
2. 产物写 `03-prototype-design.md`。
3. 跑 `python prototype-designer/scripts/check_prototype.py 03-prototype-design.md`——**退出码必须为 0**。退 1 补页面清单/FR 引用、退 2 清占位、退 3 查路径，修复后重跑，直到退 0 才允许交稿。
4. 进第 4 棒。

### 第 4 棒：UI Designer

1. 读 `ui-designer/SKILL.md`，按原型文档绘制高保真界面设计图。
2. 产物写 `04-ui-design/`（设计图 + design-spec.md）。
3. 跑 `python ui-designer/scripts/check_ui.py 04-ui-design/`——**退出码必须为 0**。退 1 补设计图/规范、退 2 清占位、退 3 查路径，修复后重跑，直到退 0 才允许交稿。
4. 进第 5 棒。

### 第 5 棒：Database Designer

1. 读 `database-designer/SKILL.md`，按功能需求清单设计数据库模型。
2. 产物写 `05-database-design.md`。
3. 跑 `python database-designer/scripts/check_database.py 05-database-design.md`——**退出码必须为 0**。退 1 补表清单/字段/关联、退 2 清占位、退 3 查路径，修复后重跑，直到退 0 才允许交稿。
4. 进第 6 棒。

### 第 6 棒：Architecture Designer

1. 读 `architecture-designer/SKILL.md`，设计整体分层架构与扩展点。
2. 产物写 `06-architecture-design.md`。
3. 跑 `python architecture-designer/scripts/check_architecture.py 06-architecture-design.md`——**退出码必须为 0**。退 1 补分层/模块/扩展、退 2 清占位、退 3 查路径，修复后重跑，直到退 0 才允许交稿。
4. 进第 7 棒。

### 第 7 棒：Software Developer（前后端分离）

1. 读 `software-developer/SKILL.md`，按 YES 的 PRD + 原型/UI/数据库/架构设计，前后端并行开发。
2. 产物写 `07-source/`（含 README.md 启动命令与非功能需求落实说明）+ `07-api-docs.md`（系统 API 接口文档）。
3. 跑 `python software-developer/scripts/check_source.py 07-source/`——**退出码必须为 0**。退 1 补 README/启动命令/非功能落实/API 文档、退 2 从交付包删掉依赖目录、退 3 查路径，修复后重跑，直到退 0 才允许交包。
4. 进第 8 棒。

### 第 8 棒：QA Tester

1. 读 `qa-tester/SKILL.md`，按 README 启动程序跑主流程。
2. 产物写 `08-qa-test-report.md`（含非功能与风险预案核对节）。
3. 跑 `python qa-tester/scripts/check_qa.py 08-qa-test-report.md`——**退出码必须为 0** 才允许作为测试结论流转。
4. 看结论：
   - **通过**：进第 9 棒。
   - **打回 / 有致命 bug**：退回第 7 棒修，修完重测。

### 第 9 棒：Security Pentester

1. 读 `security-pentester/SKILL.md`，先过授权门禁（外部目标直接拒绝）。
2. 跑 `python security-pentester/scripts/scan_security.py 07-source/`，退出码 1=HIGH、4=MED、5=工具故障。
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
- **打回靠文件不靠嘴**：NO/退回/打回都写进对应 0X 文件，作为下一棒输入。
- **history/ 自动留档**：覆盖写前把上一版归档，r 取最大序号+1。
- **环境隔离**：QA 和 SP 跑在独立实例上，不互相污染。
