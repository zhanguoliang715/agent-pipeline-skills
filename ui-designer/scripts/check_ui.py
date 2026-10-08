#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UI 设计目录检查（UI Designer 输出前门禁）。

用法：python scripts/check_ui.py 04-ui-design/
退出码：0=通过 1=缺设计图/缺 design-spec.md/规范缺内容 2=有占位残留（口径同 check_prd）
      3=目录不存在  缺参=2
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
IMG_EXTS = {".png", ".jpg", ".jpeg", ".svg", ".webp", ".gif"}


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    text_only = "--text-only" in sys.argv
    if not args:
        print("用法: check_ui.py <04-ui-design/> [--text-only]", file=sys.stderr)
        sys.exit(2)
    d = Path(args[0])
    if not d.is_dir():
        print(f"错误: 目录不存在: {d}", file=sys.stderr)
        sys.exit(3)

    problems = []
    imgs = [f for f in d.iterdir() if f.is_file() and f.suffix.lower() in IMG_EXTS]
    if not imgs and not text_only:
        problems.append("目录里没有任何设计图（png/jpg/svg/webp）；宿主无生图能力时用 --text-only 走纯规范模式")
    spec = d / "design-spec.md"
    if not spec.is_file():
        problems.append("缺 design-spec.md 设计规范文档")
    else:
        st = spec.read_text(encoding="utf-8")
        if "色" not in st or "字体" not in st:
            problems.append("design-spec.md 缺色值表或字体层级")
        if not re.search(r"FR-\d+", st):
            problems.append("design-spec.md 未引用 FR 编号（页面与功能需求对应）")
        # 纯规范模式必须有降级原因：该开关是用来救场的，不是用来跳过设计图的
        if text_only and not re.search(r"纯规范模式|无生图能力|降级原因", st):
            problems.append("纯规范模式（--text-only）必须在 design-spec.md 写明降级原因：为何没有设计图")

    print(f"UI 设计目录检查: {d}")
    for pr in problems:
        print(f"  FAIL {pr}")
    if spec.is_file() and PLACEHOLDER.search(spec.read_text(encoding="utf-8")):
        print(f"  WARN design-spec.md 仍有占位符未替换：{placeholder_desc(spec.read_text(encoding="utf-8"))}")
        sys.exit(2)
    if problems:
        sys.exit(1)
    if text_only:
        print("  通过（纯规范模式）: design-spec.md 齐全、无占位残留，未校验设计图")
    else:
        print(f"  通过: {len(imgs)} 张设计图、design-spec.md 齐全、无占位残留")
    sys.exit(0)


if __name__ == "__main__":
    main()
