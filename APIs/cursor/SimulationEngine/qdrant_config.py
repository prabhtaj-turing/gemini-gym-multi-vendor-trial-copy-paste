from common_utils.print_log import print_log
import os
import re
import logging
import json
import uuid
from typing import List, Dict, Any, Optional, Sequence
from json_repair import repair_json

from .llm_interface import call_llm, GeminiEmbeddingManager
from .db import DB
from cursor.SimulationEngine import utils

# --- Qdrant Configuration ---
EMBEDDING_MODEL_NAME = "models/text-embedding-004"

# Qdrant imports
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue

class GeminiEmbeddingFunction:
    """
    Custom embedding function for Qdrant using Google's Gemini API.
    This class interfaces with the GeminiEmbeddingManager to generate embeddings.
    """

    _model_instance = None

    def __init__(
        self,
        model_name: str = EMBEDDING_MODEL_NAME,
        task_type: str = "RETRIEVAL_DOCUMENT",
        embedding_dimensionality: Optional[int] = 768,  # 768 for embedding-001
        lru_cache_file_path: Optional[str] = "gemini_embeddings_cache.log.pkl"
    ):
        if GeminiEmbeddingFunction._model_instance is None:
            GEMINI_API_KEY_FROM_ENV = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
            if not GEMINI_API_KEY_FROM_ENV:
                raise ValueError("GEMINI_API_KEY (or GOOGLE_API_KEY) must be set in the environment.")
            print_log(f"Initializing GeminiEmbeddingManager with model: {model_name}")
            GeminiEmbeddingFunction._model_instance = GeminiEmbeddingManager(
                gemini_api_key=GEMINI_API_KEY_FROM_ENV,
                lru_cache_file_path=lru_cache_file_path,
            )
        self.model_name = model_name
        self.task_type = task_type
        self.embedding_dimensionality = embedding_dimensionality
        self._model = GeminiEmbeddingFunction._model_instance

    def __call__(self, input_texts: Sequence[str]) -> List[List[float]]:
        if not input_texts:
            return []
        try:
            embeddings_dict = self._model.embed_content(
                gemini_model=self.model_name,
                uncached_texts=list(input_texts),
                embedding_task_type=self.task_type,
                embedding_size=self.embedding_dimensionality
            )
            return embeddings_dict.get("embedding", [[] for _ in input_texts])
        except Exception as e:
            print_log(f"Error during Gemini embedding generation: {e}")
            if self.embedding_dimensionality:
                return [[0.0] * self.embedding_dimensionality for _ in input_texts]
            return [[] for _ in input_texts]


