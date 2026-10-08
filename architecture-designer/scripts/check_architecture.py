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
        print(f"  WARN 仍有占位符未替换：{placeholder_desc(text)}")
        sys.exit(2)
    if problems:
        sys.exit(1)
    print("  通过: 分层架构、模块划分、扩展性设计齐全，无占位残留")
    sys.exit(0)


if __name__ == "__main__":
    main()
