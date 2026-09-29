#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""流水线脚本回归测试（行为契约，机器实测）。

用法（仓库根）：
    python scripts/regression_test.py

退出码：0=全过  1=有失败

覆盖：
  1. 四棒 check 脚本退出码契约（0 通过 / 1 缺内容 / 2 业务警告 / 3 路径不存在 / 缺参 2）
  2. 安全棒 scan_danger.py（标准库正则层）：正样本应过、反样本应拦、断言退出码
  3. 安全棒 scan_security.py wrapper：bandit 无关断言（纯 JS 目录）
  4. 可选（本机已装 bandit==1.9.4 时）：bandit 集成路径 MED=4 / HIGH=1 / 空 .py=5

任何 FAIL = 脚本行为漂移。改脚本逻辑后必跑本测试。
validate_pipeline.py 只查结构一致性，查不了行为——行为回归靠本文件。
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
SCAN_DANGER = ROOT / "security-pentester" / "scripts" / "scan_danger.py"
SCAN_SECURITY = ROOT / "security-pentester" / "scripts" / "scan_security.py"

PRD_TEN = """# 示例 PRD

## 1. 背景与目标
- 一句话概括：我们要为新用户在首次登录场景下解决流失问题，成功后提升留存。

## 2. 目标用户与场景
- 目标用户：新用户
- 核心使用场景：首次登录

## 3. 用户故事
- US-1：作为新用户，我希望快速上手，以便继续使用。

## 4. 功能需求清单
| 编号 | 功能 | 优先级 | 描述 |
|---|---|---|---|
| FR-01 | 引导页 | P0 | 展示核心功能 |

## 5. 业务流程
1. 打开应用
2. 看到引导
3. 开始使用

异常分支：
- 当网络断开时，系统应提示重试。

## 6. 非功能需求
- 性能：列表加载 < 2s
- 安全：密码不得明文存储

## 7. 范围边界
**本期做**：FR-01
**本期不做**：社交功能

## 8. 验收标准
- FR-01：Given 新用户，When 首次登录，Then 看到引导页。

## 9. 依赖
- 外部依赖：无

## 10. 里程碑
- 阶段1：MVP，1周
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

QA_OK = """# 测试报告

结论：通过

## bug 清单
- 所有用例通过，无遗留问题
- 回归通过
"""

QA_FATAL = """# 测试报告

结论：通过

