from common_utils.print_log import print_log
import json
import os
import re
import uuid
from typing import Optional, Dict, Any, List

import requests
from dotenv import load_dotenv, find_dotenv

from .db import DB

load_dotenv(find_dotenv(filename=".env", raise_error_if_not_found=False, usecwd=False))


def search_web_content(query: str, max_results: int = 10) -> List[Dict[str, Any]]:
    """
    Searches the web content database for relevant results based on a query.
    
    Args:
        query (str): The search query string.
        max_results (int): Maximum number of results to return.

    Returns:
        List[Dict[str, Any]]: A list of search result dictionaries.
    """
    results = []
    query_terms = query.lower().split()

    # Get all web content
    web_content = DB.get("web_content", {})

    # Score each piece of content based on relevance
    scored_content = []

    for content_id, content in web_content.items():
        score = calculate_relevance_score(query_terms, content)
        if score > 0:
            scored_content.append((score, content_id, content))

    # Sort by relevance score (highest first)
    scored_content.sort(key=lambda x: x[0], reverse=True)

    # Return top results
    for i, (score, content_id, content) in enumerate(scored_content[:max_results]):
        result = {
            "snippet": content.get("snippet", ""),
            "url": content.get("url", ""),
            "source_title": content.get("title", ""),
            "publication_time": content.get("publication_time"),
            "tag": get_content_tag(content)
        }
        results.append(result)

    return results


def calculate_relevance_score(query_terms: List[str], content: Dict[str, Any]) -> float:
    """
    Calculates a relevance score for content based on query terms.
    
    Args:
        query_terms (List[str]): List of search terms.
        content (Dict[str, Any]): Content dictionary to score.

    Returns:
        float: Relevance score (0.0 to 1.0).
    """
    score = 0.0

    # Get content text for searching
    title = content.get("title", "").lower()
    snippet = content.get("snippet", "").lower()
    content_text = content.get("content", "").lower()
    keywords = [kw.lower() for kw in content.get("keywords", [])]

    # Check each query term
    for term in query_terms:
        term_score = 0.0

        # Title matches get highest weight
        if term in title:
            term_score += 0.4

        # Snippet matches get medium weight
        if term in snippet:
            term_score += 0.3

        # Content matches get lower weight
        if term in content_text:
            term_score += 0.2

        # Keyword matches get medium weight
        if term in keywords:
            term_score += 0.3

        # Partial matches
        for keyword in keywords:
            if term in keyword or keyword in term:
                term_score += 0.1

        score += term_score

    # Normalize score
    if query_terms:
        score = score / len(query_terms)

    return min(score, 1.0)


def get_content_tag(content: Dict[str, Any]) -> Optional[str]:
    """
    Determines a tag for content based on its properties.
    
    Args:
        content (Dict[str, Any]): Content dictionary.

    Returns:
        Optional[str]: Tag string or None.
    """
    tags = content.get("tags", [])
    if tags:
        return tags[0]  # Return first tag

    # Infer tag from content
    title = content.get("title", "").lower()
    snippet = content.get("snippet", "").lower()

    if any(word in title or word in snippet for word in ["news", "article", "report"]):
        return "news"
    elif any(word in title or word in snippet for word in ["tutorial", "guide", "how to"]):
        return "tutorial"
    elif any(word in title or word in snippet for word in ["video", "youtube", "stream"]):
        return "video"
    elif any(word in title or word in snippet for word in ["shop", "buy", "purchase", "store"]):
        return "shopping"

    return None


def add_web_content(url: str, title: str, snippet: str, content: str,
                    publication_time: Optional[str] = None,
                    tags: Optional[List[str]] = None,
                    keywords: Optional[List[str]] = None) -> str:
    """
    Adds new web content to the database.
    
    Args:
        url (str): The URL of the content.
        title (str): The title of the content.
        snippet (str): A brief description.
        content (str): The full content text.
        publication_time (Optional[str]): When the content was published.
        tags (Optional[List[str]]): List of tags for categorization.
        keywords (Optional[List[str]]): List of keywords for search indexing.

    Returns:
        str: The generated content ID.
    """
    content_id = f"content_{uuid.uuid4().hex[:8]}"

    web_content = DB.get("web_content", {})
    web_content[content_id] = {
        "url": url,
        "title": title,
        "snippet": snippet,
        "content": content,
        "publication_time": publication_time,
        "tags": tags or [],
        "keywords": keywords or []
    }

    DB["web_content"] = web_content

    # Update search index
    update_search_index(content_id, title, content, keywords or [])

    return content_id


