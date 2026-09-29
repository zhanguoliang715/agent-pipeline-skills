#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""代码包交付检查（Software Developer 输出前门禁）。

用法：python scripts/check_source.py 03-source/
退出码：0=通过 1=缺 README/启动命令/非功能落实缺失 2=把依赖目录打进了交付包
      3=目录不存在  缺参=2

非功能落实对照（整套部署时自动生效）：
  脚本自动在 03-source/ 的上一级找 01-prd.md，找到则把 PRD 第 6 节「非功能需求」
  和第 9 节「依赖、约束与风险/依赖」里的条目提取出来，要求 README（或 NFR.md）
  里对每条条目有落实声明（落实说明需先抄 PRD 条目原文开头，再写实现方式）。
  缺一条就 FAIL（退出码 1）——PRD 写了非功能承诺，交付包必须逐条说明怎么落实。
  独立部署（目录上一级没有 01-prd.md）时跳过本对照，只做原有检查。
"""
import re
import sys
from pathlib import Path

LEAK_DIRS = {"node_modules", ".venv", "venv", "__pycache__", "dist", "build", ".git"}

SECTION_6 = re.compile(r"##\s*6\.\s*非功能需求(.*?)(?=##\s*7\.)", re.S)
SECTION_9 = re.compile(r"##\s*9\.\s*依赖[^\n]*?(.*?)(?=##\s*10\.)", re.S)


def normalize(s: str) -> str:
    """全角冒号/空格归一化，锚匹配更稳。"""
    return s.replace("：", ":").replace(" ", "")


def extract_requirements(prd_text: str):
    """从 PRD 提取需要落实的条目：第 6 节全部 + 第 9 节以「风险」开头的行。"""
    items = []
    m6 = SECTION_6.search(prd_text)
    if m6:
        for line in m6.group(1).splitlines():
            line = line.strip()
            if line.startswith("- ") or line.startswith("* "):
                items.append(("非功能", line.lstrip("-* ").strip()))
    m9 = SECTION_9.search(prd_text)
    if m9:
        for line in m9.group(1).splitlines():
            line = line.strip()
            if line.startswith("- ") and line.lstrip("- ").startswith("风险"):
                items.append(("风险", line.lstrip("- ").strip()))
    return items


def anchor(text: str) -> str:
    """去空白后取前 8 字符作为匹配锚。"""
    return normalize(text)[:8]


def main():
    if len(sys.argv) < 2:
        print("用法: check_source.py <03-source/>", file=sys.stderr)
        sys.exit(2)
    root = Path(sys.argv[1])
    if not root.is_dir():
        print(f"错误: 目录不存在: {root}", file=sys.stderr)
        sys.exit(3)

    readme = None
    for name in ("README.md", "README", "readme.md"):
        if (root / name).exists():
            readme = root / name
            break

    leaks = []
    for child in root.iterdir():
        if child.is_dir() and child.name in LEAK_DIRS:
            leaks.append(child.name)

    problems = []
    if not readme:
        problems.append("缺 README.md")
    else:
        rt = readme.read_text(encoding="utf-8")
        if not any(k in rt for k in ("启动", "运行", "python ", "npm ", "go run", "如何")):
            problems.append("README 里没有启动/运行命令")

        # 非功能需求落实对照：自动找 03-source/ 上一级的 01-prd.md
        prd = root.parent / "01-prd.md"
        if prd.is_file():
            items = extract_requirements(prd.read_text(encoding="utf-8"))
            # 落实说明允许写在 README 里，也允许单独 NFR.md（随包携带）
            impl_text = rt
            nfr_file = root / "NFR.md"
            if nfr_file.exists():
                impl_text += "\n" + nfr_file.read_text(encoding="utf-8")
            has_nfr_section = any(k in impl_text for k in ("非功能", "风险预案", "NFR"))
            missing = []
            for kind, item in items:
                if len(normalize(item)) < 8:
                    continue  # 过短的条目（如"外部依赖：无"）不参与强制对照
                if anchor(item) not in normalize(impl_text):
                    missing.append(f"{kind}：{item}")
            if not has_nfr_section:
                problems.append("README 缺「非功能需求落实」小节（应逐条写明 PRD 非功能需求/风险预案的落实方式）")
            elif missing:
                problems.append(f"以下 PRD 非功能/风险条目在 README 没有对应落实声明: {missing[:6]}")

    print(f"代码包检查: {root}")
    for pr in problems:
        print(f"  FAIL {pr}")
    if leaks:
        print(f"  WARN 依赖/构建目录不该进交付包: {leaks}")
    if problems:
        sys.exit(1)
    if leaks:
        sys.exit(2)
    print("  通过: README 有启动命令、无依赖目录混入、非功能落实对照完整")
    sys.exit(0)


if __name__ == "__main__":
    main()
