import os
import re
from dataclasses import dataclass
from typing import List, Tuple

from ollama_client import chat

@dataclass
class Chunk:
    chunk_id: str
    source: str
    text: str


def _tokenize(text: str) -> List[str]:
    return re.findall(r"[a-zA-Z0-9\u4e00-\u9fff]+", text.lower())


class MinimalRAG:
    def __init__(self, data_dir: str = "data", chunk_size: int = 120):
        self.data_dir = data_dir
        self.chunk_size = chunk_size
        self.chunks: List[Chunk] = []

    def build(self) -> None:
        self.chunks.clear()
        for name in os.listdir(self.data_dir):
            if not name.endswith(".md"):
                continue
            path = os.path.join(self.data_dir, name)
            with open(path, "r", encoding="utf-8") as f:
                text = f.read().strip()
            parts = [p.strip() for p in text.split("\n") if p.strip()]
            for idx, part in enumerate(parts):
                self.chunks.append(
                    Chunk(chunk_id=f"{name}#{idx+1}", source=name, text=part[: self.chunk_size])
                )

    def retrieve(self, query: str, top_k: int = 3) -> List[Chunk]:
        q_tokens = set(_tokenize(query))
        scored: List[Tuple[int, Chunk]] = []
        for chunk in self.chunks:
            c_tokens = set(_tokenize(chunk.text))
            overlap = len(q_tokens & c_tokens)
            if query.strip() and query.strip() in chunk.text:
                overlap += 3
            for tok in q_tokens:
                if tok and tok in chunk.text:
                    overlap += 1
            if overlap > 0:
                scored.append((overlap, chunk))
        scored.sort(key=lambda x: x[0], reverse=True)
        if not scored:
            return self.chunks[:top_k]
        return [c for _, c in scored[:top_k]]

    def answer(self, query: str, top_k: int = 3, use_llm: bool = True) -> dict:
        refs = self.retrieve(query, top_k=top_k)
        if not refs:
            return {"answer": "未检索到相关证据。", "citations": []}
        citations = [c.chunk_id for c in refs]
        if not use_llm:
            summary = "；".join([c.text for c in refs])
            return {"answer": f"基于检索证据：{summary}", "citations": citations}

        context = "\n".join([f"[{c.chunk_id}] {c.text}" for c in refs])
        prompt = (
            f"用户问题: {query}\n\n"
            f"可用证据:\n{context}\n\n"
            "请只基于给定证据回答，最后附上你引用的 chunk_id 列表。"
        )
        answer = chat(
            "你是严谨的RAG回答助手。禁止编造证据，若证据不足请明确说明。",
            prompt,
        )
        return {"answer": answer, "citations": citations}
