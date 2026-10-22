from functools import lru_cache

from app.config import Settings, settings
from app.embedding import Embedder, FastEmbedder, OllamaEmbedder
from app.matching import TopicMatcher
from app.policy import EquivalencePolicy
from app.service import EquivalenceService


def build_ollama(config: Settings) -> Embedder:
    from ollama import Client

    return OllamaEmbedder(Client(host=config.ollama_host), config.embedding_model, config.embedding_prefix)


def build_fastembed(config: Settings) -> Embedder:
    return FastEmbedder(config.embedding_model, config.embedding_prefix)


EMBEDDER_BUILDERS = {"ollama": build_ollama, "fastembed": build_fastembed}


@lru_cache
def get_service() -> EquivalenceService:
    embedder = EMBEDDER_BUILDERS[settings.embedding_backend](settings)
    matcher = TopicMatcher(embedder, settings.covered_threshold, settings.partial_threshold)
    return EquivalenceService(matcher, EquivalencePolicy(settings.partial_rule))
