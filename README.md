# Software Pipeline Skills — 五棒软件开发流水线

把"写需求 → 评审 → 开发 → 测试 → 安全攻防"固化成五个独立的 Agent Skill，靠固定文件名和门禁规则串成流水线，不靠口头交接。

```
product-manager ──► requirement-reviewer ──► software-developer ──► qa-tester ──► security-pentester
   01-prd.md          02-requirement-review.md    03-source/            04-qa-test-report.md    05-security-pentest-report.md
```

## 五棒职责

| 棒 | 目录 | 产出 | 干什么 |
|---|---|---|---|
| 1 | `product-manager/` | `01-prd.md` | 把原始想法写成边界清楚、可验收的 PRD |
| 2 | `requirement-reviewer/` | `02-requirement-review.md` | 评审 PRD 可执行性，结论 YES / NO / 退回 |
| 3 | `software-developer/` | `03-source/` | 按 YES 的 PRD 写可运行代码，带 README 启动命令 |
| 4 | `qa-tester/` | `04-qa-test-report.md` | 搭环境跑主流程，列 bug 分级 |
| 5 | `security-pentester/` | `05-security-pentest-report.md` | 授权门禁后多轮攻防，高危修完再攻 |

## 目录结构

```
.
├── product-manager/
│   ├── SKILL.md
│   ├── references/        # prd-template, prd-checklist
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
│   ├── references/       # bug-levels, test-case-design
│   └── scripts/check_qa.py
├── security-pentester/
│   ├── SKILL.md
│   ├── references/        # vuln-severity, attack-vectors
│   └── scripts/           # scan_danger.py, scan_security.py
├── validate_pipeline.py    # 全流水线一致性校验
├── USAGE.md                # 详细使用说明
├── LICENSE
└── .gitignore
```

## 快速开始

### 依赖

- Python ≥ 3.9
- 安全棒可选：`pip install "bandit==1.9.4"`（不装也能跑，只跑正则粗扫）

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

退出码：0 通过 / 1 HIGH 或致命缺失 / 4 有 MED / 3 路径错误 / 5 扫描工具故障。

### 改完 skill 后自检

```bash
python validate_pipeline.py
```

检查五棒 SKILL.md 结构、references 不悬空、scripts 存在、固定产物名声明。退出 0 = 全绿。

## 关键设计

- **固定文件名**：五棒产物 01-05 固定命名，不靠口头传文件。
- **门禁退回分类**：纯前置确认不产出文件；已接触产物不合格则写自己那份报告标 NO/退回/打回。
- **history/ 留档**：覆盖写前把上一版归档，r 取最大序号+1，归档即只读。
- **环境隔离**：功能测试和攻防测试跑在独立实例上，不互相污染。
- **独立发版**：改哪棒升哪棒的 version，不统一跟升。

详细规则见 [USAGE.md](USAGE.md)。

## License

[MIT](LICENSE)
