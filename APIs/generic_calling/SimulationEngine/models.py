from typing import List, Optional, Literal, Union, Dict, Any
from pydantic import BaseModel, Field, field_validator
from datetime import datetime, timezone
from enum import Enum



class RecipientEndpointModel(BaseModel):
    """
    Represents a single endpoint for a recipient. Corresponds to the
    'Endpoint' schema in the OpenAPI specification.
    """
    endpoint_type: Literal["PHONE_NUMBER", "WHATSAPP_PROFILE"] = Field(..., description="Type of endpoint")
    endpoint_value: str = Field(..., description="The endpoint value (e.g., phone number)")
    endpoint_label: Optional[str] = Field(None, description="Label for the endpoint")


class RecipientInfoModel(BaseModel):
    """
    Represents the recipient_info parameter for the make_call function.
    This model matches the expected structure of the recipient_info dict parameter.
    """
    name: str = Field(..., description="Name of the recipient")
    recipient_type: Optional[Literal["CONTACT", "BUSINESS", "DIRECT", "VOICEMAIL"]] = Field(
        None, description="Type of recipient"
    )
    address: Optional[str] = Field(None, description="Address of the recipient")
    distance: Optional[str] = Field(None, description="Distance to the recipient")

    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        """Ensure name is not empty string."""
        if v is not None and v.strip() == "":
            raise ValueError("name cannot be empty string")
        return v


class RecipientModel(BaseModel):
    """
    Represents the recipient of a phone call. Corresponds to the
    'Recipient' schema specification.
    """
    contact_id: Optional[str] = Field(None, description="Unique identifier for the contact")
    contact_name: Optional[str] = Field(None, description="Name of the contact")
    contact_endpoints: Optional[List[RecipientEndpointModel]] = Field(None,
                                                                      description="List of endpoints for the contact")
    contact_photo_url: Optional[str] = Field(None, description="URL to the contact's profile photo")
    recipient_type: Optional[Literal["CONTACT", "BUSINESS", "DIRECT", "VOICEMAIL"]] = Field(
        None, description="Type of recipient"
    )
    address: Optional[str] = Field(None, description="Address of the recipient")
    distance: Optional[str] = Field(None, description="Distance to the recipient")
    confidence_level: Optional[Literal["LOW", "MEDIUM", "HIGH"]] = Field(None,
                                                                         description="Confidence level of the recipient match")

    @field_validator('contact_name')
    @classmethod
    def validate_contact_name(cls, v):
        """Ensure contact_name is not empty string if provided."""
        if v is not None and v.strip() == "":
            raise ValueError("contact_name cannot be empty string")
        return v

    @field_validator('contact_endpoints')
    @classmethod
    def validate_contact_endpoints(cls, v):
        """Ensure contact_endpoints is not empty list if provided."""
        if v is not None and len(v) == 0:
            raise ValueError("contact_endpoints cannot be empty list")
        return v