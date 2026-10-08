#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""代码包交付检查（Software Developer 输出前门禁）。

用法：python scripts/check_source.py 07-source/
退出码：0=通过 1=缺 README/启动命令/非功能落实缺失/API 接口文档缺失或无接口条目
      2=把依赖目录打进了交付包  3=目录不存在  缺参=2

API 接口文档（07-api-docs.md，前后端对接契约）：
  脚本自动在 07-source/ 的上一级找 07-api-docs.md，要求存在、含"接口"条目、无占位残留。
  缺文件/无接口条目/含占位都 FAIL（退出码 1）——系统 API 接口文档是前后端分离模式的必交产物。

非功能落实对照（整套部署时自动生效）：
  脚本自动在 07-source/ 的上一级找 01-prd.md，找到则把 PRD 第 6 节「非功能需求」
  和第 9 节「依赖、约束与风险/依赖」里的条目提取出来，要求 README（或 NFR.md）
  里对每条条目有落实声明（落实说明需先抄 PRD 条目原文开头，再写实现方式）。
  缺一条就 FAIL（退出码 1）——PRD 写了非功能承诺，交付包必须逐条说明怎么落实。
  独立部署（目录上一级没有 01-prd.md）时跳过本对照，只做原有检查。
"""
import re
import sys
from pathlib import Path

LEAK_DIRS = {"node_modules", ".venv", "venv", "__pycache__", "dist", "build", ".git"}
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
    """去空白后取前 8 字符作为匹配锚（严格照抄时的快速通道）。"""
    return normalize(text)[:8]


def matched(item: str, impl: str) -> bool:
    """非功能 / 风险条目的落实判定，三级降级：

    1) 条目带 NFR-xx / RISK-xx 编号，且落实文本中出现该编号（最稳，推荐）；
    2) 条目前 8 字符（去空白、全角冒号归一）出现在落实文本中（照抄场景）；
    3) 字符 2-gram 覆盖率 >= 40%（中文无空格，分词不可靠，按字粒度比对）。

    只做第 2 级会把语义正确、措辞不同的转述判为缺失（退 1），逼出来的是
    措辞对齐而不是质量提升，故补第 3 级。第 3 级会先剥掉"性能:"这类分类词
    前缀，避免分类词写法不同拖低覆盖率。
    """
    ni, ni2 = normalize(item), normalize(impl)

    # 1) 编号锚定
    m = re.match(r"(?:NFR|RISK)-\d+", ni)
    if m and m.group(0) in ni2:
        return True

    # 2) 前 8 字符锚（严格照抄）
    if anchor(item) in ni2:
        return True

    # 3) 字符 2-gram 覆盖率
    body = re.sub(r"^[^:：]{1,6}[:：]", "", ni) or ni
    grams = [body[i:i + 2] for i in range(len(body) - 1)]
    if not grams:
        return True
    hit = sum(1 for g in grams if g in ni2)
    return hit / len(grams) >= 0.4


def main():
    if len(sys.argv) < 2:
        print("用法: check_source.py <07-source/>", file=sys.stderr)
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

        # 非功能需求落实对照：自动找 07-source/ 上一级的 01-prd.md
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
                if not matched(item, impl_text):
                    missing.append(f"{kind}：{item}")
            if not has_nfr_section:
                problems.append("README 缺「非功能需求落实」小节（应逐条写明 PRD 非功能需求/风险预案的落实方式）")
            elif missing:
                problems.append(f"以下 PRD 非功能/风险条目在 README 没有对应落实声明: {missing[:6]}")

    # API 接口文档检查：自动找上一级 07-api-docs.md（前后端分离必交产物）
    api = root.parent / "07-api-docs.md"
    if not api.is_file():
        problems.append("缺 07-api-docs.md（系统 API 接口文档，前后端对接契约）")
    else:
        at = api.read_text(encoding="utf-8")
        if "接口" not in at:
            problems.append("07-api-docs.md 里没有接口条目（接口总览/接口明细）")
        elif PLACEHOLDER.search(at):
            problems.append(f"07-api-docs.md 仍有占位符未替换：{placeholder_desc(at)}")

    print(f"代码包检查: {root}")
    for pr in problems:
        print(f"  FAIL {pr}")
    if leaks:
        print(f"  WARN 依赖/构建目录不该进交付包: {leaks}")
    if problems:
        sys.exit(1)
    if leaks:
        sys.exit(2)
    print("  通过: README 有启动命令、无依赖目录混入、非功能落实对照完整、API 接口文档齐全")
    sys.exit(0)


if __name__ == "__main__":
    main()
