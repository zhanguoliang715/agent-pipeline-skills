#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""需求评审报告完整性检查（Requirement Reviewer 输出前门禁）。

用法：python scripts/check_review.py 02-requirement-review.md
退出码：0=通过 1=缺结论或六大维度 2=有占位残留（口径同 check_prd）
"""
import re
import sys
from pathlib import Path

DIMENSIONS = ["完整性", "可执行性", "边界", "验收", "技术可行", "合规"]
CONCLUSIONS = ["YES", "NO", "退回"]
PLACEHOLDER = re.compile(r"\[[^\]]{2,}\]")


def main():
    if len(sys.argv) < 2:
        print("用法: check_review.py <02-requirement-review.md>", file=sys.stderr)
        sys.exit(2)
    p = Path(sys.argv[1])
    if not p.is_file():
        print(f"错误: 文件不存在: {p}", file=sys.stderr)
        sys.exit(3)
    text = p.read_text(encoding="utf-8")
    upper = text.upper()

    problems = []
    warnings = []
    if not any(c in upper for c in CONCLUSIONS):
        problems.append("缺明确结论（YES/NO/退回）")
    missing_dim = [d for d in DIMENSIONS if d not in text]
    if missing_dim:
        problems.append(f"六大维度未全覆盖: {missing_dim}")
    if PLACEHOLDER.search(text):
        warnings.append("仍有方括号占位符 [...] 未替换")

    print(f"评审报告检查: {p}")
    for pr in problems:
        print(f"  FAIL {pr}")
    for w in warnings:
        print(f"  WARN {w}")
    if problems:
        sys.exit(1)
    if warnings:
        sys.exit(2)
    print("  通过: 结论明确、六维度齐全、无占位残留")
    sys.exit(0)


if __name__ == "__main__":
    main()
