import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    ollama_host: str = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    model: str = os.getenv("TRAMO_MODEL", "gemma4:e4b")
    num_ctx: int = int(os.getenv("TRAMO_NUM_CTX", "12288"))
    batch_size: int = int(os.getenv("TRAMO_BATCH_SIZE", "12"))
    request_timeout: float = float(os.getenv("TRAMO_REQUEST_TIMEOUT", "600"))
    partial_rule: float = float(os.getenv("TRAMO_PARTIAL_RULE", "0.5"))
    max_chars: int = int(os.getenv("TRAMO_MAX_CHARS", "20000"))
    max_file_bytes: int = int(os.getenv("TRAMO_MAX_FILE_BYTES", str(5 * 1048576)))


settings = Settings()
