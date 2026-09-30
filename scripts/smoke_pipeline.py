#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""流水线端到端冒烟测试（orchestrator 调度链机器实测）。

用法（仓库根）：
    python scripts/smoke_pipeline.py

退出码：0=冒烟通过  1=有失败

覆盖：
  1. 按 orchestrator 调度顺序跑九棒门禁：check_prd -> check_review ->
     check_prototype -> check_ui -> check_database -> check_architecture ->
     check_source -> check_qa -> scan_security，产物 01-09 全链路 rc=0
  2. 打回->修复->再通过 路由：把 01-prd.md 改坏（缺一节）check_prd 应 rc=1，
     写回完整版后应 rc=0；把 03-prototype-design.md 改坏（缺 FR 引用）
     check_prototype 应 rc=1，写回完整版后应 rc=0（等价于 orchestrator 的
     "门禁打回自动路由"）
  3. 全部临时产物在临时目录生成，不污染仓库

任何 FAIL = 流水线链路漂移。改任一棒门禁脚本或 orchestrator 调度后必跑本测试。
"""
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

CHECK_PRD = ROOT / "product-manager" / "scripts" / "check_prd.py"
CHECK_REVIEW = ROOT / "requirement-reviewer" / "scripts" / "check_review.py"
CHECK_PROTOTYPE = ROOT / "prototype-designer" / "scripts" / "check_prototype.py"
CHECK_UI = ROOT / "ui-designer" / "scripts" / "check_ui.py"
CHECK_DATABASE = ROOT / "database-designer" / "scripts" / "check_database.py"
CHECK_ARCHITECTURE = ROOT / "architecture-designer" / "scripts" / "check_architecture.py"
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
- US-1：作为 演示用户，我希望 整条流水线一次跑通，以便 交付验收。

## 4. 功能需求清单
| 编号 | 功能 | 优先级 | 描述 |
|---|---|---|---|
| FR-01 | 冒烟演示 | P0 | 生成九棒产物并逐个过门禁 |

## 5. 业务流程
1. 生成 PRD
2. 评审
3. 画原型
4. 做 UI
5. 设计数据库
6. 做架构
7. 前后端编码
8. 测试
9. 安全扫描

异常分支：
- 当门禁非 0 时，产物打回对应棒重做。

## 6. 非功能需求
- 性能：冒烟耗时小于 2 分钟
- 安全：演示代码不含危险模式

## 7. 范围边界
**本期做**：FR-01
**本期不做**：生产级功能

## 8. 验收标准
- FR-01：Given 演示项目，When 走完九棒，Then 九棒门禁全 rc=0。

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
## 跨文档一致性
功能清单、范围边界、验收标准与下游交付口径一致。
"""

PROTO_OK = """# 原型设计文档

## 一、页面清单
| 页面 | 对应 FR | 页面目标 |
|---|---|---|
| 演示页 | FR-01 | 冒烟演示 |

## 二、页面框架
### 演示页
- 结构：标题区/按钮区/结果区
- 交互：点击按钮 -> 调用接口 -> 展示结果

## 三、交互流程
主流程：进入页面 -> 点击 -> 出结果。
异常分支：接口失败 -> 提示错误。
"""

UI_SPEC = """# UI 设计规范

主色：#2563EB
字体：标题 20px / 正文 14px
组件：按钮 默认/悬停/禁用

FR-01 演示页
"""

DB_OK = """# 数据库设计文档

## 一、表清单
| 表名 | 用途 | 对应 FR |
|---|---|---|
| demo | 冒烟演示 | FR-01 |

## 二、表结构
### demo
| 字段 | 类型 | 主键 |
|---|---|---|
| id | INT | 是 |

## 三、关联关系
- 无（单表演示）
"""

ARCH_OK = """# 架构设计文档

## 一、分层架构
| 层 | 职责 |
|---|---|
| 表现层 | 页面渲染 |

## 二、模块划分
| 模块 | 职责 |
|---|---|
| 演示模块 | 冒烟演示 |

## 三、扩展性设计
- 新增功能挂到对应模块，扩展点已预留
"""

SOURCE_README = """# 冒烟演示项目

如何运行：python app.py

## 非功能需求落实
- 性能：冒烟耗时小于 2 分钟（冒烟实测通过）
- 安全：演示代码不含危险模式（代码审查确认）

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

API_OK = """# 系统 API 接口文档

## 接口总览
| 接口 | 方法 | 路径 | 对应 FR |
|---|---|---|---|
| 演示 | POST | /api/demo | FR-01 |

## 接口明细
### POST /api/demo
- 请求参数：none
- 返回结构：code, message
- 错误码：50001 内部错误
"""

QA_OK = """# 测试报告

结论：通过

## bug 清单
- 所有用例通过，无遗留问题
- 回归通过

