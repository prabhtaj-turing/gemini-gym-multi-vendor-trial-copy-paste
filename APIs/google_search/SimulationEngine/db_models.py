from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, field_validator
import re


class WebContent(BaseModel):
    """Model for web content stored in the database."""
    url: str = Field(..., description="URL of the web content")
    title: str = Field(..., description="Title of the content")
    snippet: str = Field(..., description="Brief description of the content")
    content: str = Field(..., description="Full text content")
    publication_time: Optional[str] = Field(None, description="Publication timestamp in ISO 8601 format")
    tags: List[str] = Field(default_factory=list, description="List of content tags")
    keywords: List[str] = Field(default_factory=list, description="List of keywords for search indexing")

    @field_validator("url")
    @classmethod
    def validate_url(cls, v):
        """Validate URL format."""
        if not v or not v.strip():
            raise ValueError('URL cannot be empty')
        url_pattern = r'^https?://[^\s/$.?#].[^\s]*$'
        if not re.match(url_pattern, v.strip()):
            raise ValueError('Invalid URL format')
        return v.strip()

    @field_validator("title", "snippet", "content")
    @classmethod
    def validate_required_fields(cls, v):
        """Validate required fields are not empty."""
        if not v or not v.strip():
            raise ValueError('Field cannot be empty')
        return v.strip()

    @field_validator("publication_time")
    @classmethod
    def validate_publication_time(cls, v):
        """Validate publication time format."""
        if v is not None and v.strip():
            iso_pattern = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})?$'
            if not re.match(iso_pattern, v.strip()):
                raise ValueError('Invalid publication time format (expected ISO 8601)')
            return v.strip()
        return v

    @field_validator("tags", "keywords")
    @classmethod
    def validate_string_lists(cls, v):
        """Validate string lists."""
        if not isinstance(v, list):
            raise ValueError('Must be a list')
        return [str(item).strip() for item in v if str(item).strip()]


class SearchIndexEntry(BaseModel):
    """Model for search index entries stored in the database."""
    query_terms: List[str] = Field(..., description="List of search terms indexed")
    content_ids: List[str] = Field(..., description="List of content IDs associated with these terms")
    relevance_scores: Dict[str, float] = Field(..., description="Relevance scores for each content ID")

    @field_validator("query_terms")
    @classmethod
    def validate_query_terms(cls, v):
        """Validate query terms."""
        if not v:
            raise ValueError('Query terms cannot be empty')
        return [term.strip().lower() for term in v if term.strip()]

    @field_validator("content_ids")
    @classmethod
    def validate_content_ids(cls, v):
        """Validate content IDs."""
        return [cid.strip() for cid in v if cid.strip()]

    @field_validator("relevance_scores")
    @classmethod
    def validate_relevance_scores(cls, v):
        """Validate relevance scores."""
        for content_id, score in v.items():
            if not isinstance(score, (int, float)) or not 0.0 <= score <= 1.0:
                raise ValueError(f'Relevance score for {content_id} must be between 0.0 and 1.0')
        return v


class GoogleSearchDB(BaseModel):
    """Main database model for Google Search simulation.
    
    This model validates the exact structure used by the Google Search functions:
    - web_content: Dict[str, WebContent] - matches DB.get("web_content", {})
    - search_index: Dict[str, SearchIndexEntry] - matches DB.get("search_index", {})
    - recent_searches: List[Dict[str, str]] - matches DB.get("recent_searches", [])
    """
    web_content: Dict[str, WebContent] = Field(default_factory=dict, description="Dictionary of web content by content ID")
    search_index: Dict[str, SearchIndexEntry] = Field(default_factory=dict, description="Search index by query term")
    recent_searches: List[Dict[str, str]] = Field(default_factory=list, description="List of recent search queries as dictionaries with 'query' and 'result' keys")

    @field_validator("recent_searches")
    @classmethod
    def validate_recent_searches(cls, v):
        """Validate recent searches structure."""
        for item in v:
            if not isinstance(item, dict):
                raise ValueError('Recent search items must be dictionaries')
            if 'query' not in item or 'result' not in item:
                raise ValueError('Recent search items must have "query" and "result" keys')
            if not isinstance(item['query'], str) or not isinstance(item['result'], str):
                raise ValueError('Query and result must be strings')
        return v

    def get_web_content_by_id(self, content_id: str) -> Optional[WebContent]:
        """Get web content by ID."""
        return self.web_content.get(content_id)

    def add_web_content(self, url: str, title: str, snippet: str, content: str,
                       publication_time: Optional[str] = None,
                       tags: Optional[List[str]] = None,
                       keywords: Optional[List[str]] = None) -> str:
        """Add new web content to the database."""
        import uuid
        
        content_id = f"content_{uuid.uuid4().hex[:8]}"
        
        web_content = WebContent(
            url=url,
            title=title,
            snippet=snippet,
            content=content,
            publication_time=publication_time,
            tags=tags or [],
            keywords=keywords or []
        )
        
        self.web_content[content_id] = web_content
        return content_id

    def add_recent_search(self, result: Dict[str, str]):
        """Add a search result to recent searches.
        
        Args:
            result: Dictionary with 'query' and 'result' keys
        """
        # Add to front
        self.recent_searches.insert(0, result)
        
        # Keep only last 50 searches
        self.recent_searches = self.recent_searches[:50]

    def get_recent_searches(self) -> List[Dict[str, str]]:
        """Get recent searches."""
        return self.recent_searches