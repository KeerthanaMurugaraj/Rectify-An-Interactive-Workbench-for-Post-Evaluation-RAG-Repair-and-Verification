from typing import List
from .chunker import Chunk
from .bm25_retriever import BM25Retriever
from .dense_retriever import DenseRetriever


def _reciprocal_rank_fusion(rankings: list[list[int]], k: int = 60) -> list[int]:
    scores: dict[int, float] = {}
    for ranking in rankings:
        for rank, idx in enumerate(ranking):
            scores[idx] = scores.get(idx, 0.0) + 1.0 / (k + rank + 1)
    return sorted(scores, key=lambda i: scores[i], reverse=True)


class HybridRetriever:
    def __init__(self, chunks: List[Chunk]):
        self.chunks = chunks
        self.bm25 = BM25Retriever(chunks)
        self.dense = DenseRetriever(chunks)

    def retrieve(self, query: str, top_k: int = 3) -> List[str]:
        n = len(self.chunks)

        bm25_tokens = query.lower().split()
        bm25_scores = self.bm25.index.get_scores(bm25_tokens)
        bm25_ranking = sorted(range(n), key=lambda i: bm25_scores[i], reverse=True)

        import numpy as np
        q_emb = self.dense.model.encode([query], normalize_embeddings=True)
        dense_scores = (self.dense.embeddings @ q_emb.T).squeeze()
        dense_ranking = list(map(int, np.argsort(dense_scores)[::-1]))

        fused = _reciprocal_rank_fusion([bm25_ranking, dense_ranking])
        return [self.chunks[i].text for i in fused[:top_k]]