## bug 清单
- 致命：程序无法启动
"""


def run(script, *args):
    cmd = [sys.executable, str(script), *args]
    p = subprocess.run(cmd, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    return p.returncode


def w(name, path, content):
    Path(path).write_text(content, encoding="utf-8")
    return str(path)


def check_qa_noarg():
    return run(CHECK_QA) == 2


TESTS = []


def test(name):
    def deco(fn):
        TESTS.append((name, fn))
        return fn
    return deco


@test("check_prd 通过=0")
def _(tmp):
    f = w("prd_ok.md", tmp / "prd_ok.md", PRD_TEN)
    return run(CHECK_PRD, f) == 0


@test("check_prd 缺章节=1")
def _(tmp):
    f = w("prd_missing.md", tmp / "prd_missing.md", "# 只有标题\n没有章节")
    return run(CHECK_PRD, f) == 1


@test("check_prd 占位残留=2")
def _(tmp):
    f = w("prd_ph.md", tmp / "prd_ph.md", PRD_TEN.replace("新用户", "[待补充]"))
    return run(CHECK_PRD, f) == 2


@test("check_prd 全角占位=2")
def _(tmp):
    f = w("prd_ph_full.md", tmp / "prd_ph_full.md", PRD_TEN.replace("新用户", "【待确认】"))
    return run(CHECK_PRD, f) == 2


@test("check_prd 文件不存在=3")
def _(tmp):
    return run(CHECK_PRD, str(tmp / "nope.md")) == 3


@test("check_prd 缺参=2")
def _(tmp):
    return run(CHECK_PRD) == 2


@test("check_review 通过=0")
def _(tmp):
    f = w("review_ok.md", tmp / "review_ok.md", REVIEW_OK)
    return run(CHECK_REVIEW, f) == 0


@test("check_review 缺结论=1")
def _(tmp):
    f = w("review_bad.md", tmp / "review_bad.md", "# 评审报告\n没有结论")
    return run(CHECK_REVIEW, f) == 1


@test("check_review 文件不存在=3")
def _(tmp):
    return run(CHECK_REVIEW, str(tmp / "nope.md")) == 3


@test("check_review 占位残留=2")
def _(tmp):
    f = w("review_ph.md", tmp / "review_ph.md",
          "# 评审报告\n结论：YES\n## 完整性\n[待确认]\n## 可执行性\n可执行。\n"
          "## 边界\n清晰。\n## 验收\n可验收。\n## 技术可行\n可行。\n## 合规\n合规。\n")
    return run(CHECK_REVIEW, f) == 2


@test("check_review 全角占位=2")
def _(tmp):
    f = w("review_ph_full.md", tmp / "review_ph_full.md",
          "# 评审报告\n结论：YES\n## 完整性\n【待确认】\n## 可执行性\n可执行。\n"
          "## 边界\n清晰。\n## 验收\n可验收。\n## 技术可行\n可行。\n## 合规\n合规。\n")
    return run(CHECK_REVIEW, f) == 2


@test("check_review 缺参=2")
def _(tmp):
    return run(CHECK_REVIEW) == 2


@test("check_source 通过=0")
def _(tmp):
    d = tmp / "src_ok"
    d.mkdir()
    w("README.md", d / "README.md", "# 项目\n运行：python main.py")
    return run(CHECK_SOURCE, str(d)) == 0


@test("check_source 缺README=1")
def _(tmp):
    d = tmp / "src_noreadme"
    d.mkdir()
    return run(CHECK_SOURCE, str(d)) == 1


@test("check_source 依赖目录混入=2")
def _(tmp):
    d = tmp / "src_leak"
    d.mkdir()
    w("README.md", d / "README.md", "# 项目\n运行：python main.py")
    (d / "node_modules").mkdir()
    return run(CHECK_SOURCE, str(d)) == 2


@test("check_source 目录不存在=3")
def _(tmp):
    return run(CHECK_SOURCE, str(tmp / "nope")) == 3


@test("check_source 缺参=2")
def _(tmp):
    return run(CHECK_SOURCE) == 2


@test("check_qa 通过=0")
def _(tmp):
    f = w("qa_ok.md", tmp / "qa_ok.md", QA_OK)
    return run(CHECK_QA, f) == 0


@test("check_qa 未修复致命=2")
def _(tmp):
    f = w("qa_fatal.md", tmp / "qa_fatal.md", QA_FATAL)
    return run(CHECK_QA, f) == 2


@test("check_qa 缺结论=1")
def _(tmp):
    f = w("qa_bad.md", tmp / "qa_bad.md", "# 测试报告\n没有结论")
    return run(CHECK_QA, f) == 1


@test("check_qa 文件不存在=3")
def _(tmp):
    return run(CHECK_QA, str(tmp / "nope.md")) == 3


@test("check_qa 缺参=2")
def _(tmp):
    return run(CHECK_QA) == 2


@test("scan_danger 干净JS=0")
def _(tmp):
    d = tmp / "danger_clean"
    d.mkdir()
    w("a.js", d / "a.js", 'console.log("hello");\n')
    return run(SCAN_DANGER, str(d)) == 0


@test("scan_danger 硬编码密钥=1")
def _(tmp):
    d = tmp / "danger_key"
    d.mkdir()
    w("a.js", d / "a.js", 'const api_key = "sk-1234567890abc";\n')
    return run(SCAN_DANGER, str(d)) == 1


@test("scan_danger eval=1")
def _(tmp):
    d = tmp / "danger_eval"
    d.mkdir()
    w("a.py", d / "a.py", 'eval(input("> "))\n')
    return run(SCAN_DANGER, str(d)) == 1


@test("scan_danger SQL拼接=4")
def _(tmp):
    d = tmp / "danger_sql"
    d.mkdir()
    w("a.py", d / "a.py", 'q = "SELECT * FROM users WHERE id=" + uid\n')
    return run(SCAN_DANGER, str(d)) == 4


@test("scan_danger 目录不存在=3")
def _(tmp):
    return run(SCAN_DANGER, str(tmp / "nope")) == 3


@test("scan_danger 缺参=2")
def _(tmp):
    return run(SCAN_DANGER) == 2


@test("scan_security 干净JS=0（bandit无关）")
def _(tmp):
    d = tmp / "sec_clean"
    d.mkdir()
    w("a.js", d / "a.js", 'console.log("hello");\n')
    return run(SCAN_SECURITY, str(d)) == 0


@test("scan_security 密钥JS=1（bandit无关）")
def _(tmp):
    d = tmp / "sec_key"
    d.mkdir()
    w("a.js", d / "a.js", 'const api_key = "sk-1234567890abc";\n')
    return run(SCAN_SECURITY, str(d)) == 1


@test("scan_security eval=1（正则保底，bandit装不装都过）")
def _(tmp):
    d = tmp / "sec_eval"
    d.mkdir()
    w("a.py", d / "a.py", 'eval(input("> "))\n')
    return run(SCAN_SECURITY, str(d)) == 1


@test("scan_security SQL拼接=4（正则保底，bandit装不装都过）")
def _(tmp):
    d = tmp / "sec_sql"
    d.mkdir()
    w("a.py", d / "a.py", 'q = "SELECT * FROM users WHERE id=" + uid\n')
    return run(SCAN_SECURITY, str(d)) == 4


@test("scan_security 目录不存在=3")
def _(tmp):
    return run(SCAN_SECURITY, str(tmp / "nope")) == 3


@test("scan_security 缺参=2")
def _(tmp):
    return run(SCAN_SECURITY) == 2


@test("scan_security 空.py=5（仅当bandit已装）")
def _(tmp):
    if shutil.which("bandit") is None:
        return True  # bandit 未装：降级路径，跳过该断言
    d = tmp / "sec_empty"
    d.mkdir()
    (d / "a.py").write_text("", encoding="utf-8")
    return run(SCAN_SECURITY, str(d)) == 5


def main():
    if len(sys.argv) != 1:
        print("用法: python scripts/regression_test.py", file=sys.stderr)
        return 2
    if not all(p.exists() for p in (CHECK_PRD, CHECK_REVIEW, CHECK_SOURCE,
                                    CHECK_QA, SCAN_DANGER, SCAN_SECURITY)):
        print(f"错误: 六棒脚本缺失，仓库不完整: {ROOT}", file=sys.stderr)
        return 2

    passed = 0
    failed = []
    skipped = []
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        for name, fn in TESTS:
            try:
                if fn(tmp):
                    passed += 1
                else:
                    failed.append(name)
            except Exception as e:
                failed.append(f"{name} (异常: {e})")

    print("=" * 64)
    print("流水线脚本回归测试")
    print("=" * 64)
    print(f"用例总数: {len(TESTS)}  通过: {passed}  失败: {len(failed)}")
    if skipped:
        print(f"跳过(可选): {skipped}")
    if failed:
        print("\n--- 失败用例 ---")
        for f in failed:
            print("  FAIL ", f)
        print(f"\n结果: 失败 {len(failed)}，退出码 1")
        return 1
    print("\n结果: 全部通过，退出码 0")
    return 0


if __name__ == "__main__":
    sys.exit(main())
