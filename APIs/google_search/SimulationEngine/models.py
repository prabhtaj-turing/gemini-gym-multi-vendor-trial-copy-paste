from typing import List, Optional, Literal, Union, Dict
from pydantic import BaseModel, Field, field_validator

# --- Google Search Models ---

class PerQueryResult(BaseModel):
    """Pydantic model for a single search result from a single query to Google Search."""
    index: str
    snippet: str
    url: Optional[str] = None
    source_title: str
    publication_time: Optional[str] = None
    tag: Optional[str] = None

    @field_validator('source_title')
    @classmethod
    def validate_source_title_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('source_title cannot be empty or whitespace only')
        return v

class SearchResults(BaseModel):
    """Pydantic model for search results returned by Google Search for a single query."""
    query: str
    results: List[PerQueryResult]

    @field_validator('results')
    @classmethod
    def validate_results_not_empty(cls, v):
        if not v:
            raise ValueError('results cannot be empty')
        return v

# --- Response Models for API validation ---

class SearchResponse(BaseModel):
    """Pydantic model for the complete search response."""
    search_results: List[SearchResults]

    @field_validator('search_results')
    @classmethod
    def validate_search_results_not_empty(cls, v):
        if not v:
            raise ValueError('search_results cannot be empty')
        return v

# --- Database Models ---

class WebContent(BaseModel):
    """Pydantic model for web content stored in the database."""
    url: str
    title: str
    snippet: str
    content: str
    publication_time: Optional[str] = None
    tags: List[str] = []
    keywords: List[str] = []

class SearchIndex(BaseModel):
    """Pydantic model for search index entries."""
    query_terms: List[str]
    content_ids: List[str]
    relevance_scores: Dict[str, float]

class GoogleSearchDB(BaseModel):
    """Pydantic model representing the entire Google Search database structure."""
    web_content: Dict[str, WebContent]
    search_index: Dict[str, SearchIndex]
    recent_searches: List[str]
