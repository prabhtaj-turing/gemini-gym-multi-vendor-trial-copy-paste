import pytest
import workday as WorkdayStrategicSourcingAPI


def _prep_db():
    """Utility: reset DB with a single supplier company."""
    WorkdayStrategicSourcingAPI.SimulationEngine.db.DB.clear()
    WorkdayStrategicSourcingAPI.SimulationEngine.db.DB["suppliers"] = {
        "supplier_companies": {
            1: {
                "id": 1,
                "external_id": "ext-1234",
                "name": "Acme Corp",
                "description": "Original description",
                "public": True,
                "segmentation": "tier1",
                "segmentation_status": "active",
                "segmentation_notes": "Original notes",
                "tags": ["original", "tag"],
                "url": "https://acme.com",
                "duns_number": "123456789",
                "self_registered": False,
                "onboarding_form_completion_status": "completed",
                "accept_all_currencies": True,
                "updated_at": "2023-01-01T00:00:00Z",
                "custom_fields": [
                    {"name": "field1", "value": "original_value"}
                ],
                "relationships": {
                    "supplier_category": {"id": 1},
                    "supplier_groups": [{"id": 1}, {"id": 2}]
                }
            }
        }
    }


def test_patch_invalid_include_relationship():
    _prep_db()
    body = {"id": "ext-1234", "name": "Updated"}
    with pytest.raises(ValueError, match="Invalid include relationship"):
        WorkdayStrategicSourcingAPI.SupplierCompanyByExternalId.patch(
            "ext-1234", _include="invalid_rel", body=body
        )


def test_patch_invalid_external_id_format():
    _prep_db()
    body = {"id": "bad#id", "name": "Updated"}
    with pytest.raises(ValueError, match="Invalid external_id format"):
        WorkdayStrategicSourcingAPI.SupplierCompanyByExternalId.patch(
            "bad#id", body=body
        )


def test_patch_body_not_dict():
    _prep_db()
    with pytest.raises(ValueError, match="Body must be a JSON object"):
        WorkdayStrategicSourcingAPI.SupplierCompanyByExternalId.patch(
            "ext-1234", body="not a dict"
        )


def test_patch_body_required():
    """Test that body is required."""
    _prep_db()
    with pytest.raises(ValueError, match="Body is required"):
        WorkdayStrategicSourcingAPI.SupplierCompanyByExternalId.patch(
            "ext-1234", body=None
        )


def test_patch_empty_external_id():
    """Test validation of empty external_id."""
    _prep_db()
    body = {"id": "ext-1234", "name": "Updated"}
    with pytest.raises(ValueError, match="Invalid external_id"):
        WorkdayStrategicSourcingAPI.SupplierCompanyByExternalId.patch(
            "", body=body
        )


def test_patch_whitespace_external_id():
    """Test validation of whitespace-only external_id."""
    _prep_db()
    body = {"id": "ext-1234", "name": "Updated"}
    with pytest.raises(ValueError, match="Invalid external_id"):
        WorkdayStrategicSourcingAPI.SupplierCompanyByExternalId.patch(
            "   ", body=body
        )


def test_patch_non_string_external_id():
    """Test validation of non-string external_id."""
    _prep_db()
    body = {"id": "ext-1234", "name": "Updated"}
    with pytest.raises(ValueError, match="Invalid external_id"):
        WorkdayStrategicSourcingAPI.SupplierCompanyByExternalId.patch(
            123, body=body
        )


def test_patch_invalid_include_type():
    """Test validation of non-string _include parameter."""
    _prep_db()
    body = {"id": "ext-1234", "name": "Updated"}
    with pytest.raises(ValueError, match="_include must be a comma-separated string"):
        WorkdayStrategicSourcingAPI.SupplierCompanyByExternalId.patch(
            "ext-1234", _include=123, body=body
        )


def test_patch_multiple_invalid_includes():
    """Test validation of multiple invalid include relationships."""
    _prep_db()
    body = {"id": "ext-1234", "name": "Updated"}
    with pytest.raises(ValueError, match="Invalid include relationship\\(s\\): invalid1, invalid2"):
        WorkdayStrategicSourcingAPI.SupplierCompanyByExternalId.patch(
            "ext-1234", _include="invalid1,invalid2,attachments", body=body
        )


