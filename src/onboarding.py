#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TRIO 3.0 · 一键尽调引导页（onboarding）
======================================
用户 clone 后运行 `python src/main.py`（无参数）即进入尽调流程。

交互引导语：
  输入你要尽调的企业情况与附件（粘贴文本或文件路径）
  → TRIO 交叉比对公开数据信号 → 输出判断包 → 可选注册预测回测
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

BANNER = """
╭──────────────────────────────────────────────────╮
│   TRIO 3.0 · 尽调矛盾发现引擎                    │
│   给你资料，我给可证伪的判断                      │
│   别的 AI 让你信它，TRIO 让你验它                │
╰──────────────────────────────────────────────────╯
"""

GUIDE = """
输入你要尽调的企业情况与附件——
  方式1：直接粘贴企业自述 / BP / 声称（一段文字）
  方式2：输入 .txt 文件路径（附件，UTF-8）
  输入 q 退出
"""


def _load_input(raw: str):
    """支持文件路径或直接文本"""
    for cand in [Path(raw), ROOT / raw]:
        if cand.exists() and cand.is_file():
            try:
                return cand.read_text(encoding="utf-8")
            except Exception:
                return None
    return None


def _show_result(result: dict):
    print(json.dumps(result, ensure_ascii=False, indent=2))


def _register_prediction(result: dict) -> None:
    """把本次判断注册为预测（30 天回测），追加到 predictions/registry.jsonl"""
    if not result.get("prediction_registration", {}).get("registered"):
        print("（本次未发现矛盾，无需注册预测）")
        return
    ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
    entry = {
        "id": f"ONBOARD-{ts[:10]}",
        "target": "用户提交的尽调标的（匿名）",
        "predicted_at": ts,
        "prediction": "high_risk" if result.get("confidence", 0) >= 0.6 else "watch",
        "confidence": result.get("confidence", 0),
        "falsification_date": "30 天后回测",
        "status": "pending",
        "outcome": None,
        "simulated": False,
        "note": "由一键尽调引导页注册；用户需在 VERIFICATION.md 规范下补充真实标的",
    }
    reg_path = ROOT / "predictions" / "registry.jsonl"
    with open(reg_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    print(f"✓ 预测已注册（{entry['id']}），30 天后回测验证")


def main() -> int:
    from main import run

    print(BANNER)
    print(GUIDE)
    while True:
        raw = input("> ").strip()
        if raw.lower() in ("q", "quit", "退出"):
            print("\n再见。用 TRIO 验证你的每个判断。\n")
            return 0
        if not raw:
            continue

        text = _load_input(raw)
        if text is None:
            text = raw  # 直接当文本处理

        print("\n[分析中] 交叉比对公开数据信号...\n")
        result = run(text)
        _show_result(result)

        if result.get("prediction_registration", {}).get("registered"):
            if input("\n是否注册预测（30 天回测验证判断）？(y/n): ").strip().lower() == "y":
                _register_prediction(result)

        print("\n" + "=" * 50)


if __name__ == "__main__":
    sys.exit(main())
