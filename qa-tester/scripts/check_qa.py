#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""功能测试报告检查（QA Tester 输出前门禁）。

用法：python scripts/check_qa.py 08-qa-test-report.md
退出码：0=通过 1=缺结论/bug 分级表/非功能与风险预案核对 2=仍有未修复致命/严重 bug
"""
import re
import sys
from pathlib import Path

CONCLUSIONS = ["通过", "打回", "不通过", "FAIL", "PASS"]


def main():
    if len(sys.argv) < 2:
        print("用法: check_qa.py <08-qa-test-report.md>", file=sys.stderr)
        sys.exit(2)
    p = Path(sys.argv[1])
    if not p.is_file():
        print(f"错误: 文件不存在: {p}", file=sys.stderr)
        sys.exit(3)
    text = p.read_text(encoding="utf-8")

    problems = []
    if not any(c in text for c in CONCLUSIONS):
        problems.append("缺测试结论（通过/打回/不通过）")
    if not re.search(r"bug|缺陷|问题", text, re.I):
        problems.append("没有 bug/缺陷清单段落")
    if not re.search(r"非功能|风险预案", text) or "核对" not in text:
        problems.append("缺「非功能与风险预案核对」段落（应逐条列出 PRD 非功能需求/风险预案的验证方式与结果）")

    print(f"测试报告检查: {p}")
    for pr in problems:
        print(f"  FAIL {pr}")

    # 未修复致命/严重 bug：只在 bug 清单行里判，避免表头与说明文字误伤。
    # 旧判据用字符类 [致命严重]，会把"严重程度：一般"这类表头也算成未修复项。
    LEVEL = re.compile(r"(致命|严重)")
    FIXED = re.compile(r"已修复|已回归|已关闭|已验证")
    BUGROW = re.compile(r"BUG-\d+|未修复|待修复|修复中|未回归")
    # 「致命：程序无法启动」这类无编号写法也要算；"严重程度：一般"因冒号位置不同被排除
    GRADE_COLON = re.compile(r"(?:致命|严重)\s*[:：]\s*\S{4,}")
    unresolved = []
    for i, line in enumerate(text.splitlines(), 1):
        s = line.strip()
        if not LEVEL.search(s) or FIXED.search(s):
            continue
        if not (BUGROW.search(s) or GRADE_COLON.search(s)):
            continue
        unresolved.append(f"L{i}: {s[:60]}")
    if unresolved:
        print(f"  WARN 可能仍有未修复致命/严重项: {len(unresolved)} 处（按 bug 清单行判定）")
        for u in unresolved[:5]:
            print(f"    - {u}")

    if problems:
        sys.exit(1)
    if unresolved:
        sys.exit(2)
    print("  通过: 结论明确、有 bug 清单、无未修复致命项、非功能与风险预案已核对")
    sys.exit(0)


if __name__ == "__main__":
    main()
