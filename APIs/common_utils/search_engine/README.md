#  **Search Engine Integration**

This document provides guidance on integrating and configuring the unified search engine framework located in `APIs/common_utils/search_engine/`.

---

## **1. Default Engine Setup**

The search engine strategy is selected using the environment variable `DEFAULT_STRATEGY_NAME`, defaulting to `substring` if unspecified.

To override the default strategy in code:

```py
from {service_name}.SimulationEngine.search_engine import search_engine_manager
search_engine_manager.override_strategy_for_engine(strategy_name="keyword")
```

**Note:** Strategy configuration is typically done by scenario teams using Colab, as shown [here](https://colab.research.google.com/drive/1yd4H7qKaEFgWTbLUs0ur3KSJnX-kFic7?usp=sharing).

### **Supported Strategies**

Defined at `APIs/common_utils/search_engine/strategies.py`:

* `substring` (case-insensitive substring matching, default strategy)  
* `keyword` (Whoosh-based)  
* `semantic` (Qdrant-based): This strategy uses the `QdrantSearchStrategy` for vector-based semantic search. It generates embeddings for text chunks using Google's Gemini model and stores them in a Qdrant vector database that runs in-memory. This allows for finding results based on meaning and context, not just keywords. The configuration for this strategy is more detailed, see `search_engine_config.json` and `APIs/common_utils/search_engine/configs.py`. The `QdrantConfig` class defines settings like the model name, embedding size, and API key.
* `fuzzy` (RapidFuzz-based)
* `hybrid` (combines semantic and fuzzy)

### **Default Configurations**

Configurations reside in `search_engine_config.json` with a hierarchical structure:

```json
{
  "global": {
    "default_strategy_name": "substring",
    "strategy_configs": {
      "keyword": {},
      "semantic": {"score_threshold": 0.9},
      "fuzzy": {"score_cutoff": 80},
      "hybrid": {
        "rapidfuzz_config": {"score_cutoff": 80},
        "semantic_config": {"score_threshold": 0.9}
      },
      "substring": {"case_sensitive": false}
    }
  },
  "services": {
    "your_service": {
      "default_strategy_name": "substring",
      "custom_engine_definitions": [],
      "strategy_configs": {
        "semantic": {"score_threshold": 0.6},
        "fuzzy": {"score_cutoff": 70}
      }
    }
  }
}
```

Service-specific configs override global defaults.

Restore default configurations:

```py
from {service_name}.SimulationEngine.search_engine import search_engine_manager
search_engine_manager.reset_all_engines()
```

Modify configurations dynamically:

```py
from {service_name}.SimulationEngine.search_engine import search_engine_manager
fuzzy_engine = search_engine_manager.override_strategy_for_engine("fuzzy")
fuzzy_engine.config.score_cutoff = 90
```

---

## **2. Querying**

Example usage:

```py
from {service_name}.SimulationEngine.search_engine import search_engine_manager

def search_ids(query_text, filter_kwargs):
    engine = search_engine_manager.get_engine()
    results = engine.search(query_text, filter=filter_kwargs)
    return set(obj["id"] for obj in results)
```

**Filters:**  
 All fields within chunk metadata (e.g., `resource_type`, `content_type`, `user_id`) are filterable. Extend metadata as needed to support additional filters.

### **Debugging Queries**

The `rawSearch()` method provides detailed, strategy-level search outputs without score cutoffs, useful for debugging and validation.

---

## **3. Custom Engines**

Custom search engines are defined in `search_engine_config.json` under your service's `custom_engine_definitions`:

```json
{
  "services": {
    "your_service": {
      "custom_engine_definitions": [
        {
          "id": "search_specific_field",
          "strategy_name": "keyword",
          "metadata": {
            "used_for": ["Searching specific field with keyword strategy"]
          }
        }
      ]
    }
  }
}
```

Fetch a custom engine:

```py
from {service_name}.SimulationEngine.search_engine import search_engine_manager

custom_engine = search_engine_manager.get_engine(engine_id="search_specific_field")
```

Override strategy for custom engines:

```py
search_engine_manager.override_strategy_for_engine("fuzzy", engine_id="search_specific_field")
```

---

## **4. How Chunk Identification and Indexing Work**

Each searchable data item (chunk) is tracked using:

* `chunk_id`: a unique UUID derived from the chunk text content, used to detect content changes.  
* `original_json_obj_hash`: a hash of the original data object to detect metadata or payload updates.

When the database state changes, chunks are automatically reindexed if content or metadata changes.

---

## **Embedding Caching**

To improve performance and reduce API calls, the `QdrantSearchStrategy` uses a caching mechanism for text embeddings. This is handled by the `GeminiEmbeddingManager`.

### **Configuration**

The cache is configured in `APIs/common_utils/search_engine/configs.py` within the `QdrantConfig` class.

*   `cache_file`: Path to the file where the cache will be stored.
*   `max_cache_size`: The maximum number of embeddings to store in the cache.

The `GeminiEmbeddingManager` (`APIs/common_utils/llm_interface.py`) handles the logic. It uses an in-memory LRU (Least Recently Used) cache that is persisted to the `cache_file`.

### **Disabling Cache**

To disable caching, you can set `lru_cache_file_path` to `None` when initializing `GeminiEmbeddingManager`. In the context of the search engine, you can modify `QdrantConfig` to have `cache_file = None`. This will prevent the cache from being created and used.

---

## **5. Implementation for a New Service**

Integrating the search engine for a new service requires minimal setup. The framework is **fully generic and handles all the complexity internally**—you only need to define how to chunk your service's data.

### **What You Need to Implement**

Create a file at `APIs/{service_name}/SimulationEngine/search_engine.py` with the following structure:

```py
from typing import List
from common_utils.search_engine.adapter import Adapter
from common_utils.search_engine.models import SearchableDocument
from common_utils.search_engine.engine import search_engine_manager

class ServiceAdapter(Adapter):
    def db_to_searchable_documents(self) -> List[SearchableDocument]:
        """
        Convert your service's database content into searchable documents.
        
        Returns:
            List[SearchableDocument]: List of documents with:
                - text_content: The searchable text content
                - metadata: Dict with filterable fields (user_id, resource_type, etc.)
                - original_json_obj: The original data object
                - parent_doc_id: (optional) ID to group related chunks
        """
        # Example implementation:
        documents = []
        for item in self.get_all_items_from_db():
            documents.append(SearchableDocument(
                text_content=item.get_searchable_text(),
                metadata={
                    "user_id": item.user_id,
                    "resource_type": item.type,
                    # Add any fields you want to filter by
                },
                original_json_obj=item.to_dict(),
                parent_doc_id=f"{item.type}_{item.id}"
            ))
        return documents

# REQUIRED: Create these exact instances
service_adapter = ServiceAdapter()

search_engine_manager = search_engine_manager.get_engine_manager("{service_name}")

__all__ = [
    "service_adapter",
    "search_engine_manager",
]
```

**CRITICAL:** 
- The file **must** be named `search_engine.py`
- **Must** contain a variable named `service_adapter`
- **Must** initialize `search_engine_manager` with your service name
- **Must** export both in `__all__`

### **What's Handled Automatically**

Once you implement the adapter, the framework handles everything else internally:

✅ **Embedding generation**: Automatically generates vector embeddings using Google's Gemini API  
✅ **Intelligent caching**: Only calls the embedding API for new or changed content  
✅ **Automatic re-indexing**: Detects database changes and updates only modified chunks  
✅ **Vector database management**: Maintains Qdrant in-memory vector store  
✅ **Strategy switching**: Supports substring, keyword, fuzzy, semantic, and hybrid search  
✅ **Change detection**: Uses content hashing to identify what needs re-indexing  

### **Usage in Your Service APIs**

```py
from {service_name}.SimulationEngine.search_engine import search_engine_manager

# The engine manager is pre-configured for your service
engine = search_engine_manager.get_engine()
results = engine.search(query_text, filter={"user_id": "123"})
```

The `search_engine_manager` instance is already bound to your service name, so you don't need to pass it again.

### **Metadata for Filtering**

Include all fields you want to filter by in the `metadata` dictionary. Common fields:
- `user_id`: Filter by user
- `resource_type`: Filter by resource type (e.g., "message", "thread")
- `content_type`: Filter by content type
- Custom fields specific to your service

### **Important Guidelines**

* **Strategy classes remain generic**: They should never reference service-specific fields directly
* **Only the adapter knows about your DB structure**: This ensures modularity and reusability
* **Test with different strategies**: Write tests that verify your API works with all search strategies (substring, keyword, semantic, fuzzy, hybrid)

---

## **6. Demos and Testing**

* **Demo files:** `APIs/common_utils/search_engine/demo.py` and `demo_with_mutation.py`  
* **Service-specific tests:** Each service should have tests in `APIs/{service_name}/tests/` that verify search functionality across all strategies

This design allows easy integration, simplified configuration, and extensibility for additional services. The unified framework in `common_utils` ensures consistency across all services while requiring minimal service-specific implementation.

