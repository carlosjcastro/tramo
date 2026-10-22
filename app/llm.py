import logging
from typing import Callable, Protocol, TypeVar

import httpx
from ollama import Client, ResponseError
from pydantic import BaseModel

from app.errors import AppError

logger = logging.getLogger("tramo")
INVALID_OUTPUT = "ai_invalid_output"
T = TypeVar("T", bound=BaseModel)


class LLMError(AppError):
    pass


class StructuredLLM(Protocol):
    model: str

    def ask(self, system: str, user: str, schema: type[T], check: Callable[[T], None] | None = None) -> T: ...

    def is_ready(self) -> bool: ...


class OllamaLLM:
    def __init__(self, client: Client, model: str, num_ctx: int, attempts: int = 2, think: bool | None = None) -> None:
        self.model = model
        self._client = client
        self._num_ctx = num_ctx
        self._attempts = attempts
        self._extra = {} if think is None else {"think": think}

    def ask(self, system: str, user: str, schema: type[T], check: Callable[[T], None] | None = None) -> T:
        for _ in range(self._attempts):
            try:
                return self._attempt(system, user, schema, check)
            except ValueError as error:
                logger.warning("Invalid model output: %s", error)
            except ResponseError as error:
                raise self._response_failure(error) from error
            except (ConnectionError, httpx.TransportError) as error:
                raise LLMError("ai_unavailable", "Ollama no responde. Abrilo y comprobá que esté en ejecución.", 503) from error
        raise LLMError(INVALID_OUTPUT, "La IA devolvió una respuesta inválida. Intentá de nuevo.", 502)

    def is_ready(self) -> bool:
        try:
            installed = {item.model for item in self._client.list().models}
        except (ConnectionError, httpx.TransportError, ResponseError):
            return False
        return self.model in installed or f"{self.model}:latest" in installed

    def _attempt(self, system: str, user: str, schema: type[T], check: Callable[[T], None] | None) -> T:
        response = self._client.chat(
            model=self.model,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            format=schema.model_json_schema(),
            options={"temperature": 0, "num_ctx": self._num_ctx},
            **self._extra,
        )
        result = schema.model_validate_json(response.message.content)
        if check:
            check(result)
        return result

    def _response_failure(self, error: ResponseError) -> LLMError:
        if error.status_code == 404:
            return LLMError("model_missing", f"El modelo {self.model} no está instalado. Ejecutá: ollama pull {self.model}", 503)
        return LLMError("ai_error", f"Ollama devolvió un error: {error.error}", 502)
