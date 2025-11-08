import os
from typing import List, Dict, Any
from common_utils.search_engine.adapter import Adapter
from common_utils.search_engine.models import SearchableDocument
from common_utils.search_engine.engine import search_engine_manager
from .db import DB


class ServiceAdapter(Adapter):
    """Adapter for converting CES Account Management database into searchable documents."""

    def db_to_searchable_documents(self) -> List[SearchableDocument]:
        """Convert the CES Account Management database into searchable documents."""
        searchable_documents = []

        # Get orders from all accounts
        account_details = DB.get("accountDetails", {})
        for account_id, account_data in account_details.items():
            orders = account_data.get("orders", {})
            if orders:
                for order_id, order_data in orders.items():
                    searchable_doc = self._create_order_document(order_id, order_data, account_id)
                    searchable_documents.append(searchable_doc)

        return searchable_documents

    def _create_order_document(
        self, order_id: str, order_data: Dict[str, Any], account_id: str
    ) -> SearchableDocument:
        """Create a SearchableDocument from order data."""
        # Create searchable text content from order information
        text_content_parts = []

        # Add order ID
        if "orderId" in order_data and order_data["orderId"]:
            text_content_parts.append(f"Order ID: {order_data['orderId']}")

        # Add order type
        if "orderType" in order_data and order_data["orderType"]:
            text_content_parts.append(f"Order type: {order_data['orderType']}")

        # Add status
        if "status" in order_data and order_data["status"]:
            text_content_parts.append(f"Status: {order_data['status']}")

        # Add status description
        if "statusDescription" in order_data and order_data["statusDescription"]:
            text_content_parts.append(order_data["statusDescription"])

        # Add order date
        if "orderDate" in order_data and order_data["orderDate"]:
            text_content_parts.append(f"Order date: {order_data['orderDate']}")

        # Add estimated completion date
        if "estimatedCompletionDate" in order_data and order_data["estimatedCompletionDate"]:
            text_content_parts.append(f"Estimated completion: {order_data['estimatedCompletionDate']}")

        # Add account ID
        text_content_parts.append(f"Account: {account_id}")

        # Combine all text content
        text_content = " ".join(text_content_parts)

        # Create metadata for filtering
        metadata = {
            "order_id": order_id,
            "account_id": account_id,
            "order_type": order_data.get("orderType", "UNKNOWN"),
            "status": order_data.get("status", "UNKNOWN"),
            "order_date": order_data.get("orderDate"),
            "estimated_completion_date": order_data.get("estimatedCompletionDate"),
            "content_type": "order",
            "service": "ces_account_management",
        }

        return SearchableDocument(
            parent_doc_id=order_id,
            text_content=text_content,
            metadata=metadata,
            original_json_obj=order_data,
        )


service_adapter = ServiceAdapter()
search_engine_manager = search_engine_manager.get_engine_manager(
    "ces_account_management"
)

# Smart strategy selection: use semantic search if API key is available, otherwise use fuzzy
if os.environ.get("GOOGLE_API_KEY") or os.environ.get("GOOGLE_GENAI_USE_VERTEXAI"):
    # Use semantic search for embedding-based querying when API key is available
    search_engine_manager.override_strategy_for_engine(strategy_name="semantic")
else:
    # Use fuzzy search for better matching without requiring external API calls
    search_engine_manager.override_strategy_for_engine(strategy_name="fuzzy")

__all__ = [
    "search_engine_manager",
    "service_adapter",
]
