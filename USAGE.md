# 软件开发流水线 Skill 使用说明

一套把"写需求 → 评审 → 开发 → 测试 → 安全攻防"固化成六个独立 Skill 的工作区。
每个角色一个目录，靠固定文件名和门禁规则串成流水线，不靠口头交接。
`pipeline-orchestrator` 是总调度，一句话跑完整条。

## 目录结构

```
repo-root/
├── product-manager/            # 棒 1：写 PRD
├── requirement-reviewer/       # 棒 2：需求评审
├── software-developer/          # 棒 3：写代码
├── qa-tester/                  # 棒 4：功能测试
├── security-pentester/          # 棒 5：安全攻防（终点）
│   └── scripts/scan_security.py # 危险代码自动扫描（正则 + bandit wrapper）
├── pipeline-orchestrator/       # 总调度（第 0 棒，串 1-5，不可单独部署）
├── scripts/                     # 仓库级（仅整套部署需要）
│   ├── regression_test.py       # 行为回归测试（机器实测退出码契约）
│   └── smoke_pipeline.py        # 端到端冒烟（五棒门禁链 + 打回/修复路由）
├── .github/workflows/           # CI：validate + regression + smoke（GitHub Actions，仅整套部署需要）
├── validate_pipeline.py         # 全流水线一致性校验器（根目录，仅整套部署需要）
├── 使用说明.txt                  # 中文版快速上手
└── USAGE.md                    # 本文件
```

每个 skill 目录内部标准结构：`SKILL.md`（指令入口）+ `references/`（知识库）+ 可选 `scripts/`。

## 独立部署

五个单棒（棒 1-5）各自可单独拷出使用，不需要整套仓库、orchestrator、仓库级脚本或 CI。拷贝整个棒目录后以该目录为 CWD 跑对应脚本即可：

| 棒 | 拷走目录 | 独立部署校验命令（CWD=棒目录） | 运行时依赖 |
|---|---|---|---|
| 1 | `product-manager/` | `python scripts/check_prd.py 01-prd.md` | Python ≥ 3.9，无第三方包 |
| 2 | `requirement-reviewer/` | `python scripts/check_review.py 02-requirement-review.md` | Python ≥ 3.9，无第三方包 |
| 3 | `software-developer/` | `python scripts/check_source.py 03-source/` | Python ≥ 3.9，运行被测程序另按 README |
| 4 | `qa-tester/` | `python scripts/check_qa.py 04-qa-test-report.md` | Python ≥ 3.9，运行被测程序另按 README |
| 5 | `security-pentester/` | `python scripts/scan_security.py 03-source/` | Python ≥ 3.9 + `pip install "bandit==1.9.4"`（不装只跑正则层） |

单棒目录自包含：`SKILL.md`（含"独立部署"章节）+ `references/`（配套本棒自身，不悬空）+ `scripts/`；产物文件名固定不变。`pipeline-orchestrator` 不可单独部署（只调度不产出，必须与五棒同仓库根）；仓库级 `scripts/`、`validate_pipeline.py`、`.github/workflows/` 仅整套部署需要。

## 棒次一览

| 棒次 | Skill 目录 | 产出文件 | 职责一句话 |
|---|---|---|---|
| 1 | `product-manager` | `01-prd.md` | 把原始想法写成边界清楚、可验收的 PRD |
| 2 | `requirement-reviewer` | `02-requirement-review.md` | 评审 PRD 可执行性，结论 YES / NO / 退回 |
| 3 | `software-developer` | `03-source/`（目录） | 按 YES 的 PRD 写可运行代码，带 README 启动命令 |
| 4 | `qa-tester` | `04-qa-test-report.md` | 搭环境跑主流程，列 bug 分级 |
| 5 | `security-pentester` | `05-security-pentest-report.md` | 授权门禁后多轮攻防，高危修完再攻 |

结论取值全流水线统一：**YES / NO / 退回 / 打回 / 不通过**，以 security-pentester 的命名规范段为唯一权威，下游不另造词。

## 怎么跑一条流水线

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

