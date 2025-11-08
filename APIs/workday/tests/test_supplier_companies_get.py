import workday as WorkdayStrategicSourcingAPI
from ..SimulationEngine import db
import pytest

def setup_test_db():
    """Setup test database with API-compliant test data."""
    # Clear existing data
    db.DB.clear()
    
    # Setup attachments
    db.DB["attachments"] = {
        "1": {"type": "attachments", "id": "1", "name": "contract.pdf", "uploaded_by": "USR1"},
        "2": {"type": "attachments", "id": "2", "name": "invoice.xlsx", "uploaded_by": "USR2"},
    }

    # Setup suppliers with API-compliant test data
    db.DB["suppliers"] = {"supplier_companies": {}}
    
    # Company 1 - with full API structure
    db.DB["suppliers"]["supplier_companies"][1] = {
        "type": "supplier_companies",
        "id": 1,
        "attributes": {
            "name": "Supplier A",
            "description": "First supplier company",
            "external_id": "EXT1",
            "segmentation_status": "approved",
            "updated_at": "2023-01-01T00:00:00Z",
            "is_suggested": False,
            "public": True,
            "segmentation": "tier_1",
            "segmentation_notes": "Top tier supplier",
            "tags": ["electronics", "hardware"],
            "url": "https://supplier-a.com",
            "duns_number": "123456789",
            "self_registered": False,
            "onboarding_form_completion_status": "completed",
            "accept_all_currencies": True,
            "custom_fields": [
                {"name": "Industry", "value": "Technology"},
                {"name": "Region", "value": "North America"}
            ]
        },
        "relationships": {
            "attachments": {
                "data": [{"id": "1", "type": "attachments"}]
            }
        },
    }
    
    # Company 2 - minimal structure
    db.DB["suppliers"]["supplier_companies"][2] = {
        "type": "supplier_companies",
        "id": 2,
        "attributes": {
            "name": "Supplier B",
            "external_id": "EXT2",
            "segmentation_status": "approved",
            "updated_at": "2023-02-01T00:00:00Z",
        },
    }
    
    # Company 3 - different status
    db.DB["suppliers"]["supplier_companies"][3] = {
        "type": "supplier_companies",
        "id": 3,
        "attributes": {
            "name": "Supplier C",
            "external_id": "",
            "segmentation_status": "pending",
            "updated_at": "2023-03-01T00:00:00Z",
        },
    }

    return db.DB