class QdrantManager:
    """
    A singleton class to manage a Qdrant instance and its interactions.
    It uses a custom embedding function and can be persistent or ephemeral.
    """

    _instance = None
    _config_key = None  # To store the configuration of the first instance

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(QdrantManager, cls).__new__(cls)
            cls._instance._initialized = False
            cls._config_key = kwargs.get("persistent", True)
        return cls._instance

    def __init__(
        self,
        db_path: str = "qdrant_db/",
        collection_name: str = "default_collection_name",
        persistent: bool = True,
    ):
        if self._initialized:
            return

        print_log(f"Initializing QdrantManager for the first time...")
        self.persistent = persistent
        self.db_path = db_path
        self.collection_name = collection_name

        print_log(f"Mode: {'Persistent' if self.persistent else 'Ephemeral (In-Memory)'}")
        if self.persistent:
            print_log(f"Database path: {self.db_path}")
        print_log(f"Collection name: {self.collection_name}")

        try:
            self.embedding_function = GeminiEmbeddingFunction()
            # Qdrant client setup
            if self.persistent:
                os.makedirs(self.db_path, exist_ok=True)
                self.client = QdrantClient(path=self.db_path)
            else:
                self.client = QdrantClient(":memory:")

            # Create collection if not exists
            if not self.client.collection_exists(self.collection_name):
                self.client.recreate_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.embedding_function.embedding_dimensionality,
                        distance=Distance.COSINE
                    )
                )
            self._initialized = True
        except Exception as e:
            print_log(f"Failed to initialize QdrantManager: {e}")
            raise

    def add_code_chunks(self, code_chunks: List[Dict[str, Any]], batch_size: int = 100):
        if not self._initialized:
            raise RuntimeError("QdrantManager is not initialized.")
        if not code_chunks:
            print_log("No code chunks to add.")
            return

        documents_to_add: List[str] = []
        metadatas_to_add: List[Dict[str, Any]] = []
        ids_to_add: List[str] = []

        for i, chunk in enumerate(code_chunks):
            if "content" not in chunk or not isinstance(chunk["content"], str):
                print_log(
                    f"Skipping chunk {i} due to missing or invalid 'content'. Chunk: {chunk}"
                )
                continue

            doc_content = chunk["content"]
            file_path_str = str(chunk.get("file_path", "unknown_file"))
            start_line_str = str(chunk.get("start_line", i))
            # Use UUID5 for Qdrant point id
            doc_id = str(uuid.uuid5(uuid.NAMESPACE_URL, doc_content))

            metadata = {
                k: v
                for k, v in chunk.items()
                if k not in ["content", "id"] and isinstance(v, (str, int, float, bool))
            }
            for key in [
                "file_path",
                "language",
                "chunk_type",
                "start_line",
                "end_line",
            ]:
                if (
                    key in chunk
                    and key not in metadata
                    and isinstance(chunk[key], (str, int, float, bool))
                ):
                    metadata[key] = chunk[key]
                elif key not in metadata:
                    if key in ["start_line", "end_line"]:
                        metadata[key] = -1
                    else:
                        metadata[key] = "unknown"

            documents_to_add.append(doc_content)
            metadatas_to_add.append(metadata)
            ids_to_add.append(doc_id)

            if len(documents_to_add) >= batch_size:
                self._add_batch(documents_to_add, metadatas_to_add, ids_to_add)
                documents_to_add, metadatas_to_add, ids_to_add = [], [], []

        if documents_to_add:
            self._add_batch(documents_to_add, metadatas_to_add, ids_to_add)

    def _add_batch(
        self, documents: List[str], metadatas: List[Dict[str, Any]], ids: List[str]
    ):
        try:
            embeddings = self.embedding_function(documents)
            points = []
            for i in range(len(documents)):
                point = PointStruct(
                    id=ids[i],
                    vector=embeddings[i],
                    payload={**metadatas[i], "document": documents[i]}
                )
                points.append(point)
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
        except Exception as e:
            print_log(f"Error adding batch to Qdrant: {e}")
            for i in range(len(ids)):
                print_log(f"Failed item ID: {ids[i]}, Metadata: {metadatas[i]}")

    def query_codebase(
        self,
        query_text: str,
        n_results: int = 5,
        where_filter: Optional[Dict[str, Any]] = None,
        where_document_filter: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        if not self._initialized:
            raise RuntimeError("QdrantManager is not initialized.")
        if not query_text:
            print_log("Query text cannot be empty.")
            return None

        try:
            print_log(f"Querying for: '{query_text}', asking for {n_results} results.")
            if where_filter:
                print_log(f"Applying metadata filter: {where_filter}")
            if where_document_filter:
                print_log(f"Applying document filter: {where_document_filter}")

            query_vector = self.embedding_function([query_text])[0]
            # Qdrant filter construction
            qdrant_filter = None
            if where_filter:
                conditions = []
                for k, v in where_filter.items():
                    conditions.append(FieldCondition(key=k, match=MatchValue(value=v)))
                qdrant_filter = Filter(must=conditions)
            # Document filter is not natively supported, so we ignore where_document_filter for now

            search_result = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=n_results,
                with_payload=True,
                with_vectors=False,
                query_filter=qdrant_filter
            )
            # Convert Qdrant search result to QdrantDB-like output
            documents = [[]]
            metadatas = [[]]
            distances = [[]]
            ids = [[]]
            for hit in search_result:
                payload = hit.payload or {}
                doc = payload.get("document", "")
                documents[0].append(doc)
                # Remove "document" from metadata
                meta = {k: v for k, v in payload.items() if k != "document"}
                metadatas[0].append(meta)
                distances[0].append(hit.score if hasattr(hit, "score") else hit.distance)
                ids[0].append(str(hit.id))
            return {
                "documents": documents,
                "metadatas": metadatas,
                "distances": distances,
                "ids": ids
            }
        except Exception as e:
            print_log(f"Error querying Qdrant: {e}")
            return None

    def get_collection_count(self) -> int:
        if not self._initialized:
            raise RuntimeError("QdrantManager is not initialized.")
        try:
            info = self.client.get_collection(self.collection_name)
            return info.points_count
        except Exception:
            return 0

    def clear_collection(self):
        if not self._initialized:
            raise RuntimeError("QdrantManager is not initialized.")

        collection_name = self.collection_name
        print_log(f"Attempting to clear collection '{collection_name}'...")
        try:
            self.client.delete_collection(collection_name=collection_name)
            print_log(f"Collection '{collection_name}' deleted.")
            # Recreate it
            self.client.recreate_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=self.embedding_function.embedding_dimensionality,
                    distance=Distance.COSINE
                )
            )
            print_log(f"Collection '{collection_name}' recreated and is now empty.")
        except Exception as e:
            print_log(f"Error clearing collection '{collection_name}': {e}")
            try:
                self.client.recreate_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(
                        size=self.embedding_function.embedding_dimensionality,
                        distance=Distance.COSINE
                    )
                )
            except Exception as e_rec:
                print_log(
                    f"Failed to re-establish collection object after deletion error: {e_rec}"
                )


