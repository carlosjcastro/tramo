import sys
import time
from pathlib import Path

from ollama import Client

from app.config import settings
from app.errors import AppError
from app.llm import OllamaLLM
from app.topics import SYSTEM_PROMPT, TopicList, unique_topics

DEFAULT_PROGRAM = Path(__file__).resolve().parents[1] / "samples" / "destino_programacion_1_unca.txt"


def attempt(think: bool | None, program: str) -> str:
    client = Client(host=settings.ollama_host, timeout=settings.request_timeout)
    llm = OllamaLLM(client, settings.model, settings.num_ctx, attempts=1, think=think)
    started = time.perf_counter()
    try:
        names = llm.ask(SYSTEM_PROMPT, f"<programa>\n{program}\n</programa>", TopicList).topics
    except AppError as error:
        return f"{time.perf_counter() - started:.1f}s fallo: {error.code}"
    return f"{time.perf_counter() - started:.1f}s {len(unique_topics(names))} temas"


def main(path: str) -> None:
    program = Path(path).read_text(encoding="utf-8")
    attempt(None, program)
    for think in (None, False):
        print(f"think={think}: {attempt(think, program)}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else str(DEFAULT_PROGRAM))
