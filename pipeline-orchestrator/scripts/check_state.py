#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""流水线状态与回路守卫（整套部署用，orchestrator 在每棒开工前调用）。

解决三件事：
  1. 状态外置——轮次/重试/打回计数写在文件里，换会话、上下文压缩都不丢；
  2. 死循环检测——同一「产物::失败项」反复失败到上限，直接判定为打转，
     返回停止信号，不再让 Agent 继续重试烧 token；
  3. 全局预算——整条流水线的总返工/总打回/攻防轮次有上限，超了就停。

用法：
    python scripts/check_state.py "<WORKDIR>/pipeline-state.json"

退出码（本脚本自成一格，不与八棒 check 的 0/1/2/3 混用）：
    0 = 状态正常，可以继续
    1 = 状态文件缺失 / JSON 非法 / 缺必填字段（结构问题，先修状态）
    2 = 停止信号：命中死循环或超出全局预算（必须交用户裁决，禁止继续重试）
    3 = 路径不存在
    4 = 用法错误（缺参）
"""
import json
import sys
from pathlib import Path

REQUIRED_TOP = ["run_id", "current_stage", "stages", "counters", "budget"]
REQUIRED_COUNTERS = ["total_reworks", "total_rejects", "pentest_rounds"]
DEFAULT_BUDGET = {
    "max_retries_per_artifact": 3,
    "max_total_reworks": 12,
    "max_total_rejects": 6,
    "max_pentest_rounds": 3,
}


def main():
    if len(sys.argv) < 2:
        print("用法: check_state.py <pipeline-state.json>", file=sys.stderr)
        sys.exit(4)
    p = Path(sys.argv[1])
    if not p.is_file():
        print(f"错误: 状态文件不存在: {p}", file=sys.stderr)
        print("提示: 按仓库根 pipeline-state.template.json 创建后再跑", file=sys.stderr)
        sys.exit(3)

    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"FAIL 状态文件不是合法 JSON: {e}", file=sys.stderr)
        sys.exit(1)
    if not isinstance(data, dict):
        print("FAIL 状态文件顶层必须是对象", file=sys.stderr)
        sys.exit(1)

    missing = [k for k in REQUIRED_TOP if k not in data]
    if missing:
        print(f"FAIL 状态文件缺必填字段: {missing}", file=sys.stderr)
        sys.exit(1)

    counters = data.get("counters") or {}
    cm = [k for k in REQUIRED_COUNTERS if k not in counters]
    if cm:
        print(f"FAIL counters 缺字段: {cm}", file=sys.stderr)
        sys.exit(1)

    for k in REQUIRED_COUNTERS:
        v = counters.get(k)
        if not isinstance(v, int) or isinstance(v, bool) or v < 0:
            print(f"FAIL counters.{k} 必须是非负整数，当前: {v!r}", file=sys.stderr)
            sys.exit(1)

    budget = dict(DEFAULT_BUDGET)
    budget.update({k: v for k, v in (data.get("budget") or {}).items() if isinstance(v, int)})

    print(f"状态检查: {p}")
    print(f"  run={data.get('run_id')} 当前棒={data.get('current_stage')}")
    print(f"  计数: 返工={counters['total_reworks']} 打回={counters['total_rejects']} "
          f"攻防轮次={counters['pentest_rounds']}")

    # 1) 死循环检测：同一「产物::失败项」重试到上限
    guard = data.get("loop_guard") or {}
    loops = []
    for key, times in guard.items():
        if isinstance(times, int) and times >= budget["max_retries_per_artifact"]:
            loops.append((key, times))
    if loops:
        print("  STOP 检测到打转（同一失败项反复重试到上限）：")
        for key, times in loops:
            print(f"    - {key} 已重试 {times} 次（上限 {budget['max_retries_per_artifact']}）")
        print("  处置: 停止重试，出《门禁阻塞报告》交用户裁决，禁止第 N+1 次重试")
        sys.exit(2)

    # 2) 全局预算
    over = []
    if counters["total_reworks"] >= budget["max_total_reworks"]:
        over.append(f"总返工 {counters['total_reworks']} >= 上限 {budget['max_total_reworks']}")
    if counters["total_rejects"] >= budget["max_total_rejects"]:
        over.append(f"总打回 {counters['total_rejects']} >= 上限 {budget['max_total_rejects']}")
    if counters["pentest_rounds"] >= budget["max_pentest_rounds"]:
        over.append(f"攻防轮次 {counters['pentest_rounds']} >= 上限 {budget['max_pentest_rounds']}")
    if over:
        print("  STOP 超出全局预算：")
        for o in over:
            print(f"    - {o}")
        print("  处置: 停止流水线，向用户汇总已完成的棒与阻塞点，由用户决定放行/重开/终止")
        sys.exit(2)

    # 3) 已通过棒的产物必须还在（防止产物被删/被回退导致下游无输入）
    stages = data.get("stages") or {}
    lost = []
    for name, st in stages.items():
        if not isinstance(st, dict):
            continue
        if st.get("status") == "passed":
            art = st.get("artifact")
            if art:
                ap = p.parent / art
                if not ap.exists():
                    lost.append(art)
    if lost:
        print(f"  FAIL 已通过的产物缺失（可能被删除或回退）: {lost}", file=sys.stderr)
        sys.exit(1)

    # 归档提醒（不阻塞）：改过的产物应该留下 history 归档
    hist = p.parent / "history"
    if hist.is_dir():
        staged = [st.get("artifact") for st in stages.values()
                   if isinstance(st, dict) and st.get("artifact")]
        for art in staged:
            st = next((v for v in stages.values()
                       if isinstance(v, dict) and v.get("artifact") == art), {})
            if int(st.get("retries", 0) or 0) <= 0:
                continue
            stem = art.split(".")[0]
            if not any(stem in f.name for f in hist.iterdir()):
                print(f"  note {art} 已重试 {st.get('retries')} 次，"
                      "但 history/ 下没有它的归档（覆盖写前应先归档）")

    print("  通过: 状态完整、无打转、预算内、已通过产物齐全")
    sys.exit(0)


if __name__ == "__main__":
    main()
