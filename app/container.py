from functools import lru_cache

from ollama import Client

from app.advisor import Advisor
from app.assessment import TopicAssessor
from app.config import settings
from app.extraction import DocumentReader
from app.llm import OllamaLLM, StructuredLLM
from app.policy import EquivalencePolicy
from app.service import EquivalenceService
from app.topics import TopicExtractor


@lru_cache
def get_llm() -> StructuredLLM:
    client = Client(host=settings.ollama_host, timeout=settings.request_timeout)
    return OllamaLLM(client, settings.model, settings.num_ctx)


@lru_cache
def get_service() -> EquivalenceService:
    llm = get_llm()
    return EquivalenceService(
        TopicExtractor(llm),
        TopicAssessor(llm, settings.batch_size),
        Advisor(llm),
        EquivalencePolicy(settings.partial_rule),
        llm.model,
    )


@lru_cache
def get_reader() -> DocumentReader:
    return DocumentReader(settings.max_file_bytes, settings.max_chars)
