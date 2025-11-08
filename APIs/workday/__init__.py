
"""
Workday Strategic Sourcing API Simulation Package.

This package provides a simulation of the Workday Strategic Sourcing API, implementing various
endpoints and functionality for managing sourcing projects, suppliers, contracts, and related
entities. The package is organized into several main categories:

Core API Modules:
    - Projects and project management
    - Project relationships and types
    - Project descriptions and metadata

Supplier Management:
    - Supplier companies and contacts
    - Supplier segmentation
    - Supplier-related reports

Contact Management:
    - Contact types and definitions
    - Contact-related operations

Spend Management:
    - Spend categories
    - Spend tracking and reporting

User Management:
    - User operations
    - User-related endpoints

Contract Management:
    - Contract operations
    - Contract awards
    - Contract-related reports

Event Management:
    - Event templates and worksheets
    - Bids and bid line items
    - Event-related operations

Field Management:
    - Custom fields
    - Field groups and options
    - Field-related operations

Payment Management:
    - Payment currencies
    - Payment terms
    - Payment types

Reporting:
    - Project reports
    - Supplier reports
    - Performance reviews
    - Contract reports
    - Event reports
    - Savings reports

SCIM Integration:
    - Service provider configuration
    - Resource types
    - Schema management

Attachments:
    - File attachment handling
    - Document management

The package also includes a simulation engine and test suite for testing and validation purposes.
"""

from . import (
    # Core API modules
    Projects,
    ProjectById,
    ProjectByExternalId,
    ProjectTypes,
    ProjectTypeById,
    ProjectRelationshipsSupplierContacts,
    ProjectRelationshipsSupplierContactsExternalId,
    ProjectRelationshipsSupplierCompanies,
    ProjectRelationshipsSupplierCompaniesExternalId,
    ProjectsDescribe,
    # Supplier related modules
    Suppliers,
    SupplierCompanies,
    SupplierCompanyById,
    SupplierCompanyByExternalId,
    SupplierCompanyContacts,
    SupplierCompanyContactById,
    SupplierCompanyContactsByExternalId,
    SupplierContacts,
    SupplierContactById,
    SupplierContactByExternalId,
    SupplierCompanySegmentations,
    SupplierCompaniesDescribe,
    # Contact related modules
    ContactTypes,
    ContactTypeById,
    ContactTypeByExternalId,
    # Spend related modules
    SpendCategories,
    SpendCategoryById,
    SpendCategoryByExternalId,
    # User related modules
    Users,
    UserById,
    # Contract related modules
    Contracts,
    ContractAward,
    Awards,
    # Event related modules
    Events,
    EventBids,
    BidsById,
    BidsDescribe,
    BidLineItems,
    BidLineItemById,
    BidLineItemsList,
    BidLineItemsDescribe,
    EventTemplates,
    EventWorksheets,
    EventWorksheetById,
    EventWorksheetLineItems,
    EventWorksheetLineItemById,
    EventSupplierCompanies,
    EventSupplierCompaniesExternalId,
    EventSupplierContacts,
    EventSupplierContactsExternalId,
    # Field related modules
    Fields,
    FieldById,
    FieldByExternalId,
    FieldGroups,
    FieldGroupById,
    FieldOptions,
    FieldOptionsByFieldId,
    FieldOptionById,
    # Payment related modules
    PaymentCurrencies,
    PaymentCurrenciesId,
    PaymentCurrenciesExternalId,
    PaymentTerms,
    PaymentTermsId,
    PaymentTermsExternalId,
    PaymentTypes,
    PaymentTypesId,
    PaymentTypesExternalId,
    # Report related modules
    ProjectReports,
    ProjectMilestoneReports,
    SupplierReports,
    SupplierReviewReports,
    PerformanceReviewReports,
    PerformanceReviewAnswerReports,
    ContractReports,
    ContractMilestoneReports,
    EventReports,
    SavingsReports,
    # SCIM related modules
    ServiceProviderConfig,
    ResourceTypes,
    ResourceTypeById,
    Schemas,
    SchemaById,
    # Attachments
    Attachments,
)

