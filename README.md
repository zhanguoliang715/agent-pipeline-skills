# Software Pipeline Skills — 五棒软件开发流水线

![Python](https://img.shields.io/badge/python-3.9+-blue.svg)
![Bandit](https://img.shields.io/badge/bandit-1.9.4-yellow.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

把"写需求 → 评审 → 开发 → 测试 → 安全攻防"固化成五个独立的 Agent Skill，靠固定文件名和门禁规则串成流水线，不靠口头交接。

## 为什么要有这个

多棒协作最容易掉链子的地方：PRD 写得含糊就开干、代码写完没人测、安全扫描只走形式、被打回的结论靠聊天记录翻。这套 skill 把每棒的输入/产出/门禁/退回路径写成死规矩，每棒交稿前必须跑一个脚本做结构校验，缺东西直接非 0 退出。

## 流水线

```
┌──────────────┐   01-prd.md    ┌──────────────────┐  02-requirement-review.md
│ product-     │ ─────────────► │ requirement-     │ ──────► YES ──┐
│ manager      │                │ reviewer         │               │
└──────────────┘                └──────────────────┘               ▼
       ▲                                │ NO / 退回            ┌──────────────┐
       │                                └──────────────────      │ software-    │
       │                                                     │ developer    │
       │                                                     └──────┬───────┘
       │                                                            │ 03-source/
       │                                                            ▼
┌──────────────┐   05-security-   ┌──────────────┐   04-qa-test-   ┌──────────────┐
│ security-    │ ◄────────────── │ qa-tester    │ ◄────────────── │              │
│ pentester    │                 └──────────────┘                 └──────────────┘
└──────────────┘
```

## 五棒职责

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
├── validate_pipeline.py    # 全流水线一致性校验
├── USAGE.md                # 详细使用说明
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

| 码 | 含义 |
|---|---|
| 0 | 通过 |
| 1 | 有 HIGH / 致命缺失 |
| 4 | 有 MED（无 HIGH） |
| 3 | 目录/路径不存在 |
| 2 | argparse 用法错误 |
| 5 | 扫描工具自身故障（不能当干净） |

### 改完 skill 后自检

```bash
python validate_pipeline.py
```

检查五棒 SKILL.md 结构、references 不悬空、scripts 存在、固定产物名声明。退出 0 = 全绿。

## 关键设计

- **固定文件名**：五棒产物 01-05 固定命名，不靠口头传文件。
- **门禁退回分类**：纯前置确认不产出文件；已接触产物不合格则写自己那份报告标 NO/退回/打回。
- **history/ 留档**：覆盖写前把上一版归档，r 取已有最大序号+1（不数文件个数，防部分清理后重号），归档即只读。
- **环境隔离**：功能测试和攻防测试跑在独立实例上，不互相污染。
- **独立发版**：改哪棒升哪棒的 version，不统一跟升。
- **两层安全扫描**：正则粗扫（多语言）+ bandit（Python 深度扫），按文件:行号去重合并。

详细规则见 [USAGE.md](USAGE.md)。

## License

[MIT](LICENSE) © 壤驷秉燊