def transform_qdrant_results(
    qdrant_output: Dict[str, Optional[List[List[Any]]]],
    fuzzy_factor_from_best: float = 2.5,
    overall_max_distance: float = 1.8,
) -> List[Dict[str, str]]:
    transformed_results: List[Dict[str, str]] = []

    if not qdrant_output:
        return transformed_results

    doc_list: Optional[List[str]] = qdrant_output.get("documents", [[]])[0]
    meta_list: Optional[List[Dict[str, Any]]] = qdrant_output.get("metadatas", [[]])[0]
    dist_list: Optional[List[float]] = qdrant_output.get("distances", [[]])[0]

    if not doc_list or not meta_list or not dist_list:
        return transformed_results

    num_results = len(doc_list)
    if num_results == 0:
        return transformed_results

    best_distance = dist_list[0]

    for i in range(num_results):
        current_distance = dist_list[i]
        current_metadata = meta_list[i]
        current_document = doc_list[i]

        if i == 0:
            if current_distance > overall_max_distance:
                break
        else:
            if current_distance > (best_distance * fuzzy_factor_from_best):
                break
            if current_distance > overall_max_distance:
                break

        file_path = current_metadata.get("file_path", "Unknown File")
        start_line = current_metadata.get("start_line", -1)
        end_line = current_metadata.get("end_line", -1)

        snippet_bounds = f"{start_line}:{end_line}"
        snippet_content = str(current_document) if current_document is not None else ""

        transformed_results.append(
            {
                "file_path": file_path,
                "snippet_bounds": snippet_bounds,
                "snippet_content": snippet_content,
            }
        )

    return transformed_results