def test_patch_company_not_found():
    """Test when company with external_id doesn't exist."""
    _prep_db()
    body = {"id": "nonexistent", "name": "Updated"}
    with pytest.raises(FileNotFoundError, match="Company not found"):
        WorkdayStrategicSourcingAPI.SupplierCompanyByExternalId.patch(
            "nonexistent", body=body
        )


def test_patch_id_mismatch():
    """Test when body id doesn't match external_id."""
    _prep_db()
    body = {"id": "different-id", "name": "Updated"}
    with pytest.raises(ValueError, match="External id in body must match url"):
        WorkdayStrategicSourcingAPI.SupplierCompanyByExternalId.patch(
            "ext-1234", body=body
        )


def test_patch_successful_name_update():
    """Test successful update of company name."""
    _prep_db()
    body = {"id": "ext-1234", "name": "Updated Acme Corp"}
    response = WorkdayStrategicSourcingAPI.SupplierCompanyByExternalId.patch(
        "ext-1234", body=body
    )
    assert response["name"] == "Updated Acme Corp"
    assert response["external_id"] == "ext-1234"
    assert response["id"] == 1


def test_patch_successful_attributes_update():
    """Test successful update using attributes dictionary."""
    _prep_db()
    body = {
        "id": "ext-1234",
        "attributes": {
            "description": "Updated description",
            "public": False,
            "segmentation": "tier2",
            "segmentation_status": "pending",
            "segmentation_notes": "Updated notes",
            "tags": ["updated", "tags"],
            "url": "https://updated-acme.com",
            "duns_number": "987654321",
            "self_registered": True,
            "onboarding_form_completion_status": "in_progress",
            "accept_all_currencies": False,
            "custom_fields": [
                {"name": "field1", "value": "updated_value"},
                {"name": "field2", "value": "new_value"}
            ]
        }
    }
    response = WorkdayStrategicSourcingAPI.SupplierCompanyByExternalId.patch(
        "ext-1234", body=body
    )
    assert response["description"] == "Updated description"
    assert response["public"] is False
    assert response["segmentation"] == "tier2"
    assert response["segmentation_status"] == "pending"
    assert response["segmentation_notes"] == "Updated notes"
    assert response["tags"] == ["updated", "tags"]
    assert response["url"] == "https://updated-acme.com"
    assert response["duns_number"] == "987654321"
    assert response["self_registered"] is True
    assert response["onboarding_form_completion_status"] == "in_progress"
    assert response["accept_all_currencies"] is False
    assert len(response["custom_fields"]) == 2


def test_patch_successful_mixed_update():
    """Test successful update using both root-level and attributes."""
    _prep_db()
    body = {
        "id": "ext-1234",
        "name": "Mixed Update Corp",
        "attributes": {
            "description": "Mixed update description",
            "public": False
        }
    }
    response = WorkdayStrategicSourcingAPI.SupplierCompanyByExternalId.patch(
        "ext-1234", body=body
    )
    assert response["name"] == "Mixed Update Corp"
    assert response["description"] == "Mixed update description"
    assert response["public"] is False


def test_patch_with_include_attachments():
    """Test successful update with include parameter for attachments."""
    _prep_db()
    body = {"id": "ext-1234", "name": "Updated with Include"}
    response = WorkdayStrategicSourcingAPI.SupplierCompanyByExternalId.patch(
        "ext-1234", _include="attachments", body=body
    )
    assert response["name"] == "Updated with Include"
    assert "included" in response
    assert "attachments" in response["included"]


def test_patch_with_multiple_includes():
    """Test successful update with multiple include parameters."""
    _prep_db()
    body = {"id": "ext-1234", "name": "Updated with Multiple Includes"}
    response = WorkdayStrategicSourcingAPI.SupplierCompanyByExternalId.patch(
        "ext-1234", 
        _include="attachments,supplier_category,supplier_groups", 
        body=body
    )
    assert response["name"] == "Updated with Multiple Includes"
    assert "included" in response
    assert "attachments" in response["included"]
    assert "supplier_category" in response["included"]
    assert "supplier_groups" in response["included"]


