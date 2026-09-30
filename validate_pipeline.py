#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""流水线一致性校验器。

放在仓库根目录，直接 `python validate_pipeline.py` 跑。
不依赖第三方包，只用标准库。校验项：
  1. 各棒 SKILL.md 都存在、frontmatter 白名单合规、有 version、有第 0 步门禁
  2. metadata.references 声明的每个文件真实存在、本文件版本与声明一致、含修订历史
  3. SKILL.md 正文里 markdown 链接到的 references 不悬空
  4. 各棒 version 不一致只警告（独立发版，改谁升谁），不 FAIL
  5. 各棒输出契约声明了自己的固定产物名（01-09）
  6. pipeline-orchestrator 作为总调度，查 SKILL.md/frontmatter/version/第 0 步门禁
有任何 FAIL 退出码为 1。
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SKILLS = [
    "product-manager",
    "requirement-reviewer",
    "prototype-designer",
    "ui-designer",
    "database-designer",
    "architecture-designer",
    "software-developer",
    "qa-tester",
    "security-pentester",
    "pipeline-orchestrator",
]
ALLOWED_FM_KEYS = {"name", "description", "license", "allowed-tools", "metadata"}
NAMING = {
    "product-manager": "01-prd.md",
    "requirement-reviewer": "02-requirement-review.md",
    "prototype-designer": "03-prototype-design.md",
    "ui-designer": "04-ui-design",
    "database-designer": "05-database-design.md",
    "architecture-designer": "06-architecture-design.md",
    "software-developer": "07-source",
    "qa-tester": "08-qa-test-report.md",
    "security-pentester": "09-security-pentest-report.md",
}

errors = []
warnings = []
versions = {}


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


for skill in SKILLS:
    d = ROOT / skill
    sf = d / "SKILL.md"
    if not sf.exists():
        errors.append(f"[{skill}] SKILL.md 不存在")
        continue
    text = read(sf)

    # frontmatter 顶层键（只看顶格/两空格缩进的 key，不进 metadata 嵌套）
    fm_keys = re.findall(r"^([a-zA-Z][\w-]*):", text.split("---", 2)[1], re.M)
    for k in fm_keys:
        if k not in ALLOWED_FM_KEYS:
            errors.append(f"[{skill}] frontmatter 非法顶层字段: {k}")

    mv = re.search(r"(?m)^\s*version:\s*([0-9.]+)", text)
    if mv:
        versions[skill] = mv.group(1)
    else:
        errors.append(f"[{skill}] 缺 metadata.version")

    if "第 0 步" not in text:
        errors.append(f"[{skill}] 缺第 0 步开工门禁")

    # metadata.references 块：形如 "    xxx.md: 1.0.1"
    # 总调度可显式声明 "references: 无"（无独立知识库），豁免检查
    declared = dict(
        re.findall(r"^\s{4}([a-z0-9.-]+\.md):\s*([0-9.]+)\s*$", text, re.M)
    )
    declares_none = "references: 无" in text
    if not declared and not declares_none:
        warnings.append(f"[{skill}] metadata 无 references 声明块（总调度可用 'references: 无' 豁免）")
    for fname, declared_ver in declared.items():
        rp = d / "references" / fname
        if not rp.exists():
            errors.append(f"[{skill}] 悬空声明 references/{fname}")
            continue
        rt = read(rp)
        mv2 = re.search(r"本文件版本：([0-9.]+)", rt)
        if not mv2:
            errors.append(f"[{skill}] references/{fname} 缺'本文件版本'")
        elif mv2.group(1) != declared_ver:
            errors.append(
                f"[{skill}] references/{fname} 版本 {mv2.group(1)} != SKILL 声明 {declared_ver}"
            )
        if "修订历史" not in rt:
            errors.append(f"[{skill}] references/{fname} 缺'## 修订历史'")

    # 正文 markdown 链接到 references/
    for link in re.findall(r"\(references/([a-z0-9.-]+\.md)\)", text):
        if not (d / "references" / link).exists():
            errors.append(f"[{skill}] 正文链接悬空 references/{link}")

    # 正文命令里引用的 scripts/ 脚本必须存在
    # 支持两种：本棒 scripts/xxx.py，或跨棒 <skill>/scripts/xxx.py
    for m in re.finditer(r"(?:([a-z-]+)/)?scripts/([a-z0-9_.-]+\.py)", text):
        owner, script = m.group(1), m.group(2)
        if owner:
            target = ROOT / owner / "scripts" / script
        else:
            target = d / "scripts" / script
        if not target.exists():
            errors.append(f"[{skill}] 引用了不存在的 scripts/{owner + '/' if owner else ''}{script}")

    # 固定产物名（orchestrator 无自己的产物，跳过）
    fname = NAMING.get(skill)
    if fname and fname not in text:
        errors.append(f"[{skill}] 输出契约未声明固定产物名 {fname}")


# 各棒版本：不强制一致（各棒独立发版，改谁升谁），只警告提醒
if len(set(versions.values())) > 1:
    warnings.append(f"各棒 version 不一致（独立发版，仅提醒）: {versions}")

print("=" * 64)
print("流水线一致性校验")
print("=" * 64)
print(f"根目录 : {ROOT}")
print(f"版本   : {versions}")
print()
if warnings:
    print(f"--- 警告 {len(warnings)} ---")
    for w in warnings:
        print("  WARN ", w)
    print()
if errors:
    print(f"--- 失败 {len(errors)} ---")
    for e in errors:
        print("  FAIL ", e)
    sys.exit(1)
else:
    print("全部通过：references 无悬空且版本对齐 / 门禁在 / 命名齐 / scripts 不悬空。")
