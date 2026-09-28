#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""代码包交付检查（Software Developer 输出前门禁）。

用法：python scripts/check_source.py 03-source/
退出码：0=通过 1=缺 README 或启动命令 2=把依赖目录打进了交付包
"""
import sys
from pathlib import Path

LEAK_DIRS = {"node_modules", ".venv", "venv", "__pycache__", "dist", "build", ".git"}


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

    print(f"代码包检查: {root}")
    for pr in problems:
        print(f"  FAIL {pr}")
    if leaks:
        print(f"  WARN 依赖/构建目录不该进交付包: {leaks}")
    if problems:
        sys.exit(1)
    if leaks:
        sys.exit(2)
    print("  通过: README 有启动命令、无依赖目录混入")
    sys.exit(0)


if __name__ == "__main__":
    main()
