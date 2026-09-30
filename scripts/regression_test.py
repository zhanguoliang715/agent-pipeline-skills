#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""流水线脚本回归测试（行为契约，机器实测）。

用法（仓库根）：
    python scripts/regression_test.py

退出码：0=全过  1=有失败

覆盖：
  1. 四棒 check 脚本退出码契约（0 通过 / 1 缺内容 / 2 业务警告 / 3 路径不存在 / 缺参 2）
  2. 安全棒 scan_danger.py（标准库正则层）：正样本应过、反样本应拦、断言退出码
  3. 安全棒 scan_security.py wrapper：bandit 无关断言（纯 JS 目录）
  4. 可选（本机已装 bandit==1.9.4 时）：bandit 集成路径 MED=4 / HIGH=1 / 空 .py=5

任何 FAIL = 脚本行为漂移。改脚本逻辑后必跑本测试。
validate_pipeline.py 只查结构一致性，查不了行为——行为回归靠本文件。
"""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

CHECK_PRD = ROOT / "product-manager" / "scripts" / "check_prd.py"
CHECK_REVIEW = ROOT / "requirement-reviewer" / "scripts" / "check_review.py"
CHECK_PROTOTYPE = ROOT / "prototype-designer" / "scripts" / "check_prototype.py"
CHECK_UI = ROOT / "ui-designer" / "scripts" / "check_ui.py"
CHECK_DATABASE = ROOT / "database-designer" / "scripts" / "check_database.py"
CHECK_ARCHITECTURE = ROOT / "architecture-designer" / "scripts" / "check_architecture.py"
CHECK_SOURCE = ROOT / "software-developer" / "scripts" / "check_source.py"
CHECK_QA = ROOT / "qa-tester" / "scripts" / "check_qa.py"
SCAN_DANGER = ROOT / "security-pentester" / "scripts" / "scan_danger.py"
SCAN_SECURITY = ROOT / "security-pentester" / "scripts" / "scan_security.py"

API_OK = """# 系统 API 接口文档

## 接口总览
| 接口 | 方法 | 路径 | 对应 FR |
|---|---|---|---|
| 登录 | POST | /api/login | FR-02 |

## 接口明细
### POST /api/login
- 请求参数：username(string, 必填)
- 请求示例：{"username": "u1"}
- 返回结构：code, message, data{token}
- 错误码：40001 参数缺失
"""

PRD_TEN = """# 示例 PRD

## 1. 背景与目标
- 一句话概括：我们要为新用户在首次登录场景下解决流失问题，成功后提升留存。

## 2. 目标用户与场景
- 目标用户：新用户
- 核心使用场景：首次登录

## 3. 用户故事
- US-1：作为新用户，我希望快速上手，以便继续使用。

## 4. 功能需求清单
| 编号 | 功能 | 优先级 | 描述 |
|---|---|---|---|
| FR-01 | 引导页 | P0 | 展示核心功能 |

## 5. 业务流程
1. 打开应用
2. 看到引导
3. 开始使用

异常分支：
- 当网络断开时，系统应提示重试。

## 6. 非功能需求
- 性能：列表加载 < 2s
- 安全：密码不得明文存储

## 7. 范围边界
**本期做**：FR-01
**本期不做**：社交功能

## 8. 验收标准
- FR-01：Given 新用户，When 首次登录，Then 看到引导页。

## 9. 依赖
- 外部依赖：无

## 10. 里程碑
- 阶段1：MVP，1周
"""

REVIEW_OK = """# 评审报告

结论：YES

## 完整性
完整。
## 可执行性
可执行。
## 边界
清晰。
## 验收
可验收。
## 技术可行
可行。
## 合规
合规。
## 一致性
一致。
"""

QA_OK = """# 测试报告

结论：通过

## bug 清单
- 所有用例通过，无遗留问题
- 回归通过

## 非功能与风险预案核对
- 性能、安全、风险预案全部核对通过
"""

QA_FATAL = """# 测试报告

结论：通过

## bug 清单
- 致命：程序无法启动

