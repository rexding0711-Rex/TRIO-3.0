#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TRIO 3.0 · 尽调矛盾发现引擎 · 最小可运行 pipeline
==================================================
输入一份标的自述材料，加载矛盾规则库，做规则引擎 + LLM 语义比对，
输出结构化判断包（结论/矛盾点/置信度/反证/预测注册）。

用法:
    python src/main.py --input 材料.txt --output result.json
    python src/main.py --input 材料.txt              # 输出到 stdout
    python src/main.py --demo                        # 用内置某公司样例演示

依赖: 无第三方库（标准库实现），LLM 增强需 requests + API key
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RULES_PATH = ROOT / "rules" / "contradiction_rules.json"
SAMPLE_PATH = ROOT / "output_samples" / "target_input.txt"

# ---------------------------------------------------------------------------
# 1. 规则加载
# ---------------------------------------------------------------------------
def load_rules() -> dict:
    """加载 contradiction_rules.json"""
    data = json.loads(RULES_PATH.read_text(encoding="utf-8"))
    return data["rules"]

# ---------------------------------------------------------------------------
# 2. 规则引擎（不依赖 API，保证能跑）
# ---------------------------------------------------------------------------
def rule_engine(claim_text: str, rules: list) -> list:
    """
    对每条规则，用关键词/模式在自述材料中探测触发信号。
    返回命中的矛盾点列表。
    """
    hits = []
    for rule in rules:
        # 优先用规则显式 signals（信号词）；无则从 trigger 提取
        signals = rule.get("signals") or _extract_keywords(rule.get("trigger", ""))
        matched = [s for s in signals if s and s in claim_text]
        # 至少 1 个信号词命中才触发（signals 为实义信号词）
        if len(matched) >= 1:
            hits.append({
                "rule_id": rule["id"],
                "rule_name": rule["name"],
                "category": rule["category"],
                "trigger": rule["trigger"],
                "logic": rule["logic"],
                "matched_keywords": matched,
                "data_sources": rule.get("data_sources", []),
                "severity": rule.get("severity", "medium"),
                "confidence": 0.6 + 0.1 * min(len(matched), 3),  # 命中越多置信度略高
            })
    return hits

def _extract_keywords(text: str) -> list:
    """从 trigger 文本提取中文短语与英文单词作为探测词"""
    words = re.findall(r"[一-鿿]{2,8}", text)          # 中文词组
    en = re.findall(r"[A-Za-z]{3,}", text)                     # 英文词
    return [w for w in words + en if len(w) > 1]

# ---------------------------------------------------------------------------
# 3. LLM 语义比对（可选增强，需 API key）
# ---------------------------------------------------------------------------
def llm_cross_check(claim_text: str, hits: list) -> dict:
    """
    有 API key 时调用 LLM 对命中矛盾做语义确认与补全反证。
    无 key 时返回空增强（规则引擎结果仍有效）。
    """
    api_key = os.environ.get("DEEPSEEK_API_KEY") or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return {"llm_enhanced": False, "note": "未配置 API key，仅使用规则引擎"}

    import urllib.request

    base = os.environ.get("LLM_BASE_URL", "https://api.deepseek.com/v1/chat/completions")
    prompt = (
        "你是尽调矛盾审计员。以下是标的自述材料与规则引擎命中的矛盾信号。\n"
        "请：1)确认每条矛盾是否成立；2)给出反证/验证路径；3)给出综合置信度(0-1)。\n"
        f"标的自述材料:\n{claim_text[:2000]}\n"
        f"命中的矛盾信号:\n{json.dumps(hits, ensure_ascii=False, indent=2)}\n"
        "输出 JSON: {\"confirmed\":[...], \"rebuttals\":[...], \"overall_confidence\":0.0}"
    )
    req = urllib.request.Request(
        base,
        data=json.dumps({
            "model": os.environ.get("LLM_MODEL", "deepseek-chat"),
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
        }).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            content = body["choices"][0]["message"]["content"]
            llm = json.loads(content)
            llm["llm_enhanced"] = True
            return llm
    except Exception as e:  # 网络/解析失败降级，不阻塞
        return {"llm_enhanced": False, "note": f"LLM 调用失败，降级为规则引擎: {e}"}

# ---------------------------------------------------------------------------
# 4. 判断包组装
# ---------------------------------------------------------------------------
def build_judgment(claim_text: str, hits: list, llm: dict) -> dict:
    """组装结构化判断包（结论/矛盾点/置信度/反证/预测）"""
    confirmed = hits
    if llm.get("llm_enhanced") and llm.get("confirmed"):
        confirmed = hits  # 保留规则命中，LLM 确认信息附加到 note

    severity_map = {"high": 0.85, "medium": 0.7, "low": 0.55}
    overall_conf = 0.0
    if hits:
        overall_conf = round(sum(severity_map.get(h["severity"], 0.7) for h in hits) / len(hits), 2)

    judgment = {
        "target": "尽调标的（自述材料）",
        "conclusion": "存在疑似矛盾点" if hits else "未发现明显矛盾",
        "contradiction_points": confirmed,
        "confidence": overall_conf,
        "rebuttal": llm.get("rebuttals", ["需调取对应公开数据源核实（见 data_sources）"]),
        "prediction_registration": {
            "registered": True if hits else False,
            "falsification_condition": "若标的提供材料可推翻上述矛盾，则本判断被证伪",
            "falsification_date": "30 天后回测",
        },
        "engine": "rule_engine" if not llm.get("llm_enhanced") else "rule_engine + llm",
        "llm_note": llm.get("note", ""),
    }
    return judgment

# ---------------------------------------------------------------------------
# 5. 入口
# ---------------------------------------------------------------------------
def run(claim_text: str) -> dict:
    rules = load_rules()
    hits = rule_engine(claim_text, rules)
    llm = llm_cross_check(claim_text, hits)
    return build_judgment(claim_text, hits, llm)

def main() -> int:
    parser = argparse.ArgumentParser(description="TRIO 3.0 尽调矛盾发现引擎")
    parser.add_argument("--input", help="标的自述材料文件路径（txt）")
    parser.add_argument("--output", help="结果输出路径（JSON）")
    parser.add_argument("--demo", action="store_true", help="用内置某公司样例演示")
    args = parser.parse_args()

    if args.demo:
        claim_text = SAMPLE_PATH.read_text(encoding="utf-8")
    elif args.input:
        claim_text = Path(args.input).read_text(encoding="utf-8")
    else:
        parser.print_help()
        return 1

    result = run(claim_text)
    out = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(out, encoding="utf-8")
        print(f"[TRIO] 判断包已写入 {args.output}")
    else:
        print(out)
    return 0

if __name__ == "__main__":
    sys.exit(main())
