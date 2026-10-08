#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""需求评审报告完整性检查（Requirement Reviewer 输出前门禁）。

用法：python scripts/check_review.py 02-requirement-review.md
退出码：0=通过 1=缺结论或七大维度 2=有占位残留（口径同 check_prd）
"""
import re
import sys
from pathlib import Path

DIMENSIONS = ["完整性", "可执行性", "边界", "验收", "技术可行", "合规", "一致性"]
CONCLUSION_LINE = re.compile(r"(?:评审)?结论\s*[:：]\s*(YES|NO|退回)", re.I)
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
        print("用法: check_review.py <02-requirement-review.md>", file=sys.stderr)
        sys.exit(2)
    p = Path(sys.argv[1])
    if not p.is_file():
        print(f"错误: 文件不存在: {p}", file=sys.stderr)
        sys.exit(3)
    text = p.read_text(encoding="utf-8")
    # 旧判据是 YES / NO / 退回 的子串存在性检查：正文提到这三个词就算有结论，
    # 结论为 NO 的报告也会退 0。改为解析规范化结论行。

    problems = []
    warnings = []
    cm = CONCLUSION_LINE.search(text)
    if not cm:
        problems.append("缺规范化结论行（应写『## 评审结论：YES / NO / 退回』，不要只在正文提到这些词）")
    else:
        print(f"  CONCLUSION={cm.group(1).upper()}")
    missing_dim = [d for d in DIMENSIONS if d not in text]
    if missing_dim:
        problems.append(f"七大维度未全覆盖: {missing_dim}")
    if PLACEHOLDER.search(text):
        warnings.append(f"仍有占位符未替换：{placeholder_desc(text)}")

    print(f"评审报告检查: {p}")
    for pr in problems:
        print(f"  FAIL {pr}")
    for w in warnings:
        print(f"  WARN {w}")
    if problems:
        sys.exit(1)
    if warnings:
        sys.exit(2)
    print("  通过: 结论明确、七维度齐全、无占位残留")
    sys.exit(0)


if __name__ == "__main__":
    main()
