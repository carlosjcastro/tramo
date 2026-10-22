from typing import Protocol

import numpy as np


class Embedder(Protocol):
    def embed(self, texts: list[str]) -> np.ndarray: ...


def normalize(vectors: np.ndarray) -> np.ndarray:
    return vectors / np.linalg.norm(vectors, axis=1, keepdims=True)


class OllamaEmbedder:
    def __init__(self, client, model: str, prefix: str) -> None:
        self._client = client
        self._model = model
        self._prefix = prefix

    def embed(self, texts: list[str]) -> np.ndarray:
        response = self._client.embed(model=self._model, input=[self._prefix + text for text in texts])
        return normalize(np.asarray(response.embeddings, dtype=np.float32))


class FastEmbedder:
    def __init__(self, model: str, prefix: str) -> None:
        from fastembed import TextEmbedding

        self._model = TextEmbedding(model)
        self._prefix = prefix

    def embed(self, texts: list[str]) -> np.ndarray:
        return normalize(np.asarray(list(self._model.embed([self._prefix + text for text in texts])), dtype=np.float32))