class TestSupplierCompaniesGet:
    """Comprehensive tests for SupplierCompanies.get function following API documentation."""
    
    def setup_method(self):
        """Setup before each test."""
        setup_test_db()

    # ======================================================================
    # BASIC API COMPLIANCE TESTS
    # ======================================================================

    def test_get_response_structure_compliance(self):
        """Test that response structure matches API documentation exactly."""
        response, status = WorkdayStrategicSourcingAPI.SupplierCompanies.get()
        assert status == 200
        
        # Verify top-level structure
        assert "data" in response
        assert "meta" in response
        assert "links" in response
        assert isinstance(response["data"], list)
        assert isinstance(response["meta"], dict)
        assert isinstance(response["links"], dict)
        
        # Verify meta structure
        assert "count" in response["meta"]
        assert isinstance(response["meta"]["count"], int)
        
        # Verify links structure
        assert "self" in response["links"]
        assert "next" in response["links"]
        assert "prev" in response["links"]
        
        # Verify each company object structure
        for company in response["data"]:
            assert "type" in company
            assert "id" in company
            assert "attributes" in company
            assert "relationships" in company
            assert "links" in company
            
            # Verify type is correct
            assert company["type"] == "supplier_companies"
            
            # Verify attributes structure contains all required fields
            attributes = company["attributes"]
            required_attrs = [
                "name", "description", "is_suggested", "public",
                "segmentation", "segmentation_status", "segmentation_notes",
                "tags", "url", "duns_number", "external_id", "self_registered",
                "onboarding_form_completion_status", "accept_all_currencies",
                "updated_at", "custom_fields"
            ]
            for attr in required_attrs:
                assert attr in attributes, f"Missing required attribute: {attr}"

    def test_get_all_companies_with_defaults(self):
        """Test retrieving all companies includes default values for missing attributes."""
        response, status = WorkdayStrategicSourcingAPI.SupplierCompanies.get()
        assert status == 200
        assert len(response["data"]) == 3
        
        # Check that minimal company (Supplier B) has all default values
        supplier_b = next(c for c in response["data"] if c["attributes"]["name"] == "Supplier B")
        assert supplier_b["attributes"]["description"] == ""
        assert supplier_b["attributes"]["is_suggested"] == False
        assert supplier_b["attributes"]["public"] == False
        assert supplier_b["attributes"]["tags"] == []
        assert supplier_b["attributes"]["custom_fields"] == []

    def test_get_empty_database(self):
        """Test behavior with empty database."""
        db.DB["suppliers"]["supplier_companies"] = {}
        response, status = WorkdayStrategicSourcingAPI.SupplierCompanies.get()
        assert status == 200
        assert response["data"] == []
        assert response["meta"]["count"] == 1

    def test_get_missing_database_sections(self):
        """Test when database sections are missing."""
        db.DB.clear()
        response, status = WorkdayStrategicSourcingAPI.SupplierCompanies.get()
        assert status == 200
        assert response["data"] == []
        assert response["meta"]["count"] == 1

    # ======================================================================
    # PAGINATION TESTS
    # ======================================================================

    def test_pagination_default_values(self):
        """Test default pagination values (size=10, number=1)."""
        response, status = WorkdayStrategicSourcingAPI.SupplierCompanies.get()
        assert status == 200
        assert len(response["data"]) == 3  # All companies fit in default page
        assert response["meta"]["count"] == 1  # Only 1 page needed

    def test_pagination_custom_size(self):
        """Test pagination with custom page size."""
        response, status = WorkdayStrategicSourcingAPI.SupplierCompanies.get(
            page={"size": 2, "number": 1}
        )
        assert status == 200
        assert len(response["data"]) == 2
        assert response["meta"]["count"] == 2  # ceil(3/2) = 2 pages

    def test_pagination_second_page(self):
        """Test retrieving second page."""
        response, status = WorkdayStrategicSourcingAPI.SupplierCompanies.get(
            page={"size": 2, "number": 2}
        )
        assert status == 200
        assert len(response["data"]) == 1  # Last page has 1 item
        assert response["data"][0]["id"] == "3"

    def test_pagination_beyond_available(self):
        """Test requesting page beyond available data."""
        response, status = WorkdayStrategicSourcingAPI.SupplierCompanies.get(
            page={"size": 10, "number": 5}
        )
        assert status == 200
        assert response["data"] == []
        assert response["meta"]["count"] == 1

    def test_pagination_calculation_edge_cases(self):
        """Test pagination count calculation with various scenarios."""
        # Add one more company to make 4 total
        db.DB["suppliers"]["supplier_companies"][4] = {
            "id": 4,
            "attributes": {"name": "Supplier D", "segmentation_status": "approved"}
        }
        
        # Test exact division
        response, status = WorkdayStrategicSourcingAPI.SupplierCompanies.get(
            page={"size": 2, "number": 1}
        )
        assert status == 200
        assert response["meta"]["count"] == 2  # 4/2 = 2 pages exactly

    # ======================================================================
    # INCLUDE TESTS
    # ======================================================================

    def test_include_empty_string(self):
        """Test with empty include string."""
        response, status = WorkdayStrategicSourcingAPI.SupplierCompanies.get(_include="")
        assert status == 200
        assert "included" not in response

    def test_include_attachments(self):
        """Test including attachments."""
        response, status = WorkdayStrategicSourcingAPI.SupplierCompanies.get(_include="attachments")
        assert status == 200
        assert "included" in response
        
        # Should include attachment "1" from Supplier A
        included_attachments = [item for item in response["included"] if item["type"] == "attachments"]
        assert len(included_attachments) == 1
        assert included_attachments[0]["id"] == "1"

    def test_include_multiple_resources(self):
        """Test including multiple resource types."""
        response, status = WorkdayStrategicSourcingAPI.SupplierCompanies.get(
            _include="attachments,supplier_category"
        )
        assert status == 200
        # Should only include attachments since supplier_category relationships don't exist

    def test_include_with_spaces_and_empty_values(self):
        """Test include parameter robustness."""
        response, status = WorkdayStrategicSourcingAPI.SupplierCompanies.get(
            _include=" attachments , , supplier_category "
        )
        assert status == 200

    def test_include_deduplication(self):
        """Test that included resources are deduplicated."""
        # Add another company pointing to same attachment
        db.DB["suppliers"]["supplier_companies"][4] = {
            "id": 4,
            "attributes": {"name": "Supplier D"},
            "relationships": {
                "attachments": {
                    "data": [{"id": "1", "type": "attachments"}]
                }
            }
        }
        
        response, status = WorkdayStrategicSourcingAPI.SupplierCompanies.get(_include="attachments")
        assert status == 200
        
        # Should have only one copy of attachment "1"
        included_attachments = [item for item in response["included"] if item["type"] == "attachments"]
        attachment_ids = [item["id"] for item in included_attachments]
        assert attachment_ids.count("1") == 1

    def test_include_with_pagination(self):
        """Test include with pagination."""
        response, status = WorkdayStrategicSourcingAPI.SupplierCompanies.get(
            page={"size": 1, "number": 1}, 
            _include="attachments"
        )
        assert status == 200
        assert len(response["data"]) == 1
        assert response["data"][0]["id"] == "1"  # Should be Supplier A
        assert "included" in response

    # ======================================================================
    # FILTER TESTS
    # ======================================================================

    def test_filter_by_external_id_equals(self):
        """Test filtering by exact external_id match."""
        response, status = WorkdayStrategicSourcingAPI.SupplierCompanies.get(
            filter={"external_id_equals": "EXT1"}
        )
        assert status == 200
        assert len(response["data"]) == 1
        assert response["data"][0]["attributes"]["external_id"] == "EXT1"

    def test_filter_by_external_id_not_equals(self):
        """Test filtering by external_id exclusion."""
        response, status = WorkdayStrategicSourcingAPI.SupplierCompanies.get(
            filter={"external_id_not_equals": "EXT1"}
        )
        assert status == 200
        assert len(response["data"]) == 2  # Should exclude Supplier A
        external_ids = [comp["attributes"]["external_id"] for comp in response["data"]]
        assert "EXT1" not in external_ids

    def test_filter_segmentation_status_string(self):
        """Test filtering by segmentation status as string."""
        response, status = WorkdayStrategicSourcingAPI.SupplierCompanies.get(
            filter={"segmentation_status_equals": "approved"}
        )
        assert status == 200
        assert len(response["data"]) == 2
        for company in response["data"]:
            assert company["attributes"]["segmentation_status"] == "approved"

    def test_filter_segmentation_status_list(self):
        """Test filtering by segmentation status as list."""
        response, status = WorkdayStrategicSourcingAPI.SupplierCompanies.get(
            filter={"segmentation_status_equals": ["approved", "pending"]}
        )
        assert status == 200
        assert len(response["data"]) == 3  # All companies match

    def test_filter_external_id_empty(self):
        """Test filtering for empty external_id."""
        response, status = WorkdayStrategicSourcingAPI.SupplierCompanies.get(
            filter={"external_id_empty": True}
        )
        assert status == 200
        assert len(response["data"]) == 1
        assert response["data"][0]["attributes"]["external_id"] == ""

    def test_filter_external_id_not_empty(self):
        """Test filtering for non-empty external_id."""
        response, status = WorkdayStrategicSourcingAPI.SupplierCompanies.get(
            filter={"external_id_not_empty": True}
        )
        assert status == 200
        assert len(response["data"]) == 2
        for company in response["data"]:
            assert company["attributes"]["external_id"] != ""

    def test_filter_external_id_equals(self):
        """Test filtering by exact external_id match."""
        response, status = WorkdayStrategicSourcingAPI.SupplierCompanies.get(
            filter={"external_id_equals": "EXT1"}
        )
        assert status == 200
        assert len(response["data"]) == 1
        assert response["data"][0]["attributes"]["external_id"] == "EXT1"

    def test_filter_external_id_not_equals(self):
        """Test filtering by external_id exclusion."""
        response, status = WorkdayStrategicSourcingAPI.SupplierCompanies.get(
            filter={"external_id_not_equals": "EXT1"}
        )
        assert status == 200
        assert len(response["data"]) == 2
        for company in response["data"]:
            assert company["attributes"]["external_id"] != "EXT1"

    def test_filter_updated_at_from(self):
        """Test filtering by updated_at_from timestamp."""
        response, status = WorkdayStrategicSourcingAPI.SupplierCompanies.get(
            filter={"updated_at_from": "2023-02-01T00:00:00Z"}
        )
        assert status == 200
        assert len(response["data"]) == 2  # Companies 2 and 3
        for company in response["data"]:
            assert company["attributes"]["updated_at"] >= "2023-02-01T00:00:00Z"

    def test_filter_updated_at_to(self):
        """Test filtering by updated_at_to timestamp."""
        response, status = WorkdayStrategicSourcingAPI.SupplierCompanies.get(
            filter={"updated_at_to": "2023-02-01T00:00:00Z"}
        )
        assert status == 200
        assert len(response["data"]) == 2  # Companies 1 and 2
        for company in response["data"]:
            assert company["attributes"]["updated_at"] <= "2023-02-01T00:00:00Z"

    def test_filter_multiple_criteria(self):
        """Test filtering with multiple criteria."""
        response, status = WorkdayStrategicSourcingAPI.SupplierCompanies.get(
            filter={
                "segmentation_status_equals": "approved",
                "external_id_equals": "EXT1"
            }
        )
        assert status == 200
        assert len(response["data"]) == 1
        assert response["data"][0]["attributes"]["segmentation_status"] == "approved"
        assert response["data"][0]["attributes"]["external_id"] == "EXT1"

    def test_filter_no_matches(self):
        """Test filter that returns no matches."""
        response, status = WorkdayStrategicSourcingAPI.SupplierCompanies.get(
            filter={"external_id_equals": "NONEXISTENT"}
        )
        assert status == 200
        assert response["data"] == []
        assert response["meta"]["count"] == 1

    def test_filter_with_none_timestamp_values(self):
        """Test filtering when database has None timestamps."""
        # Add company with None timestamp
        db.DB["suppliers"]["supplier_companies"][4] = {
            "id": 4,
            "attributes": {
                "name": "Supplier D",
                "updated_at": None,
                "segmentation_status": "approved"
            }
        }
        
        response, status = WorkdayStrategicSourcingAPI.SupplierCompanies.get(
            filter={"updated_at_from": "2023-01-01T00:00:00Z"}
        )
        assert status == 200
        # Company with None timestamp should be filtered out
        company_ids = {company["id"] for company in response["data"]}
        assert "4" not in company_ids

    # ======================================================================
    # COMBINED FUNCTIONALITY TESTS
    # ======================================================================

    def test_complex_combination_filter_page_include(self):
        """Test complex combination of filtering, pagination, and inclusion."""
        response, status = WorkdayStrategicSourcingAPI.SupplierCompanies.get(
            filter={"segmentation_status_equals": ["approved"]},
            page={"size": 1, "number": 1},
            _include="attachments"
        )
        assert status == 200
        assert len(response["data"]) == 1
        assert response["data"][0]["attributes"]["segmentation_status"] == "approved"
        assert response["meta"]["count"] == 2  # 2 approved companies, page size 1 = 2 pages

    def test_filter_then_paginate_empty_result(self):
        """Test pagination when filter results in empty set."""
        response, status = WorkdayStrategicSourcingAPI.SupplierCompanies.get(
            filter={"external_id_equals": "NONEXISTENT"},
            page={"size": 10, "number": 1}
        )
        assert status == 200
        assert response["data"] == []
        assert response["meta"]["count"] == 1

    # ======================================================================
    # LEGACY DATABASE FORMAT SUPPORT
    # ======================================================================

    def test_legacy_flat_format_conversion(self):
        """Test conversion of legacy flat format to API-compliant format."""
        # Add company in legacy flat format
        db.DB["suppliers"]["supplier_companies"][99] = {
            "id": 99,
            "name": "Legacy Company",
            "external_id": "LEG99",
            "segmentation_status": "approved",
        }
        
        response, status = WorkdayStrategicSourcingAPI.SupplierCompanies.get()
        assert status == 200
        assert len(response["data"]) == 4  # 3 original + 1 legacy
        
        # Find legacy company and verify proper conversion
        legacy_company = next((c for c in response["data"] if c["id"] == "99"), None)
        assert legacy_company is not None
        assert legacy_company["type"] == "supplier_companies"
        assert "attributes" in legacy_company
        assert legacy_company["attributes"]["name"] == "Legacy Company"
        assert legacy_company["attributes"]["external_id"] == "LEG99"
        # Should have all required default attributes
        assert "description" in legacy_company["attributes"]
        assert "is_suggested" in legacy_company["attributes"]

    def test_mixed_format_handling(self):
        """Test handling of mixed legacy and new format data."""
        # Add both formats
        db.DB["suppliers"]["supplier_companies"][98] = {
            "id": 98,
            "name": "Mixed Legacy",
            "segmentation_status": "approved"
        }
        
        response, status = WorkdayStrategicSourcingAPI.SupplierCompanies.get()
        assert status == 200
        
        # All companies should be in proper API format
        for company in response["data"]:
            assert company["type"] == "supplier_companies"
            assert "attributes" in company
            assert "relationships" in company
            assert "links" in company

    # ======================================================================
    # VALIDATION ERROR TESTS (400 responses)
    # ======================================================================

    def test_invalid_filter_parameter_type(self):
        """Test error for invalid filter parameter type."""
        response, status = WorkdayStrategicSourcingAPI.SupplierCompanies.get(filter="invalid")
        assert status == 400
        assert "errors" in response
        assert "must be a dictionary" in response["errors"][0]["detail"]

    def test_invalid_include_parameter_type(self):
        """Test error for invalid include parameter type."""
        response, status = WorkdayStrategicSourcingAPI.SupplierCompanies.get(_include=123)
        assert status == 400
        assert "errors" in response
        assert "must be a string" in response["errors"][0]["detail"]

    def test_invalid_page_parameter_type(self):
        """Test error for invalid page parameter type."""
        response, status = WorkdayStrategicSourcingAPI.SupplierCompanies.get(page="invalid")
        assert status == 400
        assert "errors" in response
        assert "must be a dictionary" in response["errors"][0]["detail"]

    def test_unknown_filter_keys(self):
        """Test error for unknown filter keys."""
        response, status = WorkdayStrategicSourcingAPI.SupplierCompanies.get(
            filter={"unknown_key": "value"}
        )
        assert status == 400
        assert "errors" in response
        assert "Unknown filter keys" in response["errors"][0]["detail"]

    def test_invalid_include_values(self):
        """Test error for invalid include values."""
        response, status = WorkdayStrategicSourcingAPI.SupplierCompanies.get(
            _include="invalid_resource"
        )
        assert status == 400
        assert "errors" in response
        assert "'include' parameter does not support following values" in response["errors"][0]["detail"]

    def test_invalid_page_size_too_large(self):
        """Test error for page size exceeding maximum."""
        response, status = WorkdayStrategicSourcingAPI.SupplierCompanies.get(
            page={"size": 101}
        )
        assert status == 400
        assert "errors" in response
        assert "between 1 and 100" in response["errors"][0]["detail"]

    def test_invalid_page_size_zero(self):
        """Test error for zero page size."""
        response, status = WorkdayStrategicSourcingAPI.SupplierCompanies.get(
            page={"size": 0}
        )
        assert status == 400
        assert "errors" in response
        assert "between 1 and 100" in response["errors"][0]["detail"]

    def test_invalid_page_number_zero(self):
        """Test error for zero page number."""
        response, status = WorkdayStrategicSourcingAPI.SupplierCompanies.get(
            page={"number": 0}
        )
        assert status == 400
        assert "errors" in response
        assert "greater than zero" in response["errors"][0]["detail"]

    def test_invalid_filter_boolean_type(self):
        """Test error for invalid boolean filter values."""
        response, status = WorkdayStrategicSourcingAPI.SupplierCompanies.get(
            filter={"external_id_empty": "not_boolean"}
        )
        assert status == 400
        assert "errors" in response
        assert "must be a boolean" in response["errors"][0]["detail"]

    def test_invalid_filter_string_type(self):
        """Test error for invalid string filter values."""
        response, status = WorkdayStrategicSourcingAPI.SupplierCompanies.get(
            filter={"external_id_equals": 123}
        )
        assert status == 400
        assert "errors" in response
        assert "must be a string" in response["errors"][0]["detail"]

    def test_invalid_segmentation_status_type(self):
        """Test error for invalid segmentation_status_equals type."""
        response, status = WorkdayStrategicSourcingAPI.SupplierCompanies.get(
            filter={"segmentation_status_equals": 123}
        )
        assert status == 400
        assert "errors" in response
        assert "must be a string or a list" in response["errors"][0]["detail"]

    def test_invalid_timestamp_format(self):
        """Test error for invalid ISO-8601 timestamp format."""
        response, status = WorkdayStrategicSourcingAPI.SupplierCompanies.get(
            filter={"updated_at_from": "invalid-timestamp"}
        )
        assert status == 400
        assert "errors" in response
        assert "valid ISO-8601 timestamp" in response["errors"][0]["detail"]

    def test_invalid_timestamp_type(self):
        """Test error for non-string timestamp."""
        response, status = WorkdayStrategicSourcingAPI.SupplierCompanies.get(
            filter={"updated_at_from": 20230101}
        )
        assert status == 400
        assert "errors" in response
        assert "must be an ISO-8601 timestamp string" in response["errors"][0]["detail"]

    # ======================================================================
    # ISO TIMESTAMP VALIDATION TESTS
    # ======================================================================

    def test_valid_iso_timestamp_formats(self):
        """Test various valid ISO-8601 timestamp formats."""
        valid_timestamps = [
            "2023-01-01",
            "2023-01-01T00:00:00Z",
            "2023-01-01T00:00:00.000Z",
            "2023-01-01T00:00:00+00:00",
            "2023-01-01T00:00:00-05:00"
        ]
        
        for timestamp in valid_timestamps:
            response, status = WorkdayStrategicSourcingAPI.SupplierCompanies.get(
                filter={"updated_at_from": timestamp}
            )
            assert status == 200, f"Failed for valid timestamp: {timestamp}"

    # ======================================================================
    # EDGE CASES AND ERROR HANDLING
    # ======================================================================

    def test_include_with_malformed_relationship_data(self):
        """Test include with malformed relationship data."""
        db.DB["suppliers"]["supplier_companies"][97] = {
            "id": 97,
            "attributes": {"name": "Malformed Relationships"},
            "relationships": {
                "attachments": {
                    "data": "invalid_format"  # Should be list or dict, not string
                }
            }
        }
        
        response, status = WorkdayStrategicSourcingAPI.SupplierCompanies.get(_include="attachments")
        assert status == 200
        # Should handle malformed data gracefully without crashing

    def test_include_with_missing_database_sections(self):
        """Test include when referenced database sections are missing."""
        if "attachments" in db.DB:
            del db.DB["attachments"]
        
        response, status = WorkdayStrategicSourcingAPI.SupplierCompanies.get(_include="attachments")
        assert status == 200
        assert "included" not in response or response.get("included") == []

    def test_company_links_generation(self):
        """Test that proper self links are generated for companies."""
        response, status = WorkdayStrategicSourcingAPI.SupplierCompanies.get()
        assert status == 200
        
        for company in response["data"]:
            assert "links" in company
            assert "self" in company["links"]
            assert f"supplier_companies/{company['id']}" in company["links"]["self"]

    def test_response_links_structure(self):
        """Test that response links follow API specification."""
        response, status = WorkdayStrategicSourcingAPI.SupplierCompanies.get()
        assert status == 200
        
        links = response["links"]
        assert "self" in links
        assert "next" in links
        assert "prev" in links
        assert "api.us.workdayspend.com" in links["self"]

    def test_all_include_values_supported(self):
        """Test that all documented include values are supported."""
        valid_includes = [
            "attachments", "supplier_category", "supplier_groups",
            "default_payment_term", "payment_types", "default_payment_type",
            "payment_currencies", "default_payment_currency", 
            "supplier_classification_values"
        ]
        
        for include_value in valid_includes:
            response, status = WorkdayStrategicSourcingAPI.SupplierCompanies.get(
                _include=include_value
            )
            assert status == 200, f"Failed for include value: {include_value}"


