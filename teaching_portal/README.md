# teaching_portal

统一课堂演示入口（单服务 + 单网页），整合四个教学模块：

- Prompt A/B
- RAG
- Agent
- Safety

## 启动

```bash
python app.py
```

访问：`http://127.0.0.1:5050`

## 环境变量

- `OLLAMA_BASE_URL`（默认 `http://127.0.0.1:11434`）
- `OLLAMA_MODEL`（默认 `qwen3.5:4b`）
- `OLLAMA_THINKING`（默认 `0`，即关闭 thinking；如需开启设为 `1`）