def update_search_index(content_id: str, title: str, content: str, keywords: List[str]):
    """
    Updates the search index with new content.
    
    Args:
        content_id (str): The ID of the content.
        title (str): The title of the content.
        content (str): The full content text.
        keywords (List[str]): List of keywords.
    """
    search_index = DB.get("search_index", {})

    # Extract terms from title and content
    all_text = f"{title} {content}".lower()
    terms = re.findall(r'\b\w+\b', all_text)
    terms.extend(keywords)

    # Add to index
    for term in set(terms):
        if len(term) > 2:  # Skip very short terms
            if term not in search_index:
                search_index[term] = {
                    "query_terms": [term],
                    "content_ids": [],
                    "relevance_scores": {}
                }

            if content_id not in search_index[term]["content_ids"]:
                search_index[term]["content_ids"].append(content_id)
                search_index[term]["relevance_scores"][content_id] = 1.0

    DB["search_index"] = search_index


def get_recent_searches() -> List[Dict[str, str]]:
    """
    Gets the list of recent searches.
    
    Returns:
        List[Dict[str, str]]: List of recent search queries. The keys are following:
            query (str): The search query that was executed
            result (str): search result for the query
    """
    return DB.get("recent_searches", [])


def add_recent_search(result: Dict[str, str]):
    """
    Adds a query result to the recent searches list.
    
    Args:
        result (Dict[str, str]): The search result to add. The keys are following:
            query (str): The search query that was executed
            result (str): search result for the query

    """
    recent_searches = get_recent_searches()

    # Add to front
    recent_searches.insert(0, result)

    # Keep only last 50 searches
    recent_searches = recent_searches[:50]

    DB["recent_searches"] = recent_searches


def set_google_api_key(api_key: str):
    """
    Sets the Google API key for use in API calls.
    This allows overriding the environment variable if necessary.
    
    Args:
        api_key (str): The Google API key to use.
    """
    if not api_key or not isinstance(api_key, str):
        raise ValueError("API key must be a non-empty string")
    
    # Set the API key in the environment
    os.environ["GOOGLE_API_KEY"] = api_key


def get_google_api_key() -> Optional[str]:
    """
    Gets the Google API key from environment variables.
    It checks for 'GOOGLE_API_KEY' first, then 'GEMINI_API_KEY'.
    
    Returns:
        Optional[str]: The Google API key, or None if not found.
    """
    return os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")


def get_gemini_response(query_text: str, api_key: Optional[str] = None):
    """
    Constructs and executes an HTTP request to query the Gemini API using the 'requests' library.

    Args:
        query_text: The user's text to send to the model.
        api_key: Optional API key to override the default one.

    Returns:
        A dictionary parsed from the JSON response, or None on error.
    """
    # Use provided API key, or get from utility function
    if api_key:
        key_to_use = api_key
    else:
        key_to_use = get_google_api_key()
    
    if not key_to_use:
        msg = f"Google or Gemini API Key not found. Please create a .env file in the project root with GOOGLE_API_KEY or GEMINI_API_KEY, or set it as an environment variable."
        raise ValueError(msg)
    
    live_api_url = os.getenv("LIVE_API_URL")
    if not live_api_url:
        msg = f"LIVE API URL not found. Please create a .env file in the project root with LIVE_API_URL, or set it as an environment variable."
        raise ValueError(msg)

    url = f"{live_api_url}?key={key_to_use}"
    headers = {
        "Content-Type": "application/json"
    }
    query_text = f"Use @Google Search to search exactly this query, do not alter it: '{query_text}'"
    data = {
        "model": "models/chat-bard-003",
        "generationConfig": {"candidateCount": 1},
        "contents": [{"role": "user", "parts": {"text": query_text}}]
    }
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()  # This will raise an exception for HTTP error codes
        return response.json()['candidates'][0]['content']['parts'][0]['text']

    except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
        print_log(f"An error occurred with the HTTP request: {e}")
        return None