def test_patch_with_whitespace_includes():
    """Test include parameter with whitespace around values."""
    _prep_db()
    body = {"id": "ext-1234", "name": "Updated with Whitespace"}
    response = WorkdayStrategicSourcingAPI.SupplierCompanyByExternalId.patch(
        "ext-1234", 
        _include=" attachments , supplier_category ", 
        body=body
    )
    assert response["name"] == "Updated with Whitespace"
    assert "included" in response
    assert "attachments" in response["included"]
    assert "supplier_category" in response["included"]


def test_patch_with_empty_include():
    """Test include parameter with empty string."""
    _prep_db()
    body = {"id": "ext-1234", "name": "Updated with Empty Include"}
    response = WorkdayStrategicSourcingAPI.SupplierCompanyByExternalId.patch(
        "ext-1234", _include="", body=body
    )
    assert response["name"] == "Updated with Empty Include"
    assert "included" not in response


def test_patch_with_relationships():
    """Test update with relationships (should be passed through)."""
    _prep_db()
    body = {
        "id": "ext-1234",
        "name": "Updated with Relationships",
        "relationships": {
            "supplier_category": {"id": 5},
            "supplier_groups": [{"id": 10}, {"id": 20}],
            "default_payment_term": {"id": 1},
            "payment_types": [{"id": 1}, {"id": 2}],
            "default_payment_type": {"id": 1},
            "payment_currencies": [{"id": 1}],
            "default_payment_currency": {"id": 1},
            "attachments": [{"id": 1, "type": "attachments"}],
            "supplier_classification_values": [{"id": "class1"}]
        }
    }
    response = WorkdayStrategicSourcingAPI.SupplierCompanyByExternalId.patch(
        "ext-1234", body=body
    )
    assert response["name"] == "Updated with Relationships"
    # Relationships should be preserved in the response
    assert "relationships" in response


def test_patch_with_type_field():
    """Test update with type field."""
    _prep_db()
    body = {
        "id": "ext-1234",
        "type": "supplier_companies",
        "name": "Updated with Type"
    }
    response = WorkdayStrategicSourcingAPI.SupplierCompanyByExternalId.patch(
        "ext-1234", body=body
    )
    assert response["name"] == "Updated with Type"


def test_patch_preserve_existing_fields():
    """Test that fields not in update are preserved."""
    _prep_db()
    body = {"id": "ext-1234", "name": "Only Name Updated"}
    response = WorkdayStrategicSourcingAPI.SupplierCompanyByExternalId.patch(
        "ext-1234", body=body
    )
    assert response["name"] == "Only Name Updated"
    # Other fields should be preserved
    assert response["description"] == "Original description"
    assert response["public"] is True
    assert response["tags"] == ["original", "tag"]


def test_patch_with_none_attributes():
    """Test update with None attributes (should not cause issues)."""
    _prep_db()
    body = {
        "id": "ext-1234",
        "attributes": None,
        "name": "Updated with None Attributes"
    }
    response = WorkdayStrategicSourcingAPI.SupplierCompanyByExternalId.patch(
        "ext-1234", body=body
    )
    assert response["name"] == "Updated with None Attributes"


def test_patch_with_empty_attributes():
    """Test update with empty attributes dictionary."""
    _prep_db()
    body = {
        "id": "ext-1234",
        "attributes": {},
        "name": "Updated with Empty Attributes"
    }
    response = WorkdayStrategicSourcingAPI.SupplierCompanyByExternalId.patch(
        "ext-1234", body=body
    )
    assert response["name"] == "Updated with Empty Attributes"


def test_patch_with_none_name():
    """Test update with None name (should be ignored)."""
    _prep_db()
    body = {"id": "ext-1234", "name": None}
    response = WorkdayStrategicSourcingAPI.SupplierCompanyByExternalId.patch(
        "ext-1234", body=body
    )
    # Name should remain unchanged
    assert response["name"] == "Acme Corp"


def test_patch_external_id_with_special_chars():
    """Test external_id with special characters that should be allowed."""
    _prep_db()
    # Add a company with special characters in external_id
    WorkdayStrategicSourcingAPI.SimulationEngine.db.DB["suppliers"]["supplier_companies"][2] = {
        "id": 2,
        "external_id": "ext-5678-with-dashes",
        "name": "Special Chars Corp"
    }
    
    body = {"id": "ext-5678-with-dashes", "name": "Updated Special Chars"}
    response = WorkdayStrategicSourcingAPI.SupplierCompanyByExternalId.patch(
        "ext-5678-with-dashes", body=body
    )
    assert response["name"] == "Updated Special Chars"
    assert response["external_id"] == "ext-5678-with-dashes"