1. **产品经理**：说出业务想法，它追问关键信息后写 `01-prd.md`。
2. **需求审核**：拿 `01-prd.md` 评审。YES 放行；NO/退回则改完重交，最多打回 2 次（共 3 次评审机会），到上限升级给你决定。
3. **程序开发**：只在 `02` 结论=YES 时开工，写 `03-source/`（含 README 启动命令）。
4. **程序测试**：按 README 起程序跑主流程，写 `04-qa-test-report.md`。起不来=致命 bug 直接打回。
5. **安全攻防**：先过授权门禁（外部/公网目标一律拒绝），再跑自动扫描 + 手动攻击，写 `05-security-pentest-report.md`。

**打回怎么走**：每棒被打回都照样写自己那份文件（结论标 NO/退回/打回），作为下一棒输入，不靠口头。纯前置确认（PM 问"真要做吗"、SP 授权核对外部目标）没接触产物时不写文件，直接对话回复。

## 工具脚本

每棒交稿前都有一个对应脚本做"结构完整性门禁"，缺东西就非 0 退出。在工作区根目录跑：

| 棒 | 命令 | 查什么 |
|---|---|---|
| PM | `python product-manager/scripts/check_prd.py 01-prd.md` | PRD 十节齐全、无占位残留 |
| RR | `python requirement-reviewer/scripts/check_review.py 02-requirement-review.md` | 有 YES/NO/退回结论、六维度全覆盖、无占位残留 |
| SD | `python software-developer/scripts/check_source.py 03-source/` | README 存在且有启动命令、无依赖目录混入 |
| QA | `python qa-tester/scripts/check_qa.py 04-qa-test-report.md` | 有结论、有 bug 清单、无未修复致命项 |
| SP | `python security-pentester/scripts/scan_security.py 03-source/` | 危险代码扫描（正则粗扫 + bandit Python 深度扫） |

退出码分两套，别混：

**四棒 check 脚本（check_prd / check_review / check_source / check_qa）**：

| 码 | 含义 |
|---|---|
| 0 | 通过 |
| 1 | 缺内容（缺章节/缺结论/缺 README 等） |
| 2 | 业务警告，各脚本语义不同：check_prd/check_review=占位残留，check_source=依赖目录混入，check_qa=未修致命/严重项 |
| 3 | 路径不存在（文件或目录） |

缺参数 = 2（用法错误，与业务警告共用 2 号）。

**安全棒 scan_security.py（scan_danger.py 同此契约）**：

| 码 | 含义 |
|---|---|
| 0 | 干净 |
| 1 | 有 HIGH |
| 4 | 有 MED（无 HIGH） |
| 3 | 目录/路径不存在 |
| 2 | argparse 用法错误（命令行写错） |
| 5 | 扫描工具自身故障（bandit 崩/JSON 坏/有 .py 但 0 行），不能当干净 |

这些脚本只查结构和完整性，不替你判断内容对错。

### 1. 一致性校验器（每次改完 Skill 必跑）

```bash
python validate_pipeline.py
```

退出码 0 = 全绿；非 0 = 有问题，按 FAIL 清单改。它自动检查：

- 各棒 SKILL.md 都在、frontmatter 白名单合规、有 version、有第 0 步门禁；
- 各棒 version 独立发版（不一致只警告，不是错误）；
- references 声明的文件真实存在、本文件版本对得上、含修订历史；
- 正文 markdown 链接和 scripts/ 脚本不悬空；
- 各棒输出契约声明了自己的固定产物名。

**改任何一个 SKILL.md 或 references 之后，先跑它，红了再改。**

### 2. 危险代码扫描（安全棒第 1 步强制）

```bash
python security-pentester/scripts/scan_security.py 03-source/
```

这个 wrapper 跑两层：

1. **多语言正则粗扫**（自带的 `scan_danger.py`）：硬编码密钥/口令、云 AccessKey、`eval`/`exec`、`os.system`/`os.popen`/`shell=True`、pickle/yaml 不安全反序列化、SQL 拼接与 f-string 插值。自动跳过 `.git`/`node_modules`/`.venv`/`__pycache__`/`dist`/`build`。
2. **bandit Python 深度扫**（PyCQA 官方 linter，规则带 CWE 编号）：只扫 `.py`，按 issue_severity 分级，LOW 丢弃。

