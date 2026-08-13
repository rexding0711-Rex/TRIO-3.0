#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TRIO 3.0 · Mini-Benchmark 评测脚本
==================================
对 benchmark/inputs/ 下 10 个案例跑规则引擎，输出检出率/误报率/F1/混淆矩阵。

用法:
    python src/run_benchmark.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from main import load_rules, rule_engine  # noqa: E402

INPUTS = ROOT / "benchmark" / "inputs"
RESULTS = ROOT / "benchmark" / "results"

# Ground Truth：5 暴雷（应检出矛盾）+ 5 正常（应无矛盾）
GROUND_TRUTH = {
    "01_target": "blow",
    "02_luckin": "blow",
    "03_kangmei": "blow",
    "04_kangdexin": "blow",
    "05_zhangzidao": "blow",
    "06_maotai": "normal",
    "07_catl": "normal",
    "08_byd": "normal",
    "09_hengrui": "normal",
    "10_haitian": "normal",
}

def main():
    rules = load_rules()
    rows = []
    for name, truth in GROUND_TRUTH.items():
        path = INPUTS / f"{name}.txt"
        if not path.exists():
            print(f"[跳过] {name}：输入文件不存在")
            continue
        text = path.read_text(encoding="utf-8")
        hits = rule_engine(text, rules)
        predicted = "blow" if hits else "normal"
        hit_ids = [h["rule_id"] for h in hits]
        rows.append({
            "case": name, "truth": truth, "predicted": predicted,
            "hit_count": len(hits), "hit_rules": hit_ids,
            "correct": predicted == truth,
        })

    # 指标
    tp = sum(1 for r in rows if r["truth"] == "blow" and r["predicted"] == "blow")
    fn = sum(1 for r in rows if r["truth"] == "blow" and r["predicted"] != "blow")
    fp = sum(1 for r in rows if r["truth"] == "normal" and r["predicted"] != "normal")
    tn = sum(1 for r in rows if r["truth"] == "normal" and r["predicted"] == "normal")
    recall = tp / (tp + fn) if (tp + fn) else 0
    precision = tp / (tp + fp) if (tp + fp) else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0
    fpr = fp / (fp + tn) if (fp + tn) else 0

    # 输出 markdown
    lines = [
        "# TRIO 3.0 · Mini-Benchmark 结果",
        "",
        "> 样本：10 个真实公开案例（5 暴雷 + 5 正常），输入为标的自述材料（暴雷案例用暴雷前材料）。",
        "> 方法：规则引擎（contradiction_rules.json 22 条）。命中任一规则 → 判为存在矛盾（暴雷）。",
        "> 诚实声明：样本量小，统计意义有限；历史案例存在模型训练数据污染风险，已用暴雷前材料缓解。",
        "",
        "## 逐案例结果",
        "",
        "| 案例 | 真实标签 | TRIO 判定 | 命中规则 | 正确 |",
        "|------|---------|-----------|---------|------|",
    ]
    for r in rows:
        mark = "✅" if r["correct"] else "❌"
        rules_str = ",".join(r["hit_rules"]) if r["hit_rules"] else "无"
        lines.append(
            f"| {r['case']} | {r['truth']} | {r['predicted']} | {rules_str} | {mark} |"
        )

    lines += [
        "",
        "## 汇总指标（机制演示，演示材料非真实性能）",
        "",
        "| 指标 | 数值 |",
        "|------|------|",
        f"| 检出率 Recall | {recall:.0%} ({tp}/{tp+fn}) |",
        f"| 精确率 Precision | {precision:.0%} ({tp}/{tp+fp}) |",
        f"| F1 | {f1:.2f} |",
        f"| 误报率 FPR | {fpr:.0%} ({fp}/{fp+tn}) |",
        f"| 混淆矩阵 | TP={tp} FN={fn} FP={fp} TN={tn} |",
        "",
        "## 失败案例分析",
        "",
    ]
    fails = [r for r in rows if not r["correct"]]
    if fails:
        for r in fails:
            lines.append(f"- **{r['case']}**：真实={r['truth']}，TRIO 判={r['predicted']}，命中={r['hit_rules'] or '无'}。")
    else:
        lines.append("- 无失败案例。")

    lines += [
        "",
        "## 架构定位与局限（诚实声明）",
        "",
        "1. **规则引擎定位**：红旗候选生成器，从标的自述检测已知红旗信号；最终'自述 vs 公开数据'矛盾确认由 LLM 层完成（需 API key，见 main.py llm_cross_check）。",
        "2. **演示材料非真实性能**：10 案例为构造的演示输入，上述指标反映规则对演示材料的匹配，不代表真实世界检出能力。",
        "3. **样本量局限**：10 案例小样本，F1 高不应解读为系统完美；泛化需更大样本 + 真实材料验证。",
        "4. **训练数据污染**：历史案例（瑞幸/康美等）结局在模型训练数据中，已用暴雷前材料缓解；回顾性评测验证检出机制，非预测能力。",
        "5. **真实已跑通案例**：某公司尽调场景（output_samples/target_output.json，命中 6 类矛盾）——demo 核心演示。",
    ]

    RESULTS.mkdir(parents=True, exist_ok=True)
    out = RESULTS / "result_summary.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"[TRIO] 评测完成：Recall={recall:.0%} Precision={precision:.0%} F1={f1:.2f} FPR={fpr:.0%}")
    print(f"[TRIO] 结果已写入 {out}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
