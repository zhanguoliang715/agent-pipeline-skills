# Software Pipeline Skills — 软件开发流水线

![Python](https://img.shields.io/badge/python-3.9+-blue.svg)
![Bandit](https://img.shields.io/badge/bandit-1.9.4-yellow.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

把"写需求 → 评审 → 开发 → 测试 → 安全攻防"固化成六个独立的 Agent Skill，靠固定文件名和门禁规则串成流水线，不靠口头交接。前五个是单棒，第六个 `pipeline-orchestrator` 是总调度，一句话跑完整条。

## 为什么要有这个

多棒协作最容易掉链子的地方：PRD 写得含糊就开干、代码写完没人测、安全扫描只走形式、被打回的结论靠聊天记录翻。这套 skill 把每棒的输入/产出/门禁/退回路径写成死规矩，每棒交稿前必须跑一个脚本做结构校验，缺东西直接非 0 退出。

## 流水线

```
┌──────────────┐   01-prd.md    ┌──────────────────┐  02-requirement-review.md
│ product-     │ ─────────────► │ requirement-     │ ──────► YES ──┐
│ manager      │                │ reviewer         │               │
└──────────────┘                └──────────────────┘               ▼
       ▲                                │ NO / 退回          ┌──────────────┐
       │                                └──────────────────► │ software-    │
       │                                                     │ developer    │
       │                                                     └──────┬───────┘
       │                                                            │ 03-source/
       │                                                            ▼
┌──────────────┐   05-security-  ┌──────────────┐   04-qa-test-   ┌──────────────┐
│ security-    │ ◄────────────── │ qa-tester    │ ◄────────────── │              │
│ pentester    │                 └──────────────┘                 └──────────────┘
└──────────────┘
```

## 单棒职责（棒 1-5；总调度 pipeline-orchestrator 见开头）

| 棒 | 目录 | 产出 | 干什么 | 门禁 |
|---|---|---|---|---|
| 1 | `product-manager/` | `01-prd.md` | 把原始想法写成边界清楚、可验收的 PRD | 第 0 步：确认真要做才开工，最多 3 轮追问 |
| 2 | `requirement-reviewer/` | `02-requirement-review.md` | 评审 PRD 可执行性，六维度打分 | 第 0 步：收到的不是 PRD 就退回；最多打回 2 次 |
| 3 | `software-developer/` | `03-source/` | 按 YES 的 PRD 写可运行代码，带 README 启动命令 | 第 0 步：02 结论不是 YES 不开工 |
| 4 | `qa-tester/` | `04-qa-test-report.md` | 搭环境跑主流程，列 bug 分级 | 第 0 步：按 README 起不来 = 致命 bug 直接打回 |
| 5 | `security-pentester/` | `05-security-pentest-report.md` | 授权门禁后多轮攻防，高危修完再攻 | 第 0 步：外部/公网目标一律拒绝 |

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
├── software-developer/
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
├── scripts/
│   ├── regression_test.py   # 行为回归测试（机器实测退出码契约）
│   └── smoke_pipeline.py    # 端到端冒烟（五棒门禁链 + 打回/修复路由）
├── .github/workflows/      # CI：validate + regression + smoke（GitHub Actions）
├── validate_pipeline.py    # 全流水线一致性校验
├── USAGE.md                # 详细使用说明
├── 使用说明.txt             # 中文版快速上手
├── 提示词模板.txt           # 傻瓜式提示词
├── LICENSE
└── .gitignore
```

## 快速开始

### 依赖

- Python ≥ 3.9
- 四棒检查脚本只用标准库，无需 pip install
- 安全棒可选深度扫描：`pip install "bandit==1.9.4"`（不装也能跑，只跑正则粗扫）

### 跑一条流水线

在一个空工作目录里按顺序让对应 Skill 干活，每棒产出固定文件名：

```
工作区/
├── 01-prd.md
├── 02-requirement-review.md
├── 03-source/
├── 04-qa-test-report.md
├── 05-security-pentest-report.md
└── history/                 # 覆盖写前的历史归档
```

每棒交稿前跑对应脚本做结构校验（在工作区根目录）：

```bash
python product-manager/scripts/check_prd.py 01-prd.md
python requirement-reviewer/scripts/check_review.py 02-requirement-review.md
python software-developer/scripts/check_source.py 03-source/
python qa-tester/scripts/check_qa.py 04-qa-test-report.md
python security-pentester/scripts/scan_security.py 03-source/
```

### 退出码

下面是安全棒 `scan_security.py` 的退出码。其他四棒脚本的 0/1/2/3 含义各不同（2 号在 check_prd=占位残留、check_review=占位残留、check_source=依赖目录混入、check_qa=未修致命项），以各脚本 `--help` 或 USAGE.md 为准。

| 码 | 含义（安全棒） |
|---|---|
| 0 | 干净 |
| 1 | 有 HIGH |
| 4 | 有 MED（无 HIGH） |
| 3 | 目录/路径不存在 |
| 2 | argparse 用法错误 |
| 5 | 扫描工具自身故障（不能当干净） |

### 改完 skill 后自检

```bash
python validate_pipeline.py     # 结构一致性（六棒 SKILL.md、references 不悬空、scripts 存在、固定产物名）
python scripts/regression_test.py  # 行为回归（六棒脚本退出码契约，机器实测）
python scripts/smoke_pipeline.py   # 端到端冒烟（五棒门禁链 + 打回/修复路由，机器实测）
```

三个都退出 0 = 全绿。validate 管"结构齐不齐"，regression 管"行为对不对"，冒烟管"整条调度链跑不跑得通"——改 `scripts/` 下任何脚本逻辑，validate 可能照样绿，必须跑回归和冒烟。

## 关键设计

- **固定文件名**：五件产物 01-05 固定命名（orchestrator 只调度不产出），不靠口头传文件。
- **门禁退回分类**：纯前置确认不产出文件；已接触产物不合格则写自己那份报告标 NO/退回/打回。
- **history/ 留档**：覆盖写前把上一版归档，r 取已有最大序号+1（不数文件个数，防部分清理后重号），归档即只读。
- **环境隔离**：功能测试和攻防测试跑在独立实例上，不互相污染。
- **独立发版**：改哪棒升哪棒的 version，不统一跟升。
- **两层安全扫描**：正则粗扫（多语言）+ bandit（Python 深度扫），按文件:行号去重合并。
- **行为回归**：`scripts/regression_test.py` 用真实样本断言六棒退出码契约，堵"改脚本逻辑但 validate 照绿"的单点风险。

详细规则见 [USAGE.md](USAGE.md)。

## License

[MIT](LICENSE) © 壤驷秉燊
