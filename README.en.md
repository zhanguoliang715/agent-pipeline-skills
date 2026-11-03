# Software Development Pipeline Skills

[简体中文](README.md) | **English**

**Ten Agent Skills that turn "build me this feature" into shippable software. Every baton must pass a script gate before handoff — missing sections exit non-zero.**

[![CI](https://github.com/zhanguoliang715/agent-pipeline-skills/actions/workflows/pipeline-ci.yml/badge.svg)](https://github.com/zhanguoliang715/agent-pipeline-skills/actions/workflows/pipeline-ci.yml)
![Python](https://img.shields.io/badge/python-3.9%2B-3776AB)
![Dependencies](https://img.shields.io/badge/pip%20install-0%20dependencies-2E7D32)
![License](https://img.shields.io/badge/license-MIT-yellow)
![skills](https://img.shields.io/badge/skills-10-2E7D32)
![regression](https://img.shields.io/badge/regression%20cases-78-1D9E75)
![spec](https://img.shields.io/badge/agentskills.io-spec%20valid-2E7D32)

## Install

```bash
npx skills add zhanguoliang715/agent-pipeline-skills
```

Installs all ten skills across Codex, Cursor, Amp, Antigravity, Claude Code and 20+ other agents in one command.

Or as a Claude Code plugin:

```bash
claude plugin marketplace add zhanguoliang715/agent-pipeline-skills
claude plugin install software-pipeline@agent-pipeline-skills
```

## The problem it solves

Making an AI produce a demo is easy. Making it produce something deliverable is not. The hard part is not the code — it is the handoffs:

- the PRD has no acceptance criteria, so development starts anyway and builds the wrong thing;
- design documents are missing, so the second feature requires a rewrite;
- nobody tests, and "should be fine" ships to production;
- security scanning is a checkbox nobody fixes;
- rejection notes live in chat history, so the next baton guesses.

This skill pack is crude but effective: **ten batons, nine fixed output filenames (`01-prd.md` … `09-security-pentest-report.md`), one validation script per baton, non-zero exit means the artifact does not flow downstream.** Handoff is enforced by files and exit codes, not by memory.

## The pipeline

| # | Skill | Output | Gate |
|---|---|---|---|
| 1 | `product-manager` | `01-prd.md` | confirm intent, max 3 rounds of questions |
| 2 | `requirement-reviewer` | `02-requirement-review.md` | verdict must be YES; max 2 rejections |
| 3 | `prototype-designer` | `03-prototype-design.md` | no wireframes without a YES |
| 4 | `ui-designer` | `04-ui-design/` | no hi-fi UI without an approved prototype |
| 5 | `database-designer` | `05-database-design.md` | no schema without a YES |
| 6 | `architecture-designer` | `06-architecture-design.md` | needs FR list + finalized schema |
| 7 | `software-developer` | `07-source/` + `07-api-docs.md` | needs all design docs |
| 8 | `qa-tester` | `08-qa-test-report.md` | cannot start from README = fatal bug |
| 9 | `security-pentester` | `09-security-pentest-report.md` | refuses external/public targets |
| 10 | `pipeline-orchestrator` | no artifact | schedules, rejects, escalates after 3 identical failures |

## Verify it yourself

```bash
git clone https://github.com/zhanguoliang715/agent-pipeline-skills.git
cd agent-pipeline-skills
python validate_pipeline.py          # structure & doc consistency
python scripts/regression_test.py    # exit-code contracts, 78 cases
python scripts/smoke_pipeline.py     # end-to-end gate chain
```

Three zero exit codes mean the repo is healthy. All assertions are machine-checked — nothing is hand-written prose.

## What it is not

- **Not a general-purpose skill pack.** It assumes a mid-size web project with frontend and backend. For algorithm libraries, data scripts, or embedded firmware, the architecture and security batons do not apply.
- **Not a code generator.** It constrains the process; you still write the business logic.
- **Not a business validator.** Baton 1 stops at "scope is clear", not at "this is worth building".

## Docs

- [Beginner handbooks](docs/新手手册/) — one per baton: how to use it, why it exists, what goes wrong.
- [Technical docs](docs/技术文档/) — one per baton: contracts, limits, trade-offs, failure modes.
- [USAGE.md](USAGE.md) — full rules and exit-code semantics.

## License

MIT.