两层命中按 `文件:行号` 去重合并。目录无 `.py` 时 bandit 自动跳过，只靠正则层；bandit 没装也降级跑正则层并打 note。

退出码：

| 码 | 含义 |
|---|---|
| 0 | 干净 |
| 1 | 有 HIGH |
| 4 | 有 MED（无 HIGH） |
| 3 | 目录/路径不存在 |
| 2 | argparse 用法错误 |
| 5 | 扫描工具自身故障（bandit 崩/JSON坏/有 .py 但 0 行），不能当干净 |

**已知边界（别指望它全抓）**：单行匹配，跨行拼接不报；整行块注释（`/* */`、`<!-- -->`）会跳过，但块注释内部跨行的代码不识别；正则是启发式，有误报，用 `--ignore` 排除。它是第一道过滤网，不是替代人工攻防。

### 3. 行为回归测试（改脚本逻辑后必跑）

```bash
python scripts/regression_test.py
python scripts/smoke_pipeline.py    # 端到端冒烟：五棒门禁链 + 打回/修复路由
```

`validate_pipeline.py` 只查结构，证明不了行为正确。回归测试用真实样本逐个断言六棒脚本的退出码契约；冒烟测试按 orchestrator 调度顺序把五棒门禁链整体跑一遍，并验证"打回 -> 修复 -> 再通过"路由，防止单脚本全绿但整条流水线接不上。

- 四棒 check 脚本：0 通过 / 1 缺内容 / 2 业务警告 / 3 路径错 / 缺参 2；
- 安全棒正则层：干净 JS=0、硬编码密钥=1、eval=1、SQL 拼接=4、目录错=3；
- 安全棒 wrapper：bandit 无关断言（纯 JS）+ bandit 已装时集成断言（空 .py=5）。

任何 FAIL = 脚本行为漂移（退出码漂了、规则漏报/误报改了）。改 `scripts/` 下任何 `.py` 之后必须跑一次，全绿才提交。

### validate_pipeline.py 也只管结构，不管对错

它能证明"各棒文件齐、引用不悬空、版本字段在、命名写了"，**证明不了"规则写得对、脚本行为正确"**。脚本误报/漏报要靠自测样本验证，validate 全绿 ≠ 行为正确。

## history/ 留档

01-05 是固定文件名，每次覆盖写之前把上一版复制到 `history/`：

- 命名：`history/产物主干-r最大序号+1-YYYYMMDDTHHMM`（产物主干、序号、时间戳按实际填写），例如 `history/02-requirement-review-r2-20260928T1435.md`。
- **r 取已有最大序号 +1，不要数文件个数**（部分清理过时数个数会重号吞档）。
- 03 是目录，归档时整个复制但排除 `.git`/依赖/构建产物。
- 归档即只读，不回头改；history/ 只进不删，清理由你决定。

## 版本维护规矩

- **各棒独立发版**：改了哪个 SKILL.md，就只升那一棒的 version；没动的棒不要跟着升。
- validate 会警告版本不一致（这是正常的独立发版，不是错误）。
- 改了某个 `references/*.md`，它自己的"本文件版本"升，SKILL.md 的 references 配套声明不写死具体版本。
- references 文件必须有"本文件版本：x.y.z"和"## 修订历史"段。
- 改完跑 `validate_pipeline.py` 确认无悬空、无结构错误。

## 环境要求

- Python ≥ 3.9；
- 四棒（PM/RR/SD/QA）的检查脚本和 `validate_pipeline.py` 只用标准库，无需 pip install；
- 安全棒的 `scan_security.py` 第二层依赖 bandit：`pip install "bandit==1.9.4"`。没装也能跑（只跑正则层并打 note），但 Python 项目建议装；
- Windows / macOS / Linux 均可，路径全用 pathlib。
