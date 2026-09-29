#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""流水线端到端冒烟测试（orchestrator 调度链机器实测）。

用法（仓库根）：
    python scripts/smoke_pipeline.py

退出码：0=冒烟通过  1=有失败

覆盖：
  1. 按 orchestrator 调度顺序跑五棒门禁：check_prd -> check_review ->
     check_source -> check_qa -> scan_security，产物 01-05 全链路 rc=0
  2. 打回->修复->再通过 路由：把 01-prd.md 改坏（缺一节）check_prd 应 rc=1，
     写回完整版后应 rc=0（等价于 orchestrator 的"门禁打回自动路由"）
  3. 全部临时产物在临时目录生成，不污染仓库

任何 FAIL = 流水线链路漂移。改任一棒门禁脚本或 orchestrator 调度后必跑本测试。
"""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

CHECK_PRD = ROOT / "product-manager" / "scripts" / "check_prd.py"
CHECK_REVIEW = ROOT / "requirement-reviewer" / "scripts" / "check_review.py"
CHECK_SOURCE = ROOT / "software-developer" / "scripts" / "check_source.py"
CHECK_QA = ROOT / "qa-tester" / "scripts" / "check_qa.py"
SCAN_SECURITY = ROOT / "security-pentester" / "scripts" / "scan_security.py"

PRD_OK = """# 冒烟演示 PRD

## 1. 背景与目标
- 一句话概括：我们要为演示用户在演示场景下解决链路验证问题，成功后达成冒烟通过。

## 2. 目标用户与场景
- 目标用户：演示用户
- 核心使用场景：端到端冒烟

## 3. 用户故事
- US-1：作为演示用户，我希望整条流水线一次跑通，以便交付验收。

## 4. 功能需求清单
| 编号 | 功能 | 优先级 | 描述 |
|---|---|---|---|
| FR-01 | 冒烟演示 | P0 | 生成五棒产物并逐个过门禁 |

## 5. 业务流程
1. 生成 PRD
2. 评审
3. 编码
4. 测试
5. 安全扫描

异常分支：
- 当门禁非 0 时，产物打回对应棒重做。

## 6. 非功能需求
- 性能：冒烟耗时小于 2 分钟
- 安全：演示代码不含危险模式

## 7. 范围边界
**本期做**：FR-01
**本期不做**：生产级功能

## 8. 验收标准
- FR-01：Given 演示项目，When 走完五棒，Then 五棒门禁全 rc=0。

## 9. 依赖
- 外部依赖：无

## 10. 里程碑
- 阶段1：冒烟通过，1 小时
"""

REVIEW_OK = """# 评审报告

结论：YES

## 完整性
完整。
## 可执行性
可执行。
## 边界
清晰。
## 验收
可验收。
## 技术可行
可行。
## 合规
合规。
"""

SOURCE_README = """# 冒烟演示项目

如何运行：python app.py

## 说明
演示用最小代码，不含危险模式。
"""

SOURCE_APP_PY = '''"""冒烟演示入口。"""
import sys


def add(a, b):
    """加法。"""
    return a + b


def main():
    print(add(1, 2))


if __name__ == "__main__":
    main()
'''

SOURCE_UTILS_JS = """// 冒烟演示工具
function sum(a, b) {
  return a + b;
}
module.exports = { sum };
"""

QA_OK = """# 测试报告

结论：通过

## bug 清单
- 所有用例通过，无遗留问题
- 回归通过
"""

SECURITY_OK = """# 安全报告

结论：无高危问题

## 扫描结果
- 正则粗扫：无 HIGH / MED 命中
- bandit 深度扫：无 HIGH / MED 命中
"""


def run(script, *args):
    cmd = [sys.executable, str(script), *args]
    p = subprocess.run(cmd, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    return p.returncode


def write(path, content):
    Path(path).write_text(content, encoding="utf-8")
    return str(path)


def main():
    print("=" * 64)
    print("流水线端到端冒烟测试（orchestrator 调度链）")
    print("=" * 64)

    fails = []
    with tempfile.TemporaryDirectory(prefix="smoke_pipeline_") as td:
        ws = Path(td)
        # 1) 生成五棒产物
        p_prd = write(ws / "01-prd.md", PRD_OK)
        p_rev = write(ws / "02-requirement-review.md", REVIEW_OK)
        src = ws / "03-source"
        src.mkdir()
        write(src / "README.md", SOURCE_README)
        write(src / "app.py", SOURCE_APP_PY)
        write(src / "utils.js", SOURCE_UTILS_JS)
        p_qa = write(ws / "04-qa-test-report.md", QA_OK)
        p_sec = write(ws / "05-security-report.md", SECURITY_OK)

        # 2) 按 orchestrator 顺序跑五棒门禁
        steps = [
            ("棒1 PM check_prd", CHECK_PRD, [p_prd], 0),
            ("棒2 RR check_review", CHECK_REVIEW, [p_rev], 0),
            ("棒3 SD check_source", CHECK_SOURCE, [str(src)], 0),
            ("棒4 QA check_qa", CHECK_QA, [p_qa], 0),
            ("棒5 SP scan_security", SCAN_SECURITY, [str(src)], 0),
        ]
        for name, script, args, want in steps:
            rc = run(script, *args)
            ok = rc == want
            print(f"  [{'PASS' if ok else 'FAIL'}] {name}: rc={rc} (期望 {want})")
            if not ok:
                fails.append(name)

        # 3) 打回->修复->再通过 路由
        broken = PRD_OK.replace("## 10. 里程碑\n- 阶段1：冒烟通过，1 小时\n", "")
        write(ws / "01-prd.md", broken)
        rc_bad = run(CHECK_PRD, p_prd)
        ok_bad = rc_bad == 1
        print(f"  [{'PASS' if ok_bad else 'FAIL'}] 打回路由: 缺里程碑 check_prd rc={rc_bad} (期望 1)")
        if not ok_bad:
            fails.append("打回路由-改坏样本")

        write(ws / "01-prd.md", PRD_OK)
        rc_good = run(CHECK_PRD, p_prd)
        ok_good = rc_good == 0
        print(f"  [{'PASS' if ok_good else 'FAIL'}] 修复路由: 写回完整版 check_prd rc={rc_good} (期望 0)")
        if not ok_good:
            fails.append("修复路由-完整样本")

    print("-" * 64)
    if fails:
        print(f"结果: 失败 {len(fails)} 项 -> {fails}，退出码 1")
        return 1
    print("结果: 冒烟通过（五棒门禁链 + 打回/修复路由均符合契约），退出码 0")
    return 0


if __name__ == "__main__":
    sys.exit(main())
