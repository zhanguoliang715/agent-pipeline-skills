#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""架构设计文档检查（Architecture Designer 输出前门禁）。

用法：python scripts/check_architecture.py 06-architecture-design.md
退出码：0=通过 1=缺分层/模块/扩展性 2=有占位残留（口径同 check_prd）
      3=文件不存在  缺参=2
"""
import re
import sys
from pathlib import Path

PLACEHOLDER = re.compile(r"\[[^\]]{2,}\]|【[^】]{2,}】|<(?!(?:https?|mailto):)[^>\n]{2,}>")


def main():
    if len(sys.argv) < 2:
        print("用法: check_architecture.py <06-architecture-design.md>", file=sys.stderr)
        sys.exit(2)
    p = Path(sys.argv[1])
    if not p.is_file():
        print(f"错误: 文件不存在: {p}", file=sys.stderr)
        sys.exit(3)
    text = p.read_text(encoding="utf-8")

    problems = []
    if not re.search(r"分层|架构", text):
        problems.append("缺分层架构（层/职责/依赖方向）")
    if "模块" not in text:
        problems.append("缺模块划分（模块/职责/对外接口）")
    if not re.search(r"扩展|演进", text):
        problems.append("缺扩展性设计（新功能怎么加/数据模型怎么演进）")

    print(f"架构设计文档检查: {p}")
    for pr in problems:
        print(f"  FAIL {pr}")
    if PLACEHOLDER.search(text):
        print("  WARN 仍有占位符未替换")
        sys.exit(2)
    if problems:
        sys.exit(1)
    print("  通过: 分层架构、模块划分、扩展性设计齐全，无占位残留")
    sys.exit(0)


if __name__ == "__main__":
    main()
