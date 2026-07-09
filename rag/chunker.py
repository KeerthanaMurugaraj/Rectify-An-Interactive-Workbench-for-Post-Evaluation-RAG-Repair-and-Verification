import json
from dataclasses import dataclass
from pathlib import Path
from typing import List


@dataclass
class Chunk:
    chunk_id: str
    doc_id: str
    title: str
    text: str


def load_and_chunk(corpus_path: str, chunk_size: int = 100, chunk_overlap: int = 20) -> List[Chunk]:
    chunks = []
    with open(corpus_path) as f:
        for line in f:
            doc = json.loads(line)
            text = doc["text"]
            words = text.split()
            step = max(1, chunk_size - chunk_overlap)
            if len(words) <= chunk_size:
                chunks.append(Chunk(
                    chunk_id=f"{doc['doc_id']}_c0",
                    doc_id=doc["doc_id"],
                    title=doc["title"],
                    text=text,
                ))
            else:
                for i, start in enumerate(range(0, len(words), step)):
                    segment = words[start: start + chunk_size]
                    chunks.append(Chunk(
                        chunk_id=f"{doc['doc_id']}_c{i}",
                        doc_id=doc["doc_id"],
                        title=doc["title"],
                        text=" ".join(segment),
                    ))
    return chunks
