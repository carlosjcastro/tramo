import logging
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.config import settings
from app.container import get_llm, get_reader, get_service
from app.domain import Report, TopicMatch
from app.errors import AppError
from app.extraction import DocumentReader
from app.llm import StructuredLLM
from app.service import EquivalenceService

STATIC_DIR = Path(__file__).parent / "static"
logger = logging.getLogger("tramo")


class AnalyzeRequest(BaseModel):
    source: str = Field(min_length=1, max_length=settings.max_chars)
    target: str = Field(min_length=1, max_length=settings.max_chars)


class RecomputeRequest(BaseModel):
    matches: list[TopicMatch] = Field(min_length=1)


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


app = FastAPI(title="Tramo")


@app.exception_handler(AppError)
async def handle_app_error(_, error: AppError) -> JSONResponse:
    return error_response(error.status, error.code, error.message)


@app.exception_handler(Exception)
async def handle_unexpected_error(_, error: Exception) -> JSONResponse:
    logger.exception("Unexpected failure", exc_info=error)
    return error_response(500, "engine_error", "Ocurrió un error inesperado. Intentá de nuevo en unos minutos.")


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/limits", response_model=Limits)
def limits(llm: StructuredLLM = Depends(get_llm)) -> Limits:
    return Limits(
        max_chars=settings.max_chars,
        max_file_bytes=settings.max_file_bytes,
        model=llm.model,
        model_ready=llm.is_ready(),
    )


@app.post("/api/extract", response_model=Extracted)
def extract(file: UploadFile, reader: DocumentReader = Depends(get_reader)) -> Extracted:
    filename = file.filename or ""
    text = reader.read(filename, file.file.read(settings.max_file_bytes + 1))
    return Extracted(filename=filename, text=text, characters=len(text))


@app.post("/api/analyze", response_model=Report)
def analyze(request: AnalyzeRequest, service: EquivalenceService = Depends(get_service)) -> Report:
    try:
        return service.analyze(request.source, request.target)
    except ValueError as error:
        raise HTTPException(status_code=422, detail={"code": "no_topics", "message": str(error)}) from error


@app.post("/api/recompute", response_model=Report)
def recompute(request: RecomputeRequest, service: EquivalenceService = Depends(get_service)) -> Report:
    return service.recompute(request.matches)


app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
