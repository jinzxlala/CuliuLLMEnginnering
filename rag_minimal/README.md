# rag_minimal

用于第 4-7 次课：最小 RAG 实现（切分、检索、引用、评测）。

## 文件

- `rag_engine.py`：纯 Python 检索引擎（无向量库依赖）
- `app.py`：Flask API，提供 `/api/rag/ask`
- `run_eval.py`：基于 fixtures 的最小评测

说明：

- `/api/rag/ask` 默认走 `检索 -> LLM 生成答案`。
- `run_eval.py` 为了稳定可重复，默认使用非 LLM 模式评测（抽取式答案）。

## 运行

```bash
python app.py
python run_eval.py
```

默认读取 `data/` 目录的 `.md` 文档。
