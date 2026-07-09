import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List
from .chunker import Chunk


class DenseRetriever:
    def __init__(self, chunks: List[Chunk], model_name: str = "all-MiniLM-L6-v2"):
        self.chunks = chunks
        self.model = SentenceTransformer(model_name)
        texts = [c.text for c in chunks]
        self.embeddings = self.model.encode(texts, normalize_embeddings=True)

    def retrieve(self, query: str, top_k: int = 3) -> List[str]:
        q_emb = self.model.encode([query], normalize_embeddings=True)
        scores = (self.embeddings @ q_emb.T).squeeze()
        top_indices = np.argsort(scores)[::-1][:top_k]
        return [self.chunks[i].text for i in top_indices]
