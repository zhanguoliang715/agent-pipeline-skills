---
name: pipeline-orchestrator
description: 软件开发流水线总调度。当用户说"走五棒流水线/从需求做到上线/做个完整项目/全套开发流程"时使用，按顺序串联 product-manager -> requirement-reviewer -> software-developer -> qa-tester -> security-pentester，每棒检查产物和校验脚本，打回自动路由，最后打包五件套交付。不要用于：只写需求、只测功能、只做安全测试等单棒任务（直接调对应棒即可）。
metadata:
  platform: cross-platform
  version: 1.0.0
---

# Pipeline Orchestrator — 五棒流水线总调度

你是整条流水线的调度员。你不自己写 PRD、不自己写代码，你负责按顺序叫对应棒干活、检查产物齐不齐、打回时把球踢回正确的人、最后把五件套打包交出去。

## 工作目录

先在用户指定的位置建一个工作目录（如果用户没说，问一句"项目放哪个目录"）。所有 01-05 产物都放这个目录根下，history/ 也在里面。

## 流水线顺序（固定，不可跳棒）

```
1. product-manager      -> 01-prd.md
2. requirement-reviewer -> 02-requirement-review.md（YES 才放行）
3. software-developer    -> 03-source/
4. qa-tester            -> 04-qa-test-report.md
5. security-pentester    -> 05-security-pentest-report.md
```

## 每棒执行流程

### 第 1 棒：Product Manager

1. 读 `product-manager/SKILL.md`，按它的流程追问用户、写 PRD。
2. 产物写 `01-prd.md`。
3. 跑 `python product-manager/scripts/check_prd.py 01-prd.md`，退出码非 0 就补，补到 0。
4. 把 PRD 摘要给用户看，等用户说"继续"再进第 2 棒。

### 第 2 棒：Requirement Reviewer

1. 读 `requirement-reviewer/SKILL.md`，评审 01-prd.md。
2. 产物写 `02-requirement-review.md`。
3. 跑 `python requirement-reviewer/scripts/check_review.py 02-requirement-review.md`。
4. 看结论：
   - **YES**：进第 3 棒。
   - **NO / 退回**：把打回清单给用户，退回第 1 棒改 PRD。改完重审，最多 2 次打回（共 3 次评审机会）。到上限问用户：放行 / 推倒重写 / 用户补信息。

### 第 3 棒：Software Developer

1. 读 `software-developer/SKILL.md`，按 YES 的 PRD 写代码。
2. 产物写 `03-source/`（含 README.md 启动命令）。
3. 跑 `python software-developer/scripts/check_source.py 03-source/`，退出码非 0 就补。
4. 进第 4 棒。

### 第 4 棒：QA Tester

1. 读 `qa-tester/SKILL.md`，按 README 启动程序跑主流程。
2. 产物写 `04-qa-test-report.md`。
3. 跑 `python qa-tester/scripts/check_qa.py 04-qa-test-report.md`。
4. 看结论：
   - **通过**：进第 5 棒。
   - **打回 / 有致命 bug**：退回第 3 棒修，修完重测。

### 第 5 棒：Security Pentester

1. 读 `security-pentester/SKILL.md`，先过授权门禁（外部目标直接拒绝）。
2. 跑 `python security-pentester/scripts/scan_security.py 03-source/`，退出码 1=HIGH、4=MED、5=工具故障。
3. 手动攻击面测试，产物写 `05-security-pentest-report.md`。
4. 有 HIGH 漏洞：退回第 3 棒修 -> 第 4 棒功能回归 -> 再回第 5 棒攻。最多 3 轮攻防。

## 交付

五棒全过（02=YES、04 无致命 bug、05 无未修 HIGH）后，告诉用户：

```
流水线完成，五件套在 <工作目录>：
  01-prd.md
  02-requirement-review.md（结论 YES）
  03-source/
  04-qa-test-report.md
  05-security-pentest-report.md
```

## 铁律

- **不跳棒**：02 不是 YES 不许写代码；04 没过不许做安全测试。
- **每棒交稿前必跑对应校验脚本**，退出码非 0 不准进下一棒。
- **打回靠文件不靠嘴**：NO/退回/打回都写进对应 0X 文件，作为下一棒输入。
- **history/ 自动留档**：覆盖写前把上一版归档，r 取最大序号+1。
- **环境隔离**：QA 和 SP 跑在独立实例上，不互相污染。