# ======================================================================
# COMPATIBILITY TESTS FOR EXISTING FRAMEWORK
# ======================================================================

def test_supplier_companies_get():
    """Compatibility test - but aligned with API documentation."""
    db.DB.clear()
    db.DB["suppliers"] = {"supplier_companies": {}}
    db.DB["suppliers"]["supplier_companies"][1] = {
        "id": 1,
        "name": "Test Company"
    }
    
    response, status = WorkdayStrategicSourcingAPI.SupplierCompanies.get()
    assert status == 200
    
    # Response should be API-compliant structure
    assert isinstance(response, dict)
    assert "data" in response
    assert len(response["data"]) == 1
    assert response["data"][0]["type"] == "supplier_companies"
    assert response["data"][0]["id"] == "1"
    assert response["data"][0]["attributes"]["name"] == "Test Company"

def test_get_with_filter():
    """Test filtering functionality with API-compliant expectations."""
    db.DB.clear()
    db.DB["suppliers"] = {"supplier_companies": {}}
    
    db.DB["suppliers"]["supplier_companies"][1] = {
        "id": 1,
        "attributes": {"name": "Company 1", "segmentation_status": "approved", "external_id": ""}
    }
    
    response, status = WorkdayStrategicSourcingAPI.SupplierCompanies.get(
        filter={"external_id_empty": True}
    )
    assert status == 200
    assert len(response["data"]) == 1
    assert response["data"][0]["attributes"]["name"] == "Company 1"

