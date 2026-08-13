# TRIO 3.0 · 使用指南

> 面向第三方用户/评审：从 clone 到跑通，再到深度使用。
> 核心：规则引擎零依赖可跑，LLM 增强可选。

---

## 环境要求

- Python 3.8+（规则引擎仅用标准库，无第三方依赖）
- 可选：API key（DeepSeek/OpenAI）用于 LLM 语义增强
- 无需数据库、无需 GPU

## 快速开始（2 分钟）

```bash
# 1. 获取
git clone https://github.com/rexding0711-Rex/TRIO-3.0.git
cd TRIO-3.0

# 2. 一键体验（推荐）：进入交互引导页
python src/main.py
# → 引导你输入企业情况/附件，直接开始尽调

# 3. 或直接指定模式：
python src/main.py --demo                        # 跑内置演示（命中 6 类矛盾）
python src/main.py --input 材料.txt --output result.json   # 自定义材料
# → 得到判断包 JSON：结论 / 矛盾点 / 置信度 / 预测注册
```

**不需要 `pip install` 就能跑规则引擎**——它是标准库实现。

## 完整使用

### 1. 规则引擎（无 API key）

```bash
python src/main.py --input 材料.txt          # 输出到终端
python src/main.py --input 材料.txt --output result.json   # 保存到文件
```

输入：标的自述材料（txt，任意格式，含公司声称/业务描述）。
输出：结构化判断包——

```json
{
  "conclusion": "存在疑似矛盾点",
  "contradiction_points": [{ "rule_id": "R-011", "rule_name": "实控人-限高失信", "severity": "high" }],
  "confidence": 0.77,
  "rebuttal": ["需调取对应公开数据源核实"],
  "prediction_registration": { "falsification_date": "30 天后回测" }
}
```

### 2. LLM 语义增强（可选，需 API key）

```bash
pip install -r requirements.txt              # 只需 requests
export DEEPSEEK_API_KEY=你的key
python src/main.py --input 材料.txt           # 自动启用 LLM 交叉验证
```

配置项（环境变量）：

| 变量 | 默认 | 说明 |
|------|------|------|
| `DEEPSEEK_API_KEY` | 无 | 启用 LLM 增强 |
| `LLM_BASE_URL` | `https://api.deepseek.com/v1/chat/completions` | OpenAI 兼容端点 |
| `LLM_MODEL` | `deepseek-chat` | 模型名 |

### 3. 复现评测

```bash
python src/run_benchmark.py
# → 输出 10 案例评测结果至 benchmark/results/result_summary.md
```

### 4. 扩展规则库

`rules/contradiction_rules.json` 每条规则含：`id` / `category` / `trigger` / `logic` / `signals`（信号词）/ `data_sources` / `severity`。

新增规则只需追加一个条目，例如：

```json
{
  "id": "R-023",
  "name": "关联交易-披露缺失",
  "category": "财务",
  "trigger": "声称无重大关联交易，但公开数据显示存在大额关联方往来",
  "logic": "关联交易未披露，可能存在利益输送",
  "signals": ["关联交易", "关联方"],
  "data_sources": ["年报关联交易披露", "工商关联方信息"],
  "severity": "high"
}
```

## 跨平台

| 平台 | 命令 | 说明 |
|------|------|------|
| Linux/macOS | `python3 src/main.py --demo` | 标准 |
| Windows | `py src/main.py --demo` | 或 `python` |
| 任何 | `python src/main.py --demo` | 规则引擎跨平台 |

## 常见问题

**Q: 没有 API key 能跑吗？**
能。规则引擎零依赖运行，LLM 增强只是可选层。无 key 时输出会标注"仅使用规则引擎"。

**Q: 输入文件编码？**
UTF-8 文本。Windows 记事本另存时选 UTF-8。

**Q: 判断包的置信度是什么？**
规则命中强度（0.6-0.85），非校准后概率。真实概率校准需预测注册回填（见 `calibration/`）。

**Q: 这是生产系统吗？**
不是。demo 级开源资产，规则引擎定位是红旗候选生成，最终矛盾确认需 LLM 层 + 人工复核（见 README 状态声明）。

## 目录结构

```
TRIO-3.0/
├── src/              # main.py（pipeline）+ run_benchmark.py（评测）
├── rules/            # 22 条矛盾发现规则（MIT）
├── benchmark/        # 评测案例 + 诚实结果
├── predictions/      # 预测注册表 + git 公证机制
├── calibration/      # 校准曲线 + 说明
├── compliance/       # 数据来源 / 隐私 / 边界
├── docs/             # 方案 / 技术文档 / 本指南
├── output_samples/   # 某公司案例完整输出
├── index.html        # Demo 展示页
└── LICENSE           # MIT
```
