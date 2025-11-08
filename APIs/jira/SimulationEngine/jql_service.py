"""
JQL Service Layer - Handles JQL parsing and coordinates with generic search strategies.

This layer is responsible for:
1. Parsing JQL queries into structured components
2. Converting JQL conditions into generic search operations
3. Coordinating with generic search strategies (substring, semantic, fuzzy, etc.)
4. Applying JQL-specific filtering, sorting, and pagination
5. Reconstructing full issues from document chunks
"""

import re
from typing import Dict, List, Optional, Any, Union
from .search_engine import service_adapter
from .search_engine import search_engine_manager


class JQLService:
    """Service layer that handles JQL parsing and coordinates with generic search strategies."""
    
    def __init__(self):
        self.service_adapter = service_adapter
        self.search_engine_manager = search_engine_manager

    def _reconstruct_issues_from_chunks(self, strategy_name: str = "substring") -> List[Dict]:
        """Reconstruct full issue objects from document chunks."""

        # Get strategy instance

        strategy = self.search_engine_manager.get_strategy_instance(strategy_name)
        # Always sync data from database first to ensure we have latest data
        self.service_adapter.sync_from_db(strategy)
        
        
        # If strategy has no data, force initialization
        has_data = False
        if hasattr(strategy, 'doc_store'):
            has_data = bool(strategy.doc_store)
        elif hasattr(strategy, 'indexed_docs'):
            has_data = bool(strategy.indexed_docs)
        
        if not has_data:
            self.service_adapter.init_from_db(strategy)
        
        # Group chunks by parent_doc_id (issue ID)
        issue_groups = {}
        
        # Handle different strategy storage formats
        if hasattr(strategy, 'doc_store'):
            # Most strategies use doc_store (dict)
            documents = strategy.doc_store.values()
        elif hasattr(strategy, 'indexed_docs'):
            # Some strategies use indexed_docs (list)
            documents = strategy.indexed_docs
        else:
            # Fallback - no documents
            documents = []
            
        # Recalculate documents since we may have consumed the iterator
        if hasattr(strategy, 'doc_store'):
            documents = strategy.doc_store.values()
        elif hasattr(strategy, 'indexed_docs'):
            documents = strategy.indexed_docs
        else:
            documents = []
            
        for chunk in documents:
            parent_id = chunk.parent_doc_id
            if parent_id not in issue_groups:
                issue_groups[parent_id] = []
            issue_groups[parent_id].append(chunk)
        
        # Reconstruct issues from chunks
        issues = []
        for chunks in issue_groups.values():
            if chunks:
                # All chunks from the same issue have the same original_json_obj
                issue = chunks[0].original_json_obj
                if issue:
                    issues.append(issue)
        
        return issues

    def _extract_search_terms_from_jql(self, jql: str) -> List[str]:
        """Extract text search terms from JQL query for generic search strategies."""
        search_terms = []
        
        # Match text search patterns like: summary ~ "bug report" or description ~ "login"
        # Also handle single quotes: summary ~ 'bug report'
        text_search_pattern = r'(?:summary|description|text|comment)\s*~\s*["\']([^"\']+)["\']'
        matches = re.findall(text_search_pattern, jql, re.IGNORECASE)
        search_terms.extend(matches)
        
        # Match exact text matches: summary = "exact text"
        exact_text_pattern = r'(?:summary|description|text|comment)\s*=\s*["\']([^"\']+)["\']'
        matches = re.findall(exact_text_pattern, jql, re.IGNORECASE)
        search_terms.extend(matches)
        
        # Handle unquoted search terms after ~ operator (common in test cases)
        # Example: summary ~ authentication
        unquoted_pattern = r'(?:summary|description|text|comment)\s*~\s*([^\s\'"]+)'
        unquoted_matches = re.findall(unquoted_pattern, jql, re.IGNORECASE)
        search_terms.extend(unquoted_matches)
        
        return search_terms

    def _parse_jql_components(self, jql: str) -> Dict[str, Any]:
        """Parse JQL into its component parts."""
        # Separate ORDER BY clause
        order_by_clause = None
        jql_conditions = jql
        order_by_match = re.search(r"(?i)\bORDER BY\b", jql)
        if order_by_match:
            idx = order_by_match.start()
            jql_conditions = jql[:idx].strip()
            order_by_clause = jql[idx:].strip()
            # Remove the ORDER BY keyword
            order_by_clause = re.sub(r"(?i)^ORDER BY", "", order_by_clause).strip()

        # Extract search terms for generic strategies
        search_terms = self._extract_search_terms_from_jql(jql_conditions)
        
        return {
            "jql_conditions": jql_conditions,
            "order_by_clause": order_by_clause,
            "search_terms": search_terms
        }

    def search_issues(
        self,
        jql: str = "",
        strategy_name: str = "substring",
        limit: Optional[int] = None,
        additional_filters: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Search issues using JQL with generic search strategies.
        
        Args:
            jql: JQL query string
            strategy_name: Generic search strategy to use:
                - 'substring': Simple substring matching (always available)
                - 'whoosh': Advanced keyword search with indexing (requires: pip install whoosh)
                - 'semantic': Semantic/AI search (requires: pip install qdrant-client sentence-transformers)
                - 'fuzzy': Fuzzy string matching (requires: pip install rapidfuzz)
                - 'hybrid': Combines semantic + fuzzy (requires both qdrant and rapidfuzz)
            limit: Maximum number of results
            additional_filters: Additional metadata filters
            
        Returns:
            List of matching issues
            
        Examples:
            # Basic JQL with substring search
            jql_service.search_issues('summary ~ "bug"', strategy_name="substring")
            
            # Semantic search for conceptually similar terms
            jql_service.search_issues('summary ~ "authentication problem"', strategy_name="semantic")
            
            # Fuzzy search handles typos
            jql_service.search_issues('summary ~ "acess control"', strategy_name="fuzzy")
            
            # Hybrid combines multiple approaches
            jql_service.search_issues('summary ~ "performance issue"', strategy_name="hybrid")
        """
        from .utils import _parse_jql, _evaluate_expression, _get_sort_key
        
        # Validate query
        if jql and not jql.strip():
            raise ValueError("JQL query cannot be just whitespace")
        
        # Get all issues for JQL evaluation
        all_issues = self._reconstruct_issues_from_chunks(strategy_name)
        
        if not jql.strip():
            # Empty query returns all issues
            filtered_issues = all_issues
        else:
            # Parse JQL components
            jql_components = self._parse_jql_components(jql)
            jql_conditions = jql_components["jql_conditions"]
            order_by_clause = jql_components["order_by_clause"]
            search_terms = jql_components["search_terms"]
            
            # Track whether we used search strategy for text filtering
            used_search_strategy = False
            
            # Option 1: Use generic search strategy to pre-filter if we have search terms
            if search_terms and strategy_name != "substring":
                # Use generic strategy for initial filtering
                strategy = self.search_engine_manager.get_strategy_instance(strategy_name)
                search_query = " ".join(search_terms)
                
                # Get candidate documents from generic search
                candidate_docs = strategy.search(
                    query=search_query,
                    filter=additional_filters,
                    limit=None  # Don't limit at strategy level
                )
                
                # Convert back to issue format for JQL evaluation
                candidate_issues = []
                seen_issue_ids = set()
                for doc in candidate_docs:
                    if hasattr(doc, 'original_json_obj') and doc.original_json_obj:
                        issue = doc.original_json_obj
                        issue_id = issue.get('id')
                        if issue_id and issue_id not in seen_issue_ids:
                            candidate_issues.append(issue)
                            seen_issue_ids.add(issue_id)
                    elif isinstance(doc, dict) and 'id' in doc:
                        # Handle case where strategy returns issue objects directly
                        issue_id = doc.get('id')
                        if issue_id and issue_id not in seen_issue_ids:
                            candidate_issues.append(doc)
                            seen_issue_ids.add(issue_id)
                
                # Use candidates as the base set for JQL evaluation
                base_issues = candidate_issues if candidate_issues else all_issues
                used_search_strategy = True
            elif search_terms and strategy_name == "substring":
                # For substring strategy, we can still use it for pre-filtering
                strategy = self.search_engine_manager.get_strategy_instance(strategy_name)
                search_query = " ".join(search_terms)
                
                candidate_docs = strategy.search(
                    query=search_query,
                    filter=additional_filters,
                    limit=None
                )
                
                
                # Convert to issues
                candidate_issues = []
                seen_issue_ids = set()
                for doc in candidate_docs:
                    if isinstance(doc, dict) and 'id' in doc:
                        issue_id = doc.get('id')
                        if issue_id and issue_id not in seen_issue_ids:
                            candidate_issues.append(doc)
                            seen_issue_ids.add(issue_id)
                
                base_issues = candidate_issues if candidate_issues else all_issues
                used_search_strategy = True
            else:
                # Use all issues for JQL evaluation
                base_issues = all_issues
            
            # Parse JQL and apply conditions with search-strategy-aware evaluation
            if jql_conditions:
                expression = _parse_jql(jql_conditions)
                filtered_issues = []
                for issue in base_issues:
                    # If we used search strategy and have search terms, use smart evaluation
                    if used_search_strategy and search_terms:
                        if self._evaluate_expression_with_search_context(expression, issue, search_terms):
                            filtered_issues.append(issue)
                    else:
                        # Use standard JQL evaluation
                        if _evaluate_expression(expression, issue):
                            filtered_issues.append(issue)
            else:
                filtered_issues = base_issues
                
            # Apply ORDER BY if specified
            if order_by_clause:
                parts = order_by_clause.split()
                order_field = parts[0]
                order_dir = "ASC"
                if len(parts) > 1 and parts[1].upper() in ["ASC", "DESC"]:
                    order_dir = parts[1].upper()
                
                reverse = order_dir == "DESC"
                
                try:
                    filtered_issues = sorted(
                        filtered_issues,
                        key=lambda issue: _get_sort_key(issue, order_field),
                        reverse=reverse,
                    )
                except Exception:
                    # If sorting fails, continue without sorting
                    pass

        # Apply additional filters
        if additional_filters:
            temp_filtered = []
            for issue in filtered_issues:
                match = True
                for filter_key, filter_value in additional_filters.items():
                    issue_value = issue.get("fields", {}).get(filter_key)
                    if str(issue_value) != str(filter_value):
                        match = False
                        break
                if match:
                    temp_filtered.append(issue)
            filtered_issues = temp_filtered

        # Apply limit
        if limit is not None:
            filtered_issues = filtered_issues[:limit]

        return filtered_issues

    def _evaluate_expression_with_search_context(self, expr, issue: dict, search_terms: List[str]) -> bool:
        """
        Evaluates JQL expression with search context awareness.
        For text-based conditions that match our search terms, we can use the search strategy results
        but only if we're confident the search strategy actually filtered properly.
        Otherwise, fall back to strict JQL evaluation.
        """
        from .utils import _evaluate_expression
        
        if expr['type'] == 'always_true':
            return True

        if expr['type'] == 'logical':
            operator = expr['operator']
            if operator == 'AND':
                return all(self._evaluate_expression_with_search_context(child, issue, search_terms) for child in expr['children'])
            elif operator == 'OR':
                return any(self._evaluate_expression_with_search_context(child, issue, search_terms) for child in expr['children'])
            elif operator == 'NOT':
                return not self._evaluate_expression_with_search_context(expr['child'], issue, search_terms)

        if expr['type'] == 'condition':
            
            # This ensures that text conditions like summary ~ "bug" are evaluated
            # against the actual issue content, not just trusted from search strategy
            return _evaluate_expression(expr, issue)

        return False


# Global instance
jql_service = JQLService() 