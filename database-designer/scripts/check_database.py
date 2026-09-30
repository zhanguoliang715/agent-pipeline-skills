#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""数据库设计文档检查（Database Designer 输出前门禁）。

用法：python scripts/check_database.py 05-database-design.md
退出码：0=通过 1=缺表清单/字段/关联关系 2=有占位残留（口径同 check_prd）
      3=文件不存在  缺参=2
"""
import re
import sys
from pathlib import Path

PLACEHOLDER = re.compile(r"\[[^\]]{2,}\]|【[^】]{2,}】|<(?!(?:https?|mailto):)[^>\n]{2,}>")


def main():
    if len(sys.argv) < 2:
        print("用法: check_database.py <05-database-design.md>", file=sys.stderr)
        sys.exit(2)
    p = Path(sys.argv[1])
    if not p.is_file():
        print(f"错误: 文件不存在: {p}", file=sys.stderr)
        sys.exit(3)
    text = p.read_text(encoding="utf-8")

    problems = []
    if not re.search(r"表清单|表名", text):
        problems.append("缺表清单（表名/用途/对应FR）")
    if not re.search(r"字段|列", text):
        problems.append("缺字段定义（字段名/类型/主键等）")
    if not re.search(r"关联|外键", text):
        problems.append("缺关联关系（外键/一对多/多对多）")

    print(f"数据库设计文档检查: {p}")
    for pr in problems:
        print(f"  FAIL {pr}")
    if PLACEHOLDER.search(text):
        print("  WARN 仍有占位符未替换")
        sys.exit(2)
    if problems:
        sys.exit(1)
    print("  通过: 表清单、字段定义、关联关系齐全，无占位残留")
    sys.exit(0)


if __name__ == "__main__":
    main()