def test_get_with_include():
    """Test include functionality with API-compliant expectations."""
    db.DB.clear()
    db.DB["attachments"] = {
        "1": {"type": "attachments", "id": "1", "name": "test.pdf"}
    }
    db.DB["suppliers"] = {"supplier_companies": {}}
    
    for i in [1, 2]:
        db.DB["suppliers"]["supplier_companies"][i] = {
            "id": i,
            "attributes": {"name": f"Company {i}"}
        }
    
    response, status = WorkdayStrategicSourcingAPI.SupplierCompanies.get(_include="attachments")
    assert status == 200
    assert len(response["data"]) == 2

def test_get_with_page():
    """Test pagination with API-compliant expectations."""
    db.DB.clear()
    db.DB["suppliers"] = {"supplier_companies": {}}
    
    for i in range(1, 4):
        db.DB["suppliers"]["supplier_companies"][i] = {
            "id": i,
            "attributes": {"name": f"Company {i}"}
        }
    
    response, status = WorkdayStrategicSourcingAPI.SupplierCompanies.get(
        page={"size": 2, "number": 1}
    )
    assert status == 200
    assert len(response["data"]) == 2
    assert response["meta"]["count"] == 2

def test_segmentation_status_filter_list():
    """Test segmentation status filtering with correct expectations."""
    db.DB.clear()
    db.DB["suppliers"] = {"supplier_companies": {}}
    
    for i in range(1, 4):
        db.DB["suppliers"]["supplier_companies"][i] = {
            "id": i,
            "attributes": {
                "name": f"Company {i}",
                "segmentation_status": "approved"
            }
        }
    
    response, status = WorkdayStrategicSourcingAPI.SupplierCompanies.get(
        filter={"segmentation_status_equals": ["approved"]},
        page={"size": 2, "number": 2}
    )
    assert status == 200
    assert response["meta"]["count"] == 2  # ceil(3/2) = 2 pages
    assert len(response["data"]) == 1  # Second page has 1 item