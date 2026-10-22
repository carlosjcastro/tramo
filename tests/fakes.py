import numpy as np


class KeywordEmbedder:
    def __init__(self, vocabulary: list[str]) -> None:
        self._vocabulary = vocabulary

    def embed(self, texts: list[str]) -> np.ndarray:
        vectors = np.array([[float(word in text.lower()) for word in self._vocabulary] for text in texts]) + 1e-6
        return vectors / np.linalg.norm(vectors, axis=1, keepdims=True)
