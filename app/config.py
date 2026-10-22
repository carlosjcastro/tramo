import os
from dataclasses import dataclass


def env_flag(name: str, default: bool) -> bool:
    value = os.getenv(name, "").strip().lower()
    return {"true": True, "false": False}.get(value, default)


def env_list(name: str, default: str) -> tuple[str, ...]:
    return tuple(item.strip() for item in os.getenv(name, default).split(",") if item.strip())


@dataclass(frozen=True)
class Settings:
    ollama_host: str = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    model: str = os.getenv("TRAMO_MODEL", "gemma4:e4b")
    think: bool = env_flag("TRAMO_THINK", False)
    num_ctx: int = int(os.getenv("TRAMO_NUM_CTX", "12288"))
    batch_size: int = int(os.getenv("TRAMO_BATCH_SIZE", "12"))
    request_timeout: float = float(os.getenv("TRAMO_REQUEST_TIMEOUT", "600"))
    partial_rule: float = float(os.getenv("TRAMO_PARTIAL_RULE", "0.5"))
    max_chars: int = int(os.getenv("TRAMO_MAX_CHARS", "20000"))
    max_file_bytes: int = int(os.getenv("TRAMO_MAX_FILE_BYTES", str(5 * 1048576)))
    max_json_bytes: int = int(os.getenv("TRAMO_MAX_JSON_BYTES", "524288"))
    max_pages: int = int(os.getenv("TRAMO_MAX_PAGES", "100"))
    max_unzipped_bytes: int = int(os.getenv("TRAMO_MAX_UNZIPPED_BYTES", str(30 * 1048576)))
    allowed_hosts: tuple[str, ...] = env_list("TRAMO_ALLOWED_HOSTS", "localhost,127.0.0.1")
    trust_proxy: bool = os.getenv("TRAMO_TRUST_PROXY", "false").lower() == "true"
    analyze_limit: int = int(os.getenv("TRAMO_ANALYZE_LIMIT", "3"))
    analyze_window: int = int(os.getenv("TRAMO_ANALYZE_WINDOW", "600"))
    extract_limit: int = int(os.getenv("TRAMO_EXTRACT_LIMIT", "20"))
    general_limit: int = int(os.getenv("TRAMO_GENERAL_LIMIT", "120"))
    general_window: int = int(os.getenv("TRAMO_GENERAL_WINDOW", "60"))
    max_concurrent_analyses: int = int(os.getenv("TRAMO_MAX_CONCURRENT_ANALYSES", "1"))


settings = Settings()
