# Software Pipeline Skills — 软件开发流水线

![Python](https://img.shields.io/badge/python-3.9+-blue.svg)
![Bandit](https://img.shields.io/badge/bandit-1.9.4-yellow.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

把"写需求 → 评审 → 设计（原型 / UI / 数据库 / 架构）→ 前后端开发 → 测试 → 安全攻防"固化成十个独立的 Agent Skill，靠固定文件名和门禁规则串成流水线，不靠口头交接。前九个是单棒，第十个 `pipeline-orchestrator` 是总调度，一句话跑完整条。

## 为什么要有这个

多棒协作最容易掉链子的地方：PRD 写得含糊就开干、设计文档缺失就写代码、代码写完没人测、安全扫描只走形式、被打回的结论靠聊天记录翻。这套 skill 把每棒的输入/产出/门禁/退回路径写成死规矩，每棒交稿前必须跑一个脚本做结构校验，缺东西直接非 0 退出。

## 流水线

```
1. product-manager        -> 01-prd.md
2. requirement-reviewer   -> 02-requirement-review.md（YES 才放行，最多打回 2 次）
3. prototype-designer     -> 03-prototype-design.md（产品经理画页面线框稿）
4. ui-designer            -> 04-ui-design/（设计师出高保真界面图）
5. database-designer      -> 05-database-design.md（技术经理设计库表与关联）
6. architecture-designer  -> 06-architecture-design.md（技术经理定分层架构）
7. software-developer     -> 07-source/ + 07-api-docs.md（前后端分离开发 + 接口文档）
8. qa-tester              -> 08-qa-test-report.md（功能测试，起不来=致命 bug 打回）
9. security-pentester     -> 09-security-pentest-report.md（授权门禁后多轮攻防）
```

## 单棒职责（棒 1-9；总调度 pipeline-orchestrator 见开头）

| 棒 | 目录 | 产出 | 干什么 | 门禁 |
|---|---|---|---|---|
| 1 | `product-manager/` | `01-prd.md` | 把原始想法写成边界清楚、可验收的 PRD | 第 0 步：确认真要做才开工，最多 3 轮追问 |
| 2 | `requirement-reviewer/` | `02-requirement-review.md` | 评审 PRD 可执行性，七维度打分（含跨文档一致性对账） | 第 0 步：收到的不是 PRD 就退回；最多打回 2 次 |
| 3 | `prototype-designer/` | `03-prototype-design.md` | 产品经理按功能需求画页面框架线稿图（Axure/Figma 思路） | 第 0 步：02 结论不是 YES 不开工 |
| 4 | `ui-designer/` | `04-ui-design/` | 设计师把线框转高保真界面设计图（配色/字体/组件规范） | 第 0 步：原型文档缺失或未放行不开工 |
| 5 | `database-designer/` | `05-database-design.md` | 技术经理设计表结构、字段、主外键与关联关系 | 第 0 步：02 结论不是 YES 不开工 |
| 6 | `architecture-designer/` | `06-architecture-design.md` | 技术经理定分层架构、模块边界与扩展点 | 第 0 步：无 FR 清单不开工 |
| 7 | `software-developer/` | `07-source/` + `07-api-docs.md` | 前后端分离开发：前端按原型+UI 写界面，后端按数据库文档写接口并出 API 文档，最后联调 | 第 0 步：02 不是 YES 或设计文档不齐不开工 |
| 8 | `qa-tester/` | `08-qa-test-report.md` | 搭环境跑主流程，列 bug 分级，核对非功能与风险预案 | 第 0 步：按 README 起不来 = 致命 bug 直接打回 |
| 9 | `security-pentester/` | `09-security-pentest-report.md` | 授权门禁后多轮攻防，高危修完回归再攻 | 第 0 步：外部/公网目标一律拒绝 |

## 目录结构

```
.
├── product-manager/
│   ├── SKILL.md
│   ├── references/        # prd-template.md, prd-checklist.md
│   └── scripts/check_prd.py
├── requirement-reviewer/
│   ├── SKILL.md
│   ├── references/review-checklist.md
│   └── scripts/check_review.py
├── prototype-designer/          # 新增：产品原型设计
│   ├── SKILL.md
│   ├── references/prototype-checklist.md
│   └── scripts/check_prototype.py
├── ui-designer/                 # 新增：UI 设计
│   ├── SKILL.md
│   ├── references/ui-guidelines.md
│   └── scripts/check_ui.py
├── database-designer/           # 新增：数据库设计
│   ├── SKILL.md
│   ├── references/db-design-checklist.md
│   └── scripts/check_database.py
├── architecture-designer/       # 新增：架构设计
│   ├── SKILL.md
│   ├── references/architecture-checklist.md
│   └── scripts/check_architecture.py
├── software-developer/          # 前后端分离开发
│   ├── SKILL.md
│   ├── references/coding-standards.md
│   └── scripts/check_source.py
├── qa-tester/
│   ├── SKILL.md
│   ├── references/        # bug-levels.md, test-case-design.md
│   └── scripts/check_qa.py
├── security-pentester/
│   ├── SKILL.md
│   ├── references/        # vuln-severity.md, attack-vectors.md
│   └── scripts/           # scan_danger.py, scan_security.py
├── pipeline-orchestrator/  # 总调度（一句话跑完整条流水线）
│   └── SKILL.md
├── scripts/                 # 仓库级（仅整套部署需要）
│   ├── regression_test.py   # 行为回归测试（机器实测退出码契约）
│   └── smoke_pipeline.py    # 端到端冒烟（门禁链 + 打回/修复路由）
├── .github/workflows/      # CI：validate + regression + smoke（GitHub Actions，仅整套部署需要）
├── validate_pipeline.py    # 全流水线一致性校验（仅整套部署需要）
├── USAGE.md                # 详细使用说明
├── 使用说明.txt             # 中文版快速上手
├── LICENSE
└── .gitignore
```

## 独立部署

九个单棒（棒 1-9）各自可单独拷出使用，**不需要**整套仓库、orchestrator、仓库级脚本或 CI：

| 棒 | 拷走目录 | 独立部署校验命令（以该棒目录为 CWD） |
|---|---|---|
| 1 | `product-manager/` | `python scripts/check_prd.py 01-prd.md` |
| 2 | `requirement-reviewer/` | `python scripts/check_review.py 02-requirement-review.md` |
| 3 | `prototype-designer/` | `python scripts/check_prototype.py 03-prototype-design.md` |
| 4 | `ui-designer/` | `python scripts/check_ui.py 04-ui-design/` |
| 5 | `database-designer/` | `python scripts/check_database.py 05-database-design.md` |
| 6 | `architecture-designer/` | `python scripts/check_architecture.py 06-architecture-design.md` |
| 7 | `software-developer/` | `python scripts/check_source.py 07-source/` |
| 8 | `qa-tester/` | `python scripts/check_qa.py 08-qa-test-report.md` |
| 9 | `security-pentester/` | `python scripts/scan_security.py 07-source/` |

每个单棒目录是自包含的：`SKILL.md`（含"独立部署"章节）+ `references/` + `scripts/`，运行时依赖与产物命名见各棒 SKILL.md。`pipeline-orchestrator` 不可单独部署（它只调度不产出，必须与九棒同仓库根），仓库级 `scripts/`、`validate_pipeline.py`、`.github/` 也仅整套部署需要。

## 快速开始

### 依赖

- Python ≥ 3.9
- 八个 check 脚本只用标准库，无需 pip install
- 安全棒可选深度扫描：`pip install "bandit==1.9.4"`（不装也能跑，只跑正则粗扫）

### 跑一条流水线

在一个空工作目录里按顺序让对应 Skill 干活，每棒产出固定文件名：

```
工作区/
├── 01-prd.md
├── 02-requirement-review.md
├── 03-prototype-design.md
├── 04-ui-design/
├── 05-database-design.md
├── 06-architecture-design.md
├── 07-source/
├── 07-api-docs.md
├── 08-qa-test-report.md
├── 09-security-pentest-report.md
└── history/                 # 覆盖写前的历史归档
```

每棒交稿前跑对应脚本做结构校验（在工作区根目录）：

```bash
python product-manager/scripts/check_prd.py 01-prd.md
python requirement-reviewer/scripts/check_review.py 02-requirement-review.md
python prototype-designer/scripts/check_prototype.py 03-prototype-design.md
python ui-designer/scripts/check_ui.py 04-ui-design/
python database-designer/scripts/check_database.py 05-database-design.md
python architecture-designer/scripts/check_architecture.py 06-architecture-design.md
python software-developer/scripts/check_source.py 07-source/
python qa-tester/scripts/check_qa.py 08-qa-test-report.md
python security-pentester/scripts/scan_security.py 07-source/
```

### 退出码

退出码分两套，别混：

**八个 check 脚本（check_prd / check_review / check_prototype / check_ui / check_database / check_architecture / check_source / check_qa）**：

| 码 | 含义 |
|---|---|
| 0 | 通过 |
| 1 | 缺内容（缺章节/缺结论/缺页面清单/缺设计图/缺表关联/缺分层/缺 README/缺 API 文档等） |
| 2 | 业务警告，各脚本语义不同（占位残留 / 依赖目录混入 / 未修致命项） |
| 3 | 路径不存在（文件或目录） |

缺参数 = 2（用法错误，与业务警告共用 2 号）。2 号具体语义：check_prd/check_review/check_prototype/check_database/check_architecture=占位残留，check_source=依赖目录混入，check_qa=未修致命/严重项，check_ui=占位残留。

**安全棒 `scan_security.py`**：

| 码 | 含义 |
|---|---|
| 0 | 干净 |
| 1 | 有 HIGH |
| 4 | 有 MED（无 HIGH） |
| 3 | 目录/路径不存在 |
| 2 | argparse 用法错误 |
| 5 | 扫描工具自身故障（不能当干净） |

### 改完 skill 后自检

```bash
python validate_pipeline.py     # 结构一致性（十棒 SKILL.md、references 不悬空、scripts 存在、固定产物名）
python scripts/regression_test.py  # 行为回归（各棒脚本退出码契约，机器实测）
python scripts/smoke_pipeline.py   # 端到端冒烟（门禁链 + 打回/修复路由，机器实测）
```

三个都退出 0 = 全绿。validate 管"结构齐不齐"，regression 管"行为对不对"，冒烟管"整条调度链跑不跑得通"——改 `scripts/` 下任何脚本逻辑，validate 可能照样绿，必须跑回归和冒烟。

## 关键设计

- **固定文件名**：九件产物 01-09 固定命名（orchestrator 只调度不产出），不靠口头传文件。
- **前后端分离**：Software Developer 按三阶段走——前端（原型+UI）与后端（数据库+接口）并行开发，按 `07-api-docs.md` 接口文档联调；API 文档是前后端对接契约，随代码包一起交。
- **门禁退回分类**：纯前置确认不产出文件；已接触产物不合格则写自己那份报告标 NO/退回/打回。
- **history/ 留档**：覆盖写前把上一版归档，r 取已有最大序号+1（不数文件个数，防部分清理后重号），归档即只读。
- **环境隔离**：功能测试和攻防测试跑在独立实例上，不互相污染。
- **独立发版**：改哪棒升哪棒的 version，不统一跟升。
- **两层安全扫描**：正则粗扫（多语言）+ bandit（Python 深度扫），按文件:行号去重合并。
- **行为回归**：`scripts/regression_test.py` 用真实样本断言各棒退出码契约，堵"改脚本逻辑但 validate 照绿"的单点风险。

详细规则见 [USAGE.md](USAGE.md)。

## License

[MIT](LICENSE) © 壤驷秉燊
