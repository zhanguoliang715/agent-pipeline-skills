#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""原型设计文档检查（Prototype Designer 输出前门禁）。

用法：python scripts/check_prototype.py 03-prototype-design.md
退出码：0=通过 1=缺页面清单/未引用FR 2=有占位残留（口径同 check_prd）
      3=文件不存在  缺参=2
"""
import re
import sys
from pathlib import Path

PLACEHOLDER = re.compile(r"\[[^\]]{2,}\]|【[^】]{2,}】|<(?!(?:https?|mailto):)[^>\n]{2,}>")


def main():
    if len(sys.argv) < 2:
        print("用法: check_prototype.py <03-prototype-design.md>", file=sys.stderr)
        sys.exit(2)
    p = Path(sys.argv[1])
    if not p.is_file():
        print(f"错误: 文件不存在: {p}", file=sys.stderr)
        sys.exit(3)
    text = p.read_text(encoding="utf-8")

    problems = []
    if "页面" not in text:
        problems.append("缺页面清单/页面框架")
    if not re.search(r"FR-\d+", text):
        problems.append("未引用 FR 编号（页面清单必须与功能需求清单对应）")

    print(f"原型设计文档检查: {p}")
    for pr in problems:
        print(f"  FAIL {pr}")
    if PLACEHOLDER.search(text):
        print("  WARN 仍有占位符未替换（[ ] / 【 】 / 非链接 < >）")
        sys.exit(2)
    if problems:
        sys.exit(1)
    print("  通过: 页面清单齐全、已引用 FR、无占位残留")
    sys.exit(0)


if __name__ == "__main__":
    main()
