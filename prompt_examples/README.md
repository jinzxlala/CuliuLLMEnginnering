# prompt_examples

用于第 2-3 次课：把需求变成结构化输出，并做最小 A/B Prompt 测试。

## 运行

```bash
python run_prompt_lab.py --task "解释为什么同一行数字不能重复"
python run_prompt_lab.py --batch fixtures/tasks.jsonl
```

## 输出

- 单任务模式：终端打印 A/B 结果
- 批量模式：生成 `reports/prompt_ab_results.jsonl`

## 配置

- `OLLAMA_BASE_URL`（默认 `http://127.0.0.1:11434`）
- `OLLAMA_MODEL`（默认 `qwen3.5:4b`）
- `OLLAMA_THINKING`（默认 `0`，即关闭 thinking；如需开启设为 `1`）
