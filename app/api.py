import json
import logging
from pathlib import Path
from typing import Iterator

from fastapi import Depends, FastAPI, HTTPException, Request, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.clientip import client_ip
from app.config import settings
from app.container import Limiters, get_limiters, get_llm, get_reader, get_service
from app.domain import Report, TopicMatch
from app.domain import Progress
from app.errors import AppError
from app.extraction import DocumentReader
from app.guards import BodyLimitMiddleware, SecurityHeadersMiddleware
from app.llm import StructuredLLM
from app.ratelimit import RateLimitError
from app.sanitize import clean_input, safe_filename
from app.service import EquivalenceService

STATIC_DIR = Path(__file__).parent / "static"
logger = logging.getLogger("tramo")


MAX_MATCHES = 300
MAX_FIELD = 600
VALIDATION_MESSAGES = {
    "string_too_short": "Completá los dos programas antes de generar el informe.",
    "string_too_long": "Uno de los textos supera el máximo de caracteres permitido.",
    "too_long": "La solicitud trae más elementos de los permitidos.",
}
INVALID_MESSAGE = "Los datos enviados no son válidos. Revisá los dos programas."


class AnalyzeRequest(BaseModel):
    source: str = Field(min_length=1, max_length=settings.max_chars)
    target: str = Field(min_length=1, max_length=settings.max_chars)

    @field_validator("source", "target")
    @classmethod
    def sanitize(cls, value: str) -> str:
        cleaned = clean_input(value).strip()
        if not cleaned:
            raise ValueError("The text is empty after cleaning")
        return cleaned


class RecomputeRequest(BaseModel):
    matches: list[TopicMatch] = Field(min_length=1, max_length=MAX_MATCHES)

    @field_validator("matches")
    @classmethod
    def bound_text(cls, matches: list[TopicMatch]) -> list[TopicMatch]:
        for match in matches:
            texts = [match.target.text, match.reason, *(source.text for source in match.sources)]
            if len(match.sources) > 10 or any(len(text) > MAX_FIELD for text in texts):
                raise ValueError("A match is longer than allowed")
        return matches


class Limits(BaseModel):
    max_chars: int
    max_file_bytes: int
    model: str
    model_ready: bool


class Extracted(BaseModel):
    filename: str
    text: str
    characters: int


def error_response(status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(status_code=status, content={"detail": {"code": code, "message": message}})


def encode(event: dict) -> str:
    return json.dumps(event, ensure_ascii=False) + "\n"


def failure_event(code: str, message: str) -> str:
    return encode({"type": "error", "code": code, "message": message})


def stream_events(service: EquivalenceService, request: AnalyzeRequest, gate, token: float) -> Iterator[str]:
    try:
        for event in service.analyze_events(request.source, request.target):
            if isinstance(event, Progress):
                yield encode({"type": "progress", **event.model_dump()})
            else:
                yield encode({"type": "report", "report": event.model_dump(mode="json")})
    except ValueError as error:
        yield failure_event("no_topics", str(error))
    except AppError as error:
        yield failure_event(error.code, error.message)
    except Exception as error:
        logger.exception("Unexpected failure", exc_info=error)
        yield failure_event("engine_error", "Ocurrió un error inesperado. Intentá de nuevo en unos minutos.")
    finally:
        gate.release(token)


def limiter_for(name: str):
    def check(request: Request, limiters: Limiters = Depends(get_limiters)) -> None:
        getattr(limiters, name).check(client_ip(request))

    return check


def general_limit(request: Request, limiters: Limiters = Depends(get_limiters)) -> None:
    limiters.general.check(client_ip(request))


app = FastAPI(title="Tramo", docs_url=None, redoc_url=None, openapi_url=None)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(BodyLimitMiddleware, upload_limit=settings.max_file_bytes + 65536, json_limit=settings.max_json_bytes)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=list(settings.allowed_hosts))


@app.exception_handler(AppError)
async def handle_app_error(_, error: AppError) -> JSONResponse:
    response = error_response(error.status, error.code, error.message)
    if isinstance(error, RateLimitError):
        response.headers["Retry-After"] = str(error.retry_after)
    return response


@app.exception_handler(RequestValidationError)
async def handle_invalid_request(_, error: RequestValidationError) -> JSONResponse:
    first = error.errors()[0]["type"] if error.errors() else ""
    return error_response(422, "invalid_input", VALIDATION_MESSAGES.get(first, INVALID_MESSAGE))


@app.exception_handler(Exception)
async def handle_unexpected_error(_, error: Exception) -> JSONResponse:
    logger.exception("Unexpected failure", exc_info=error)
    return error_response(500, "engine_error", "Ocurrió un error inesperado. Intentá de nuevo en unos minutos.")


@app.get("/api/health", dependencies=[Depends(general_limit)])
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/limits", response_model=Limits, dependencies=[Depends(general_limit)])
def limits(llm: StructuredLLM = Depends(get_llm)) -> Limits:
    return Limits(
        max_chars=settings.max_chars,
        max_file_bytes=settings.max_file_bytes,
        model=llm.model,
        model_ready=llm.is_ready(),
    )


@app.post("/api/extract", response_model=Extracted, dependencies=[Depends(limiter_for("extract"))])
def extract(file: UploadFile, reader: DocumentReader = Depends(get_reader)) -> Extracted:
    filename = safe_filename(file.filename or "")
    text = reader.read(filename, file.file.read(settings.max_file_bytes + 1))
    return Extracted(filename=filename, text=text, characters=len(text))


@app.post("/api/analyze", response_model=Report, dependencies=[Depends(limiter_for("analyze"))])
def analyze(
    request: AnalyzeRequest,
    service: EquivalenceService = Depends(get_service),
    limiters: Limiters = Depends(get_limiters),
) -> Report:
    with limiters.gate.hold():
        try:
            return service.analyze(request.source, request.target)
        except ValueError as error:
            raise HTTPException(status_code=422, detail={"code": "no_topics", "message": str(error)}) from error


@app.post("/api/analyze/stream", dependencies=[Depends(limiter_for("analyze"))])
def analyze_stream(
    request: AnalyzeRequest,
    service: EquivalenceService = Depends(get_service),
    limiters: Limiters = Depends(get_limiters),
) -> StreamingResponse:
    token = limiters.gate.acquire()
    return StreamingResponse(
        stream_events(service, request, limiters.gate, token),
        media_type="application/x-ndjson",
        headers={"X-Accel-Buffering": "no"},
    )


@app.post("/api/recompute", response_model=Report, dependencies=[Depends(general_limit)])
def recompute(request: RecomputeRequest, service: EquivalenceService = Depends(get_service)) -> Report:
    return service.recompute(request.matches)


app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