## 非功能与风险预案核对
- 性能：冒烟耗时小于 2 分钟，实测通过
- 安全：演示代码不含危险模式，审查通过
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
        # 1) 生成九棒产物
        p_prd = write(ws / "01-prd.md", PRD_OK)
        p_rev = write(ws / "02-requirement-review.md", REVIEW_OK)
        p_proto = write(ws / "03-prototype-design.md", PROTO_OK)
        ui = ws / "04-ui-design"
        ui.mkdir()
        (ui / "演示页.png").write_bytes(b"fake")
        write(ui / "design-spec.md", UI_SPEC)
        p_db = write(ws / "05-database-design.md", DB_OK)
        p_arch = write(ws / "06-architecture-design.md", ARCH_OK)
        src = ws / "07-source"
        src.mkdir()
        write(src / "README.md", SOURCE_README)
        write(src / "app.py", SOURCE_APP_PY)
        write(src / "utils.js", SOURCE_UTILS_JS)
        p_api = write(ws / "07-api-docs.md", API_OK)
        p_qa = write(ws / "08-qa-test-report.md", QA_OK)
        p_sec = write(ws / "09-security-pentest-report.md", SECURITY_OK)

        # 2) 按 orchestrator 顺序跑九棒门禁
        steps = [
            ("棒1 PM check_prd", CHECK_PRD, [p_prd], 0),
            ("棒2 RR check_review", CHECK_REVIEW, [p_rev], 0),
            ("棒3 PD check_prototype", CHECK_PROTOTYPE, [p_proto], 0),
            ("棒4 UI check_ui", CHECK_UI, [str(ui)], 0),
            ("棒5 DB check_database", CHECK_DATABASE, [p_db], 0),
            ("棒6 AR check_architecture", CHECK_ARCHITECTURE, [p_arch], 0),
            ("棒7 SD check_source", CHECK_SOURCE, [str(src)], 0),
            ("棒8 QA check_qa", CHECK_QA, [p_qa], 0),
            ("棒9 SP scan_security", SCAN_SECURITY, [str(src)], 0),
        ]
        for name, script, args, want in steps:
            rc = run(script, *args)
            ok = rc == want
            print(f"  [{'PASS' if ok else 'FAIL'}] {name}: rc={rc} (期望 {want})")
            if not ok:
                fails.append(name)

        # 3) 打回->修复->再通过 路由（PRD 缺一节 -> 补回）
        broken = PRD_OK.replace("## 10. 里程碑\n- 阶段1：冒烟通过，1 小时\n", "")
        write(ws / "01-prd.md", broken)
        rc_bad = run(CHECK_PRD, p_prd)
        ok_bad = rc_bad == 1
        print(f"  [{'PASS' if ok_bad else 'FAIL'}] 打回路由: 缺里程碑 check_prd rc={rc_bad} (期望 1)")
        if not ok_bad:
            fails.append("打回路由-改坏PRD样本")

        write(ws / "01-prd.md", PRD_OK)
        rc_good = run(CHECK_PRD, p_prd)
        ok_good = rc_good == 0
        print(f"  [{'PASS' if ok_good else 'FAIL'}] 修复路由: 写回完整版 check_prd rc={rc_good} (期望 0)")
        if not ok_good:
            fails.append("修复路由-完整PRD样本")

        # 4) 设计文档打回->修复 路由（原型缺 FR 引用 -> 补回）
        broken_proto = PROTO_OK.replace("| 演示页 | FR-01 | 冒烟演示 |", "| 演示页 | 冒烟演示 |")
        write(ws / "03-prototype-design.md", broken_proto)
        rc_bad2 = run(CHECK_PROTOTYPE, p_proto)
        ok_bad2 = rc_bad2 == 1
        print(f"  [{'PASS' if ok_bad2 else 'FAIL'}] 设计打回路由: 原型缺FR引用 check_prototype rc={rc_bad2} (期望 1)")
        if not ok_bad2:
            fails.append("打回路由-改坏原型样本")

        write(ws / "03-prototype-design.md", PROTO_OK)
        rc_good2 = run(CHECK_PROTOTYPE, p_proto)
        ok_good2 = rc_good2 == 0
        print(f"  [{'PASS' if ok_good2 else 'FAIL'}] 设计修复路由: 写回完整原型 check_prototype rc={rc_good2} (期望 0)")
        if not ok_good2:
            fails.append("修复路由-完整原型样本")

    print("-" * 64)
    if fails:
        print(f"结果: 失败 {len(fails)} 项 -> {fails}，退出码 1")
        return 1
    print("结果: 冒烟通过（九棒门禁链 + 打回/修复路由均符合契约），退出码 0")
    return 0


if __name__ == "__main__":
    sys.exit(main())
