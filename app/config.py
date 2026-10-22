import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    embedding_backend: str = os.getenv("TRAMO_EMBEDDING_BACKEND", "fastembed")
    embedding_model: str = os.getenv("TRAMO_EMBEDDING_MODEL", "sentence-transformers/paraphrase-multilingual-mpnet-base-v2")
    embedding_prefix: str = os.getenv("TRAMO_EMBEDDING_PREFIX", "")
    ollama_host: str = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    covered_threshold: float = float(os.getenv("TRAMO_COVERED_THRESHOLD", "0.65"))
    partial_threshold: float = float(os.getenv("TRAMO_PARTIAL_THRESHOLD", "0.5"))
    partial_rule: float = float(os.getenv("TRAMO_PARTIAL_RULE", "0.5"))
    max_chars: int = int(os.getenv("TRAMO_MAX_CHARS", "8000"))


settings = Settings()
