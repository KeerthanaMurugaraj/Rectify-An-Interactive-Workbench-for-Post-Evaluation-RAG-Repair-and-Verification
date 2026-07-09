from rank_bm25 import BM25Okapi
from typing import List
from .chunker import Chunk


class BM25Retriever:
    def __init__(self, chunks: List[Chunk]):
        self.chunks = chunks
        tokenized = [c.text.lower().split() for c in chunks]
        self.index = BM25Okapi(tokenized)

    def retrieve(self, query: str, top_k: int = 3) -> List[str]:
        tokens = query.lower().split()
        scores = self.index.get_scores(tokens)
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
        return [self.chunks[i].text for i in top_indices]
