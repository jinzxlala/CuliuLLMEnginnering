# agent_minimal

用于第 8-10 次课：最小 Agent（路由 + 工具 + 状态）。

## 能力

- 工具 1：`get_rules`（读取规则摘要）
- 工具 2：`evaluate_move`（本地规则校验）
- 路由：优先规则匹配，兜底调用 Ollama
- 可追踪：返回 `trace`（路由决策 + 工具调用 + LLM 汇总）

说明：

- 当前实现为 `工具执行 -> LLM 汇总回答`，便于课堂演示“工具与模型协作”。

## 运行

```bash
python app.py
```

服务地址：`http://127.0.0.1:5052`

## 环境变量

- `OLLAMA_BASE_URL`（默认 `http://127.0.0.1:11434`）
- `OLLAMA_MODEL`（默认 `qwen3.5:4b`）
- `OLLAMA_THINKING`（默认 `0`，即关闭 thinking；如需开启设为 `1`）
