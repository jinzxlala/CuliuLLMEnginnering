# 01_base_repo 教学基线实现

本目录提供课程前 11 次课可直接运行的四个最小工程模块与一个统一演示门户：

- `prompt_examples/`：Prompt 结构化输出与 A/B 测试基线
- `rag_minimal/`：最小 RAG（文档切分、检索、引用、评测）
- `agent_minimal/`：最小 Agent（任务路由、工具调用、执行追踪）
- `safety_logging/`：安全防护与运行日志（黑白名单、错误码、指标）
- `teaching_portal/`：统一课堂演示入口（网页一站式演示四个模块）

## 统一模型与环境

- LLM 服务：本地 Ollama
- 课程统一模型：`qwen3.5:4b`
- 默认地址：`http://127.0.0.1:11434`

## 快速开始

```bash
pip install flask requests
```

每个子目录都有独立 `README.md`，可单独运行。

统一入口演示可直接运行：

```bash
cd teaching_portal
python app.py
```
