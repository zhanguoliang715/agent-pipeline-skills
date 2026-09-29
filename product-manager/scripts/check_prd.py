#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PRD 完整性检查（Product Manager 输出前门禁）。

用法：python scripts/check_prd.py 01-prd.md
退出码：0=通过 1=缺必含章节 2=有占位残留/待确认未填
"""
import re
import sys
from pathlib import Path

REQUIRED_SECTIONS = [
    "背景与目标", "目标用户与场景", "用户故事", "功能需求清单",
    "业务流程", "非功能需求", "范围边界", "验收标准",
    "依赖", "里程碑",
]
PLACEHOLDER = re.compile(r"\[[^\]]{2,}\]|【[^】]{2,}】")
TODO = re.compile(r"待补充|TODO|待写|TBD", re.I)


def main():
    if len(sys.argv) < 2:
        print("用法: check_prd.py <01-prd.md>", file=sys.stderr)
        sys.exit(2)
    p = Path(sys.argv[1])
    if not p.is_file():
        print(f"错误: 文件不存在: {p}", file=sys.stderr)
        sys.exit(3)
    text = p.read_text(encoding="utf-8")

    missing = [s for s in REQUIRED_SECTIONS if s not in text]
    warnings = []
    if PLACEHOLDER.search(text):
        warnings.append("仍有方括号占位符 [...] 未替换")
    if TODO.search(text):
        warnings.append("仍有 TODO/待补充/TBD 未填")

    print(f"PRD 检查: {p}")
    if missing:
        print(f"  FAIL 缺章节: {missing}")
    if warnings:
        for w in warnings:
            print(f"  WARN {w}")
    if missing:
        sys.exit(1)
    if warnings:
        sys.exit(2)
    print("  通过: 十节齐全，无占位残留")
    sys.exit(0)


if __name__ == "__main__":
    main()