def test_patch_external_id_with_numbers():
    """Test external_id with numbers."""
    _prep_db()
    # Add a company with numbers in external_id
    WorkdayStrategicSourcingAPI.SimulationEngine.db.DB["suppliers"]["supplier_companies"][3] = {
        "id": 3,
        "external_id": "ext123456",
        "name": "Numbers Corp"
    }
    
    body = {"id": "ext123456", "name": "Updated Numbers"}
    response = WorkdayStrategicSourcingAPI.SupplierCompanyByExternalId.patch(
        "ext123456", body=body
    )
    assert response["name"] == "Updated Numbers"
    assert response["external_id"] == "ext123456"


def test_patch_external_id_with_uppercase():
    """Test external_id with uppercase letters."""
    _prep_db()
    # Add a company with uppercase in external_id
    WorkdayStrategicSourcingAPI.SimulationEngine.db.DB["suppliers"]["supplier_companies"][4] = {
        "id": 4,
        "external_id": "EXT-UPPERCASE",
        "name": "Uppercase Corp"
    }
    
    body = {"id": "EXT-UPPERCASE", "name": "Updated Uppercase"}
    response = WorkdayStrategicSourcingAPI.SupplierCompanyByExternalId.patch(
        "EXT-UPPERCASE", body=body
    )
    assert response["name"] == "Updated Uppercase"
    assert response["external_id"] == "EXT-UPPERCASE"


def test_patch_with_extra_fields():
    """Test update with extra fields not in the model (should be allowed)."""
    _prep_db()
    body = {
        "id": "ext-1234",
        "name": "Updated with Extra Fields",
        "extra_field1": "extra_value1",
        "extra_field2": {"nested": "value"},
        "attributes": {
            "description": "Updated description",
            "extra_attribute": "extra_attr_value"
        }
    }
    response = WorkdayStrategicSourcingAPI.SupplierCompanyByExternalId.patch(
        "ext-1234", body=body
    )
    assert response["name"] == "Updated with Extra Fields"
    assert response["description"] == "Updated description"


def test_patch_database_structure_initialization():
    """Test that the function properly initializes database structure if missing."""
    # Clear DB completely
    WorkdayStrategicSourcingAPI.SimulationEngine.db.DB.clear()
    
    # Add a company directly to test initialization
    WorkdayStrategicSourcingAPI.SimulationEngine.db.DB["suppliers"] = {
        "supplier_companies": {
            1: {
                "id": 1,
                "external_id": "ext-1234",
                "name": "Test Corp"
            }
        }
    }
    
    body = {"id": "ext-1234", "name": "Updated Test Corp"}
    response = WorkdayStrategicSourcingAPI.SupplierCompanyByExternalId.patch(
        "ext-1234", body=body
    )
    assert response["name"] == "Updated Test Corp"


def test_patch_complex_custom_fields():
    """Test update with complex custom fields."""
    _prep_db()
    body = {
        "id": "ext-1234",
        "attributes": {
            "custom_fields": [
                {"name": "string_field", "value": "string_value"},
                {"name": "number_field", "value": 42},
                {"name": "boolean_field", "value": True},
                {"name": "list_field", "value": ["item1", "item2"]},
                {"name": "dict_field", "value": {"key": "value"}},
                {"name": "null_field", "value": None}
            ]
        }
    }
    response = WorkdayStrategicSourcingAPI.SupplierCompanyByExternalId.patch(
        "ext-1234", body=body
    )
    assert len(response["custom_fields"]) == 6
    assert response["custom_fields"][0]["value"] == "string_value"
    assert response["custom_fields"][1]["value"] == 42
    assert response["custom_fields"][2]["value"] is True
    assert response["custom_fields"][3]["value"] == ["item1", "item2"]
    assert response["custom_fields"][4]["value"] == {"key": "value"}
    assert response["custom_fields"][5]["value"] is None 