import importlib
import os
import json
import tempfile
from common_utils.error_handling import get_package_error_mode
from .SimulationEngine.db import DB, load_state, save_state
from common_utils.init_utils import create_error_simulator, resolve_function_import
from workday.SimulationEngine import utils
from workday import SimulationEngine

# Get the directory of the current file
_INIT_PY_DIR = os.path.dirname(__file__)

# Create error simulator using the utility function
error_simulator = create_error_simulator(_INIT_PY_DIR)

# Get the error mode for the package
ERROR_MODE = get_package_error_mode()

# Function map
_function_map = {
  "get_supplier_contact_by_id": "workday.SupplierContactById.get",
  "update_supplier_contact_by_id": "workday.SupplierContactById.patch",
  "delete_supplier_contact_by_id": "workday.SupplierContactById.delete",
  "list_spend_categories": "workday.SpendCategories.get",
  "create_spend_category": "workday.SpendCategories.post",
  "add_supplier_companies_to_project_by_external_id": "workday.ProjectRelationshipsSupplierCompaniesExternalId.post",
  "remove_supplier_companies_from_project_by_external_id": "workday.ProjectRelationshipsSupplierCompaniesExternalId.delete",
  "add_supplier_contacts_to_project_by_internal_id": "workday.ProjectRelationshipsSupplierContacts.post",
  "remove_supplier_contacts_from_project_by_internal_id": "workday.ProjectRelationshipsSupplierContacts.delete",
  "get_field_group_by_id": "workday.FieldGroupById.get",
  "update_field_group_by_id": "workday.FieldGroupById.patch",
  "delete_field_group_by_id": "workday.FieldGroupById.delete",
  "list_custom_fields": "workday.Fields.get",
  "create_custom_field": "workday.Fields.post",
  "list_supplier_company_segmentations": "workday.SupplierCompanySegmentations.get",
  "create_supplier_company_segmentation": "workday.SupplierCompanySegmentations.post",
  "get_supplier_contact_by_external_id": "workday.SupplierContactByExternalId.get",
  "update_supplier_contact_by_external_id": "workday.SupplierContactByExternalId.patch",
  "delete_supplier_contact_by_external_id": "workday.SupplierContactByExternalId.delete",
  "update_contact_type_by_id": "workday.ContactTypeById.patch",
  "delete_contact_type_by_id": "workday.ContactTypeById.delete",
  "list_supplier_companies": "workday.SupplierCompanies.get",
  "create_supplier_company": "workday.SupplierCompanies.post",
  "get_scim_service_provider_config": "workday.ServiceProviderConfig.get",
  "create_field_options": "workday.FieldOptions.post",
  "list_contract_awards": "workday.ContractAward.list_awards",
  "get_contract_award_by_id": "workday.ContractAward.get_award",
  "list_contract_award_line_items": "workday.ContractAward.list_contract_award_line_items",
  "get_contract_award_line_item_by_id": "workday.ContractAward.get_contract_award_line_item",
  "get_field_details_by_id": "workday.FieldById.get",
  "update_field_details_by_id": "workday.FieldById.patch",
  "delete_field_by_id": "workday.FieldById.delete",
  "list_event_templates": "workday.EventTemplates.get",
  "get_event_template_by_id": "workday.EventTemplates.get_by_id",
  "list_field_groups": "workday.FieldGroups.get",
  "create_field_group": "workday.FieldGroups.post",
  "get_event_worksheet_by_id": "workday.EventWorksheetById.get",
  "update_payment_type_by_external_id": "workday.PaymentTypesExternalId.patch",
  "delete_payment_type_by_external_id": "workday.PaymentTypesExternalId.delete",
  "get_supplier_company_contact_by_id": "workday.SupplierCompanyContactById.get",
  "update_supplier_company_contact_by_id": "workday.SupplierCompanyContactById.patch",
  "delete_supplier_company_contact_by_id": "workday.SupplierCompanyContactById.delete",
  "add_supplier_companies_to_event_by_internal_id": "workday.EventSupplierCompanies.post",
  "remove_supplier_companies_from_event_by_internal_id": "workday.EventSupplierCompanies.delete",
  "list_bid_line_items_for_bid": "workday.BidLineItems.get",
  "list_performance_review_report_entries": "workday.PerformanceReviewReports.get_entries",
  "get_performance_review_report_schema": "workday.PerformanceReviewReports.get_schema",
  "get_project_type_by_id": "workday.ProjectTypeById.get",
  "list_supplier_company_contacts_by_company_external_id": "workday.SupplierCompanyContacts.get",
  "list_scim_schemas": "workday.Schemas.get",
  "get_scim_user_by_id": "workday.UserById.get",
  "partially_update_scim_user_by_id": "workday.UserById.patch",
  "replace_scim_user_by_id": "workday.UserById.put",
  "deactivate_scim_user_by_id": "workday.UserById.delete",
  "list_project_milestone_report_entries": "workday.ProjectMilestoneReports.get_entries",
  "get_project_milestone_report_schema": "workday.ProjectMilestoneReports.get_schema",
  "update_payment_currency_by_external_id": "workday.PaymentCurrenciesExternalId.patch",
  "delete_payment_currency_by_external_id": "workday.PaymentCurrenciesExternalId.delete",
  "list_contact_types": "workday.ContactTypes.get",
  "create_contact_type": "workday.ContactTypes.post",
  "update_field_options_by_id": "workday.FieldOptionById.patch",
  "delete_field_options_by_id": "workday.FieldOptionById.delete",
  "list_savings_report_entries": "workday.SavingsReports.get_entries",
  "get_savings_report_schema": "workday.SavingsReports.get_schema",
  "list_event_report_entries": "workday.EventReports.get_entries",
  "get_event_report_entries_by_report_id": "workday.EventReports.get_event_report_entries",
  "list_user_owned_event_report_entries": "workday.EventReports.get_reports",
  "get_event_report_schema": "workday.EventReports.get_schema",
  "get_scim_schema_by_uri": "workday.SchemaById.get",
  "list_event_worksheets": "workday.EventWorksheets.get",
  "add_supplier_contacts_to_event_by_internal_id": "workday.EventSupplierContacts.post",
  "remove_supplier_contacts_from_event_by_internal_id": "workday.EventSupplierContacts.delete",
  "list_contracts": "workday.Contracts.get",
  "create_contract": "workday.Contracts.post",
  "get_contract_by_id": "workday.Contracts.get_contract_by_id",
  "update_contract_by_id": "workday.Contracts.patch_contract_by_id",
  "delete_contract_by_id": "workday.Contracts.delete_contract_by_id",
  "get_contract_by_external_id": "workday.Contracts.get_contract_by_external_id",
  "update_contract_by_external_id": "workday.Contracts.patch_contract_by_external_id",
  "delete_contract_by_external_id": "workday.Contracts.delete_contract_by_external_id",
  "get_contract_fields_description": "workday.Contracts.get_contracts_description",
  "list_contract_types": "workday.Contracts.get_contract_types",
  "create_contract_type": "workday.Contracts.post_contract_types",
  "get_contract_type_by_id": "workday.Contracts.get_contract_type_by_id",
  "update_contract_type_by_id": "workday.Contracts.patch_contract_type_by_id",
  "delete_contract_type_by_id": "workday.Contracts.delete_contract_type_by_id",
  "get_contract_type_by_external_id": "workday.Contracts.get_contract_type_by_external_id",
  "update_contract_type_by_external_id": "workday.Contracts.patch_contract_type_by_external_id",
  "delete_contract_type_by_external_id": "workday.Contracts.delete_contract_type_by_external_id",
  "update_contact_type_by_external_id": "workday.ContactTypeByExternalId.patch",
  "delete_contact_type_by_external_id": "workday.ContactTypeByExternalId.delete",
  "list_contract_milestone_report_entries": "workday.ContractMilestoneReports.get_entries",
  "get_contract_milestone_report_schema": "workday.ContractMilestoneReports.get_schema",
  "update_payment_currency_by_id": "workday.PaymentCurrenciesId.patch",
  "delete_payment_currency_by_id": "workday.PaymentCurrenciesId.delete",
  "list_payment_types": "workday.PaymentTypes.get",
  "create_payment_type": "workday.PaymentTypes.post",
  "add_supplier_contacts_to_event_by_external_ids": "workday.EventSupplierContactsExternalId.post",
  "remove_supplier_contacts_from_event_by_external_ids": "workday.EventSupplierContactsExternalId.delete",
  "get_supplier_company_contacts_by_external_id": "workday.SupplierCompanyContactsByExternalId.get",
  "get_spend_category_details_by_external_id": "workday.SpendCategoryById.get",
  "update_spend_category_details_by_external_id": "workday.SpendCategoryById.patch",
  "delete_spend_category_by_external_id": "workday.SpendCategoryById.delete",
  "get_scim_resource_type_metadata_by_name": "workday.ResourceTypeById.get",
  "list_payment_terms": "workday.PaymentTerms.get",
  "create_payment_term": "workday.PaymentTerms.post",
  "update_payment_type_by_id": "workday.PaymentTypesId.patch",
  "delete_payment_type_by_id": "workday.PaymentTypesId.delete",
  "add_supplier_companies_to_event_by_external_id": "workday.EventSupplierCompaniesExternalId.post",
  "remove_supplier_companies_from_event_by_external_id": "workday.EventSupplierCompaniesExternalId.delete",
  "get_contract_report_entries": "workday.ContractReports.get_entries",
  "get_contract_report_schema": "workday.ContractReports.get_schema",
  "list_events_with_filters": "workday.Events.get",
  "create_event": "workday.Events.post",
  "get_event_by_id": "workday.Events.get_by_id",
  "update_event_by_id": "workday.Events.patch",
  "delete_event_by_id": "workday.Events.delete",
  "list_supplier_review_report_entries": "workday.SupplierReviewReports.get_entries",
  "get_supplier_review_report_schema": "workday.SupplierReviewReports.get_schema",
  "get_bid_line_item_by_id": "workday.BidLineItemById.get",
  "list_payment_currencies": "workday.PaymentCurrencies.get",
  "create_payment_currency": "workday.PaymentCurrencies.post",
  "list_field_options_by_field_id": "workday.FieldOptionsByFieldId.get",
  "list_awards_with_filters": "workday.Awards.get",
  "list_award_line_items_for_award": "workday.Awards.get_award_line_items",
  "get_award_line_item_by_id": "workday.Awards.get_award_line_item",
  "update_payment_term_by_id": "workday.PaymentTermsId.patch",
  "delete_payment_term_by_id": "workday.PaymentTermsId.delete",
  "get_project_details_by_id": "workday.ProjectById.get",
  "update_project_details_by_id": "workday.ProjectById.patch",
  "delete_project_by_id": "workday.ProjectById.delete",
  "describe_supplier_company_fields": "workday.SupplierCompaniesDescribe.get",
  "get_supplier_company_by_external_id": "workday.SupplierCompanyByExternalId.get",
  "update_supplier_company_by_external_id": "workday.SupplierCompanyByExternalId.patch",
  "delete_supplier_company_by_external_id": "workday.SupplierCompanyByExternalId.delete",
  "list_all_suppliers": "workday.Suppliers.get_suppliers",
  "get_supplier_by_id": "workday.Suppliers.get_supplier",
  "list_all_bid_line_items": "workday.BidLineItemsList.get",
  "get_supplier_company_by_id": "workday.SupplierCompanyById.get",
  "update_supplier_company_by_id": "workday.SupplierCompanyById.patch",
  "delete_supplier_company_by_id": "workday.SupplierCompanyById.delete",
  "get_bid_by_id": "workday.BidsById.get",
  "get_field_by_external_id": "workday.FieldByExternalId.get",
  "update_field_by_external_id": "workday.FieldByExternalId.patch",
  "delete_field_by_external_id": "workday.FieldByExternalId.delete",
  "get_project_report_entries_by_id": "workday.ProjectReports.get_project_report_entries",
  "list_user_owned_project_report_entries": "workday.ProjectReports.get_entries",
  "get_project_report_schema": "workday.ProjectReports.get_schema",
  "list_attachments_by_ids": "workday.Attachments.get",
  "create_attachment": "workday.Attachments.post",
  "list_all_attachments_with_filter": "workday.Attachments.list_attachments",
  "get_attachment_by_id": "workday.Attachments.get_attachment_by_id",
  "update_attachment_by_id": "workday.Attachments.patch_attachment_by_id",
  "delete_attachment_by_id": "workday.Attachments.delete_attachment_by_id",
  "get_attachment_by_external_id": "workday.Attachments.get_attachment_by_external_id",
  "update_attachment_by_external_id": "workday.Attachments.patch_attachment_by_external_id",
  "delete_attachment_by_external_id": "workday.Attachments.delete_attachment_by_external_id",
  "list_event_worksheet_line_items": "workday.EventWorksheetLineItems.get",
  "create_event_worksheet_line_item": "workday.EventWorksheetLineItems.post",
  "create_multiple_event_worksheet_line_items": "workday.EventWorksheetLineItems.post_multiple",
  "create_supplier_contact": "workday.SupplierContacts.post",
  "list_scim_users": "workday.Users.get",
  "create_scim_user": "workday.Users.post",
  "get_project_by_external_id": "workday.ProjectByExternalId.get",
  "update_project_by_external_id": "workday.ProjectByExternalId.patch",
  "delete_project_by_external_id": "workday.ProjectByExternalId.delete",
  "list_projects": "workday.Projects.get",
  "create_project": "workday.Projects.post",
  "describe_bid_line_items_fields": "workday.BidLineItemsDescribe.get",
  "update_payment_term_by_external_id": "workday.PaymentTermsExternalId.patch",
  "delete_payment_term_by_external_id": "workday.PaymentTermsExternalId.delete",
  "list_performance_review_answer_report_entries": "workday.PerformanceReviewAnswerReports.get_entries",
  "get_performance_review_answer_report_schema": "workday.PerformanceReviewAnswerReports.get_schema",
  "add_supplier_companies_to_project": "workday.ProjectRelationshipsSupplierCompanies.post",
  "remove_supplier_companies_from_project": "workday.ProjectRelationshipsSupplierCompanies.delete",
  "describe_bid_fields": "workday.BidsDescribe.get",
  "get_event_worksheet_line_item_by_id": "workday.EventWorksheetLineItemById.get",
  "update_event_worksheet_line_item_by_id": "workday.EventWorksheetLineItemById.patch",
  "delete_event_worksheet_line_item_by_id": "workday.EventWorksheetLineItemById.delete",
  "get_project_fields_description": "workday.ProjectsDescribe.get",
  "list_supplier_report_entries": "workday.SupplierReports.get_entries",
  "get_supplier_report_schema": "workday.SupplierReports.get_schema",
  "list_event_bids": "workday.EventBids.get",
  "list_project_types": "workday.ProjectTypes.get",
  "list_scim_resource_types": "workday.ResourceTypes.get",
  "get_scim_resource_type_by_name": "workday.ResourceTypes.get_by_resource",
  "get_spend_category_by_id": "workday.SpendCategoryByExternalId.get",
  "update_spend_category_by_id": "workday.SpendCategoryByExternalId.patch",
  "delete_spend_category_by_id": "workday.SpendCategoryByExternalId.delete",
  "add_supplier_contacts_to_project_by_external_ids": "workday.ProjectRelationshipsSupplierContactsExternalId.post",
  "remove_supplier_contacts_from_project_by_external_ids": "workday.ProjectRelationshipsSupplierContactsExternalId.delete"
}

def __getattr__(name: str):
    return resolve_function_import(name, _function_map, error_simulator)

def __dir__():
    return sorted(set(globals().keys()) | set(_function_map.keys()))

__all__ = list(_function_map.keys())