## 非功能与风险预案核对
- 性能、安全、风险预案全部核对通过
"""


def run(script, *args):
    cmd = [sys.executable, str(script), *args]
    p = subprocess.run(cmd, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    return p.returncode


def w(name, path, content):
    Path(path).write_text(content, encoding="utf-8")
    return str(path)


def check_qa_noarg():
    return run(CHECK_QA) == 2


TESTS = []


def test(name):
    def deco(fn):
        TESTS.append((name, fn))
        return fn
    return deco


@test("check_prd 通过=0")
def _(tmp):
    f = w("prd_ok.md", tmp / "prd_ok.md", PRD_TEN)
    return run(CHECK_PRD, f) == 0


@test("check_prd 缺章节=1")
def _(tmp):
    f = w("prd_missing.md", tmp / "prd_missing.md", "# 只有标题\n没有章节")
    return run(CHECK_PRD, f) == 1


@test("check_prd 占位残留=2")
def _(tmp):
    f = w("prd_ph.md", tmp / "prd_ph.md", PRD_TEN.replace("新用户", "[待补充]"))
    return run(CHECK_PRD, f) == 2


@test("check_prd 全角占位=2")
def _(tmp):
    f = w("prd_ph_full.md", tmp / "prd_ph_full.md", PRD_TEN.replace("新用户", "【待确认】"))
    return run(CHECK_PRD, f) == 2


@test("check_prd 新教法文字标注假设待确认=0")
def _(tmp):
    # SKILL.md 1.4.6 起：不再教 [假设待确认] 方括号占位，改用普通文字注明
    f = w("prd_newway.md", tmp / "prd_newway.md",
          PRD_TEN.replace("目标用户：新用户", "目标用户：新用户（假设待确认：是否含老用户回流）"))
    return run(CHECK_PRD, f) == 0


@test("check_prd 旧教法方括号假设待确认=2")
def _(tmp):
    # 旧教法写 [假设待确认] 必须仍被门禁拦下（占位残留契约不回退）
    f = w("prd_oldway.md", tmp / "prd_oldway.md",
          PRD_TEN.replace("目标用户：新用户", "目标用户：新用户 [假设待确认]"))
    return run(CHECK_PRD, f) == 2


@test("check_prd 尖括号占位=2")
def _(tmp):
    # 尖括号 <角色> 这类未替换占位必须被拦（门禁正则含 <...>，自动链接除外）
    f = w("prd_angle.md", tmp / "prd_angle.md",
          PRD_TEN.replace("目标用户：新用户", "目标用户：<角色>"))
    return run(CHECK_PRD, f) == 2


@test("check_prd markdown自动链接不误伤=0")
def _(tmp):
    # <https://...> 是 markdown 自动链接语法，不是占位，必须放行
    f = w("prd_autolink.md", tmp / "prd_autolink.md",
          PRD_TEN.replace("- 外部依赖：无", "- 外部依赖：无\n- 参考链接：<https://example.com>"))
    return run(CHECK_PRD, f) == 0


@test("check_prd 文件不存在=3")
def _(tmp):
    return run(CHECK_PRD, str(tmp / "nope.md")) == 3


@test("check_prd 缺参=2")
def _(tmp):
    return run(CHECK_PRD) == 2


@test("check_review 通过=0")
def _(tmp):
    f = w("review_ok.md", tmp / "review_ok.md", REVIEW_OK)
    return run(CHECK_REVIEW, f) == 0


@test("check_review 缺结论=1")
def _(tmp):
    f = w("review_bad.md", tmp / "review_bad.md", "# 评审报告\n没有结论")
    return run(CHECK_REVIEW, f) == 1


@test("check_review 文件不存在=3")
def _(tmp):
    return run(CHECK_REVIEW, str(tmp / "nope.md")) == 3


@test("check_review 缺一致性维度=1")
def _(tmp):
    # 七大维度之一缺失必须 FAIL（跨文档一致性是刺 2 新增维度）
    f = w("review_nodim.md", tmp / "review_nodim.md",
          REVIEW_OK.replace("## 一致性\n一致。\n", ""))
    return run(CHECK_REVIEW, f) == 1


@test("check_review 占位残留=2")
def _(tmp):
    f = w("review_ph.md", tmp / "review_ph.md",
          "# 评审报告\n结论：YES\n## 完整性\n[待确认]\n## 可执行性\n可执行。\n"
          "## 边界\n清晰。\n## 验收\n可验收。\n## 技术可行\n可行。\n## 合规\n合规。\n"
          "## 一致性\n一致。\n")
    return run(CHECK_REVIEW, f) == 2


@test("check_review 全角占位=2")
def _(tmp):
    f = w("review_ph_full.md", tmp / "review_ph_full.md",
          "# 评审报告\n结论：YES\n## 完整性\n【待确认】\n## 可执行性\n可执行。\n"
          "## 边界\n清晰。\n## 验收\n可验收。\n## 技术可行\n可行。\n## 合规\n合规。\n"
          "## 一致性\n一致。\n")
    return run(CHECK_REVIEW, f) == 2


@test("check_review 新教法文字阻断建议=0")
def _(tmp):
    # SKILL.md 1.4.6 起：问题清单不再用 [阻断]/[建议] 方括号，改纯文字
    f = w("review_newway.md", tmp / "review_newway.md",
          "# 评审报告\n结论：NO\n## 完整性\n完整。\n## 可执行性\n可执行。\n"
          "## 边界\n清晰。\n## 验收\n可验收。\n## 技术可行\n可行。\n## 合规\n合规。\n"
          "## 一致性\n一致。\n"
          "## 问题清单\n- 阻断：缺少验收标准 → 补充\n- 建议：文案待定 → 后续优化\n")
    return run(CHECK_REVIEW, f) == 0


@test("check_review 旧教法方括号阻断=2")
def _(tmp):
    # 旧教法写 [阻断] 必须仍被门禁拦下（占位残留契约不回退）
    f = w("review_oldway.md", tmp / "review_oldway.md",
          "# 评审报告\n结论：NO\n## 完整性\n完整。\n## 可执行性\n可执行。\n"
          "## 边界\n清晰。\n## 验收\n可验收。\n## 技术可行\n可行。\n## 合规\n合规。\n"
          "## 一致性\n一致。\n"
          "## 问题清单\n- [阻断] 缺少验收标准 → 补充\n")
    return run(CHECK_REVIEW, f) == 2


@test("check_review 尖括号占位=2")
def _(tmp):
    # 尖括号 <角色> 未替换占位必须被拦（与 check_prd 同口径）
    f = w("review_angle.md", tmp / "review_angle.md",
          REVIEW_OK.replace("完整。", "完整。<角色>"))
    return run(CHECK_REVIEW, f) == 2


@test("check_review 缺参=2")
def _(tmp):
    return run(CHECK_REVIEW) == 2


@test("check_source 通过=0")
def _(tmp):
    # 独立工作区：07-source/ 上一级有 07-api-docs.md（前后端分离必交契约）
    ws = tmp / "ws_ok"
    ws.mkdir()
    w("07-api-docs.md", ws / "07-api-docs.md", API_OK)
    d = ws / "07-source"
    d.mkdir()
    w("README.md", d / "README.md", "# 项目\n运行：python main.py")
    return run(CHECK_SOURCE, str(d)) == 0


@test("check_source 缺README=1")
def _(tmp):
    ws = tmp / "ws_noreadme"
    ws.mkdir()
    w("07-api-docs.md", ws / "07-api-docs.md", API_OK)
    d = ws / "07-source"
    d.mkdir()
    return run(CHECK_SOURCE, str(d)) == 1


@test("check_source 缺API文档=1")
def _(tmp):
    # 前后端分离模式：没有 07-api-docs.md 必须 FAIL
    ws = tmp / "ws_noapi"
    ws.mkdir()
    d = ws / "07-source"
    d.mkdir()
    w("README.md", d / "README.md", "# 项目\n运行：python main.py")
    return run(CHECK_SOURCE, str(d)) == 1


@test("check_source API文档占位=1")
def _(tmp):
    ws = tmp / "ws_api_ph"
    ws.mkdir()
    w("07-api-docs.md", ws / "07-api-docs.md",
      API_OK.replace("/api/login", "[待确认]"))
    d = ws / "07-source"
    d.mkdir()
    w("README.md", d / "README.md", "# 项目\n运行：python main.py")
    return run(CHECK_SOURCE, str(d)) == 1


@test("check_source 依赖目录混入=2")
def _(tmp):
    ws = tmp / "ws_leak"
    ws.mkdir()
    w("07-api-docs.md", ws / "07-api-docs.md", API_OK)
    d = ws / "07-source"
    d.mkdir()
    w("README.md", d / "README.md", "# 项目\n运行：python main.py")
    (d / "node_modules").mkdir()
    return run(CHECK_SOURCE, str(d)) == 2


@test("check_source 带PRD非功能未落实=1")
def _(tmp):
    # 刺 5：PRD 写了非功能需求/风险预案，交付包 README 无落实声明 → FAIL
    ws = tmp / "ws_nfr_bad"
    ws.mkdir()
    w("01-prd.md", ws / "01-prd.md", PRD_TEN)
    w("07-api-docs.md", ws / "07-api-docs.md", API_OK)
    d = ws / "07-source"
    d.mkdir()
    w("README.md", d / "README.md", "# 项目\n运行：python main.py\n")
    return run(CHECK_SOURCE, str(d)) == 1


@test("check_source 带PRD非功能已落实=0")
def _(tmp):
    # 落实声明逐条抄 PRD 条目原文开头 + 实现说明 → 通过
    ws = tmp / "ws_nfr_ok"
    ws.mkdir()
    w("01-prd.md", ws / "01-prd.md", PRD_TEN)
    w("07-api-docs.md", ws / "07-api-docs.md", API_OK)
    d = ws / "07-source"
    d.mkdir()
    w("README.md", d / "README.md",
      "# 项目\n运行：python main.py\n\n## 非功能需求落实\n"
      "- 性能：列表加载 < 2s（实测 1.5s）\n"
      "- 安全：密码不得明文存储（存环境变量，日志不打印）\n")
    return run(CHECK_SOURCE, str(d)) == 0


@test("check_source 目录不存在=3")
def _(tmp):
    return run(CHECK_SOURCE, str(tmp / "nope")) == 3


@test("check_source 缺参=2")
def _(tmp):
    return run(CHECK_SOURCE) == 2


@test("check_qa 缺非功能核对=1")
def _(tmp):
    # 刺 4：报告缺「非功能与风险预案核对」段落必须 FAIL
    f = w("qa_nonfr.md", tmp / "qa_nonfr.md",
          QA_OK.replace("## 非功能与风险预案核对\n- 性能、安全、风险预案全部核对通过\n", ""))
    return run(CHECK_QA, f) == 1


@test("check_qa 通过=0")
def _(tmp):
    f = w("qa_ok.md", tmp / "qa_ok.md", QA_OK)
    return run(CHECK_QA, f) == 0


@test("check_qa 未修复致命=2")
def _(tmp):
    f = w("qa_fatal.md", tmp / "qa_fatal.md", QA_FATAL)
    return run(CHECK_QA, f) == 2


@test("check_qa 缺结论=1")
def _(tmp):
    f = w("qa_bad.md", tmp / "qa_bad.md", "# 测试报告\n没有结论")
    return run(CHECK_QA, f) == 1


@test("check_qa 文件不存在=3")
def _(tmp):
    return run(CHECK_QA, str(tmp / "nope.md")) == 3


@test("check_qa 缺参=2")
def _(tmp):
    return run(CHECK_QA) == 2


@test("check_prototype 通过=0")
def _(tmp):
    f = w("proto_ok.md", tmp / "proto_ok.md",
          "# 原型设计文档\n## 一、页面清单\n| 页面 | 对应 FR | 页面目标 |\n| 登录页 | FR-02 | 用户登录 |\n"
          "## 二、页面框架\n### 登录页\n- 结构：顶部导航/内容区/底部操作\n- 交互：点击登录 → 校验 → 跳首页\n")
    return run(CHECK_PROTOTYPE, f) == 0


@test("check_prototype 缺FR引用=1")
def _(tmp):
    f = w("proto_nofr.md", tmp / "proto_nofr.md",
          "# 原型设计文档\n## 一、页面清单\n| 页面 | 页面目标 |\n| 登录页 | 用户登录 |\n")
    return run(CHECK_PROTOTYPE, f) == 1


@test("check_prototype 占位残留=2")
def _(tmp):
    f = w("proto_ph.md", tmp / "proto_ph.md",
          "# 原型设计文档\n## 一、页面清单\n| 页面 | 对应 FR | 页面目标 |\n| 登录页 | FR-02 | [待确认] |\n")
    return run(CHECK_PROTOTYPE, f) == 2


@test("check_prototype 文件不存在=3")
def _(tmp):
    return run(CHECK_PROTOTYPE, str(tmp / "nope.md")) == 3


@test("check_prototype 缺参=2")
def _(tmp):
    return run(CHECK_PROTOTYPE) == 2


@test("check_ui 通过=0")
def _(tmp):
    d = tmp / "ui_ok"
    d.mkdir()
    (d / "登录页.png").write_bytes(b"fake")
    w("design-spec.md", d / "design-spec.md",
      "# UI 设计规范\n主色：#2563EB\n字体：标题 20px\nFR-02 登录页\n")
    return run(CHECK_UI, str(d)) == 0


@test("check_ui 缺设计图=1")
def _(tmp):
    d = tmp / "ui_noimg"
    d.mkdir()
    return run(CHECK_UI, str(d)) == 1


@test("check_ui 缺design-spec=1")
def _(tmp):
    d = tmp / "ui_nospec"
    d.mkdir()
    (d / "登录页.png").write_bytes(b"fake")
    return run(CHECK_UI, str(d)) == 1


@test("check_ui 目录不存在=3")
def _(tmp):
    return run(CHECK_UI, str(tmp / "nope")) == 3


@test("check_ui 缺参=2")
def _(tmp):
    return run(CHECK_UI) == 2


@test("check_database 通过=0")
def _(tmp):
    f = w("db_ok.md", tmp / "db_ok.md",
          "# 数据库设计文档\n## 一、表清单\n| 表名 | 用途 | 对应 FR |\n| users | 用户 | FR-02 |\n"
          "## 二、表结构\n### users\n| 字段 | 类型 | 主键 |\n| id | INT | 是 |\n"
          "## 三、关联关系\n- orders.user_id -> users.id\n")
    return run(CHECK_DATABASE, f) == 0


@test("check_database 缺关联关系=1")
def _(tmp):
    f = w("db_norel.md", tmp / "db_norel.md",
          "# 数据库设计文档\n## 一、表清单\n| 表名 | 用途 |\n| users | 用户 |\n"
          "## 二、表结构\n### users\n| 字段 | 类型 |\n| id | INT |\n")
    return run(CHECK_DATABASE, f) == 1


@test("check_database 占位残留=2")
def _(tmp):
    f = w("db_ph.md", tmp / "db_ph.md",
          "# 数据库设计文档\n## 一、表清单\n| 表名 | 用途 |\n| users | 【待确认】 |\n"
          "## 二、表结构\n### users\n| 字段 | 类型 |\n| id | INT |\n"
          "## 三、关联关系\n- orders.user_id -> users.id\n")
    return run(CHECK_DATABASE, f) == 2


@test("check_database 文件不存在=3")
def _(tmp):
    return run(CHECK_DATABASE, str(tmp / "nope.md")) == 3


@test("check_database 缺参=2")
def _(tmp):
    return run(CHECK_DATABASE) == 2


@test("check_architecture 通过=0")
def _(tmp):
    f = w("arch_ok.md", tmp / "arch_ok.md",
          "# 架构设计文档\n## 一、分层架构\n| 层 | 职责 |\n| 表现层 | 页面渲染 |\n"
          "## 二、模块划分\n| 模块 | 职责 |\n| 用户模块 | 用户管理 |\n"
          "## 三、扩展性设计\n- 新增功能挂到对应模块，扩展点已预留\n")
    return run(CHECK_ARCHITECTURE, f) == 0


@test("check_architecture 缺扩展性=1")
def _(tmp):
    f = w("arch_noext.md", tmp / "arch_noext.md",
          "# 架构设计文档\n## 一、分层架构\n| 层 | 职责 |\n| 表现层 | 页面渲染 |\n"
          "## 二、模块划分\n| 模块 | 职责 |\n| 用户模块 | 用户管理 |\n")
    return run(CHECK_ARCHITECTURE, f) == 1


@test("check_architecture 占位残留=2")
def _(tmp):
    f = w("arch_ph.md", tmp / "arch_ph.md",
          "# 架构设计文档\n## 一、分层架构\n| 层 | 职责 |\n| 表现层 | <待定> |\n"
          "## 二、模块划分\n| 模块 | 职责 |\n| 用户模块 | 用户管理 |\n"
          "## 三、扩展性设计\n- 扩展点已预留\n")
    return run(CHECK_ARCHITECTURE, f) == 2


@test("check_architecture 文件不存在=3")
def _(tmp):
    return run(CHECK_ARCHITECTURE, str(tmp / "nope.md")) == 3


@test("check_architecture 缺参=2")
def _(tmp):
    return run(CHECK_ARCHITECTURE) == 2


@test("scan_danger 干净JS=0")
def _(tmp):
    d = tmp / "danger_clean"
    d.mkdir()
    w("a.js", d / "a.js", 'console.log("hello");\n')
    return run(SCAN_DANGER, str(d)) == 0


@test("scan_danger 硬编码密钥=1")
def _(tmp):
    d = tmp / "danger_key"
    d.mkdir()
    w("a.js", d / "a.js", 'const api_key = "sk-1234567890abc";\n')
    return run(SCAN_DANGER, str(d)) == 1


@test("scan_danger eval=1")
def _(tmp):
    d = tmp / "danger_eval"
    d.mkdir()
    w("a.py", d / "a.py", 'eval(input("> "))\n')
    return run(SCAN_DANGER, str(d)) == 1


@test("scan_danger SQL拼接=4")
def _(tmp):
    d = tmp / "danger_sql"
    d.mkdir()
    w("a.py", d / "a.py", 'q = "SELECT * FROM users WHERE id=" + uid\n')
    return run(SCAN_DANGER, str(d)) == 4


@test("scan_danger 目录不存在=3")
def _(tmp):
    return run(SCAN_DANGER, str(tmp / "nope")) == 3


@test("scan_danger 缺参=2")
def _(tmp):
    return run(SCAN_DANGER) == 2


@test("scan_security 干净JS=0（bandit无关）")
def _(tmp):
    d = tmp / "sec_clean"
    d.mkdir()
    w("a.js", d / "a.js", 'console.log("hello");\n')
    return run(SCAN_SECURITY, str(d)) == 0


@test("scan_security 密钥JS=1（bandit无关）")
def _(tmp):
    d = tmp / "sec_key"
    d.mkdir()
    w("a.js", d / "a.js", 'const api_key = "sk-1234567890abc";\n')
    return run(SCAN_SECURITY, str(d)) == 1


@test("scan_security eval=1（正则保底，bandit装不装都过）")
def _(tmp):
    d = tmp / "sec_eval"
    d.mkdir()
    w("a.py", d / "a.py", 'eval(input("> "))\n')
    return run(SCAN_SECURITY, str(d)) == 1


@test("scan_security SQL拼接=4（正则保底，bandit装不装都过）")
def _(tmp):
    d = tmp / "sec_sql"
    d.mkdir()
    w("a.py", d / "a.py", 'q = "SELECT * FROM users WHERE id=" + uid\n')
    return run(SCAN_SECURITY, str(d)) == 4


@test("scan_security 目录不存在=3")
def _(tmp):
    return run(SCAN_SECURITY, str(tmp / "nope")) == 3


@test("scan_security 缺参=2")
def _(tmp):
    return run(SCAN_SECURITY) == 2


@test("scan_security 空.py=5（仅当bandit已装）")
def _(tmp):
    if shutil.which("bandit") is None:
        return True  # bandit 未装：降级路径，跳过该断言
    d = tmp / "sec_empty"
    d.mkdir()
    (d / "a.py").write_text("", encoding="utf-8")
    return run(SCAN_SECURITY, str(d)) == 5


def main():
    if len(sys.argv) != 1:
        print("用法: python scripts/regression_test.py", file=sys.stderr)
        return 2
    if not all(p.exists() for p in (CHECK_PRD, CHECK_REVIEW, CHECK_PROTOTYPE, CHECK_UI,
                                    CHECK_DATABASE, CHECK_ARCHITECTURE, CHECK_SOURCE,
                                    CHECK_QA, SCAN_DANGER, SCAN_SECURITY)):
        print(f"错误: 各棒脚本缺失，仓库不完整: {ROOT}", file=sys.stderr)
        return 2

    passed = 0
    failed = []
    skipped = []
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        for name, fn in TESTS:
            try:
                if fn(tmp):
                    passed += 1
                else:
                    failed.append(name)
            except Exception as e:
                failed.append(f"{name} (异常: {e})")

    print("=" * 64)
    print("流水线脚本回归测试")
    print("=" * 64)
    print(f"用例总数: {len(TESTS)}  通过: {passed}  失败: {len(failed)}")
    if skipped:
        print(f"跳过(可选): {skipped}")
    if failed:
        print("\n--- 失败用例 ---")
        for f in failed:
            print("  FAIL ", f)
        print(f"\n结果: 失败 {len(failed)}，退出码 1")
        return 1
    print("\n结果: 全部通过，退出码 0")
    return 0


if __name__ == "__main__":
    sys.exit(main())
