#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TRIO 3.0 · 一键尽调引导页（onboarding v3）
==========================================
clone 后 `python src/main.py` 无参数即进入尽调流程。

修复（DeepSeek 审计 9005）：
  1. 多行粘贴：支持整段粘贴（空行回车结束），不再拆成逐行分析
  2. Windows 路径：反斜杠路径兼容（D:\\xx.txt / D:/xx.txt）
  3. LLM 增强提示：引导语告知配置 API key 自动启用
  4. 诚实性：不自动注册匿名预测（无公证无意义），改为提示真实注册规范
"""
import sys
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
  方式1：直接粘贴企业自述 / BP / 声称（可多行，粘贴完按 空行回车 结束）
  方式2：输入 .txt 文件路径（Windows 用 D:\\xx.txt 或 D:/xx.txt 均可）
  方式3：输入 q 退出

（提示：配置 DEEPSEEK_API_KEY 后，自动启用 LLM 语义增强）
"""


def _is_quit(raw: str) -> bool:
    return raw.lower() in ("q", "quit", "退出")


def _read_file_text(raw: str):
    """解析路径（兼容 Windows 反斜杠），存在则返回文件内容"""
    norm = raw.replace("\\", "/")
    for cand in [Path(norm), ROOT / norm]:
        if cand.exists() and cand.is_file():
            try:
                return cand.read_text(encoding="utf-8")
            except Exception:
                return None
    return None


def _read_material():
    """
    读取尽调材料：
      - 首行若是有效文件路径 → 读文件
      - 否则按多行粘贴收集，直到空行
    返回 (material, is_quit)
    """
    try:
        first = input("> ").rstrip("\n").strip()
    except (EOFError, KeyboardInterrupt):
        return None, True

    if not first:
        return None, False
    if _is_quit(first):
        return None, True

    # 尝试文件路径（兼容反斜杠）
    file_text = _read_file_text(first)
    if file_text is not None:
        return file_text, False

    # 非路径 → 多行粘贴收集（空行结束）
    lines = [first]
    print("  （继续粘贴，空行回车结束）")
    while True:
        try:
            more = input().rstrip("\n")
        except (EOFError, KeyboardInterrupt):
            break
        if more.strip() == "":
            break
        lines.append(more)
    return "\n".join(lines), False


def main() -> int:
    from main import run

    print(BANNER)
    print(GUIDE)
    while True:
        print()
        material, quit = _read_material()
        if quit:
            print("\n再见。用 TRIO 验证你的每个判断。\n")
            return 0
        if not material or not material.strip():
            print("（输入为空——请粘贴企业情况，或输入 .txt 文件路径）")
            continue

        print("\n[分析中] 交叉比对公开数据信号...\n")
        result = run(material)
        print(__import__("json").dumps(result, ensure_ascii=False, indent=2))

        if result.get("prediction_registration", {}).get("registered"):
            print(
                "\n（提示：demo 不自动注册匿名预测。真实预测注册需真实标的 + git 公证，"
                "见 predictions/VERIFICATION.md——否则 30 天回测无从验证）"
            )
        print("\n" + "=" * 50)


if __name__ == "__main__":
    sys.exit(main())
