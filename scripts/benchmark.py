import time

from ollama import Client
from pydantic import BaseModel

from app.config import settings
from app.errors import AppError
from app.llm import OllamaLLM

SYSTEM = "Extraé los temas de contenido del programa. Devolvé solo los temas."
PROGRAM = "Variables y tipos de datos. Estructuras de control. Arreglos. Funciones y procedimientos."


class Topics(BaseModel):
    topics: list[str]


def attempt(think: bool | None) -> str:
    client = Client(host=settings.ollama_host, timeout=settings.request_timeout)
    llm = OllamaLLM(client, settings.model, settings.num_ctx, attempts=1, think=think)
    started = time.perf_counter()
    try:
        topics = llm.ask(SYSTEM, PROGRAM, Topics).topics
    except AppError as error:
        return f"{time.perf_counter() - started:.1f}s fallo: {error.code}"
    return f"{time.perf_counter() - started:.1f}s {len(topics)} temas {topics}"


def main() -> None:
    attempt(None)
    for think in (None, False):
        print(f"think={think}: {attempt(think)}")


if __name__ == "__main__":
    main()
