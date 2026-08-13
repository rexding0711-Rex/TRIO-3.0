#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TRIO 3.0 · 交互式引导页（onboarding）
======================================
用户 clone 后运行 `python src/main.py`（无参数）即进入本引导。

引导流程：演示 → 自定义分析 → 评测复现 → LLM 配置 → 使用指南
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

BANNER = """
╭─────────────────────────────────────────────╮
│   TRIO 3.0 · 尽调矛盾发现引擎               │
│   别的 AI 让你信它，TRIO 让你验它            │
│   每个判断都有案底，案底可被审判              │
╰─────────────────────────────────────────────╯
"""


def pause():
    input("\n按回车返回菜单...")


def run_demo():
    from main import run
    text = (ROOT / "output_samples" / "target_input.txt").read_text(encoding="utf-8")
    print("\n[演示] 分析某公司自述材料（命中 6 类矛盾）...\n")
    result = run(text)
    print(json.dumps(result, ensure_ascii=False, indent=2)[:1500])
    print("\n（完整输出见 output_samples/target_output.json）")
    pause()


def analyze_custom():
    from main import run
    path = input("\n请输入尽调材料文件路径（txt，UTF-8）: ").strip()
    p = Path(path)
    if not p.exists():
        p = ROOT / path
    if not p.exists():
        print(f"\n找不到文件: {path}")
        pause()
        return
    text = p.read_text(encoding="utf-8")
    print("\n[分析中] 规则引擎交叉比对...\n")
    result = run(text)
    out = input("保存结果到文件？(y/n，默认 n): ").strip().lower()
    if out == "y":
        save = Path("result.json")
        save.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"✓ 已保存到 {save}")
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    pause()


def run_benchmark():
    print("\n[评测] 复现 10 案例评测...\n")
    subprocess.run([sys.executable, str(ROOT / "src" / "run_benchmark.py")])
    pause()


def llm_config():
    print("""
[LLM 语义增强配置]（可选，规则引擎无需此步）

1. 安装依赖:   pip install -r requirements.txt
2. 设置 key:   export DEEPSEEK_API_KEY=你的key
3. 运行:       python src/main.py --input 材料.txt
                （有 key 时自动启用 LLM 交叉验证）

配置项（环境变量）:
  DEEPSEEK_API_KEY   必需
  LLM_BASE_URL       默认 https://api.deepseek.com/v1/chat/completions
  LLM_MODEL          默认 deepseek-chat

Windows PowerShell 用 $env:DEEPSEEK_API_KEY="你的key"
""")
    pause()


def show_guide():
    print("\n[使用指南] 完整说明见 docs/USAGE.md，要点：\n")
    print("  python src/main.py --demo           # 跑演示")
    print("  python src/main.py --input 材料.txt  # 自定义分析")
    print("  python src/main.py --output 结果.json # 保存结果")
    print("  python src/run_benchmark.py          # 复现评测")
    pause()


MENU = """
请选择操作：
  [1] 跑演示案例（某公司，命中 6 类矛盾）
  [2] 分析我的尽调材料
  [3] 复现 10 案例评测
  [4] 配置 LLM 语义增强（可选）
  [5] 查看使用指南
  [0] 退出
你的选择: """


def main() -> int:
    print(BANNER)
    while True:
        choice = input(MENU).strip()
        if choice == "1":
            run_demo()
        elif choice == "2":
            analyze_custom()
        elif choice == "3":
            run_benchmark()
        elif choice == "4":
            llm_config()
        elif choice == "5":
            show_guide()
        elif choice == "0":
            print("\n再见。用 TRIO 验证你的每个判断。\n")
            return 0
        else:
            print("无效选择，请重试。")


if __name__ == "__main__":
    sys.exit(main())
