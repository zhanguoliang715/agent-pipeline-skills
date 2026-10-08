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

_BRACKET = re.compile(r"\[(?!\^)[^\]]{2,}\]|【[^】]{2,}】")
_ANGLE = re.compile(r"<(?!(?:https?|mailto):)[^>\n]{2,}>")


def _strip_legal_angle(text: str) -> str:
    """先移除合法的尖括号结构（自动链接 / HTML 标签 / 泛型），避免误报。

    旧判据直接查裸尖括号，会把 <div>、Map<String, Object>、[^1] 这类合法写法
    判成未替换占位，导致干净产物退 2 交不了稿。
    """
    t = re.sub(r"<(?:https?|mailto):[^>\n]*>", "", text)
    t = re.sub(r"</?[a-zA-Z][\w-]*(?:\s[^<>]*?)?/?>", "", t)
    t = re.sub(r"<[A-Za-z_][\w.]*(?:\s*,\s*[A-Za-z_][\w.\[\]<>\s]*)+\s*>", "", t)
    return t


class _Placeholder:
    """占位检测器：search() 返回命中列表（空列表即无占位，可直接当布尔用）。"""

    def findall(self, text: str):
        hits = []
        for m in _BRACKET.finditer(text):
            hits.append(("括号占位", m.group(0)))
        for m in _ANGLE.finditer(_strip_legal_angle(text)):
            hits.append(("尖括号占位", m.group(0)))
        return hits

    def search(self, text: str):
        return self.findall(text)


PLACEHOLDER = _Placeholder()


def placeholder_desc(text: str) -> str:
    """把命中按类型汇总成可读文案，排错时不用猜是哪种括号。"""
    kinds = {}
    for kind, raw in PLACEHOLDER.findall(text):
        kinds.setdefault(kind, []).append(raw)
    if not kinds:
        return ""
    return "；".join(f"{k} {len(v)} 处：{', '.join(v[:3])}" for k, v in kinds.items())


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
        print(f"  WARN 仍有占位符未替换：{placeholder_desc(text)}")
        sys.exit(2)
    if problems:
        sys.exit(1)
    print("  通过: 表清单、字段定义、关联关系齐全，无占位残留")
    sys.exit(0)


if __name__ == "__main__":
    main()
