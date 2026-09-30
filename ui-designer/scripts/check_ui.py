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

PLACEHOLDER = re.compile(r"\[[^\]]{2,}\]|【[^】]{2,}】|<(?!(?:https?|mailto):)[^>\n]{2,}>")
IMG_EXTS = {".png", ".jpg", ".jpeg", ".svg", ".webp", ".gif"}


def main():
    if len(sys.argv) < 2:
        print("用法: check_ui.py <04-ui-design/>", file=sys.stderr)
        sys.exit(2)
    d = Path(sys.argv[1])
    if not d.is_dir():
        print(f"错误: 目录不存在: {d}", file=sys.stderr)
        sys.exit(3)

    problems = []
    imgs = [f for f in d.iterdir() if f.is_file() and f.suffix.lower() in IMG_EXTS]
    if not imgs:
        problems.append("目录里没有任何设计图（png/jpg/svg/webp）")
    spec = d / "design-spec.md"
    if not spec.is_file():
        problems.append("缺 design-spec.md 设计规范文档")
    else:
        st = spec.read_text(encoding="utf-8")
        if "色" not in st or "字体" not in st:
            problems.append("design-spec.md 缺色值表或字体层级")
        if not re.search(r"FR-\d+", st):
            problems.append("design-spec.md 未引用 FR 编号（页面与功能需求对应）")

    print(f"UI 设计目录检查: {d}")
    for pr in problems:
        print(f"  FAIL {pr}")
    if spec.is_file() and PLACEHOLDER.search(spec.read_text(encoding="utf-8")):
        print("  WARN design-spec.md 仍有占位符未替换")
        sys.exit(2)
    if problems:
        sys.exit(1)
    print(f"  通过: {len(imgs)} 张设计图、design-spec.md 齐全、无占位残留")
    sys.exit(0)


if __name__ == "__main__":
    main()
