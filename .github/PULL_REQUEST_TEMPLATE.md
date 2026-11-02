## 这个 PR 改了什么

<!-- 一句话说清，别写"优化了一些细节" -->

## 涉及哪一棒

- [ ] 仓库级（validate / CI / 文档）
- [ ] 单棒：______

## 契约检查

- [ ] 没有为了跑通而放宽校验脚本的判据
- [ ] 若改了退出码语义，已同步 `scripts/regression_test.py`
- [ ] 若改了产物文件名，已同步 `validate_pipeline.py`、`USAGE.md`、`pipeline-orchestrator/SKILL.md`
- [ ] 若改了 `references/`，版本号已升，`validate_pipeline.py` 通过

## 三连自检结果

```
python validate_pipeline.py          # 退出码：
python scripts/regression_test.py    # 通过 / 总数：
python scripts/smoke_pipeline.py     # 退出码：
```

## 对用户可见的变化

<!-- 会影响已有产物、命令或工作流的，写清怎么迁移 -->
