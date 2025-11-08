from typing import List, Dict, Any
from common_utils.search_engine.models import SearchableDocument
from common_utils.search_engine.adapter import Adapter
from common_utils.search_engine.engine import search_engine_manager
from .db import DB


class ServiceAdapter(Adapter):
    """Adapter for converting Canva database into searchable documents."""

    def db_to_searchable_documents(self) -> List[SearchableDocument]:
        """
        Convert the Canva database into searchable documents.

        Returns:
            List[SearchableDocument]: List of searchable documents for all designs.
        """
        searchable_documents = []
        
        # Get designs from the database
        designs = DB.get("Designs", {})
        
        for design_id, design_data in designs.items():
            searchable_doc = self._adapt_design(design_id, design_data)
            searchable_documents.append(searchable_doc)
        
        return searchable_documents

    def _adapt_design(self, design_id: str, design_data: Dict[str, Any]) -> SearchableDocument:
        """
        Adapt a design to a searchable document.

        Args:
            design_id (str): The design's unique identifier.
            design_data (Dict[str, Any]): The complete design data from the database.

        Returns:
            SearchableDocument: The searchable document for the design.
        """
        # Extract key fields for search
        title = design_data.get("title", "")
        design_type = design_data.get("design_type", {})
        design_type_name = design_type.get("name", "") if isinstance(design_type, dict) else ""
        
        # Build searchable text content combining title and design type
        text_content = f"{title}"
        if design_type_name:
            text_content += f" {design_type_name}"
        
        # Extract ownership information
        owner = design_data.get("owner", {})
        user_id = owner.get("user_id") if isinstance(owner, dict) else None
        team_id = owner.get("team_id") if isinstance(owner, dict) else None
        
        # Create metadata for filtering
        metadata = {
            "content_type": "design",
            "design_id": design_id,
            "title": title,
            "design_type": design_type_name,
            "user_id": user_id,
            "team_id": team_id,
            "created_at": design_data.get("created_at"),
            "updated_at": design_data.get("updated_at"),
        }

        return SearchableDocument(
            parent_doc_id=design_id,
            text_content=text_content,
            metadata=metadata,
            original_json_obj=design_data,
        )


service_adapter = ServiceAdapter()
search_engine_manager = search_engine_manager.get_engine_manager("canva")

__all__ = ["service_adapter", "search_engine_manager"]
