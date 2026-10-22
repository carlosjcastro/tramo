from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.config import settings
from app.container import get_service
from app.domain import Report
from app.service import EquivalenceService

STATIC_DIR = Path(__file__).parent / "static"


class AnalyzeRequest(BaseModel):
    source: str = Field(min_length=1, max_length=settings.max_chars)
    target: str = Field(min_length=1, max_length=settings.max_chars)


app = FastAPI(title="Tramo")


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/analyze", response_model=Report)
def analyze(request: AnalyzeRequest, service: EquivalenceService = Depends(get_service)) -> Report:
    try:
        return service.analyze(request.source, request.target)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