def transform_qdrant_results_via_llm(
        raw_qdrant_output: Dict[str, Optional[List[List[Any]]]],
        query: str,
        max_candidates_for_llm_expansion: int = 15,
    ):
    final_snippets: List[Dict[str, str]] = []
    if not raw_qdrant_output or not raw_qdrant_output.get('ids') or not raw_qdrant_output.get('ids')[0]:
        return []

    prepared_candidates = []
    num_raw_candidates = len(raw_qdrant_output['ids'][0])
    for i in range(num_raw_candidates):
        metadata = raw_qdrant_output['metadatas'][0][i] if raw_qdrant_output.get('metadatas') and raw_qdrant_output['metadatas'][0] and i < len(raw_qdrant_output['metadatas'][0]) else {}
        document = raw_qdrant_output['documents'][0][i] if raw_qdrant_output.get('documents') and raw_qdrant_output['documents'][0] and i < len(raw_qdrant_output['documents'][0]) else ""
        distance = raw_qdrant_output['distances'][0][i] if raw_qdrant_output.get('distances') and raw_qdrant_output['distances'][0] and i < len(raw_qdrant_output['distances'][0]) else float('inf')
        
        prepared_candidates.append({
            "candidate_id": f"candidate_{i}",
            "file_path": metadata.get("file_path", "unknown_file"),
            "chunk_start_line": metadata.get("start_line", -1),
            "chunk_end_line": metadata.get("end_line", -1),
            "chunk_content": document,
            "chunk_type": metadata.get("chunk_type", "unknown"),
            "retrieval_distance": round(distance, 4)
        })

    if not prepared_candidates:
        return []

    candidates_for_llm_review = prepared_candidates[:max_candidates_for_llm_expansion]
    if not candidates_for_llm_review:
        return []
        
    candidates_json_str = json.dumps(candidates_for_llm_review, indent=2)

    llm_prompt = f"""You are an expert code analysis assistant. Your task is to review candidate code snippets retrieved by a vector search based on a user query. You need to identify the most relevant snippets, suggest boundaries for logically complete code blocks, and provide reasoning.

User Query: "{query}"

Candidate Snippets to Review:
{candidates_json_str}

For each candidate snippet provided above:
1.  Assess its relevance to the User Query. Consider its content, file path, original chunk type, and retrieval distance (lower is better, but prioritize semantic meaning).
2.  If a snippet is relevant, suggest the 1-indexed start and end line numbers for a "logically complete" code block. This block should ideally encapsulate the relevant information (e.g., entire function, class, method, or a self-contained paragraph/section for text). The original chunk_content and its line numbers are your primary guide.

Output a JSON list of objects. Each object in the list should correspond to one of the input candidates that you deem relevant and for which you are suggesting a completed block. Each object MUST have the following keys:
- "candidate_id": string (must match one of the input candidate_id values)
- "is_relevant": boolean (true if you select this candidate for the final output)
- "suggested_start_line": integer (1-indexed, inclusive start line of the complete block)
- "suggested_end_line": integer (1-indexed, inclusive end line of the complete block)

If none of the provided candidates are deemed relevant, return an empty JSON list `[]`.
Focus ONLY on the candidates provided in the JSON above.
Example of an item in your JSON output list:
{{
  "candidate_id": "candidate_0",
  "is_relevant": true,
  "suggested_start_line": 42,
  "suggested_end_line": 95,
}}

Return ONLY the JSON list.
"""
    try:
        llm_response_content=[]
        llm_response_content = call_llm(llm_prompt, model_name="gemini-2.5-flash", temperature=0.1)
        llm_response_content = llm_response_content.strip()
        llm_response_content = re.sub(r'^```(?:json)?\s*', '', llm_response_content)
        llm_response_content = re.sub(r'\s*```$', '', llm_response_content)
        llm_evaluations = repair_json(llm_response_content)
        if llm_evaluations:
            llm_evaluations = json.loads(llm_evaluations)
        else:
            llm_evaluations = []
        if not isinstance(llm_evaluations, list):
            raise ValueError("LLM response was not a JSON list.")
    except (json.JSONDecodeError, ValueError) as e:
        utils._log_util_message(logging.ERROR, f"LLM response parsing error for codebase_search: {e}. Response: {llm_response_content[:500]}", True)
        return []
    except Exception as e:
        utils._log_util_message(logging.ERROR, f"LLM call failed during codebase_search: {e}", True)
        return []

    reviewed_candidates_map = {cand["candidate_id"]: cand for cand in candidates_for_llm_review}

    # Collect selected snippets paired with their retrieval distance for ordering
    selected_with_distance: List[tuple] = []

    for eval_item in llm_evaluations:
        if not isinstance(eval_item, dict) or not eval_item.get("is_relevant"):
            continue

        candidate_id = eval_item.get("candidate_id")
        original_candidate_details = reviewed_candidates_map.get(candidate_id)

        if not original_candidate_details:
            utils._log_util_message(logging.WARNING, f"LLM returned eval for unknown candidate_id: {candidate_id}", False)
            continue

        file_path = original_candidate_details["file_path"]
        suggested_start_line = eval_item.get("suggested_start_line")
        suggested_end_line = eval_item.get("suggested_end_line")

        if not all([file_path != "unknown_file", 
                    isinstance(suggested_start_line, int), suggested_start_line > 0,
                    isinstance(suggested_end_line, int), suggested_end_line >= suggested_start_line]):
            utils._log_util_message(logging.WARNING, f"Invalid boundaries from LLM for {candidate_id} ({file_path}): start={suggested_start_line}, end={suggested_end_line}", False)
            continue

        try:
            file_entry = DB["file_system"].get(file_path)
            if not file_entry or file_entry.get("is_directory"):
                utils._log_util_message(logging.WARNING, f"File not found or is a directory: {file_path} for candidate {candidate_id}", False)
                continue
            
            full_file_lines = file_entry.get("content_lines", [])
            if not full_file_lines:
                utils._log_util_message(logging.WARNING, f"File is empty: {file_path} for candidate {candidate_id}", False)
                continue

            actual_start_idx = max(0, suggested_start_line - 1)
            actual_end_idx = min(len(full_file_lines), suggested_end_line)

            if actual_start_idx < actual_end_idx:
                completed_snippet_lines = full_file_lines[actual_start_idx:actual_end_idx]
                completed_snippet_content = "".join(completed_snippet_lines)

                snippet_obj = {
                    "file_path": file_path,
                    "snippet_bounds": f"{suggested_start_line}:{suggested_end_line}",
                    "snippet_content": completed_snippet_content
                }
                # Lower retrieval_distance indicates higher relevance; use as primary sort key
                retrieval_distance = original_candidate_details.get("retrieval_distance", float('inf'))
                try:
                    distance_value = float(retrieval_distance)
                except Exception:
                    distance_value = float('inf')
                selected_with_distance.append((distance_value, snippet_obj))
            else:
                utils._log_util_message(logging.WARNING, f"Processed suggested bounds for {candidate_id} resulted in invalid slice: {actual_start_idx} to {actual_end_idx}", False)
        except KeyError:
            utils._log_util_message(logging.WARNING, f"File path {file_path} not found in DB for candidate {candidate_id}", False)

        except Exception as e:
            utils._log_util_message(logging.ERROR, f"Error extracting snippet for {candidate_id} ({file_path}): {e}", True)
            continue

    # Order selected snippets by retrieval distance (ascending => more relevant first)
    if selected_with_distance:
        selected_with_distance.sort(key=lambda x: (x[0]))
        final_snippets = [item[1] for item in selected_with_distance]

    return final_snippets    
