import os
import json
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
import logging

class BaseSearchConfig(BaseModel):
    default_limit: int = 100
    log_level: int = logging.ERROR


class WhooshConfig(BaseSearchConfig):
    pass # TODO: We can extend it based on features provided by whoosh

class QdrantConfig(BaseSearchConfig):
    score_threshold: float = 0.90
    model_name: str = "models/text-embedding-004"
    embedding_task_type: str = "RETRIEVAL_DOCUMENT"
    embedding_size: int = 768
    api_key: str = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    cache_file: Optional[str] = "default_qdrant_cache.tmp"
    max_cache_size: int = 10000


class RapidFuzzConfig(BaseSearchConfig):
    scorer: str = "WRatio"
    score_cutoff: int = 80


class SubstringConfig(BaseSearchConfig):
    case_sensitive: bool = False


class HybridConfig(BaseSearchConfig):
    qdrant_config: QdrantConfig = Field(default_factory=QdrantConfig)
    rapidfuzz_config: RapidFuzzConfig = Field(default_factory=RapidFuzzConfig)


current_dir = os.path.dirname(os.path.abspath(__file__))

SEARCH_ENGINE_CONFIG = json.load(open(os.path.join(current_dir, "search_engine_config.json")))

def get_default_strategy_name(service_name: str) -> str:
    """
    Gets the default search strategy name for a service, falling back to the global default.
    """
    service_config = SEARCH_ENGINE_CONFIG.get("services", {}).get(service_name, {})
    global_config = SEARCH_ENGINE_CONFIG.get("global", {})
    return service_config.get("default_strategy_name", global_config.get("default_strategy_name", "substring"))

def get_custom_engine_definitions(service_name: str) -> List[Dict]:
    global_config = SEARCH_ENGINE_CONFIG.get("global", {})
    return SEARCH_ENGINE_CONFIG.get("services", {}).get(service_name, {}).get("custom_engine_definitions", global_config.get("custom_engine_definitions", []))

def get_strategy_configs(service_name: str) -> Dict:
    global_config = SEARCH_ENGINE_CONFIG.get("global", {})
    return SEARCH_ENGINE_CONFIG.get("services", {}).get(service_name, {}).get("strategy_configs", global_config.get("strategy_configs", {}))


__all__ = [
    "WhooshConfig",
    "QdrantConfig",
    "RapidFuzzConfig",
    "SubstringConfig",
    "HybridConfig",
    "get_default_strategy_name",
    "get_custom_engine_definitions",
    "get_strategy_configs",
]
