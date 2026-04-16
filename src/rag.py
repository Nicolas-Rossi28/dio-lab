from __future__ import annotations
import random
from typing import List, Dict
from datasets import load_dataset
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

DATASET_NAME = "Josephgflowers/Finance-Instruct-500k"
SAMPLE_SIZE = 5_000


class FinanceRAG:

    def __init__(self):
        self.docs: List[Dict] = []
        self.vectorizer = None
        self.matrix = None

    def load_dataset(self, sample: int = SAMPLE_SIZE) -> None:
        print(f"[RAG] Carregando {DATASET_NAME} ...")
        ds = load_dataset(DATASET_NAME, split="train", streaming=False)

        indices = random.sample(range(len(ds)), min(sample, len(ds)))
        subset = ds.select(indices)

        # Colunas reais do dataset: 'system', 'user', 'assistant'
        self.docs = [
            {
                "instruction": str(row.get("user", "") or "").strip(),
                "output":      str(row.get("assistant", "") or "").strip(),
            }
            for row in subset
        ]

        # Remove documentos vazios
        self.docs = [d for d in self.docs if d["instruction"]]

        corpus = [d["instruction"] for d in self.docs]
        print(f"[RAG] Documentos válidos: {len(corpus)}")

        self.vectorizer = TfidfVectorizer(
            max_features=20_000,
            ngram_range=(1, 2),
            stop_words="english",
        )
        self.matrix = self.vectorizer.fit_transform(corpus)
        print(f"[RAG] Índice pronto: {len(self.docs)} documentos.")

    def search(self, query: str, k: int = 3) -> List[Dict]:
        if self.vectorizer is None or self.matrix is None:
            return []
        q_vec = self.vectorizer.transform([query])
        scores = cosine_similarity(q_vec, self.matrix).flatten()
        top_k = np.argsort(scores)[::-1][:k]
        return [self.docs[i] for i in top_k if scores[i] > 0.01]
