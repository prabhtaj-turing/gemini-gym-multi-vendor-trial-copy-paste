from typing import List, Dict, Any

from common_utils.search_engine.adapter import Adapter
from common_utils.search_engine.engine import search_engine_manager
from common_utils.search_engine.models import SearchableDocument

from .db import DB


class ServiceAdapter(Adapter):
    """Adapter for converting CES Account Management database into searchable documents."""

    def db_to_searchable_documents(self) -> List[SearchableDocument]:
        """Convert the CES Account Management database into searchable documents."""
        searchable_documents = []

        # Get orders from all accounts
        order_details = DB.get("orderDetails", {})
        for order_id, order_data in order_details.items():
            searchable_doc = self._create_order_document(order_id, order_data)
            searchable_documents.append(searchable_doc)

        activation_guides = DB.get("activationGuides", {})
        for title, content in activation_guides.items():
            searchable_doc = self._create_activation_guide_document(title, content)
            searchable_documents.append(searchable_doc)

        return searchable_documents

    def _create_order_document(
        self, order_id: str, order_data: Dict[str, Any]
    ) -> SearchableDocument:
        """Create a SearchableDocument from order data."""
        # Create searchable text content from order information
        text_content_parts = []


        if "order_id" in order_data and order_data["order_id"]:
            text_content_parts.append(f'Order ID: {order_data["order_id"]}')
        if "appointment_technician_notes" in order_data and order_data["appointment_technician_notes"]:
            text_content_parts.append(f'Appointment Technician Notes: {order_data["appointment_technician_notes"]}')
        if "appointment_status" in order_data and order_data["appointment_status"]:
            text_content_parts.append(f'Appointment Status: {order_data["appointment_status"]}')
        if "appointment_visit_id" in order_data and order_data["appointment_visit_id"]:
            text_content_parts.append(f'Appointment Visit ID: {order_data["appointment_visit_id"]}')
        if "equipment_tracking_number" in order_data and order_data["equipment_tracking_number"]:
            text_content_parts.append(f'Equipment Tracking Number: {order_data["equipment_tracking_number"]}')
        if "equipment_device_name" in order_data and order_data["equipment_device_name"]:
            text_content_parts.append(f'Equipment Device Name: {order_data["equipment_device_name"]}')
        if "appointment_scheduled_start_time" in order_data and order_data["appointment_scheduled_start_time"]:
            text_content_parts.append(f'Appointment Scheduled Start Time: {order_data["appointment_scheduled_start_time"]}')
        if "equipment_shipping_status" in order_data and order_data["equipment_shipping_status"]:
            text_content_parts.append(f'Equipment Shipping Status: {order_data["equipment_shipping_status"]}')
        if "service_activation_status" in order_data and order_data["service_activation_status"]:
            text_content_parts.append(f'Service Activation Status: {order_data["service_activation_status"]}')
        if "equipment_tracking_url" in order_data and order_data["equipment_tracking_url"]:
            text_content_parts.append(f'Equipment Tracking Url: {order_data["equipment_tracking_url"]}')
        if "service_type" in order_data and order_data["service_type"]:
            text_content_parts.append(f'Service Type: {order_data["service_type"]}')
        if "appointment_scheduled_end_time" in order_data and order_data["appointment_scheduled_end_time"]:
            text_content_parts.append(f'Appointment Scheduled End Time: {order_data["appointment_scheduled_end_time"]}')
        if "service_name" in order_data and order_data["service_name"]:
            text_content_parts.append(f'Service Name: {order_data["service_name"]}')
        if "overall_order_status" in order_data and order_data["overall_order_status"]:
            text_content_parts.append(f'Overall Order Status: {order_data["overall_order_status"]}')
        if "contact_phone" in order_data and order_data["contact_phone"]:
            text_content_parts.append(f'Contact Phone: {order_data["contact_phone"]}')
        if "customer_name" in order_data and order_data["customer_name"]:
            text_content_parts.append(f'Customer Name: {order_data["customer_name"]}')
        if "order_date" in order_data and order_data["order_date"]:
            text_content_parts.append(f'Order Date: {order_data["order_date"]}')
        if "service_identifier_for_activation" in order_data and order_data["service_identifier_for_activation"]:
            text_content_parts.append(f'Service Identifier For Activation: {order_data["service_identifier_for_activation"]}')
        if "equipment_delivery_date_estimate" in order_data and order_data["equipment_delivery_date_estimate"]:
            text_content_parts.append(f'Equipment Delivery Date Estimate: {order_data["equipment_delivery_date_estimate"]}')
        if "account_id" in order_data and order_data["account_id"]:
            text_content_parts.append(f'Account ID: {order_data["account_id"]}')


        # Combine all text content
        text_content = " ".join(text_content_parts)

        # Create metadata for filtering
        metadata = {
            "order_id": order_id,
            "account_id": order_data.get("account_id"),
            "appointment_technician_notes": order_data.get("appointment_technician_notes", "UNKNOWN"),
            "appointment_status": order_data.get("appointment_status", "UNKNOWN"),
            "appointment_visit_id": order_data.get("appointment_visit_id", "UNKNOWN"),
            "equipment_tracking_number": order_data.get("equipment_tracking_number", "UNKNOWN"),
            "equipment_device_name": order_data.get("equipment_device_name", "UNKNOWN"),
            "appointment_scheduled_start_time": order_data.get("appointment_scheduled_start_time", "UNKNOWN"),
            "equipment_shipping_status": order_data.get("equipment_shipping_status", "UNKNOWN"),
            "service_activation_status": order_data.get("service_activation_status", "UNKNOWN"),
            "equipment_tracking_url": order_data.get("equipment_tracking_url", "UNKNOWN"),
            "service_type": order_data.get("service_type", "UNKNOWN"),
            "appointment_scheduled_end_time": order_data.get("appointment_scheduled_end_time", "UNKNOWN"),
            "service_name": order_data.get("service_name", "UNKNOWN"),
            "overall_order_status": order_data.get("overall_order_status", "UNKNOWN"),
            "contact_phone": order_data.get("contact_phone", "UNKNOWN"),
            "customer_name": order_data.get("customer_name", "UNKNOWN"),
            "order_date": order_data.get("order_date", "UNKNOWN"),
            "service_identifier_for_activation": order_data.get("service_identifier_for_activation", "UNKNOWN"),
            "equipment_delivery_date_estimate": order_data.get("equipment_delivery_date_estimate", "UNKNOWN"),
            "content_type": "order",
            "service": "ces_system_activation",
        }
        
        return SearchableDocument(
            parent_doc_id=order_id,
            text_content=text_content,
            metadata=metadata,
            original_json_obj=order_data,
        )

    def _create_activation_guide_document(
        self, title: str, guide_data: Dict[str, Any]
    ) -> SearchableDocument:
        """Create a SearchableDocument from activation guide data."""
        text_content_parts = []

        if guide_data.get("title"):
            text_content_parts.append(guide_data["title"])
        if guide_data.get("appliesTo"):
            text_content_parts.append(f'Applies to: {guide_data["appliesTo"]}')
        if guide_data.get("keywords"):
            text_content_parts.append(f'Keywords: {", ".join(guide_data["keywords"])}')
        if guide_data.get("introduction"):
            text_content_parts.append(guide_data["introduction"])

        if guide_data.get("whatsInTheBox"):
            text_content_parts.append(
                f'Whats in the box: {", ".join(guide_data["whatsInTheBox"])}'
            )

        if guide_data.get("prerequisites"):
            text_content_parts.append(
                f'Prerequisites: {", ".join(guide_data["prerequisites"])}'
            )

        if guide_data.get("processOverview"):
            text_content_parts.append(
                f'Process Overview: {guide_data["processOverview"]}'
            )

        if guide_data.get("steps"):
            steps_text_parts = ["Steps:"]
            for step in guide_data["steps"]:
                step_text = (
                    f"Step {step.get('step')}: {step.get('title')}. "
                    f"{step.get('description', '')}"
                )
                if "instructions" in step:
                    instructions = step["instructions"]
                    if "iOS (iPhone)" in instructions:
                        step_text += (
                            " For iOS (iPhone): "
                            + " ".join(instructions["iOS (iPhone)"])
                        )
                    if "Android (Samsung/Pixel)" in instructions:
                        step_text += (
                            " For Android (Samsung/Pixel): "
                            + " ".join(instructions["Android (Samsung/Pixel)"])
                        )
                steps_text_parts.append(step_text)
            text_content_parts.append(" ".join(steps_text_parts))

        if guide_data.get("troubleshooting"):
            troubleshooting_parts = ["Troubleshooting:"]
            for item in guide_data["troubleshooting"]:
                troubleshooting_parts.append(
                    f"{item.get('problem')} {item.get('solution')}"
                )
            text_content_parts.append(" ".join(troubleshooting_parts))

        text_content = " ".join(text_content_parts)

        metadata = {
            "title": guide_data.get("title"),
            "applies_to": guide_data.get("appliesTo"),
            "last_updated": guide_data.get("lastUpdated"),
            "keywords": guide_data.get("keywords", []),
            "content_type": "activation_guide",
            "service": "ces_system_activation",
        }

        return SearchableDocument(
            parent_doc_id=title,
            text_content=text_content,
            metadata=metadata,
            original_json_obj=guide_data,
        )


service_adapter = ServiceAdapter()
search_engine_manager = search_engine_manager.get_engine_manager(
    "ces_system_activation"
)

search_engine_manager.override_strategy_for_engine(strategy_name="semantic")

__all__ = [
    "search_engine_manager",
    "service_adapter",
]