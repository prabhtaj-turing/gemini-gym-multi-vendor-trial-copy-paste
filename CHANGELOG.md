# Release Notes

Welcome! 👋  
This file lists all the important changes made to this project over time. Each release is grouped by version, and changes are categorized so you can quickly understand what's new, what's changed, and what's fixed. Here's a quick guide:

- **Added** → New features that weren't there before.
- **Changed** → Updates to existing functionality (but still backward compatible).
- **Deprecated** → Features that still work but are scheduled to be removed.
- **Removed** → Features that are no longer available.
- **Fixed** → Bug fixes that correct unintended behavior.
- **Security** → Important changes that address vulnerabilities.

Feel free to scroll through the versions below to see what's changed over time. 👇

## 📋 Release Summary

| Version | Release Date | Key Highlights |
|---------|--------------|----------------|
| **[0.1.6](#016)** | 2025-11-06 | Bug Fixes and Service Improvements |
| **[0.1.5](#015)** | 2025-10-09 | Comprehensive API Bug Fixes and Test Coverage Improvements |
| **[0.1.4.4](#0144)** | 2025-10-20 | Cross-Service Enhancements and Model Consistency |
| **[0.1.4.3](#0143)** | 2025-10-16 | Generic Communication Modules and Advanced Porting |
| **[0.1.4.2](#0142)** | 2025-10-14 | CES Infobot Configuration and Pydantic Enhancements |
| **[0.1.4.1](#0141)** | 2025-10-13 | New CES Services and Account Management Improvements |
| **[0.1.4](#014)** | 2025-09-15 | Bug Fixes and Service Improvements |
| **[0.1.3](#013)** | 2025-09-11 | Major Testing Infrastructure Enhancements - Added 17,000+ lines of test coverage |
| **[0.1.2](#012)** | 2025-09-08 | API Bug Fixes and Improvements |
| **[0.1.2](#012)** | 2025-09-05 | LinkedIn API Updates, Phone Number Validation Relaxation |
| **[0.1.2](#012)** | 2025-09-04 | Additional Bug Fixes and Service Improvements |
| **[0.1.1](#011)** | 2025-09-03 | Framework Enhancements and API Updates |
| **[0.1.1](#011)** | 2025-08-29 | Terminal Service Optimization |
| **[0.1.1](#011)** | 2025-08-28 | Dependencies and Infrastructure Updates |
| **[0.1.1](#011)** | 2025-08-26 | Search Engine Consolidation |
| **[0.1.1](#011)** | 2025-08-25 | Framework Features Enhancement |
| **[0.1.1](#011)** | 2025-08-22 | Confluence API Major Enhancements |
| **[0.1.1](#011)** | 2025-08-20 | SAPConcur and Google Sheets API Improvements |
| **[0.1.1](#011)** | 2025-08-19 | Workday API Type Hint Enhancements |
| **[0.1.0](#010)** | 2025-08-15 | Major Release - Google Drive, Gmail, Slack Filesystem Support |
| **[0.1.0](#010)** | 2025-08-13 | YouTube Service Major Enhancements |
| **[0.1.0](#010)** | 2025-08-07 | Comprehensive API Improvements |
| **[0.1.0](#010)** | 2025-08-05 | YouTube Playlists and Video Upload |
| **[0.0.10](#0010)** | 2025-07-30 | Instagram API and Google Calendar Enhancements |
| **[0.0.10](#0010)** | 2025-07-23 | Copilot API and Authentication Improvements |
| **[0.0.10](#0010)** | 2025-07-18 | Google Meet API and Service Updates |
| **[0.0.9](#009)** | 2025-07-17 | AI Agent Framework and API Enhancements |
| **[0.0.8](#008)** | 2025-07-16 | Gmail API Major Updates |
| **[0.0.8](#008)** | 2025-07-14 | Google Calendar and Jira API Improvements |
| **[0.0.7.1](#0071---2025-07-07)** | 2025-07-07 | Performance and Bug Fixes |
| **[0.0.7](#007---2025-07-03)** | 2025-07-03 | Simulation Engine and Database Enhancements |
| **[0.0.6](#006---2025-06-30)** | 2025-06-30 | OAuth2 Framework and Service Updates |
| **[0.0.5](#005---2025-05-28)** | 2025-05-28 | Tech Debt and Project Structure Improvements |
| **[0.0.4](#004---2025-05-25)** | 2025-05-25 | Comprehensive Input Validation Framework |
| **[0.0.3](#003---2025-05-24)** | 2025-05-24 | Database Integration and API Improvements |
| **[0.0.2](#002---2025-05-23)** | 2025-05-23 | Core Framework and Service Implementation |
| **[0.0.1](#001---2025-05-21)** | 2025-05-21 | Initial Release |

---


---

# [0.1.6]

## Release - 2025-10-31

### **API Changes & Improvements**

#### **Google Sheets API**
- **Enhanced create_spreadsheet**: Improved drive ID handling and size formatting with better error handling
- **Data Format Standardization**: Updated create_spreadsheet to use simple data format with strict A1 range validation
- **Sheet Name Validation**: Added comprehensive sheet name validation in create_spreadsheet function

#### **Google Docs API**
- **Batch Update Enhancements**: Enhanced batch_update_document with legacy textRun conversion improvements
- **Content Format Standardization**: Standardized content format in batchUpdate to use {elementId, text} structure
- **Timestamp Fixes**: Fixed batchUpdate to use current time for document timestamps instead of hardcoded values

#### **Google Slides API**
- **Page Validation**: Enhanced get_page function to raise ValidationError on invalid page data
- **Patch Operations**: Implemented deep merge for patch operations with atomic updates
- **Batch Update Documentation**: Enhanced API documentation and added tests for batch update functionality

#### **Google Calendar API**
- **All-Day Event Support**: Added comprehensive support for all-day events in update_event
- **Metadata Updates**: Enhanced update_calendar_metadata to allow clearing optional fields with None
- **Sorting Improvements**: Fixed orderBy="updated" to sort by updated field instead of startTime
- **Calendar Validation**: Enhanced calendarId validation with improved error messages

#### **WhatsApp API**
- **Contact Lookup**: Improved contact lookup functionality with +country code support
- **Phone Number Matching**: Enhanced phone number matching in list_messages to search all contacts and handle JID-based phone extraction with proper normalization
- **Pydantic Validation**: Added comprehensive Pydantic validation to WhatsappContact model output

#### **Google Maps Live API**
- **Testing Infrastructure**: Added supporting libraries and comprehensive test coverage for Google Maps Live functionality

#### **Email Normalization**
- **Cross-Service Enhancement**: Implemented email normalization across multiple services for improved consistency

### **Code Quality & Refactoring**

#### **Import Statement Standardization**
- **Confluence Module**: Refactored import statements in Confluence module and tests for improved organization
- **Clock Module**: Updated import statements in Clock module and tests with better organization
- **Messages Module**: Refactored import statements in Messages module and tests
- **Device Settings Module**: Cleaned up import statements across device_setting module tests
- **YouTube Module**: Refactored import statements in YouTube module and tests, fixed failing tests
- **BigQuery Module**: Updated import changes for improved module organization
- **Stripe Module**: Fixed imports for Stripe service
- **Canva API**: Updated import statements in Canva API test files to use relative paths
- **Gmail Module**: Refactored import statements in Gmail test files to use relative paths
- **Google Drive Module**: Cleaned up import statements in GDrive API unit tests
- **GitHub Actions**: Updated GitHub imports and fixed test file imports
- **CES Services**: Fixed test imports for CES Account Management & Loyalty Auth services

#### **Test Infrastructure Improvements**
- **GitHub Actions Tests**: Enhanced test infrastructure for GitHub Actions workflows
- **Device Settings Tests**: Expanded test cases for device_settings service with improved coverage
- **Import Consistency**: Standardized import statements across test files to use relative paths

### **Bug Fixes**

#### **Google Drive API**
- **Bug #1201**: Fixed comment deletion logic to include associated replies (cascade delete)
- **Bug #1207**: Fixed sorting comments to fallback to createdTime when modifiedTime is missing
- **Bug #1212**: Fixed update_file_metadata_or_content to prevent includeLabels from overwriting existing labels
- **Bug #1213**: Fixed update_shared_drive_metadata to properly merge restrictions object instead of overwriting
- **Bug #1236**: Updated create_permission domain validation and admin parameter handling
- **Bug #1238**: Fixed get_content to make content field optional in RevisionModel
- **Bug #1337**: Fixed error message for NoneType iteration issue in list_user_files query parsing
- **Bug #1372**: Added protection against root folder deletion in delete_file_permanently

#### **WhatsApp API**
- **Bug #1140**: Enhanced WhatsApp send_message contact lookup with +country code support
- **Bug #1234**: Fixed list_messages to properly match phone numbers from contacts instead of relying only on JID
- **Bug #1235**: Added Pydantic validation to WhatsappContact model output in search_contacts
- **Bug #1313**: Fixed send_file to correctly serialize media_type enum as string instead of enum object
- **Bug #1490**: Improved error handling in send_message to provide detailed ValidationError messages instead of generic errors
- **Bug #1491**: Fixed send_message to handle missing sender_jid gracefully when creating quoted_message_info
- **Bug #1492**: Fixed list_messages to include status and forwarded fields, and complete media_info object in format_message_to_standard_object

#### **Google Calendar API**
- **Bug #1055**: Fixed KeyError issue for invalid calendarId in list_events
- **Bug #1056**: Fixed update_calendar_metadata to validate calendarId in calendars instead of calendar_list
- **Bug #1057**: Fixed create_calendar_list to validate calendar existence before creating entry
- **Bug #1061**: Improved error messages in EventDateTimeModel to specify which field (start/end) has invalid datetime format
- **Bug #1123**: Added calendarId validation to list_events function
- **Bug #1135**: Added comprehensive EXDATE documentation to Google Calendar event functions (create_event, update_event, patch_event)
- **Bug #1216**: Fixed orderBy="updated" to sort by updated field instead of startTime in list_events
- **Bug #1219**: Fixed update_calendar_metadata to allow clearing optional fields with None values
- **Bug #1349**: Fixed create_event to raise InvalidInputError instead of TypeError for invalid calendarId (alignment with docstring)
- **Bug #1354**: Fixed get_calendar_metadata to raise InvalidInputError and ResourceNotFoundError instead of TypeError/ValueError (alignment with docstring)

#### **Google Slides API**
- **Bug #1101**: Fixed batch_update_presentation to support predefined layouts like "BLANK", "TITLE", "TITLE_AND_BODY" without requiring actual layout objects
- **Bug #1493**: Fixed get_page to raise appropriate ValidationError instead of NotFoundError for pages with invalid data structure
- **Batch Update**: Fixed deep merge for patch operations and implemented atomic updates

#### **Google People API**
- **Bug #950**: Fixed search_people to handle data inconsistency where phone types are stored as strings vs enum objects
- **Bug #993**: Fixed search_people enum serialization issues and NoneType errors when displayName is None
- **Bug #1007**: Fixed list_connections enum serialization issues in phoneNumbers type field

#### **Google Sheets API**
- **Bug #853**: Fixed create_spreadsheet to return all promised fields including driveId, permissions, parents, size, createdTime, and modifiedTime
- **Bug #1098**: Fixed append_spreadsheet_values and get_spreadsheet_values range parameter handling issues
- **Bug #1338**: Fixed create_spreadsheet drive ID handling and size formatting (size as string, driveId population)
- **Bug #1494**: Fixed create_spreadsheet to accept data input in Sheet1!A1:D3 format for backward compatibility

#### **Google Docs API**
- **Bug #611**: Fixed get_document to return content in consistent structure (elementId/text format)
- **Bug #677**: Fixed batch_update_document to properly handle location and endOfSegmentLocation, and cast floats to integers
- **Bug #902**: Fixed batch_update_document docstring and schema alignment for InsertTextRequest structure
- **Bug #1221**: Fixed batch_update_document to use consistent content format (elementId/text) instead of mixing textRun structure
- **Bug #1222**: Fixed create_document to use current time for createdTime and modifiedTime instead of hardcoded values
- **Bug #1348**: Fixed get_document to handle empty string for suggestionsViewMode parameter correctly

#### **Phone API**
- **Bug #988**: Fixed show_call_recipient_choices to properly apply default value for endpoint_type parameter
- **Bug #1025**: Fixed show_call_recipient_choices docstring to mark endpoint and endpoints as optional with proper context
- **Bug #1070**: Fixed make_call validation issues for boolean parameter type conversion and URL validation
- **Bug #1232**: Fixed make_call to search for contact by name when contact_name is provided in recipient object
- **Bug #1233**: Fixed show_call_recipient_choices to handle missing or empty contact_endpoints gracefully

#### **Contacts API**
- **Bug #1138**: Fixed search_contacts to include all missing fields in pydantic models (isWorkspaceUser, notes, whatsapp, phone)
- **Bug #1194**: Fixed create_contact docstring to clarify that at least one of 'family_name', 'email', or 'phone' must be provided
- **Bug #1452**: Fixed list_contacts docstring to correctly specify organizations list type as List[Dict[str, Any]] instead of List[Dict[str, str]]
- **Bug #1453**: Fixed create_contact to include organizations field in returned contact object

#### **Generic Calling API**
- **Bug #1406**: Fixed test file imports to use proper import statements via init file

#### **Airline**
- **Bug #1126**: Updated flight search docstring to clarify response structure and removed unused fields.
- **Bug #1456**: Corrected `list_all_airports` docstring — clarified that return keys are **IATA codes**, not city codes.
- **Bug #1117**: Fixed `book_reservation` function validation to ensure proper handling of flight_type parameter for one-way and round-trip bookings
- **Bug #1119**: Fixed `book_reservation` function validation to ensure proper cabin class validation for basic_economy, economy, and business classes

#### **Android Media Control**
- **Bug #1125**: Enhanced `previous()` to restart the current track when already at the first playlist item, matching real media player behavior.
- **Bug #1134**: Fixed pause/resume/stop actions to handle no-op scenarios gracefully. Actions now return success when already in the target state.
- **Bug #1294 / #1295**: Refactored media control methods to verify playlist availability and improved `play_media` to support forced position resets and handle missing media scenarios.
- **Bug #1458 / #1459**:
  * **Resume:** Supports PAUSED and PLAYING; already PLAYING is now a no-op.
  * **Stop:** Works even when no media is loaded (no-op) and syncs playlist after reset.
  * **Docs & Tests:** Improved clarity and coverage for new behaviors.

#### **Android Notes and Lists**
- **Bug #1297**: Fixed `append_to_note` so that `None` text content is treated as empty text instead of appending `"None"`.
- **Bug #1299**: Refactored `delete_notes_and_lists` to apply all provided filters consistently, fixing ignored parameters.
- **Bug #1300**: Updated `get_notes_and_lists` to return all items when no search parameters are provided.
- **Bug #1301**: Fixed `update_list_item` to resolve correct item IDs and prevent overwriting when `updated_element=None`.
- **Bug #1455**: Added missing input validation and sensible default values in `add_to_list`.
- **Bug #1461**: Improved `create_list` with input validation and default values.
- **Bug #1462**: Updated `create_note` docstring to include missing return field.
- **Bug #1476**: Strengthened validation and data handling in `show_notes_and_lists` and `delete_notes_and_lists`, added deep-copy protection and whitespace cleanup.

#### **Notifications**
- **Bug #1172**: Fixed critical issue where notifications and messages databases were not sharing state, preventing reply actions from appearing in message lists. Added fallback and persistence coverage.
- **Bug #1466**: Updated `reply_notification` and `build_reply_response` to support new `card_id` parameter. Added stricter validation and improved error handling.

#### **SAP Concur**
- **Bug #1122**: Corrected `get_user_details` docstring to accurately reflect all supported `payment_method` values (`gift_card`, `certificate`, `credit_card`).
- **Bug #1095 / #1094 / #1152**: Aligned documentation and data consistency across Concur endpoints.
- **Bug #1152**: Refactored date handling in `map_input_air_segment_to_db_segment` and `_get_trip_dates_from_segments` for better compatibility with both `datetime` and string formats.

#### **Stripe**
- **Bug #1043**: Fixed a redundant validation error.
- **Bug #1128**: Implemented missing `create_payment_intent` API with full Pydantic validation and error handling.
- **Bug #1311**: Enhanced `list_payment_intents` to support pagination (`starting_after`, `ending_before`, `offset`).
- **Bug #1469**: Updated the `list_products` docstring to align with the Pydantic model’s schema and field definitions.
- **Bug #1428**: Fixed Stripe test files to use proper imports via init file


#### **Figma**
- **Bug #1130**: Clear current selection when changing files and auto-select newly created nodes.
- **Bug #1292**: Updated `node_id` validation to allow colons (`:`) as valid characters.
- **Bug #1293**: Corrected `Returns` documentation for TEXT nodes — replaced `text` with `characters` field.
- **Bug #1370**: Added new `create_project` utility method for project creation within Figma workspace.

#### **Zendesk**
- **Bug #1087**: General stability and schema fixes for Zendesk module (merged legacy issue).
- **Bug #1302**: Updated method to use payload values for both processing and DB creation.
- **Bug #1303**: Added validation to prevent duplicate user creation when the same external ID already exists.
- **Bug #1304**: Cleaned up and updated `search` tool docstring, removing outdated notes.
- **Bug #1305**: Enhanced ticket update functionality with detailed audit trail and structured change events.
- **Bug #1430**: Internal refactor and stability improvements in Zendesk integration.
- **Bug #1474 / #1475**: Added validation and error-handling improvements for Zendesk API utilities.

#### **BigQuery**
- **Bug #1424**: Fixed import issues in **BigQuery** module to improve compatibility and dependency management.

#### **CES Services**
- **Bug #1436**: Fixed data structure and schema alignment in **CES Account Management**.
- **Bug #1437**: Updated **CES Loyalty Auth** module for consistent authentication flow.

#### **Instagram API**
- **Bug #1078**: Fixed timestamp field returning None instead of string in comment info, breaking sort operations
- **Bug #1163**: Fixed return object timestamp field to return proper string value instead of None
- **Bug #1182**: Standardized comment ID format while preventing collision
- **Bug #1359**: Added whitespace trimming to username input before lookup to prevent failed matches

#### **Google Chat API**
- **Bug #1105**: Fixed list_spaces to properly return available spaces in Action block instead of empty results
- **Bug #1166**: Updated query parameter documentation to specify that customer field only supports '=' operator
- **Bug #1169**: Fixed membership resource name generation to extract member ID correctly and added support for group memberships with proper Pydantic validation
- **Bug #1171**: Fixed displayName uniqueness check to only apply within same spaceType instead of across all spaces
- **Bug #1181**: Fixed thread.name filter parsing to use exact field matching instead of broad substring checks
- **Bug #1191**: Fixed requestId to return proper value from Pydantic Models
- **Bug #1280**: Enhanced parse_space_type_filter to support single quotes in addition to double quotes and fixed user membership space lookup logic

#### **LinkedIn API**
- **Bug #1146**: Fixed post_id validation to accept URN format as specified in API schema
- **Bug #1165**: Fixed empty string validation to properly handle Optional str parameter
- **Bug #1186**: Update primaryOrganizationType validation by removing invalid "NONPROFIT" value
- **Bug #1360**: Removed 'EDITOR' role in function_calling_schema and fixed acl_data in-place mutation by creating copy before modification
- **Bug #1361**: Aligned function_calling_schema poll options definition with Pydantic model expecting list format and added objective field to adContext schema

#### **Google Maps Live API**
- **Bug #1154**: Fixed "current location" to properly resolve environment variable instead of treating as literal place name
- **Bug #1174**: Aligned search_along_route parameter definition between function_calling_schema and Pydantic model, and fixed PriceLevel filter to use user's actual selection
- **Bug #1356**: Updated function_calling_schema for origin_location_bias and destination_location_bias to accept object type for coordinate dictionaries

#### **Device Settings API**
- **Bug #1175**: Fixed adjust_volume to raise error or return failure message when setting cannot be mapped to database key
- **Bug #1176**: Fixed mute_volume to raise error when setting cannot be mapped instead of returning misleading success message
- **Bug #1177**: Fixed create_action_card VOLUME_ADJUSTED comparison to use enum member instead of string value
- **Bug #1178**: Added proper error handling for non-string, non-None setting_type inputs to raise ValueError instead of causing AttributeError
- **Bug #1179**: Fixed set_volume to update main VOLUME setting when setting all volumes and completed error message with list of valid options
- **Bug #1180**: Fixed unmute_volume to raise error when setting not found in defaults dictionary instead of returning misleading success message
- **Bug #1353**: Updated SettingInfo Pydantic model to accept 0-100 range for percentage_value to allow zero values for volume and brightness
- **Bug #1355**: Fixed app existence check to be case-insensitive for app_name parameter

#### **Hubspot API**
- **Bug #1184**: Improved documentation for clarity on actual function behaviour and corrected updatedAt timestamp format to avoid double UTC designators
- **Bug #1357**: Fixed ISO 8601 timestamp generation to avoid appending 'Z' to strings already containing UTC offset

#### **Salesforce API**
- **Bug #726**: Fixed create_task to implement comprehensive semantic validation preventing logically inconsistent data states including completed tasks with future reminders, completion before due dates, contradictory priority states, and invalid recurrence configurations. Added input sanitization for XSS payloads and SOQL injection protection. Enhanced validation to prevent negative CallDurationInSeconds, zero RecurrenceInterval, empty string IDs, and improved referential integrity checking for WhatId references
- **Bug #1241**: Fixed create_event to include Name parameter in Pydantic validation process ensuring proper type checking and data integrity
- **Bug #1242**: Fixed create_task to include Name parameter in Pydantic validation by adding Name field to TaskCreateModel and populating task_attributes dictionary
- **Bug #1243**: Fixed execute_soql_query with three critical improvements: corrected type comparison logic in _evaluate_single_condition to handle boolean, date, and numerical comparisons properly instead of converting all values to strings; enhanced ORDER BY parsing to handle optional sort direction; improved IN clause parsing to correctly handle comma-separated string literals
- **Bug #1246**: Fixed query_tasks to remove non-existent filterable fields (ActivityDate, OwnerId, WhoId, WhatId, IsReminderSet, ReminderDateTime) from schema and Pydantic model, ensuring only valid database fields are used for filtering
- **Bug #1248**: Added validation in search_tasks to verify all database values are dictionaries before processing, preventing AttributeError on malformed entries
- **Bug #1249**: Fixed update_event to include Name parameter in Pydantic validation by adding Name field to EventUpdateKwargsModel and including it in update_properties dictionary

#### **MySQL API**
- **Bug #934**: Fixed function name format issue causing 'Invalid function name format: mysql_mysql_query' error by correcting function registration and naming convention
- **Bug #1270**: Fixed SQL injection vulnerability in get_resource by implementing parameterized queries instead of directly embedding unsanitized uri components (db_name, table_name) into query templates
- **Bug #1271**: Fixed _tables_for_db helper function to use correct database name instead of hardcoded 'handler_main_test' catalog when querying information_schema.tables for the 'main' database
- **Bug #1272**: Enhanced mysql_query SELECT query handling to properly default to empty list when data key contains None value, not just when key is missing

#### **Jira API**
- **Bug #1059**: Enhanced create_issue_link docstring to document available link types and aligned API implementation to store link types in proper case matching official documentation instead of lowercase
- **Bug #1096**: Implemented comprehensive get_issue_create_metadata return object with complete project metadata including key, name, lead, and issueTypes list with proper field structures
- **Bug #1155**: Enhanced create_issue due_date validation to reject empty strings and added clear format specification (YYYY-MM-DD) in docstring
- **Bug #1168**: Added assignee username existence validation in assign_issue_to_user to check against DB['users'] before assignment preventing invalid data states
- **Bug #1250**: Updated create_issue documentation to include default values for priority ('Low') and assignee ('Unassigned') in function_calling_schema and enhanced Returns docstring section to document all fields including attachments, due_date, and comments
- **Bug #1251**: Fixed create_project return value docstring to specify lead field type as Optional[str] to accurately reflect that lead can be None when proj_lead argument is not provided
- **Bug #1252**: Added ValueError to create_project_component Raises section documenting exception for input strings exceeding maximum allowed length
- **Bug #1253**: Fixed create_user to use validated_payload from Pydantic validation instead of raw payload dictionary when constructing user object, preventing AttributeError when optional object fields are explicitly set to None
- **Bug #1254**: Implemented group restriction transfer logic in delete_group_by_name to migrate comments and worklogs to swap group before deletion, and enhanced validation to check for whitespace-only strings in addition to empty strings for all group name parameters
- **Bug #1256**: Fixed find_users to properly implement includeInactive parameter by adding active field to user database schema and correcting filter logic to distinguish between active and inactive users
- **Bug #1258**: Corrected get_all_priorities docstring to specify priorities key contains List[Dict[str, str]] instead of incorrectly documented List[str]
- **Bug #1259**: Updated JiraAttachment Pydantic model configuration to accept additional fields (parentId, encoding) by setting extra='allow' or adding explicit field definitions
- **Bug #1260**: Updated get_project_by_key to return only documented fields (key, name) by filtering out undocumented lead field from database object
- **Bug #1261**: Fixed get_attachment_metadata helper function to exclude content field from returned dictionary, aligning implementation with function name and docstring description
- **Bug #1262**: Updated function_calling_schema for update_component_by_id to add minLength: 1 constraint for name and description parameters, aligning schema with implementation validation
- **Bug #1263**: Fixed update_issue_by_id comments handling to append new comments to existing list instead of overwriting, preserving comment history
- **Bug #1483**: Fixed find_groups_for_picker accountId filtering logic to search for username in group users list instead of accountId, aligning with database schema structure
- **Bug #1484**: Moved DB['issues'] initialization check to occur before _generate_id call in create_issue to prevent KeyError when issues key doesn't exist
- **Bug #1485**: Enhanced assign_issue_to_user to recognize 'Unassigned' as valid assignee name for unassigning issues, bypassing user existence validation for this special case
- **Bug #1487**: Updated get_user_by_username_or_account_id function name and documentation to clarify deprecation status and primary supported lookup method
- **Bug #1488**: Enhanced find_users to ensure all returned user objects contain documented keys (profile, groups, labels, settings, history, watch) by adding default values or filtering logic

#### **Confluence API**
- **Bug #1109**: Fixed create_content enum serialization by using model_dump(mode="json") instead of model_dump() to convert enum objects to their string values for proper JSON serialization
- **Bug #1110**: Fixed update_content enum serialization by using model_dump(mode="json") to return string values instead of enum objects
- **Bug #1139**: Enhanced update_content and create_content with comprehensive validation for required body.storage.value field and improved logic to update only provided fields instead of overwriting entire objects
- **Bug #1150**: Added proper validation in get_content_list to raise appropriate error with clear message for empty string and whitespace-only spaceKey values
- **Bug #1151**: Implemented conditional validation in create_content based on content type: postingDay required and validated as YYYY-MM-DD format for blogpost type; ancestors required as non-empty list of content IDs for comment type
- **Bug #1245**: Updated create_space return type hint to Dict[str, Optional[str]] to accurately reflect that description field can be None
- **Bug #1281**: Implemented cascading delete in delete_content to remove associated entries from DB["content_properties"] and DB["content_labels"] when content is permanently deleted
- **Bug #1283**: Fixed get_content_list version expansion logic to use correct content_id key lookup in DB['content_properties']; added validation to raise MissingTitleForPageError when type is 'page' and title is missing; updated error handling to propagate ValueError instead of silencing it; implemented actual expand parameter functionality in get_content_history helper
- **Bug #1284**: Updated get_space_content_by_type to add 'link', 'children', and 'ancestors' keys to returned content objects, aligning implementation with docstring contract
- **Bug #1285**: Enhanced search_content CQL tokenizer_regex to support numeric values and null keyword in addition to quoted strings; removed broad exception handler to properly propagate ValueError for invalid CQL syntax; added validation to handle missing body.storage keys in content records; removed unreachable return False statement after return True in _evaluate_cql_tree
- **Bug #1286**: Aligned search_content_cql schema with database structure by removing unsupported filter fields (ancestor, label, creator) or implementing proper field mapping; fixed _evaluate_cql_tree to return False instead of True for empty RPN queues
- **Bug #1287**: Implemented special restore behavior in update_content to only update version and status when transitioning trashed content to current, preventing modification of other fields; added draft update prevention logic to raise appropriate error; fixed space field structure in return value to match documented schema with space object instead of spaceKey string; added link field to returned content object

#### **Gemini CLI API**
- **Bug #1148**: Enhanced shell command parsing in get_shell_command to properly detect shell operators (&&, ||, ;) before applying internal cd handler, preventing misinterpretation of compound commands
- **Bug #1153**: Updated search_file_content to accept both directory and file paths, implementing file-specific search when file path is provided and updating documentation to clarify supported path types
- **Bug #1264**: Fixed glob function filter_gitignore implementation to match patterns against full relative path from repository root instead of only basename; removed redundant absolute path check after resolve_workspace_path call
- **Bug #1265**: Fixed is_truncated flag calculation in read_file to account for offset-based truncation from beginning of file, ensuring flag and warning header appear when content is sliced from start
- **Bug #1266**: Fixed replace function apply_replacement to perform surgical string replacement on original content instead of normalized version, preventing unintended whitespace changes; removed unconditional trailing newline addition to preserve exact literal text from new_string; corrected exception type from FileNotFoundError to FileExistsError when attempting to create file at existing path with empty old_string
- **Bug #1267**: Fixed search_file_content filePath calculation to return paths relative to workspace root instead of search_path for consistent file path representation
- **Bug #1268**: Added validation in write_file to verify existing path components are directories before parent directory creation; implemented metadata field initialization for new file and directory entries to maintain consistent database schema

#### **TikTok API**
- **Bug #1062**: Implemented search and list functionality for TikTok accounts without requiring business_id parameter, adding methods to fetch all accounts or search by account attributes

#### **Workday Strategic Sourcing API**
- **Bug #1120**: Standardized payment_method field naming across all database entries and API operations, ensuring consistent use of payment_method throughout the service
- **Bug #1291**: Fixed list_scim_users complex object attribute filtering to return empty list instead of list of empty objects when requested sub-attributes don't exist on any role objects

#### **YouTube API**
- **Bug #1159**: Enhanced list_channel_sections docstring and schema to clearly specify that empty strings are invalid for channel_id and section_id parameters, and documented the exactly-one-of requirement (channel_id, section_id, or mine) in both parameters section and schema
- **Bug #1161**: Updated list_videos schema to document the exclusive filter requirement specifying that only one of 'chart', 'id', or 'my_rating' can be provided in parameters section in addition to Raises section

#### **Blender API**
- **Bug #1160**: Updated get_scene_info docstring to accurately reflect world_settings return type as Dict[str, Any] instead of Dict[str, List[float]], accommodating all actual field types including strings and floats

#### **Android Clock API**
- **Bug #1158**: Updated modify_alarm_v2 and modify_timer_v2 docstrings to correctly specify required versus optional parameters, fixing documentation inconsistencies
- **Bug #1274**: Fixed create_clock to properly handle 24-hour time_of_day parameter without incorrect 12-hour conversion and am_pm_or_unknown combination; added validation to raise error when date and recurrence parameters are provided for TIMER type
- **Bug #1275**: Refactored create_timer to use single datetime.now() call for all timestamp calculations (fire_time, start_time, created_at) eliminating race condition and ensuring timestamp consistency
- **Bug #1276**: Fixed modify_alarm 24-hour to 12-hour time conversion to preserve PM indicator when converting times like '13:30:00' to '1:30:00 PM' instead of incorrect '1:30:00 AM'
- **Bug #1277**: Enhanced modify_alarm_v2 to update fire_time date component when alarm date is modified, maintaining data consistency; corrected function_calling_schema to mark all filters and modifications object properties as optional instead of required; added type validation to raise TypeError when recurrence value is not a list
- **Bug #1278**: Fixed modify_timer_v2 RESUME operation to extend fire_time by pause duration instead of only updating start_time; added validation to ensure mutual exclusivity of duration and duration_to_add parameters; corrected duration_to_add logic to add time to remaining_duration without resetting timer progress
- **Bug #1279**: Enhanced show_matching_timers query filtering to use normalized time and duration values from _parse_duration and _parse_time functions instead of raw query strings for accurate matching
- **Bug #1309**: Fixed change_alarm_state time_of_day processing to detect contradictions between 24-hour time and am_pm_or_unknown values, raising validation error instead of creating inconsistent time filters
- **Bug #1310**: Updated change_timer_state RESET operation to recalculate fire_time based on new start_time and original_duration, ensuring fire_time synchronization with timer state

#### **Android Reminders API**
- **Bug #1167**: Enhanced modify_reminder docstring to specify that either reminder_ids or retrieval_query must be provided but not both, clarifying mutually exclusive input requirements
- **Bug #1288**: Updated create_reminder to allow untitled reminders by removing is_boring_title check for None/empty titles, aligning implementation with optional title in function_calling_schema; removed redundant ValidationError re-raising; fixed is_future_datetime comparison to use >= instead of > to accept reminders scheduled for exact current time
- **Bug #1289**: Fixed get_reminders date and time range filtering to combine date and time into single datetime value for proper multi-day range comparison
- **Bug #1290**: Removed unused ask_for_confirmation parameter from modify_reminder logic (though keeping in signature for API compatibility); enhanced success message to reflect all applied modifications instead of only first truthy action

#### **Google Cloud Storage API**
- **Bug #1269**: Implemented soft delete policy handling in delete_bucket to check for active softDeletePolicy and perform soft deletion (set softDeleted flag and softDeleteTime) instead of hard delete when policy is enabled

#### **Slack API**

- **Bug #1085**: Allowing unauthorized users to invite others to a channel. Expected `PermissionError` is not thrown.
- **Bug #1113**: `list_users` permits cross-team listing without authorization. Lacks proper auth enforcement; conflicts with expected behavior.
- **Bug #1137**: Missing database support for `has:star`, `is:pinned`, and `is:saved` filters, rendering them non-functional.
- **Bug #1149**: Admin/member check in multiple functions raises hidden `PermissionError`, not documented in FCD; affects model recoverability.
- **Bug #1319**: `get_conversation_history` returns empty result while `list_channels` indicates messages exist.
- **Bug #1321**: Adding a user to a channel doesn't validate existence of `user_id`, causing potential data corruption.
- **Bug #1327**: `leave_conversation` crashes due to missing `members` field in `conversations` database structure.
- **Bug #1328**: Inconsistent search behavior when using date filters and wildcard searches; invalid wildcard logic implementation.
- **Bug #1329**: Channel existence validation happens after user validation, masking user-level errors when channel is invalid.
- **Bug #1330**: Channel type resolution fails due to incorrect use of `type` vs. `is_private`, causing type-based filters to break.
- **Bug #1331**: Pagination relies on unsorted user list from dictionary values; causes inconsistent paging behavior.
- **Bug #1332**: Incorrect conversation `user` assignment logic in DM creation for sorted `user_list`.
- **Bug #1334**: Misinterprets `content` as binary for Base64 encoding when `filename` suggests it; leads to data corruption.
- **Bug #1335**: Message payload incorrectly sets `user` field to username or literal "bot" instead of correct user ID.
- **Bug #1336**: Pagination break due to cursor mismatch between user filter and user ID in cursor.
- **Bug #1340**: Missing timestamp handling matches messages without `ts` when queried with `"None"`, leading to false positives.
- **Bug #1341**: Timestamps returned as integers, not strings; undocumented extra fields in usergroup response.
- **Bug #1342**: Payload `channel` stores unresolved channel name instead of ID, violating documented schema.
- **Bug #1343**: File read helper masks specific errors like `FileNotFoundError` under a generic `FileReadError`, against docstring.
- **Bug #1344**: `meMessage` does not store subtype, so "me"-style messages render incorrectly.
- **Bug #1345**: Missing `is_starred`, `is_pinned`, and `is_saved` fields in file response; case-sensitive filtering issues.
- **Bug #1346**: `has:link` filter checks nonexistent `links` key; fails to inspect message text for URLs.
- **Bug #1347**: Timestamp filter errors blame user input instead of underlying data issues.
- **Bug #1350**: Improper handling of non-dict or `None` values for `DB['channels']` key; causes `TypeError`.
- **Bug #1351**: Channel initialization with inconsistent schema (`members` at top level).
- **Bug #1438**: Incorrect module imports in tests prevent proper mocking and wrapping; test failures persist.
- **Bug #1444**: Redundant and unreachable code when updating reaction; mutation already applied.
- **Bug #1445**: Timestamp precision contract (6 decimal places) not enforced; accepts invalid formats.
- **Bug #1446**: Arbitrary truncation of `display_name` to 5 characters breaks consistency with existing data.
- **Bug #1447**: `lookupByEmail` raises undocumented `InvalidEmailError` from helper; violates public docstring.

### **Copilot API**

- **Bug #916**: `get_absolute_path` has insufficient protection against path traversal. It only validates absolute paths and still allows relative paths to escape the workspace root.
- **Bug #1037**: Subprocess execution within Copilot does not inherit the full system `PATH`. Additionally, the internal dehydrate → execute → hydrate pattern persists, resulting in inconsistent behavior.
- **Bug #1107**: API accepts invalid types for critical parameters. It allows a JSON object for the `command` parameter (expected: string), and coerces `"true"` into boolean `True` for `is_background` (expected: boolean). Lacks strict type validation.
- **Bug #1108**: Critical security vulnerabilities due to `shell=True`. Allows command injection via semicolons, reverse shells, file/network exfiltration, sandbox bypass using redirection, and exposes sensitive `env` variables.
- **Bug #1121**: `shlex.split()` used for parsing commands does not support heredoc strings. API fails when heredoc input is passed. Either documentation requires an update, or heredoc support must be added.
- **Bug #1440**: Test imports bypass the `__init__.py` wrapping. Improper import patterns like `from ..module.submodule import func` cause unwrapped execution and test failures. Requires import normalization in all test files.

#### **Additional Fixes**
- **Bug #1397**: Fixed Google Calendar test files to use proper imports via init file
- **Bug #1399**: Fixed Google Drive test files to use proper imports via init file
- **Bug #1400**: Fixed Google Sheets test files to use proper imports via init file
- **Bug #1402**: Fixed WhatsApp test files to use proper imports via init file
- **Bug #1404**: Fixed Contacts test files to use proper imports via init file
- **Bug #1129**: Restored gift card balance when canceling orders in cancel_order
- **Bug #1315**: Reverted get_order_details to original Tau Bench behavior, removed unintended logic changes introduced by **Bug #413**.
- **Bug #1145**: Fixed Shopify return functionality by changing `return_reason` field type from enum to string for better flexibility and API compatibility
- **Bug #1189**: Fixed Gmail draft message creation when `userId` parameter contains email addresses by improving database lookup logic
- **Bug #1314**: Enhanced Gmail message retrieval by adding BCC and CC fields support for metadata format responses
- **Bug #1317**: Synchronized `list_customers` function logic with docstring specifications, including proper field validation and sorting implementation
- **Bug #1320**: Fixed sorting functionality in Shopify `list_products` with comprehensive test coverage for the sort criteria
- **Bug #1325**: Fixed sorting functionality in Shopify `search_products` with comprehensive test coverage for the sort criteria
- **Bug #997**: Added a new Pydantic model, ActiveConferenceModel, to specifically validate the activeConference object, ensuring it contains the required conferenceId field during updation of the Google Meet meeting space.
- **Bug #1147**: Added duration and state as optional fields to the RecordingStorage model and updated the doc string return value to match tool response, ensuring data consistency and accurate API contract for listing Google Meet conference recordings.
- **Bug #1035**: Enhanced error handling for new file creation in edit_file function with fail-fast mechanism to prevent creating files with leading delimiters, including comprehensive unit tests.
- **Bug #1111**: Enhanced command execution handling with non-zero exit code policies including utility functions for primary command identification and allowed exit codes for commands like grep, diff, and cmp with comprehensive test coverage.
- **Bug #1115**: Added sync_db_file_to_sandbox function to common_utils and created API wrappers for synchronizing database file entries with active sandbox, including proxy functions in cursorAPI and terminal API.
- **Bug #1188**: Implemented comprehensive file editing functionality with multiple occurrence handling, including support for editing specific occurrences, comprehensive error handling, and extensive test coverage for various edge cases.
- **Bug #1307**: Refactored cursorAPI and qdrant_config for improved snippet handling with string format snippet_bounds, optional commit_hash and git metadata, and distance-based snippet sorting for enhanced relevance. 
- **Bug #1240**: Enhanced update_issue docstring to document all milestone fields including repository_id and complete creator information
- **Bug #1308**: Aligned create_issue user object structure between implementation and database for consistent API responses
- **Bug #1312**: Expanded create_repository owner object to include all required fields (node_id, type, site_admin) and updated return type hint
- **Bug #1144**: Implemented AND logic for multi-word searches across all search functions (search_issues_and_pull_requests, search_repositories, search_users, search_repository_code) with word-boundary matching to prevent false positives
- **Bug #1324**: Fixed file storage format to match real GitHub API behavior, ensuring proper compatibility with agent tools and search functionality
- **Bug #1111**: Refactored run_command to correctly handle chained commands (e.g., using && or ||). The fix removes special internal parsing for commands like cd and mkdir, delegating all external command execution to the shell for more robust and predictable behavior.
- **Bug #1114**: Unified the logic in run_terminal_cmd with the Terminal API to correctly handle chained commands. The fix removes special internal command parsing and delegates execution to the shell, ensuring reliable behavior and accurate tracking of the current working directory.
- **Bug #1036**: Refined edit_file context matching to differentiate between weak (whitespace-only) and strong contexts, preventing incorrect edits on ambiguous whitespace.
- **Bug #1075**: Update doc sting and specs from label names to label IDs in modify_message_labels.
- **Bug #1298**: Set user actual email in sender and from email when sender is me to resolved to the actual email address.
- **Bug #1306**: Pass payload key to send draft method and removed the try catch around input pedantic validation in send draft method.
- **Bug #1318**: Fix include spam and trash filter for draft_list so we can properly filter out spam and trash drafts by passing include_spam_trash parameter.
- **Bug #999**: Added semantic search in list design.
- **Bug #828**: Updated Canva design type structure, added validated ID generation, default thumbnail, and Canva URLs support with updated validations and tests.
- **Bug #1099**: Updated draft creation to use a default sender when sender is missing or provided as an empty value.
- **Bug #1190**: Standardized color validation with COLOR_REGEX, restricted label type to user, resolved userId mapping in label operations
- **Email Normalization**: Added email normalization functionality across services
- **Import Refactoring**: Comprehensive import statement refactoring across multiple modules for improved code organization
- **Code Quality**: Various code quality improvements including docstring fixes, type hints, and error handling enhancements


# [0.1.5]

## Release - 2025-10-10

### **API Changes & Improvements**

#### **Google Drive API**
- **Enhanced Role Mapping**: Improved API/model role handling with comprehensive role mapping functionality
- **Permission Management**: Enhanced permission role validation and mapping across Google Drive API

### **Tech Debt Closure**

#### **Instagram**

- **Enhanced Input Validation**: Comprehensive validation across all User, Media, and Comment operations with improved type checking and error handling
- **Pydantic Models**: Introduced complete Pydantic models for Instagram entities with type-safe data structures and validation constraints
- **Database Improvements**: Restructured database storage using dictionaries, removed redundant models, and streamlined data structures
- **Code Quality**: Fixed file naming, optimized imports, enhanced type hints, and improved test organization
- **Testing Expansion**: Significantly expanded test coverage including decorator tests, edge cases, and improved test stability

#### **Google Chat**

- **Comprehensive Input Validation**: Overhauled validation across all operations including Spaces, Messages, Members, Reactions, Events, Media, and User Spaces with strict type checking
- **Centralized Utilities**: Added utility functions (`parse_page_token`, `parse_space_type_filter`, `apply_filters`, `space_sort_key`) with 148+ lines of custom error definitions
- **Expanded Pydantic Models**: Massively expanded models (592+ lines) for Space, Message, Member, and Reaction entities with comprehensive validation rules
- **Enhanced Documentation**: Improved docstrings, parameter descriptions, and return type consistency across all modules to align with Google Chat API best practices
- **Massive Test Expansion**: Added 4,900+ lines of comprehensive unit tests including dedicated 819-line test file for filter functionality
- **Code Quality**: Implemented proper PATCH semantics, refactored key functions, eliminated silent failures, and enhanced type safety throughout

#### **Google Maps**

- **Enhanced Input Validation**: Comprehensive validation across all Places API operations including place details, autocomplete, text search, nearby search, and photo retrieval
- **Pydantic Models**: Added 306+ lines of Pydantic models for Place, Photo, and related entities with type-safe data structures and validation constraints
- **Code Refactoring**: Significantly refactored Places and Photos modules with improved organization, validation logic, and error handling patterns
- **Test Coverage Expansion**: Added 505+ new test lines for Places API, updated import/performance/smoke tests, fixed flaky tests, and added comprehensive edge case testing

#### **GitHub Actions**

- **Enhanced Input Validation**: Improved validation for workflow operations (`get_workflow`, `list_workflows`, `get_workflow_run`, `get_workflow_run_jobs`) with pagination and parameter validation
- **Documentation Improvements**: Enhanced docstrings across all modules, fixed return type annotations in `list_workflows`, and improved parameter descriptions
- **Code Refactoring**: Refactored workflow retrieval functions with improved validation logic, type hints, and error handling patterns

### **Bug Fixes**

#### **Google People API**
- **Bug #693**: Implemented sources parameter filtering in search_people function with proper collection mapping
- **Bug #690**: Aligned search_people sources enum with official Google People API (5 correct enum values)
- **Bug #840**: Enhanced search_people method to handle None values gracefully
- **Bug #694**: Fixed core search functionality to reliably find contacts by resourceName and handle special characters
- **Bug #695**: Fixed incomplete/invalid objects in search_people responses when using read_mask
- **Bug #870**: Fixed enum serialization issues and improved documentation across 10 functions

#### **Google Drive API**
- **Bug #830**: Fixed delete_permission to return success confirmation instead of None
- **Bug #886**: Aligned PermissionBodyModel with official Google Drive API roles
- **Bug #852**: Enhanced validation to reject string values for copyRequiresWriterPermission parameter
- **Bug #835**: Fixed delete_file_comment to return success confirmation
- **Bug #821**: Corrected parents field handling in update_file_metadata_or_content
- **Bug #773**: Fixed wildcard handling in get_drive_account_info fields parameter
- **Bug #774**: Added null byte validation to get_drive_account_info fields parameter
- **Bug #775**: Enhanced handling of sub-fields of non-objects in get_drive_account_info
- **Bug #786**: Fixed delete_file_permanently to return success indicator instead of None
- **Bug #772**: Prevented database modification during GET operations (read-only enforcement)
- **Bug #798**: Fixed _ensureuser function to prevent implicit user creation in read-only operations
- **Bug #845**: Fixed hydrate_db function to prevent malformed database entries
- **Bug #851**: Enhanced create_shared_drive validation for restrictions object
- **Bug #905**: Fixed critical security vulnerability in create_permission authorization
- **Bug #908**: Updated create_permission to match real API validation behavior
- **Bug #936**: Fixed ModifiedTime key update in update_file_metadata_or_content
- **Bug #1020**: Fixed create_file_or_folder modifiedDate parameter validation

#### **Google Calendar API**
- **Bug #899**: Enhanced create_calendar_list to allow empty description strings
- **Bug #945**: Updated update_event docstring to mark summary as Optional[str] in Returns section
- **Bug #397**: Fixed timeZone parameter format validation in get_event
- **Bug #656**: Fixed path traversal vulnerability in create_calendar_list_entry timeZone parameter
- **Bug #657**: Enhanced input validation to reject empty strings for optional parameters
- **Bug #758**: Fixed patch_event to prevent events with negative duration
- **Bug #759**: Enhanced recurrence validator to check actual month lengths
- **Bug #760**: Fixed multiple security vulnerabilities in patch_event including XSS and DoS protection
- **Bug #846**: Fixed FC Spec and docstring alignment for timeMin and timeMax parameters
- **Bug #862**: Improved error message for start/end time validation in update_event
- **Bug #863**: Fixed multiple security vulnerabilities in update_calendar_metadata
- **Bug #864**: Enhanced input validation and sanitization in update_calendar_metadata
- **Bug #868**: Fixed HTML entity encoding in create_secondary_calendar
- **Bug #874**: Fixed error type for invalid calendarId in delete_secondary_calendar
- **Bug #915**: Fixed critical data integrity and security flaws in update_event
- **Bug #917**: Fixed authorization logic and timeZone parameter handling in get_event
- **Bug #924**: Enhanced timezone validation in update_event
- **Bug #1054**: Fixed patch_calendar_list to use pydantic models and allow None values

#### **Google Sheets API**
- **Bug #878**: Fixed batch_get_spreadsheet_values data fetching functionality
- **Bug #832**: Enhanced get_spreadsheet to return complete properties object
- **Bug #778**: Fixed batch_update_spreadsheet_values to properly update spreadsheet values
- **Bug #820**: Fixed get_spreadsheet_values to fetch all data with correct range handling
- **Bug #827**: Enhanced get_spreadsheet_values to handle sheet name and range parameters correctly
- **Bug #887**: Fixed batch_get_spreadsheet_values to use first visible sheet when no sheet specified
- **Bug #925**: Fixed clear_spreadsheet_values to properly clear sheet contents
- **Bug #943**: Fixed create_spreadsheet to set correct createdTime, modifiedTime, and size fields

#### **Copilot API**
- **Bug #954**: Enhanced list_dir function error handling and input validation
- **Bug #953**: Fixed grep_search function reliability and security vulnerabilities

#### **WhatsApp API**
- **Bug #791**: Fixed load_state UnicodeDecodeError in WhatsApp database operations

#### **Phone API**
- **Bug #962**: Fixed show_call_recipient_choices endpoint_type field validation

#### **Confluence API**
- **Bug #564**: Fixed ancestor logic during content creation to properly use ancestors field for comment type content
- **Bug #637**: Implemented expand parameter with proper validation, error handling, and schema alignment; added limit size validation and CQL parser improvements
- **Bug #892**: Enhanced spaceKey validation to enforce non-empty string requirement and updated docstring
- **Bug #914**: Fixed space parameter handling in query to properly filter results instead of being ignored
- **Bug #935**: Replaced mock data with actual history metadata including updated times for content items
- **Bug #948**: Implemented CQL now() function support for created and lastmodified fields
- **Bug #982**: Added SQL injection protection and proper validation for id and status parameters

#### **Contacts API**
- **Bug #952**: Fixed create_contact input validation and sanitization for phone and name fields

#### **Google Docs API**
- **Bug #689**: Fixed implicit user creation issue in create_document
- **Bug #797**: Fixed _ensureuser function to prevent implicit user creation in read-only operations
- **Bug #970**: Fixed batch_update_document functionality

#### **Google Slides API**
- **Bug #800**: Fixed _ensureuser function to prevent implicit user creation in read-only operations

#### **Jira API**
- **Bug #646**: Fixed duplicate issue_id generation to ensure unique IDs for each created issue
- **Bug #721**: Added statusCategory field to API response and corrected docstring
- **Bug #768**: Enhanced input validation to reject empty strings for proj_key and proj_name parameters
- **Bug #895**: Added proper None validation for optional profile parameter to prevent AttributeError
- **Bug #910**: Enhanced error reporting to return all invalid IDs instead of only the first one
- **Bug #927**: Fixed due_date validation to reject empty strings and ensure consistency between update and get operations
- **Bug #941**: Clarified JQL date format requirements in docstring with explicit format specifications
- **Bug #949**: Fixed case-sensitive project key handling in JQL queries
- **Bug #951**: Added updated date/time attribute support for issue tracking
- **Bug #967**: Implemented expand and fields parameters with proper validation or updated docstring to reflect limitations
- **Bug #1009**: Standardized issue link data structure to use consistent format for inwardIssue and outwardIssue
- **Bug #1023**: Fixed DB validation test setup to properly report and fix malformed records
- **Bug #1045**: Aligned create_version tool spec with implementation to correctly declare name as required parameter

#### **Android Clock API**
- **Bug #698**: Added stopwatch pause/stop functionality and made start/end time optional for elapsed time tracking
- **Bug #734**: Implemented bulk alarm operations without filter requirement and fixed time comparison logic for create_clock alarms
- **Bug #928**: Enhanced bulk timer updates to work without filters when bulk_operation=true
- **Bug #929**: Fixed time format conversion from 24-hour to 12-hour format in modify_alarm function
- **Bug #947**: Fixed time format filtering between 12-hour and 24-hour formats and improved recurrence pattern expansion
- **Bug #976**: Updated return docstring to include all fields returned by timer functions
- **Bug #1012**: Clarified snooze_duration format in docstring to specify integer value in seconds

#### **Android Reminders API**
- **Bug #898**: Updated docstring to document mutually exclusive constraint between reminder_id and retrieval query
- **Bug #911**: Added unique ID validation to prevent duplicate reminder IDs in patch operations

#### **Salesforce API**
- **Bug #756**: Enhanced search term validation to handle whitespace-only strings and enforce input length limits
- **Bug #944**: Implemented support for Salesforce date literals like TODAY and NEXT_N_DAYS:7 in SOQL queries

#### **Workday Strategic Sourcing API**
- **Bug #724**: Fixed TypeError in event creation by properly handling database key types
- **Bug #727**: Resolved DB key type inconsistency by standardizing to integer keys across all event operations

#### **Android Message API**
- **Bug #733**: Enhanced phone number validation to enforce E.164 format and reject malformed numbers

#### **Gemini CLI API**
- **Bug #842**: Fixed pytest output handling to surface stdout including test summaries, tracebacks, and environment errors

#### **TikTok API**
- **Bug #1044**: Added validation to raise error when both username and key parameters are None

#### **Slack API**
- **Bug #875**: Add: Support for blank and whitespace team_id
- **Bug #877**: Add: Empty string support for different variables
- **Bug #879**: Add: Support to send already invited user in response
- **Bug #900**: Doc Update: Creating Channel name should be unique
- **Bug #940**: Remove: Blank channel id from channel_ids
- **Bug #956**: Fix: Raise validationerror for limit parameter
- **Bug #961**: Check channel name prefix # for slack functions 
- **Bug #963**: Restricts search to a channel by name
- **Bug #965**: Fixed bugs with slack send_me_message tool.
- **Bug #966**: Fixed bugs with slack send_me_message tool
- **Bug #971**: Tool-Spec Fix, FCD Fix
- **Bug #986**: Type check for limit argument in multiple functions
 
#### **Google Maps API**
- **Bug #516**: Enhanced utility functions with comprehensive improvements for better search functionality and data handling
- **Bug #969**: Google Maps Live — Updated tool spec to mark `origin_location_bias` parameter as required in directions API

#### **Google Chat API**
- **Bug #780**: Fixed confusing error message when attempting to create messages in non-existent spaces with clearer error reporting
- **Bug #884**: Enhanced documentation by adding `displayName` field description in docstring for space type parameter
- **Bug #1015**: Fixed enum serialization bug in `add_space_member` API to properly handle enum values
- **Bug #1017**: Fixed Spaces functionality with improved error handling and validation

#### **Instagram API**
- **Bug #801**: Enhanced `get_user_id_by_username` functionality with improved error handling and comprehensive test coverage
- **Bug #807**: Fixed comment API functionality with improved error handling and validation
- **Bug #823**: Added comprehensive user_id validation across Comment, Media, and User modules with extensive test coverage
- **Bug #931**: Fixed media API inconsistencies with improved parameter handling and validation
- **Bug #974**: Updated documentation across Comment, Media, and User modules for better clarity and consistency
- **Bug #975**: Improved User API functionality with enhanced error handling and code organization

#### **Device Settings API**
- **Bug #628**: Added `set_brightness` functionality with comprehensive test coverage for brightness control
- **Bug #629**: Implemented WiFi connection functionality including `connect_wifi` and `list_all_available_wifi` with extensive test coverage
- **Bug #705**: Updated docstrings to reflect case-insensitive parameter handling for improved documentation accuracy
- **Bug #826**: Fixed FLASHLIGHT get function to return proper on/off boolean values instead of inconsistent string representations
- **Bug #946**: Resolved type validation bug in device settings with improved type checking and validation
- **Bug #980**: Fixed empty string handling issue in device settings get function with proper validation

#### **LinkedIn API**
- **Bug #998**: Fixed `primaryOrganizationType` field to return proper string values instead of enum objects with comprehensive test coverage

#### **Hubspot API**
- **Bug #1019**: Fixed `create_form` functionality with improved validation and error handling

#### **Shopify API**
- **Bug #861**: Fixed issue related to shopify list customers api where some of the parameter handling was not correct

#### **Retail API**
- **Bug #938, #939, #983, #984**: Added proper validations for empty parameters for the retail service.
- **Bug #912**: Added validation in Retail `get_order_details` API to correctly handle empty string parameters

#### **Google Home API**
- **Bug #1001, #1005, #1006, #1014**: Reinforced the documentation as well as schema with proper enum values for the google home service.

#### **Terminal | Gemini CLI | Cursor**
- **Bug #728**: Enhanced cursor.edit_file function documentation to clarify delimiter usage and context preservation rules, improving the reliability of code edits.
- **Bug #932**: Fixed tar command execution in same source and target directory across cursor.run_terminal_cmd, gemini_cli.run_shell_command, and terminal.run_command
- **Bug #990**: Terminal api functions (cursor.run_terminal_cmd, gemini_cli.run_shell_command, and terminal.run_command) can now execute with full system PATH and support all system-installed tools such as javac, mvn, npm
**Bug #838 & 841**: Fixed the issue with supressed errors for all terminal related service. This should improve error reporting for failing tool call which utilizes terminal funciotnality in Terminal, Cursor, and gemini CLI services

#### **Gmail API**
- **Bug #964 & #995**: Fixed Gmail API's label count sync issue; message and label counts now can be updated correctly on label changes, and label names are now case-sensitive to match the official API.
**Bug #616**: Fixed issue in the Gmail service, list_drafts where the 'AND' operator caused incorrect results
**Bug #893 & 779**: Modified Gmail tools to accept multiple recipients and added CC+BCC functionality. 

#### **Google Meet API**
**Bug #1046**: Fixed google_meet issue in create_meeting_space tool to handle cases where a space with the given name already exists in the database.

#### **Device Actions API**
- **Bug #715**: Added support for `browser` key in phone state model to store recently opened web pages and browser status
- **Bug #717**: Fixed issue where device could not be turned back on after `power_off` action
- **Bug #968**: Fixed `open_app` action behavior to validate `extras` — now requires a `query` key with a string value when extras are presents

### **Airline**
- **BUG #903**: Added checks in `book_reservation` to raise `CustomValidationError` if `flights`, `passengers`, or `payment_methods` lists are empty and added unit tests.
- **BUG #904**: Enhanced expression validation in `calculate` function by stripping whitespace before processing.
- **BUG #854**: Added input validation for tool transfer_to_human_agents which validates the white space only empty string.
- **BUG #889**: Added input validation for tool update_reservation_baggages whitespace only empty string and value check against the possible enum values.
- **BUG #890**: Added input validation for tool get_user_details to validate the white space and update ocstring for returning object.
- **BUG #785**: Fixed issue where the `create_user` utility function was not in sync with the DB schema and did not perform validations, leading to potential data inconsistencies. Utilized the `User PydanticModel` for validation while creating a new user via the `create_user` utility method.

### **Android Media Control**
- **BUG #839**: Updated media player merging logic to include vendor players and added unit tests for vendor database workflow.

### **Android Notes and Lists**
- **BUG #787**: Added validation to ensure `list_name` is a string, updated logic to allow adding items to a list by its name, and expanded test suite for edge cases.
- **BUG #790 and #837**: Apply the search engine to all search methods and fix search_notes_and_lists which was importing a method from utils in _function_map.
- **BUG #850**: Applies validations to verify that the parameters list_id, search_term or list_item_id, query, query_expansion are being sent    
- **BUG #872**: Enhanced `delete_list_item` to support deletion by search term, updated documentation, and added tests for new behavior.
- **BUG #960**: Updated the docstring for `show_notes_and_lists` method to indicate that empty lists can be returned.

### **Andriod Notifications**
- **BUG #921**: Added input validation for tool get_notifications for sender_name and app_name with whitesapces.

### **Figma**
- **BUG #802**: Fixes Empty Response issue by changing the value of the layout_wrap parameter from None to "NO_WRAP"
- **BUG #860**: Updated docstring to clearly mentioned the parameter constraints.

### **SAPConcur**
- **BUG #831**: Introduced `ReservationAlreadyCancelledError` in `cancel_booking` to handle already cancelled bookings and updated docstring.

### **Zendesk**
- **BUG #716**: Fixes issue related to generated_timestamp conversion and removes show_ticket from __init__, as it was duplicated.
- **BUG #873**: Updated descriptions in `show_ticket` and `update_ticket` to specify IDs must be >= 0, refined `TicketUpdateInputData` model, and added validation for `voice_comment`.
- **BUG #891**: Introduced a new validator for `name` field in `UserCreateInputData` to ensure it's not empty or whitespace and added unit tests for validation.
- **BUG #989**: Added missing field in update_ticket, that can be updated and are missings.
- **BUG #855**: Fixed edge case in `zendesk.get_ticket_details` for `ticket_id = 0` from adversarial QA and removed the minimum `1` requirement from the FC spec of `get_ticket_details` in Zendesk.  
- **BUG #894**: Fixed issue in `zendesk.create_user` method as per bug report 894 from adversarial QA.

#### **Porting Functions**
- New Porting Functions - Clock, Media Library, Phone, Google Home
- Fixes for Gmail Porting

---

# [0.1.4.4]

## Release - 2025-10-20

### Cross-Service Enhancements

* **Schema & Model Consistency:** Aligned tool specification response schemas with Pydantic response models across several services, including `ces_billing`, `ces_system_activation`, and `ces_loyalty_auth`.  
  * Ensured consistency for `required` vs. `optional` fields.  
  * Explicitly marked optional fields as `nullable: True` in response schemas where applicable.  
* **Strict Model Validation:** Enforced strict validation for `ces_billing` and `ces_system_activation` models by inheriting from `StrictBaseModel`, which forbids extra properties being passed.  
* **New Utility:** Added a new `get_conversation_end_status` utility function.  
  * This function retrieves the stored message for a terminating call from the database.  
  * It has been integrated into the `_utils_map` for `ces_billing` and `ces_system_activation`.

### Service-Specific Updates

* **CES Account Management (`ces_account_management`)**  
  * Significantly expanded the `CustomerAccountDetails` response schema.  
  * Added new structured properties for: `billingAddress`, `serviceAddress`, `communicationPreferences`, `devices`, and `services`.  
  * Removed the `orders` field from the `CustomerAccountDetails` response model.

### Internal & Refactoring

* **Database:** CES Billing - Renamed the database field `end_of_conversation_status` to `_end_of_conversation_status` and updated all relevant test cases.

---

# [0.1.4.3]

## Release - 2025-10-16

### Overview

Version 0.1.4.3 is an enhancement release that introduces two new generic communication modules, significantly expands test coverage across the platform, and adds advanced porting capabilities for service migrations. This release focuses on unifying communication interfaces and improving code quality through comprehensive testing.

### New Features

#### New Generic Communication Modules

##### 1. **Generic Calling** (`generic_calling`)

A unified calling interface that abstracts phone and WhatsApp calling functionality:

**Features:**

- Single entry point for all calling operations  
- Intelligent routing to appropriate service (Phone or WhatsApp)  
- Support for both voice and video calls  
- Speakerphone control  
- Contact selection and validation  
- Comprehensive error handling for invalid recipients

**Key Functions:**

- `make_call()` - Make calls via appropriate service  
- `show_call_recipient_choices()` - Display available recipients  
- `show_call_recipient_not_found_or_specified()` - Handle missing recipients

**Architecture:**

- SimulationEngine integration for testing  
- Custom error classes for specific failure scenarios  
- Pydantic models for data validation  
- Service-agnostic interface design

##### 2. **Generic Messages** (`generic_messages`)

A unified messaging interface for SMS and WhatsApp messaging:

**Features:**

- Single API for all text messaging needs  
- Automatic routing between SMS and WhatsApp  
- Multi-media attachment support (images, videos, documents, audio)  
- Bulk messaging capabilities  
- Message formatting and validation  
- Recipient management and selection

**Key Functions:**

- `send()` - Send messages via appropriate service  
- `show_recipient_choices()` - Display available recipients  
- `ask_for_message_body()` - Request message content  
- Service-specific routing logic

**Media Support:**

- Images (IMAGE_RETRIEVAL, IMAGE_GENERATION, IMAGE_UPLOAD, GOOGLE_PHOTO)  
- Videos, Documents, and Audio files  
- Different handling for SMS vs WhatsApp attachments  
- Automatic format conversion where needed

---

# [0.1.4.2]

## Release - 2025-10-14

### Overview

This patch release (v0.1.4.2) introduces a centralized configuration system for CES services' integration with Google Cloud Platform (GCP) Infobot, along with enhanced test coverage for existing functionality. This release focuses on improving service configuration management and code quality.

### New Features

#### CES Infobot Configuration System

A new centralized configuration management system has been introduced for CES services that integrate with Google's Infobot platform:

##### **Core Configuration Module** (`common_utils/ces_infobot_config.py`)

- **Purpose**: Provides a standardized way to manage GCP/Infobot integration settings across all CES services  
- **Key Features**:  
  - Centralized configuration for GCP project settings, locations, and API endpoints  
  - Service-specific configuration management through `CESInfobotConfigManager`  
  - Support for configuration loading from files or environment variables  
  - Base64 encoded service account authentication support  
  - Tool resource management for each CES service  
  - Configuration persistence and reset functionality

##### **Configuration Structure**:

```py
- GCP Project settings (project ID, location, app ID)
- API configuration (version, endpoint)
- Authentication (service account info, scopes, CA bundle)
- Service-specific tool resources mapping
```

#### Integration with Existing CES Services

The new configuration system has been integrated with:

- **CES Account Management** - Enhanced image upload and API integration  
- **CES System Activation** - Improved service activation workflows

### Enhancements

#### Pydantic Model & Tool Spec Improvements for CES Services

##### **Tool Spec Decorator Enhancements**

All CES services have been enhanced with the addition of response schemas and a new, cleaner tool specification format:

- **Previous Format (v0.1.4.1)**:

```py
@tool_spec(spec={'name': '...', 'description': '...', 'parameters': {...}})
```

- **New Format (v0.1.4.2)**:

```py
@tool_spec(
    input_model=GetCustomerAccountDetailsInput,
    output_model=CustomerAccountDetails,
    description="...",
    error_model=[...],
    spec={'name': '...', 'description': '...', 'parameters': {...}, 'response':{...}}
)
```

##### **Pydantic Model Enhancements**

- **Input/Output Model Separation**: Created separate Input and Output models for all CES service functions  
  - Example: `GetBillingInfoInput`, `GetbillinginfoResponse`  
- **Field Descriptions**: All model fields now use `pydantic.Field` with explicit descriptions  
  - Example: `callId: str = Field(..., description="Call identifier")`  
- **Model Validators**: Added `@field_validator` and `@model_validator` for complex validation  
- **Enhanced Type Hints**: Added support for `Union` and `Literal` types  
- **Import Updates**:  
  - From: `from pydantic import BaseModel`  
  - To: `from pydantic import BaseModel, Field, field_validator, model_validator`

##### **Affected CES Services**

- **ces_account_management**: Updated all function signatures and models  
- **ces_billing**: Complete model refactoring with Field descriptions  
- **ces_loyalty_auth**: Migrated to new tool_spec format  
- **ces_system_activation**: Enhanced with validators  
- **ces_flights**: Updated with new model patterns

#### CES Billing Improvements

- **MDN Validation** - Updated mdn validation logic to allow 8-11 digits instead of the previous 10-11 digits  
- **Default DB Messages** - Ensured default messages are updated in DB for the terminating calls, escalate, fail, cancel, ghost, and done, if called without the optional argument.  
- **New Utilities** - Two new utilities were added:  
  - `get_conversation_end_status` - Retrieves the stored message for the terminating call from the database when given the specific termination function called.  
  - `get_default_start_flows` - Retrieves the default start flows data from the database.

#### Improved Test Coverage

##### **New Test Files Added**:

1. **`common_utils/tests/test_ces_infobot_config.py`**  
     
   - Comprehensive test suite for the new configuration system  
   - Tests for default values, custom configurations, and environment variable loading  
   - Configuration persistence and reset functionality tests  
   - Service-specific tool resource management tests

   

2. **`common_utils/tests/test_tool_spec_decorator_comprehensive.py`**  
     
   - Enhanced coverage for the tool specification decorator  
   - Tests for ErrorObject.to_dict() method  
   - Schema cleaning and inline reference processing  
   - Pydantic model validation and error handling  
   - Wrapper function validation and return handling

   

3. **`ces_account_management/tests/test_infobot_config_integration.py`**  
     
   - Integration tests for account management with new config system  
   - Token generation with configured service account  
   - Error handling for invalid configurations  
   - Image upload functionality with new config

   

4. **`ces_system_activation/tests/test_infobot_config_integration.py`**  
     
   - Integration tests for system activation services  
   - Configuration management within activation workflows  
   - Service-specific settings validation

   

5. **`ces_billing/tests/test_docstrings.py`**  
     
   - Automated docstring validation for billing module  
   - Ensures consistent documentation standards  
   - Validates function and class documentation structure

---

# [0.1.4.1]

## Release - 2025-10-13 

### Overview

This release (v0.1.4.1) introduces four new CES services, enhances the existing CES Account Management module, and includes improvements to testing coverage and a new dependency for report generation.

### New Features

#### New CES Services

The release adds four new CES services designed to enhance customer service capabilities:

##### 1. **CES Billing Service** (`ces_billing`)

- Complete billing management system for customer accounts  
- Features include:  
  - Billing information retrieval  
  - AutoPay enrollment functionality  
  - Bill processing and routing  
  - Escalation capabilities for billing disputes  
  - Support for bill reduction requests and repeat maxout handling

##### 2. **CES Flights** (`ces_flights`)

- Comprehensive flight booking and management service  
- Features include:  
  - Flight search with extensive filtering options (dates, passengers, airlines, prices, baggage)  
  - Flight booking with traveler details  
  - Round-trip booking support  
  - Integration with multiple airlines  
  - Seat class selection (economy, premium economy, business, first class)

##### 3. **CES Loyalty Authentication** (`ces_loyalty_auth`)

- Customer loyalty program and authentication management  
- Features include:  
  - Customer profile authentication and retrieval  
  - Loyalty offer enrollment  
  - Pre-authentication call data management  
  - Secure authentication state management  
  - Profile information access with payment history

##### 4. **CES System Activation** (`ces_system_activation`)

- Service activation and technician visit management  
- Features include:  
  - Technician appointment scheduling and rescheduling  
  - Service activation status tracking  
  - Activation guide search functionality  
  - Customer notification system  
  - Visit detail management and issue flagging  
  - Order detail searches

### Enhancements

#### CES Account Management Improvements

The existing **CES Account Management** module received significant enhancements:

##### Enhanced Test Coverage

- **`test_core_functions.py`** - Comprehensive testing for core account management functions including:  
    
  - Account information retrieval and updates  
  - Plan and feature management  
  - Terminal function operations (escalate, cancel, fail, done)  
  - Account validation and error handling


- **`test_query_available_plans_and_features.py`** - Dedicated tests for:  
    
  - Plan availability queries  
  - Feature compatibility checks  
  - Plan comparison functionality  
  - Service tier validation


- **`test_utils.py`** - Utility function testing covering:  
    
  - Helper functions and validators  
  - Data transformation utilities  
  - Common operations used across the module  
  - File and phone utility integration

##### Functionality Improvements

- **Search Architecture Change**: Migrated from embedding-based search to LLM-based search using Gemini API  
  - The `search_plans_by_query()` function now uses `_get_gemini_response()` for intelligent query processing  
  - Provides more accurate and contextually relevant results than traditional keyword or embedding matching  
  - Supports semantic understanding of device types, cost levels, data amounts, features, and usage patterns  
  - Better handling of natural language queries like "affordable plans" or "plans under $50"  
- Better validation for account operations  
- Enhanced error handling for edge cases  
- Improved integration with the SimulationEngine framework

#### New Dependencies

- Added `reportlab==4.4.4` - Python library for generating PDFs and graphics

---

# [0.1.4]

## Release - 2025-09-18

### **API Changes & Improvements**

#### **Google Home API**
- **Relaxed Validation**: We have now allowed any Device name to be passed and now we can process new device with existing traits. If the new device has to use a new trait then that is a limitation. This is a major improvement and will allow us to process new devices with existing traits fixing majority of Google Home porting samples. 

### **Bug Fixes**

#### **Google Calendar API**
- **Bug #471**: Enforced timezone awareness for timeMin and timeMax parameters in event queries
- **Bug #462**: Fixed issue related to secondary calendar deletion operations
- **Bug #397**: Clarified timeZone format requirements in get_event docstring
- **Bug #405**: Enhanced create_calendar functionality and error handling
- **Bug #396**: Allowed empty recurrence list in patch_event operations
- **Bug #665**: Fixed XSS vulnerability in create_secondary_calendar - API incorrectly accepted and stored XSS payloads without validation or sanitization
- **Bug #660**: Fixed data integrity issue in create_secondary_calendar - function accepted potentially conflicting IDs without validation
- **Bug #658**: Fixed timezone validation in create_calendar_list_entry - system now validates against IANA timezone database instead of accepting invalid timezone values
- **Bug #655**: Fixed XSS vulnerability in summary and description fields by adding comprehensive input validation and sanitization
- **Bug #659**: Fixed security vulnerability in Google Calendar create_calendar_list_entry

#### **Google Docs API**
- **Bug #550**: Added deleteContentRange and replaceAllText support for content operations

#### **Google Sheets API**
- **Bug #393**: Enhanced batch_update_spreadsheet to properly handle empty request arrays
- **Bug #723**: Fixed Google Sheets validation to allow reading from empty spreadsheets with default Sheet1 structure

#### **Google Slides API**
- **Bug #559**: Fixed docstring issue in batchUpdate function for better parameter documentation

#### **Google Drive API**
- **Bug #777**: Fixed `list_files` filtering issue where exact value matches were failing with "contains" filter (e.g., 'Trace Books' contains 'Trace Books')

#### **WhatsApp API**
- **Bug #440**: Fixed plus sign (+) handling in phone number parsing for chats and messages
- **Bug #386**: Improved search_contacts_data functionality and reliability

#### **Phone API**
- **Bug #463**: Fixed validation bug by adding contact consistency validation to prevent mismatched contact names and endpoints during call operations
- **Bug #533**: Fixed docstring inconsistencies for phone number format validation
- **Bug #389**: Enhanced make_call function to handle incomplete recipient information

#### **Contacts API**
- **Bug #492**: Fixed is_whatsapp_user flag incorrectly set to True when no phone number provided

#### **Google People API**
- **Bug #690**: Fixed improper handling of invalid enum values in sources parameter - aligned search_people sources enum with official Google People API

#### **GitHub API**
- Many quality of life improvements for documentation, validation and robustness

#### **Gmail API**

- **Bug #697, #700, #703, #719, #720, #722, #779**: Fixed issue where previous email validation fix was being applied in unwanted places, causing failures on multiple endpoints
- Many quality of life improvements for documentation, validation and robustness

#### **Cursor API**
- **Bug #663**: Added validation of database hydration before starting read operations and raising timely validation errors. Making implementation more robust
- Many quality of life improvements for documentation, validation and robustness


#### **Hubspot API**
- **Bug #592**: Enhanced `create_or_update_marketing_event_attendee` to allow inviting attendees without specifying join or leave times.
- **Bug #602**: Fixed date-based filtering in `get_marketing_events` to ensure it returns accurate results.
- **Bug #603 & #604**: Clarified campaign archiving behavior by ensuring all campaigns include an `is_archived` status ensuring that `get_campaigns` returns both archived and unarchived campaigns.
- **Bug #619**: Improved `update_template_by_id` by separating the archive and delete actions into their own dedicated functions.
- **Bug #620**: Enabled searching for templates by their label in `get_templates`.
- **Bug #737**: Resolved a critical error that made the Hubspot `SimulationEngine` inaccessible.

#### **LinkedIn API**
- **Bug #615**: Fixed an issue preventing post updates from being saved correctly.
- **Bug #699**: Ensured that updating a post only modifies the specified fields, preventing accidental data loss.

### **Hubspot API Update**

- **Enhanced Input Validation & Error Handling**:
  - Implemented a comprehensive validation framework across all Hubspot API operations, ensuring stricter type checking and value constraints for parameters like IDs, timestamps, and required fields.
  - Introduced a suite of specific, custom error classes to provide clearer and more actionable feedback for invalid API requests.
- **Improved Reliability & Robustness**:
  - Added new unit tests, significantly increasing test coverage to verify the new validation logic and ensure the stability and reliability of the API simulation.
- **Documentation & Code Quality**:
  - Updated API documentation, tool spec, and function descriptions to align with the new, stricter validation rules, providing better guidance for developers.
  - Refactored the codebase for better organization and maintainability.

#### **Android (Clock)**

- **Bug #624, #626**: Enhanced `show_matching_alarm` and `show_matching_timers` to support keyword-based search (instead of exact string match)

#### **Confluence**

- **Bug #584**: Fixed `SimulationEngine` import issue

#### **Salesforce**

- **Bug #590**: Fixed case-sensitive search issue in `query_events`. Improved comparison logic in `Event.py` to allow case-insensitive matching for string values

#### **Jira**

* **Bug #646**: Fixed duplicate issue ID generation after project deletion. Improved `_generate_id()` to handle gaps and malformed IDs while maintaining backward compatibility

#### **Workday**

- **Bug #609, #724**: Fixed `create_event` error caused by string/integer concatenation. Updated event ID generation to consistently treat keys as strings
- **Note**: Tech Debt Batch 2 Workday also is merged
* **Bug #644**: SAPConcur — Updated `normalize_cabin_class` to add missing decoding for fare class `"N"`.  
* **Bug #709 & #710**: Database / Stripe  
  - Fixed `get_active_database`: `current_db` used as an object but defined as a `str`.  
  - Fixed `stripe.list_invoices` tool_spec.  
* **Bug #706 & #683**: Stripe API  
  - Updated customer email description to specify maximum length of 512 characters in API documentation.  
  - Enhanced product name validation: maximum length 2048 characters, added error handling for long names, and added unit tests (including edge case for exact limit).  
* **Bug #645**: Airline — Added validation in cancel reservation if reservation is already cancelled.  
* **Bug #648**: Airline — Added validation for get reservation details to throw error for whitespace-only reservation ID.  
* **Bug #669**: Airline — Added validation for Search flight with valid calendar date only.  
* **Bug #670**: Airline — Added validation for Search flight with only three-digit coding for origin and destination.  
* **Bug #681**: Airline — Added validations in Update reservation flight for valid calendar date.  
* **Bug #754**: Airline — Added validation to ensure non-free baggage is less than total baggage.  
* **Bug #651–654**: Zendesk Search API — Added support for `"OR"` logic in queries, allowing multiple values in a single field (e.g., `status:open OR pending`).  
* **Bug #634**: Notes & Lists Service  
  - Refactored `search_notes_and_lists` function to remove legacy support and simplify parameters.  
  - Updated tests to reflect new function signature and behavior.  

* **Bug #651**: Zendesk Search API — Added support for `"OR"` logic in queries, allowing multiple values in a single field (e.g., `status:open OR pending`).  

### **Assertion Utils**

#### **Changed - Function: normalize_string**

Punctuation Handling: Added logic to the normalize_string function to explicitly remove common punctuation marks (., ,, ;, :) to ensure more consistent and thorough string normalization. This improves the function's ability to handle raw text input by cleaning it more effectively.

#### **Added - Function: parse_iso_datetime_string_to_utc**

New Utility Function: Added parse_iso_datetime_string_to_utc, a new function that robustly converts various ISO 8601 and RFC 3339 timestamp formats to a timezone-aware UTC datetime object. This function simplifies handling and standardizing timestamps from different data sources. It supports formats with and without fractional seconds and different timezone offsets, including 'Z' and '+00:00'.
 Accepted formats:
        - "2023-12-25T14:30:00Z"
        - "2023-12-25T14:30:00+00:00" 
        - "2023-12-25T14:30:00.123Z"
        - "2023-12-25T14:30:00-03:00"
        - "2023-12-25T14:30:00" (assumed to be UTC)
---

# [0.1.3]

## Release - 2025-09-12

### **API Changes & Improvements**

#### **Google Slides API**

- **Enhanced Documentation Structure**: Significantly improved `create_presentation` function with detailed structure definitions and comprehensive docstring updates
- **Conditional Requirements Documentation**: Better documentation for conditional requirements in slide creation, including proper pageType and slideProperties relationships
- **Schema Validation Improvements**: Enhanced schema validation for slide properties and notes page structures

#### **Phone API**

- **Contact Validation Improvements**: Added `validate_recipient_contact_consistency` function to ensure contact names and endpoints belong to the same contact in the database
- **Call Validation Security**: Enhanced security by preventing mismatched contact data during call operations
- **Documentation Updates**: Improved function documentation to clarify contact validation requirements

#### **SAP Concur API**

- **User Details Functionality**: Fixed `get_user_details` function with improved error handling and data retrieval

#### **Google Drive API**

- **Changes API Enhancement**: Updated `Changes.py` with improved change tracking and monitoring capabilities
- **Files API Updates**: Enhanced `Files.py` with better file management and metadata handling

#### **Generic Reminders API**

- **New Simulation Engine Components**: Added complete simulation engine infrastructure with models and utilities
- **Enhanced State Management**: Improved state management capabilities for reminder operations
- **Database Integration**: Better database integration with comprehensive CRUD operations

### **Tech Debt Closure**

#### **Figma**

##### **Enhanced Input Validation & Error Handling**

- **Comprehensive Input Validation**: Enhanced validation across all Figma API operations with improved type checking and boundary validation
- **Coordinate Validation**: Added validation for x and y coordinates in `clone_node` function to ensure values are within reasonable bounds (-10000 to 10000)
- **Node ID Validation**: Enhanced `clone_node` function to ensure `node_id` is a non-empty string with proper validation
- **Annotation Validation**: Improved `set_annotation` function with comprehensive checks for `annotationId` and `categoryId` types and values
- **Property Validation**: Enhanced property name validation in annotation operations with better error handling

##### **Documentation & Tool Spec Improvements**

- **Enhanced Documentation**: Significantly improved docstrings and tool specifications across all Figma API modules
- **Parameter Clarification**: Updated descriptions for `file_key` and `node_id` in file management to specify allowed characters
- **Layout Mode Documentation**: Clarified descriptions for `layout_mode` and `layout_wrap` in layout operations with specific allowed values
- **JSON Serialization**: Added validation for the 'value' field in annotation properties to ensure JSON-serializability
- **Return Type Consistency**: Updated `download_figma_images` return type from `Tuple[Optional[str], Optional[str]]` to `Tuple[str, str]` for consistent output

##### **Model & Data Structure Enhancements**

- **RGBAColor Model Refactor**: Refactored `RGBAColor` and `CreateTextArgs` models to use `Annotated` for field validation
- **Enhanced Error Handling**: Improved error handling across all Figma operations with more specific error types
- **Data Validation**: Added comprehensive Pydantic validation models for better type safety and data integrity

##### **Code Quality Improvements**

- **Import Optimization**: Cleaned up redundant imports and improved import structure
- **Error Message Enhancement**: Improved error messages for better debugging and user experience
- **Code Organization**: Better organization of validation logic and error handling patterns
- **Type Safety**: Enhanced type hints and annotations across all Figma API modules


#### **Stripe**

##### **Enhanced Input Validation & Error Handling**

- **Comprehensive Input Validation**: Enhanced validation across all Stripe API operations with improved type checking and boundary validation
- **Error Handling Improvements**: Enhanced error handling in `create_product` function to raise `ApiError` for various exceptions including `KeyError` and `TypeError`
- **User-Friendly Error Messages**: Added new `error_utils.py` module with generic, reusable functions for converting technical validation errors to user-friendly messages
- **Pydantic Validation**: Implemented comprehensive Pydantic validation models for better type safety and data integrity across all Stripe operations
- **Refund Validation**: Enhanced `create_refund` function with input validation for `payment_intent` and `refund` parameters
- **Refund Reason Validation**: Added validation to ensure refund reason is one of: `duplicate`, `fraudulent`, or `requested_by_customer`

##### **Documentation & Tool Spec Improvements**

- **Enhanced Documentation**: Significantly improved docstrings and tool specifications across all Stripe API modules
- **Customer Documentation**: Updated `create_customer` docstring to clarify currently used metadata fields and removed outdated examples that don't exist in the DefaultDB
- **API Tool Spec Enhancement**: Enhanced API tool_spec documentation for coupon, price, and refund endpoints with clearer parameter descriptions
- **Parameter Clarification**: Improved documentation for various Stripe operations with better parameter descriptions and validation requirements

##### **Model & Data Structure Enhancements**

- **Enhanced Models**: Updated Stripe models with improved validation and error handling capabilities
- **Data Validation**: Added comprehensive validation for all Stripe data structures with better type safety
- **Error Definitions**: Enhanced custom error definitions for better error categorization and handling

#### **Tiktok:**
- Error dict returns replaced with exceptions and stricter type validation for all endpoints.
- API input and output types are now explicitly defined; responses include more detailed data fields.
- Video publishing now validates `post_info` with a Pydantic model and requires `thumbnail_offset` and `is_ai_generated` fields.


#### **Blender**
- Type annotations were refined across modules for more precise return types (e.g., using `Union`, `List`, specific value types instead of generic `Any`).
- Function signatures and docstrings updated to reflect new, stricter return types and clarify argument defaults.
- Redundant or unused typing imports removed for cleaner code.
- Dictionary value types in API endpoints (such as asset import, generation, and status functions) are now more restrictive and accurate.
- Variable type declarations were simplified or removed where unnecessary.
- Documentation was clarified to better describe default values, parameter types, and return structures.


#### **YouTube**
- Improved input validation and error handling for parameters in multiple modules (e.g., type checks, non-empty string checks, existence checks in DB).
- Expanded and standardized API documentation and OpenAPI tool specifications for endpoints (clearer descriptions, allowed values, and error cases).
- Enhanced sorting, filtering, and pagination logic for endpoints like search, comment threads, and video categories.
- Updated function signatures and return types for stricter type safety and clarity.
- Added or enforced explicit error raising for invalid input, returning clear messages for clients and developers.


### **Infrastructure and Quality Improvements**

#### **Coverage Configuration**

- **Enhanced Coverage Reporting**: Updated `.coveragerc` configuration for better test coverage reporting and analysis

#### **Database Updates**

- **Canva Integration**: Minor database improvements for better Canva API integration
- **Blender Database**: Updated `BlenderDefaultDB.json` with improved default configurations

#### **Code Quality**

- **Better Type Annotations**: Improved type hints across multiple APIs for better IDE support and code clarity
- **Enhanced Error Handling**: Improved custom error handling with more specific error types and better validation messages
- **Documentation Standards**: Standardized documentation format across all new and updated functions

### **Testing Infrastructure Enhancements**

#### **Comprehensive Test Suite Expansion**

- **Massive Test Coverage Addition**: Added over **17,000 lines** of new test cases across multiple APIs
- **Airline API**: Added 7 new test modules including model validation, file utils, imports, and database validation tests
- **BigQuery API**: Added 8 comprehensive test modules including execute query, utils, and CRUD operation tests
- **Blender API**: Added 6 extensive test modules including models, state management, and database validation tests
- **Call LLM API**: Added 8 test modules covering LLM response generation, docstrings, and utilities testing
- **Canva API**: Added 4 new test modules for database state, file utilities, imports, and models
- **Generic Reminders API**: Added 5 comprehensive test modules including extensive import testing

#### **Test Quality Improvements**

- **Model Validation Testing**: Extensive validation tests for data models ensuring data integrity and proper error handling
- **Import and Package Testing**: Comprehensive tests to verify module imports and package integrity across services
- **Database State Management**: Thorough testing of database operations, state management, and data consistency
- **Utility Function Testing**: Complete coverage of utility functions with edge case testing and error condition validation
- **Docstring Validation**: Added extensive docstring testing across APIs to ensure documentation quality


### **Bug Fixes**

* **Bug #533**: Phone API — Fixed docstring inconsistencies for phone number format validation  
* **Bug #580**: SAP Concur API — Fixed missing `saved_passengers` and `dob` fields in user details response
* **Bug #582**: Google Chat API — Fixed spaces search functionality and improved space management capabilities
* **Bug #579**: SAP Concur — Fixed `get_user_details` not returning critical fields (`family_name`, `email`).
* **Bug #580**: SAP Concur — Add new `get_user_details` missing critical fields (`saved_passengers`, `dob`).
* **Bug #585**: Stripe — Added method `list_invoices` to list the all invoices.
* **Google Slides API**: Fixed docstring issue in `batchUpdate` function for better parameter documentation
* **Jira API**: Fixed inconsistent args and tool_spec docstring in `find_groups` function

---

# [0.1.2]

## Release - 2025-09-11

### **API Changes & Improvements**

#### **Google Slides API**
- **Enhanced Documentation**: Fixed `create_presentation` function with proper structure definitions and improved docstring documentation
- **Conditional Requirements**: Improved conditional requirements documentation for better parameter clarity
- **Batch Update Fixes**: Fixed docstring issues in `batchUpdate` function for better parameter documentation

#### **Google Drive API**
- **Permission Documentation**: Enhanced `update_file_metadata_or_content` permissions docstring to specify required keys like create_file
- **Page Token Handling**: Fixed page token handling to make it optional in relevant operations

#### **Phone API**
- **Call Validation**: Enhanced phone call validation with improved contact consistency checks
- **Test Data Compliance**: Fixed test data to comply with validation and database requirements

#### **SAP Concur API**
- **Last Name Bug Fix**: Resolved last name handling issues in user operations

#### **Stripe API**
- **Documentation Enhancement**: Enhanced API tool_spec documentation for coupon, price, and refund endpoints
- **Tech Debt Resolution**: Addressed various technical debt issues in Stripe integration

#### **Retail API**
- **Order Status Fix**: Fixed order status check conflicts in `modify_pending_order_*` tools to prevent breaking after `modify_pending_order_items`

#### **Google Chat API**
- **API Improvements**: Enhanced Google Chat API functionality and error handling

#### **Calendar & Home Assistant**
- **Hotfix**: Applied critical fixes for calendar and home assistant integrations

### **Bug Fixes**

- **Bug #384**: Android Media Control — Fixed `change_playback_state` returning non-serializable enum
- **Bug #385**: Android Notifications — Fixed `get_notifications` returning enum objects instead of strings
- **Bug #394**: Various API fixes and improvements
- **Bug #395**: Additional API enhancements and bug fixes
- **Bug #533**: Phone API — Fixed docstring inconsistencies for phone number format validation
- **Bug #544**: Database and validation fixes
- **Bug #552**: Notes and Lists API improvements
- **Bug #553**: Google Chat API enhancements
- **Bug #555**: Additional service improvements
- **Bug #558**: Various API bug fixes
- **Bug #582**: Google Chat API — Fixed spaces search functionality and improved space management capabilities
- **Google Slides**: Fixed docstring issues in `batchUpdate` function for better parameter documentation
- **Phone Validation**: Enhanced phone call validation with improved contact consistency checks
- **SAP Concur**: Fixed last name handling bugs in user operations
- **Retail Orders**: Resolved order status check conflicts in pending order modification tools
- **Google Drive**: Fixed page token handling to make it optional in relevant operations
- **Blender API**: Fixed date time test case issues
- **Database Issues**: Addressed various database-related issues and validation problems

### **Testing Infrastructure**

- **Comprehensive Test Coverage**: Added extensive test cases for multiple APIs including:
  - File utilities testing
  - Import package validation
  - Model validation tests
  - Database file testing
  - Module integrity and error handling tests
- **Test Suite Enhancement**: Improved test coverage for BigQuery, Call LLM, and Generic Reminders APIs
- **Validation Improvements**: Enhanced validation tests for data models and error handling

### **Technical Improvements**

- **Code Quality**: Addressed review comments and resolved various code quality issues
- **Documentation**: Improved documentation across multiple APIs for better developer experience
- **Error Handling**: Enhanced error handling and validation across various services
- **Serialization**: Fixed enum values flag for proper serialization

## Release - 2025-09-08

### **API Changes & Improvements**

### **Bug Fixes**

* **Bug #384**: Android Media Control — Fixed `change_playback_state` returning non-serializable enum.
* **Bug #385**: Android Notifications — Fixed `get_notifications` returning enum objects instead of strings.
* **Bug #400**: Figma — Fixed `create_rectangle` to treat empty `parent_id` as `None`.
* **Bug #401**: Figma — Corrected validation so `stroke_weight: 0` is accepted.
* **Bug #403**: Zendesk — Fixed `create_user` validation: enforced non-zero IDs, non-empty strings, and valid phone number formats.
* **Bug #409**: Android Notes & Lists — Fixed `append_to_note` validation: `note_id` cannot be empty.
* **Bug #466**: Android Notes & Lists — Removed unsupported `share_notes_and_lists` function.
* **Bug #522**: Figma — Fixed inconsistent field naming: `currentPageID` → `currentPageId`.
* **Bug #529**: Android Notes & Lists — Updated `create_note` docstring to clarify optional vs. required params.
* **Bug #535**: Android Notes & Lists — Fixed schema mismatch in `add_to_list`: at least one list identifier is required.
* **Bug #536**: Android Notifications — Ensured `get_notifications` uses `build_notification_response` for proper JSON output.
* **Bug #539**: Android Media Control — Fixed serialization issues across playback functions (`next`, `pause`, `resume`, `replay`).
* **Bug #554**: Figma — Fixed case-sensitivity mismatch in parent lookup (`currentPageId` vs. `currentPageID`).
* **Bug #508**: Updated Gmail Label update logic to synchronize isRead boolean with UNREAD label value.
* **Bug #581**: Fixed Gmail insert message to create the Thread objects in DB for new thread IDs
* **Bug #380**: Android Clock — Clarified docstring for `create_clock` to better explain valid duration formats and ranges.
* **Bug #381**: Android Clock — Updated `modify_alarm` docstring to clearly state that time must include hours, minutes, and seconds.
* **Bug #382**: Android Message — Cleaned up `prepare_chat_message` docstring to avoid confusion about required fields.
* **Bug #410**: Android Message — Improved `send_chat_message` validation so optional fields no longer cause errors when left empty.
* **Bug #442**: Jira — Re-enabled support for the `components` field in `create_issue`, which had been removed in an earlier update.
* **Bug #537**: Slack — Updated multiple functions to support both channel IDs and channel names, as per API guidelines.
* **Bug #439**: Device Settings: Added support to get device setting brightness
* **Bug #545**: Google Maps Live: Fixed docstring and toolspec for search_along_route parameter in query_places function
* **Bug #549**: Google Chat: Updated docstring and tool spec for google_chat.create_space function
* **Bug #553**: Google Chat: Updated docstring and toolspec for membership.type in add_space_member function

## Release - 2025-09-05

### **API Changes & Improvements**

#### **LinkedIn API Update**

- **Core API Enhancements**:

  - **Posts API**: The `create_post` and `update_post` functions now support a detailed User Generated Content post schema, enabling content with media, polls, carousels, and specific distribution settings.

  - **Organizations API**: Added pagination and field projection capabilities to `get_organizations_by_vanity_name` and introduced new functions for managing Access Control Lists (ACLs).

  - **Profile Management**: Improved the localized name structure for core profile functions (`get_me`, `create_me`, `update_me`).

- **Improved Data Integrity & Error Handling**:

  - Standardized documentation and Implemented robust input validation across all modules using comprehensive Pydantic models to ensure data integrity.

  - Introduced over 10 specialized error classes, such as `InvalidOrganizationIdError` and `UserNotFoundError`, for more precise error categorization and handling.

#### **Phone Number Validation Relaxation**

- **Phone Number Validation**: Relaxed phone number validation by removing phonenumbers library and implementing a custom solution
  - Check length between 7 & 15 characters
  - Only extra characters allowed: +, -, (, )
  - Normalization removes only -, (, ) and spaces
- **Affected Services**: Phone, WhatsApp, BigQuery, Contacts, Zendesk

### **Bug Fixes**

- **Bug #454**: Jira: Added project validation in create_issue to prevent issues being created with invalid project names
- **Bug #456, #458, #459**: Jira: Fixed create_issue so that comments are no longer discarded
- **Bug #479, #485**: Jira: Corrected create_issue() to properly accept the due_date field as per documentation
- **Bug #493, #497**: Jira: Fixed create_issue bug where due_date provided as a string was ignored or set to None
- **Bug #476**: Salesforce: Updated execute_soql_query to properly handle queries using the OR keyword
- **Bug #509**: Salesforce: Fixed field name mismatches (Subject→Name, StartDateTime→StartTime, ActivityDate→DueDate) and improved operator support (LIKE, !=, OR) in execute_soql_query
- **Bug #477**: YouTube: Resolved upload_video() error where valid category IDs were incorrectly flagged as "Category not found."
- **Bug #491**: Gemini CLI: Fixed run_shell_command execution path so command logging and responses are accurate. Clarified handling of empty stdout/stderr and ensured return codes are the primary success/failure indicator
- **Bug #447, #451**: Confluence: Fixed create_content so that it now validates the spaceKey. Previously, pages could be created even if the specified space did not exist
- **Bug #470**: Confluence: Implemented search_content to perform actual database lookups and return results. Previously, it was a stub that always returned an empty list
- **Bug #374**: Reminders (Android): Fixed validation — occurrence_count must now be greater than 0
- **Bug #375**: Workday Strategic Sourcing: Corrected schema so list_projects() only requires relevant filter parameters
- **Bug #457**: Generic Media: made referral key playlist in track optional string
- **Bug #466**: Notes and Lists: Removed the unsupported tool `share_notes_and_lists` from the notes_and_lists service to avoid confusion
- **Bug #471**: Google Calendar: Enforced timezone awareness for timeMin and timeMax parameters in event queries.
- **Bug #492**: Contacts: Fixed is_whatsapp_user flag incorrectly set to True when no phone number provided.
- **Bug #440**: WhatsApp: Fixed plus sign (+) handling in phone number parsing for chats and messages.
- **Bug #462**: Google Calendar: Fixed issue related to secondary calendar deletion operations.
- **Bug #393**: Google Sheets: Enhanced batch_update_spreadsheet to properly handle empty request arrays.
- **Bug #386**: WhatsApp: Improved search_contacts_data functionality and reliability.
- **Bug #397**: Google Calendar: Clarified timeZone format requirements in get_event docstring.
- **Bug #405**: Google Calendar: Enhanced create_calendar functionality and error handling.
- **Bug #396**: Google Calendar: Allowed empty recurrence list in patch_event operations.
- **Bug #389**: Phone: Enhanced make_call function to handle incomplete recipient information.
- **Bug Fix**: Google Docs: Added deleteContentRange and replaceAllText support for content operations.


## Release - 2025-09-04

### **API Changes & Improvements**

#### **Google Calendar API - Critical DateTime/Timezone Fixes**

- **Enhanced Datetime & Timezone Support**
  - Multi-format datetime support - Now accepts UTC (Z suffix), timezone offsets (+02:00, -07:00), and naive format with separate timezone field
  - Timezone offset handling - Fixed critical issue where API ignored timezone offsets like +02:00, -07:00 and only supported UTC format
  - Timezone-aware datetime objects - Resolved issue where API returned naive datetime objects by implementing timezone preservation through local_to_UTC() and UTC_to_local() conversion functions
  - RFC3339 compliance improvements - Enhanced datetime validation to support RFC3339 standard formats instead of basic ISO 8601, aligning with Google Calendar API requirements
  - Centralized datetime validation - Implemented unified validation through common_utils.datetime_utils with support for three datetime formats:
    - ISO_8601_UTC_Z: YYYY-MM-DDTHH:MM:SSZ
    - ISO_8601_UTC_OFFSET: YYYY-MM-DDTHH:MM:SS+/-HH:MM
    - ISO_8601_WITH_TIMEZONE: YYYY-MM-DDTHH:MM:SS with separate timezone field

- **Technical Implementation**
  - Enhanced parameter validation - All datetime parameters now support multiple Google Calendar API-compliant formats
  - Timezone information preservation - Event storage converts to UTC internally while preserving original timezone context for API responses

#### **Stripe API Updates**

- **`create_price`**: Made the **`unit_amount`** parameter required to enforce stricter validation.
- **`create_coupon`**: Made the **`name`** field optional and significantly enhanced the validation logic for discount amounts and currency.

#### **Cursor grep_search Enhancement**

- Migrated globbing from Python fnmatch to wcmatch for enhanced pattern matching
- Added support for brace sets/alternation (e.g., '{p1,p2}', '*.{js,jsx,ts,tsx}')
- Implemented extglobs (@, !, +), POSIX classes, and recursive globstar '**'
- Behavior now aligns with ripgrep-style braces with comprehensive test coverage

#### **Zendesk API Updates**

- **`create_ticket`**: Improved type safety and readability by replacing generic types with more specific definitions.

### **Custom Query Language Improvements**

#### **Jira**

- Enhanced group and issue search with full UUID support
- Added new filters for groups and issues to make search more flexible

#### **Slack**

- Expanded search with advanced filters such as sender, file type, filename, pinned/saved status, and date-based queries
- Improved validation and error handling for more reliable results

#### **Gmail**

- Smarter email search with filters for attachments, categories, message sizes, and dates
- Support for complex queries using logical operators (AND/OR)
- Improved error handling and overall query reliability

#### **Google Calendar**

- Event search improved with filters for location and attendee details
- Optimized event listing for smoother performance

#### **Google Drive**

- Improved file search with enhanced query handling
- Better support for substring matching across file attributes

#### **Google Chat**

- Added advanced query parsing with logical operators and parenthesis support
- Improved filtering with required fields, pagination, and ordering

### **Framework & Infrastructure Improvements**

#### **Push DB Porting System**

- **Database Migration Framework**: Implemented comprehensive Push DB Porting system for migrating vendor databases to canonical schema formats
- **Multi-Service Support**: Added porting scripts for 6+ services including Calendar, Gmail, WhatsApp, Contacts, Device Settings, and Clock
- **Schema Validation**: Integrated Pydantic-based validation with `validate_with_default_schema()` function for robust data integrity
- **Cross-Platform Compatibility**: Enhanced porting system to handle vendor-specific data formats and normalize them to standardized API schemas
- **Automated Testing**: Added comprehensive test suite with `test_porting.py` to validate porting accuracy and detect schema mismatches
- **CLI Integration**: Added command-line interface support for executing functions and automated database porting
- **Error Handling**: Enhanced error reporting and validation with detailed feedback for porting failures

#### **FC Spec Quality Improvements**

- **FC Spec Improvements**: Fixed indentation by removing default indentation in the code while keeping the indentation within the description
- **FC Spec Improvements**: Updated file generation to ensure description comes before type key
- **Docstring and Tool Spec Fixes**: Corrected docstring and tool spec issues across multiple services to ensure more accurate and reliable FC schemas.

### **Bug Fixes**

- **Bug Fix**: SAPConcur: Updated the docstring in create_or_update_trip tool to Pydantic model validation.
- **Bug #438**: Notes and Lists: Added "completed" flag in list items. Added relevant utils function to mark list item as completed and tool to filter items based on complete status.
- **Bug Fixes**: Jira: Fixed 5 bugs in jira.create_issue (IDs: 449, 454, 456, 458, 459)
- **Bug Fix**: Clock: Addressed clock DB import issue.

# [0.1.1]

## Patch - 2025-09-04

### **Framework & FC Spec Improvements**

- **FC Spec Improvements**: Enhanced the FCSpec generator to correctly handle descriptions by striping space before and after quotes and preserving internal formatting including newlines and spaces.

# [0.1.1]

## Release - 2025-09-03

### **Framework & FC Spec Improvements**

- **New FC Schema Generation Framework**: Generated FCSpec are now translated into dictionaries and added directly above function definitions as tool_spec decorator spec parameters. Schemas are now directly generated through the jsonification of the spec dictionary.
- **Deployment Changes**: Schemas are now part of Zipped APIs
- **Docstring Fixes**: Corrected docstring issues across multiple services to ensure more accurate and reliable FC schema generation.

### **API Changes & Flexibility**

This release enhances API flexibility by making several previously required parameters optional across multiple services.

- **Google Calendar API**: The eventId in the event retrieval function is now optional, making it easier to use in some cases.
- **Google Slides API**: Several fields related to creating presentations have been made optional, reducing the amount of information required to create a presentation.
- **Jira API**: The delete_subtasks option (used when deleting issues) is now optional, giving users more flexibility.
- **Slack API**: The force option when inviting users is now optional. The limit field in the member listing function is optional. Both include_locale and limit in the user listing function are now optional as well.

### **Enhancements & Improvements**

- **Confluence API**: Added a check to ensure the spaceKey value is not empty or just whitespace when retrieving a space.
- **Google Drive API**: Introduced a new option (useDomainAdminAccess) for listing files. Improved validation for setting expiration times in permissions. Optimized internal code for handling lists.
- **Google Calendar API**: Added better checks to ensure valid input when deleting or updating events.
- **Google Sheets API**: Updated documentation to improve clarity on how batch data is retrieved.
- **Jira API**: Now checks for empty or invalid input when retrieving components or project-related information.
- **Salesforce API**: Expanded the task and event creation features to support more Salesforce-standard fields. Updated data models for better alignment. Replaced the use of Name with Subject where appropriate to match typical Salesforce usage.

### **Bug Fixes**

- **Bug #427**: SAPConcur: Converted `start_date` and `end_date` from `datetime` objects to strings.
- **Bug #438**: Notes and Lists: Added "completed" flag in list items. Added relevant utils function to mark as list item as completed and tool to filter items based on complete status.
- **Bug**: SAPConcur: Added a custom `SeatsUnavailableError` exception to handle booking failures when flight seats are not available.

## Release - 2025-08-29

### **Framework & FC Spec Improvements**

- **Property Parsing**: Enhanced the property parser to correctly handle backticks (`) and to better preserve indentation and newlines in nested properties for improved formatting.
- **Docstring Fixes**: Corrected docstring issues across multiple services to ensure more accurate and reliable FC schema generation.

### **Enhancements & Improvements**

- **Utility Functions**: Improved utility functions and documentation for **MongoDB** and **Zendesk** to enhance the developer experience.

### **API Changes & Flexibility**

This release makes our APIs more flexible by converting many previously required parameters to optional.

- **Slack API (Breaking Change)**: The `blocks` parameter for `Chat.postMessage` must now be passed as a **JSON string** instead of a list of dictionaries.
- **Jira API**: Creating an issue (`create_issue`) now only requires a `project` and `summary`.
- **Canva API**: `create_design` parameters (`design_type`, `asset_id`, `title`) are now optional.
- **Gmail API**: Numerous parameters and keys are now optional across `Drafts.create`, `Labels.create/update/patch`, and `Messages.insert`.
- **Google Sheets API**: Key parameters are now optional for `Spreadsheets.create` and `Spreadsheets.Values.get`.
- **Notes and Lists API**: `update_list_item` parameters are now optional.
- **Salesforce API**: Added `Description`, `Location`, and `OwnerId` as new optional fields to `QueryCriteriaModel`.
- **Zendesk API**: The `email` parameter for `Users.create_user` is now optional.

### **Bug Fixes**

- **Bug #429**: Fixed an issue by converting `datetime` objects to `str` for `start_date` and `end_date` fields to ensure all API responses are properly JSON serializable.
- **gmail_sender_default**: Added default sender population based on the authenticated user if the sender field is not provided.

### **New Services**

- **Claude Code API**: Introduced a new, comprehensive AI-powered code assistance API simulation.
  - **Added**: Complete file system operations (read, edit, list, search, grep) with workspace validation.
  - **Added**: Secure shell command execution with environment management and `.env` file support.
  - **Added**: Web request handling and robust task management modules.
  - **Added**: This new service includes over 8,400 lines of production code and 5,700 lines of test code, achieving over 96% test coverage.

### **Housekeeping**

- **Build Artifacts**: Deleted `analysis_output/docstring.txt` and `analysis_output/fcspec.json`.

## Release - 2025-08-28

### **Framework & FC Spec Improvements**

- **Schema Generation**: Fixed schema consistency by ensuring all schemas include explicit `required` field information, preserving parameter order and clarifying mandatory vs. optional parameters.
- **Property Parsing**: Resolved property name validation issues with proper identifier checking and fixed bugs related to parsing complex nested property types.
- **Description Integrity**: Reverted aggressive description cleaning to better preserve original docstring formatting and improve documentation integrity.
- **Docstring Fixes**: Corrected docstring issues across multiple services to ensure accurate FC schema generation.

### **Documentation & Code Quality**

- **Utility Function Enhancements**: Improved utility functions and documentation across multiple services (including Stripe, SAPConcur, Airline, and BigQuery) for a better developer experience.
  - **Changed**: Enhanced docstrings and parameter descriptions for all utility functions.
  - **Added**: Implemented utility mapping in service `__init__.py` files for dynamic function resolution.
  - **Changed**: Standardized the documentation format for all utility functions to improve consistency.

### **Bug Fixes & Improvements**

- **Device Action**: Improved search accuracy by replacing the simple search strategy with a more robust hybrid approach.
- **Gmail**: Fixed a data inconsistency issue in the history feature by unifying default values.
- **Cursor**: Aligned the optionality of parameters for the `read_file` and `run_terminal_command` functions with their real-world implementations.

## Release - 2025-08-26

### **Documentation & Code Quality**

- **Docstring Overhaul**:
  - **Changed**: Enhanced the quality of docstring field headers with clearer explanations for complex object and array parameters.
  - **Changed**: Rewrote parameter descriptions using more natural, purpose-driven language.
  - **Fixed**: Applied systematic fixes to resolve description sanity check issues, ensuring docstrings meet quality standards.
  - **Changed**: Standardized the format and style of docstrings across all modules for improved consistency.

### **Dependencies**

- **Added**: Added the `tabulate==0.9.0` library to `requirements.txt`.

### **Bug Fixes & Improvements**

- **Bug #413**: Retail - Corrected the `get_order` tool to ensure it returns complete order information as expected  
- **Bug #415**: Google Calender - Fixed a critical bug in the `create_event` method that allowed creating events in non-existent calendars, which was breaking Colab integrations
- **Bug #416**: Device Actions - Resolved an issue to allow any app type, unblocking key usage scenarios
- **Bug**: Terminal - Fixed an unreported bug in terminal utilities to properly read markdown files

## Release - 2025-08-25

### **New Features**

- **Gemini CLI**: Added support for relative paths to all file system functions. This enhances compatibility with the Cursor API by accepting relative paths while maintaining existing security measures.

### **Framework and Infrastructure**

- **FCSpec Enhancements**: Overhauled the property definition parser in `FCSpec.py`, replacing fragile regex-based logic with a more robust programmatic approach. This improves parsing flexibility and reliability.
- **Runtime Mutations**: Removed all statically generated mutation code files from the codebase. The framework now generates these files at runtime, streamlining the repository and improving the development workflow.

### **Data Standardization**

- **Email Validation**: Implemented strict email normalization across multiple services by using the `EmailStr` type for sender, recipient, and attendee fields. This ensures consistent and valid email formats.
  - **Affected Services**: Gmail, Google Calendar, HubSpot, and Jira.
- **Datetime Normalization**: Standardized datetime handling to UTC across multiple APIs, ensuring consistency and adherence to the ISO 8601 standard.

### **Documentation & Code Quality**

- **Docstring Improvements**:
  - **Changed**: Significantly enhanced the quality of docstring field headers, providing clearer explanations for complex object and array parameters.
  - **Changed**: Rewrote parameter descriptions to use more natural, purpose-driven language instead of generic technical terms.
  - **Fixed**: Applied systematic fixes to resolve description sanity checks, ensuring all docstrings are meaningful and meet quality standards.
  - **Changed**: Standardized the format and style of docstrings across all modules for improved consistency.

## Release - 2025-08-22

### **Framework and Infrastructure**

- **Phone Number Validation Utility**: Introduced a new, centralized utility for validating and normalizing phone numbers to the E.164 standard across the platform.
- **Enhanced Schema Generation**: The FCSpec generator now cleans descriptions for better readability, and the schema validator adds checks for improved compatibility.
- **State Minification for Binary Files**: Enhanced state minification across terminal-based services (Copilot, Cursor, Gemini CLI, Terminal) to correctly handle and reduce the content of binary files in state snapshots.

### **GitHub API Major Technical Debt Refactor**

- **Comprehensive Pydantic Validation**: Overhauled the entire GitHub API by implementing strict, Pydantic-based input validation for repositories, pull requests, and issues. This improves reliability and provides clearer error messages.
- **Improved Timestamp Management**: Centralized and standardized timestamp handling within the API simulation for better consistency.
- **Expanded Test Coverage**: Significantly increased the number of unit and integration tests to cover new validation logic and edge cases, ensuring greater robustness.

### **Canva API Major Refactor and Enhancement**

- **Modular Redesign**: The Canva API has been completely refactored into distinct, feature-focused modules: `DesignCreation`, `DesignListing`, `DesignRetrieval`, `DesignExport`, `DesignImport`, and `Comment`.
- **New Functionality**: Introduced a wide range of new features, including comprehensive design import/export capabilities and a full commenting system (threads and replies).
- **Robust Validation and Testing**: Added extensive input validation and a new, comprehensive test suite covering the entire API surface.

### **Slack API Enhancement**

- **File Search Overhaul**: Completely refactored the `search_files` logic to correctly find files shared across multiple channels, handle files that exist globally but are not referenced in any channel, and improve overall search reliability.

### **Google Services API Enhancements**

- **Google Slides**: Significantly improved flexibility in the `batch_update_presentation` function by making numerous request parameters optional, allowing for more targeted and simpler updates.
- **Google Calendar**: Enhanced several event functions (`delete_event`, `get_event`, `create_event`, `patch_event`, `update_event`) by making parameters optional for a better developer experience. The parameter order for `patch_event`, `update_event`, and `quick_add_event` was corrected for consistency.
- **Google People, Chat & Meet**: Improved API docstrings across these services, clarifying many parameters as optional to better reflect their actual usage.

### **Phone Number Normalization Rollout**

- **Standardized Phone Numbers**: Integrated the new phone number utility across multiple services to ensure all phone numbers are consistently validated and stored in E.164 format.
- **Affected Services**:
  - **BigQuery**: Normalized phone numbers during data insertion and in query results.
  - **Contacts & Google People**: Ensured phone numbers are stored in E.164 format upon creation and update.
  - **Messages, Phone, WhatsApp**: All communication tools now validate and normalize recipient phone numbers. The logic for resolving recipients in WhatsApp has also been improved.
  - **Zendesk**: User phone numbers are now standardized.
  - **Shopify**: Customer, shipping, and billing address phone numbers are validated and normalized.

### **Code Execution**

- **Simplified `write_to_file`**: Refactored the `write_to_file` function to exclusively handle string content, removing previous binary write capabilities to streamline its functionality.

### **Utility Scripts**

- **Assertion Utils**: New assertion_utils script code.

## Release - 2025-08-20

### **Github Issues Fixes**

- **Search update and list**: fixed bugs in Search, update and list issues endpoints
- **Search Repository**: Fixed issues with search repository

### **Gmail Issues Fixes**

- **Label ID Validation**: Added validation for label id in update_labels function

### **Doc String Calibration for FCSpec translation**

- Major activity across 100+ tools on various services to fix the miss match between Doc string and FCSpec Schema
- Enhanced FCSpec Schema translation Module to support advance features e.g. Parsing union types
- Added test cases for Doc String Validation for all the tools

## Release - 2025-08-19

### **Google Slides Tech Debt**

- **Doc String and Input Validation**: Major enhancements to `create_presentation`, `batch_update_presentation`, `get_presentation`, `get_page`, and `summarize_presentation` in Tech Debt

### **Framework and Infrastructure**

- **Terminal Unification**: Unified terminal functionality across Gemini CLI, Terminal, and Cursor for a consistent experience.
- **Timestamp Correction**: Fixed timestamp mismatch issues for terminal commands across Gemini CLI, Terminal, and Cursor.
- **Database State Minification**: Added `get_minified_state` functionality to multiple services for optimized database state retrieval.
- **File System Utilities**: Enhanced file system utilities with output redirection and metadata preservation.
- **Test Stability**: Improved database state management in integration tests to ensure test stability.

### **New Requirement**

- added new requirement for `jsonpath-ng`

# [0.1.0]

## Release - 2025-08-15

### **Google Calendar API Major Enhancement**

- **sendUpdates Integration with Gmail**: Implemented comprehensive sendUpdates feature integration with Gmail for enhanced calendar event notifications
- **Enhanced Event Management**: Added robust sendUpdates functionality with comprehensive validation and error handling
- **Test Coverage Expansion**: Added extensive test coverage with 1,400+ lines of tests including integration tests between Calendar and Gmail APIs
- **Database Enhancement**: Enhanced Calendar database with improved data structures for better event management
- **Utility Functions**: Added new utility functions for better sendUpdates handling and API operations

### **Google Cloud Storage Major Technical Debt Refactor**

- **Comprehensive API Improvements**: Complete overhaul of Google Cloud Storage API with enhanced validation and error handling
- **Enhanced Bucket Operations**: Improved `Buckets.list`, `Buckets.insert`, `Buckets.relocate`, and `Buckets.restore` functions with comprehensive validation
- **IAM Policy Management**: Fixed and enhanced `getIamPolicy` and `setIamPolicy` functions with proper validation and error handling
- **Storage Layout & Retention**: Enhanced `getStorageLayout` and `lockRetentionPolicy` functions with robust validation and improved functionality
- **Test Coverage Expansion**: Added extensive test coverage with 4,000+ lines of tests covering all major functions and edge cases
- **Error Handling**: Implemented comprehensive custom error definitions and improved error handling across all operations

### **Jira API Major Technical Debt Refactor**

- **Comprehensive API Improvements**: Complete overhaul of Jira API with enhanced validation, error handling, and type safety
- **Enhanced Functionality**: Improved 20+ Jira API modules including ApplicationProperties, ApplicationRole, Component, Dashboard, Filter, Group, Issue, and more
- **Type Hint Standardization**: Updated all return types to use proper type hints (`Dict[str, Any]`, `List[Dict[str, Any]]`) for better API documentation
- **Input Validation**: Added comprehensive input validation across all functions with proper error handling for invalid parameters
- **Test Coverage Expansion**: Added extensive test coverage with 3,400+ lines of tests covering all major functions and validation scenarios
- **Error Handling**: Enhanced custom error definitions and improved error handling across all Jira operations

### **Messages API Enhancement**

- **Recipient Name Matching**: Enhanced `_list_messages` function to support recipient name matching from nested contact structures
- **Contact Integration**: Improved contact integration with better recipient matching capabilities
- **Test Coverage**: Added comprehensive test coverage for contact integration and edge cases

### **Google Search API Bug Fix**

- **Critical Bug Fix**: Fixed Google Search API functionality to resolve critical issues affecting search operations
- **Test Coverage**: Added comprehensive test coverage for search functionality

### **Jira Search Engine Fix**

- **AttributeError Resolution**: Fixed AttributeError in Jira Search Engine initialization for improved stability
- **Error Handling**: Enhanced error handling in Jira search functionality

### **Shopify API Enhancement**

- **Order Management**: Added `target_payment_method_id` parameter to `shopify_modify_pending_order_items` function for enhanced order customization
- **Payment Flexibility**: Improved payment method handling for pending order modifications

### **Slack API Enhancement**

- **Conversation Management**: Enhanced Slack open conversation functionality with improved user management
- **Current User Handling**: Added `get_current_user` and `set_current_user` functions for better conversation context management
- **Error Handling**: Implemented proper error handling with `CurrentUserNotSetError` for improved reliability
- **Test Coverage**: Added comprehensive test coverage for edge cases and user management scenarios

### **TikTok API Enhancement**

- **Business API Improvements**: Enhanced TikTok Business.Get API with comprehensive validation and improved testing
- **Publish Status Enhancement**: Improved TikTok publish status API with comprehensive validation and consistent database structure

### **Airline API Enhancement**

- **Passenger Management**: Removed optional passenger name fields from booking and simulation models for cleaner data structures
- **Data Validation**: Enhanced validation logic with better error handling and input checks
- **Database Schema**: Updated database schema for improved data consistency

### **Framework and Infrastructure**

- **Test Suite Improvements**: Enhanced test suite with better error handling and validation across multiple services
- **Code Quality**: Improved code quality with better error handling, validation, and comprehensive test coverage
- **Documentation**: Enhanced API documentation with improved docstrings and examples

## Release - 2025-08-13

### **Gmail API Enhancements**

- **Attachment Handling Improvements**: Enhanced Gmail message insertion with improved MIME parsing and base64 decode error handling
- **Test Coverage Enhancement**: Added comprehensive test coverage for attachment handling scenarios, including MIME parsing exceptions and base64 decode failures
- **Error Handling**: Improved error handling for attachment processing with targeted tests for exception handling blocks

### **Google Search API**

- **Recent Search Functionality**: Implemented comprehensive recent search system with search history tracking and retrieval capabilities
- **Search History Management**: Added `get_recent_searches` and `add_recent_search` functions for managing search history across different endpoints
- **Database Integration**: Enhanced Google Search database with recent searches structure and improved data persistence
- **Search Integration**: Integrated recent search tracking into the main search function for automatic history management

### **Notifications Service**

- **Read Status Management**: Added utility function to list notifications without updating read status for better notification management
- **Enhanced Functionality**: Improved notification handling with better control over read status updates

### **Google Drive API**

- **File Export Enhancement**: Fixed `Files.export()` functionality to work with files that have no content, improving export reliability
- **Content Management**: Enhanced file content handling and export capabilities for better file processing

### **Google Calendar API**

- **Event Name Validation**: Updated event creation to allow colons (":") in event names for better event naming flexibility
- **Primary Calendar Logic**: Enhanced `delete_event()` function to properly use "primary" calendar instead of string literal for better calendar operations

### **Google Docs API**

- **Size Field Alignment**: Fixed document size field to be consistently returned as a string when documents are created via Google Docs API
- **Data Consistency**: Improved data consistency between Google Docs and Google Drive services

### **Terminal Service**

- **Timestamp Optimization**: Enhanced terminal service to avoid unnecessary timestamp updates during command execution
- **Performance Improvement**: Improved terminal performance by reducing redundant timestamp operations

### **Dependencies and Infrastructure**

- **Requirements Update**: Updated project dependencies to include new packages: uvicorn (0.35.0), starlette (0.47.2), psutil (7.0.0)
- **MCP Framework**: Updated MCP (Model Context Protocol) to version 1.12.4 for improved protocol support
- **Web Framework Support**: Added web framework dependencies for enhanced server capabilities

### **Search Engine Consolidation**

- **Centralized Search Engine**: Consolidated search engine functionality from individual services into common_utils for better maintainability
- **Service Adapter Migration**: Migrated search engine service adapters to centralized location for improved code organization
- **Search Strategy Optimization**: Enhanced search strategies across multiple services with centralized configuration

### **Framework Features**

- **Authentication Framework**: Implemented comprehensive authentication framework with service-specific configurations and error handling
- **Error Management System**: Enhanced error handling with centralized error management and service-based error formatting
- **Mutation System**: Improved mutation system with better configuration management and static mutation support
- **Documentation Framework**: Enhanced documentation generation with improved FCSpec handling and framework feature support

### **Confluence API Major Enhancements**

- **Content Management Improvements**: Enhanced ContentAPI with improved content descendant handling and property management
- **Space API Enhancements**: Improved SpaceAPI functionality with better space management capabilities
- **Type Hint Corrections**: Fixed docstring type annotations from `any` to `Any` for better code quality and IDE support
- **Test Coverage Expansion**: Added extensive test coverage with 7,500+ lines of tests for comprehensive API validation
- **Error Handling**: Enhanced custom error definitions and improved error handling across all Confluence operations
- **Utility Functions**: Added new utility functions for better content property management and API operations

### **Cursor Edit File functionality**

- Reverted Cursor Edit with LLM functionality

### BigQuery Service Major Technical Debt Refactor

- **API Structure & Response Format Improvements**
  - **Complete API response standardization** to match BigQuery REST API format
  - **Enhanced `list_tables` function** with proper pagination support and BigQuery API response structure
  - **Improved `describe_table` function** with standardized table reference format and metadata
  - **Better parameter validation** with comprehensive input checking across all functions
  - **1,781 lines of code improvements** with enhanced error handling and type safety
  
- **Function Signature & Parameter Enhancements**
  - **Updated `list_tables` signature** to accept `project_id`, `dataset_id`, `max_results`, and `page_token` parameters
  - **Enhanced `describe_table` function** with separate project, dataset, and table ID parameters
  - **Improved input validation** with proper type checking and error messages
  - **Better parameter documentation** with comprehensive docstrings and examples

- **Response Structure Standardization**
  - **BigQuery API-compliant response format** with `kind`, `etag`, `nextPageToken`, and `totalItems` fields
  - **Standardized table reference structure** with proper `tableReference` object format
  - **Enhanced metadata handling** with proper timestamp conversion and formatting
  - **Improved schema representation** with consistent field structure and data types

### MongoDB Service Major Technical Debt Refactor

- **Key Fixes**
  - **Critical Bug**: Fixed `InvalidQueryEprror` → `InvalidQueryError` typo causing import failures
  - **Error Handling**: Added comprehensive exception handling with proper MongoDB error mapping
  - **Enhanced import structure**: Improved import structure and reduced technical debt by consolidating imports for `data_operations.py`

- **Core Improvements**
  - **MongoDB**: Enhanced `create_collection`, `drop_collection`, `collection_storage_size`, `rename_collection`, `list_collections`
  - **Validation**: Added MongoDB naming convention validation and database existence checks

- **Impact**
  - Fixed critical import failures
  - 15+ new exception handling scenarios  
  - Enhanced developer experience with better error messages

### **Bug Fixes & Improvements**

- **Bug #306**: Fixed Google Search recent search functionality implementation
- **Bug #327**: Fixed Google Calendar primary calendar usage in delete_event() function  
- **Bug #330**: Fixed Google Calendar event name validation to allow colons in event names
- **Bug #335**: Fixed various service-specific issues and improved error handling
- **Bug #344**: Fixed Google Drive export functionality for files with no content
- **Bug #345**: Fixed Google Docs size field alignment for consistent data representation
- **Bug #355**: Fixed various framework and service issues
- **Bug #316**: Fixed multiple service-specific bugs and improved stability
- **PR #3397**: Major Confluence API tech debt improvements with comprehensive enhancements
- **Bug #350**: Corrected the list_scim_users filter to properly query for active users.
- **Bug #351**: Updated API documentation: the roles field in list_scim_users now correctly shows a list of strings.
- **Bug #354**: Fixed a TypeError on event creation by casting the integer event ID to a string.
- **PR #3373**: SAPConcur - The `update_reservation_flights` tool now accepts an optional `price` for each flight. This allows users to either specify a price directly or let the system calculate it, providing greater flexibility
- **PR #3281**: Aligned the flight search logic in SAPconcur with Airline API. Corrected a critical flaw in the one-stop flight search logic. The system now aggregates flight segments from all available bookings before searching for connections, ensuring that valid connecting flights are no longer missed if their legs originate from different bookings

## Release - 2025-08-07

### **Notes and Lists**

- **Remove Fetch Actions-Related Implementations:** Eliminate all code and configuration related to the "actions/fetch-actions" feature. This includes Action models, Default database entries for actions, log_actions, fetch_actions, test cases

### **Notifications service**

- **Remove Fetch Actions-Related Implementations:** Eliminate all code and configuration related to the "actions/fetch-actions" feature. This includes Action models, Default database entries for actions, log_actions, fetch_actions, test cases

### **Google Maps Live API**

- **Recent Search Functionality**: Implemented comprehensive recent search system with search history tracking and retrieval capabilities
- **Search History Management**: Added `get_recent_searches` and `add_recent_search` functions for managing search history across directions and places endpoints
- **Database Integration**: Enhanced Google Maps Live database with recent searches structure and improved data persistence
- **Directions Integration**: Integrated recent search tracking into directions API for automatic history management
- **Places Integration**: Enhanced places API with recent search functionality for location-based search history

### **Gmail API**

- **Draft Send Enhancement**: Enhanced draft sending validation with comprehensive checks for required fields (recipient, subject, body)
- **Error Handling**: Improved error handling to raise ValueError for missing fields when sending drafts and new messages
- **Validation Improvements**: Enhanced validation for draft operations with better field checking and error reporting

### **Google Calendar API**

- **Primary Calendar Logic**: Updated `create_event()` to find the user's primary calendar instead of creating in the string "primary"
- **Event Creation Enhancement**: Improved event creation logic with better primary calendar detection and validation

### **Google Home API**

- **Validation Enhancement**: Updated validation and API signatures to properly handle command value requirements
- **Trait API Improvements**: Enhanced mutate traits API with improved validation and error handling

### **Google Drive API**

- **Hydrate DB JSON Fix**: Resolved JSON serialization issues in hydrate_db functionality for improved data persistence
- **Database Operations**: Enhanced database operations with better JSON handling and error recovery

### **Device Settings API**

- **Database Enhancement**: Improved database initialization and management for better device settings persistence

### **YouTube Tool API**

- **Recent Search Mechanism**: Implemented comprehensive recent search functionality with search history tracking and retrieval capabilities
- **Search History Management**: Added `get_recent_searches` and `add_recent_search` functions for managing search history across different endpoints
- **Database Integration**: Enhanced YouTube Tool database with recent searches structure and improved data persistence
- **Search Integration**: Integrated recent search tracking into the main search function for automatic history management
- **Error Handling Improvements**: Added try-catch blocks and enhanced error handling for better service reliability
- **Return Type Standardization**: Generalized return structure for consistency across services with improved type handling

### **SAPConcur API**

- **Flight Search Optimization**: Refactored flight search logic to aggregate all unique air segments from bookings for more comprehensive search results
- **Connection Timing Enhancement**: Improved connection timing validation to allow flights with equal arrival and departure times for better connection matching
- **Code Refactoring**: Streamlined flight search functions by removing redundant booking context parameters and simplifying segment enrichment logic
- **Performance Improvements**: Enhanced search performance by eliminating duplicate flight number processing and optimizing segment filtering

### **Google Sheets API**

- **Type Hint Enhancements**: Updated parameter type annotations to use proper type hints (`List[List[Any]]`) for better schema generation and API documentation

### **Workday API**

- **Type Hint Enhancements**: Updated parameter type annotations across all Workday modules to use proper type hints (`List[Dict[str, Any]]`, `List[str]`) for better API documentation and validation

### **Bug Fixes & Improvements**

- **Bug #292**: Fixed Google Calendar primary calendar handling by changing calendar name from "primary" to avoid silent errors
- **Bug #300**: Fixed Google Home API to enforce that commands not requiring values reject provided values for better API consistency
- **Bug #314**: Fixed SAPConcur one-stop flight connections by improving the search algorithm to properly handle connecting flights
- **Bug #311 and #319**: Fixed `get_reservation_details` by updating the docstring and aligning the function's output to only return documented values.
- **Bug #326**: Fixed `update_reservation_flights` by improving the docstring and removing an unused parameter to prevent incorrect usage.

## Release - 2025-08-05

### **YouTube Service Major Enhancements**

- **Complete Playlists Module**: Implemented comprehensive YouTube Playlists functionality with full CRUD operations, playlist management, and video organization capabilities
- **Video Upload Functionality**: Added complete video upload system with file validation, metadata handling, and upload progress tracking
- **Enhanced Error Handling**: Implemented robust error simulation and custom error definitions for all YouTube operations
- **Comprehensive Testing**: Added 1,040+ lines of test coverage for playlists and video upload functionality
- **Database Integration**: Enhanced YouTube database with playlist data structures and video metadata

### **Shopify Service Enhancements**

- **Transfer to Human Agents**: Added new functionality for transferring customer interactions to human agents with proper routing and handoff management
- **Line Items Enhancement**: Improved order management with ID and variant ID support for line items, enhancing order tracking and modification capabilities
- **Database Optimization**: Fixed fulfillable quantity mismatch in Shopify default database with comprehensive data restructuring
- **Order Management**: Enhanced order processing with improved validation and error handling for complex order scenarios

### **SAPConcur Flight Search Improvements**

- **Flight Search Refactor**: Major refactor of flight search functionality with improved search algorithms and result filtering
- **Enhanced Booking System**: Improved flight booking capabilities with better availability checking and reservation management
- **Database Optimization**: Streamlined flight data structures for improved performance and accuracy
- **Comprehensive Testing**: Added extensive test coverage for flight search and booking operations

### **Google Services Enhancements**

- **Google Sheets Batch Update**: Fixed `google_sheets.Spreadsheets.SpreadsheetValues.batchUpdate` functionality with improved error handling
- **Google Search API Key Management**: Enhanced API key handling with improved security and fallback mechanisms
- **Google Maps Live API**: Enhanced with comprehensive test coverage and improved functionality
- **Alternate FCDS Schemas**: Added concise and medium detail schemas for better API documentation

### **Mutation Engine and System Infrastructure**

- **Star Argument Handling**: Refactored function signatures across 20+ APIs to enhance clarity and consistency with List and Optional type hints
- **Import System Enhancement**: Added absolute imports for SimulationEngine and utils across 9 API modules for better module organization
- **Logging System**: Refactored all `print` statements throughout the codebase to use a new `print_log` function for standardized logging
- **Warning Suppression**: Disabled warnings globally across the codebase to streamline development and testing outputs

### **YouTube Tool and Live Integration**

- **YouTube Tool Integration**: Added docstring tests and custom error handling for environment variable issues
- **YouTube Live Integration**: Added a new service to interact with YouTube Live, including features to manage and monitor live streams
- **Mutation Manager**: Introduced a major new Mutation Manager, which creates mutated versions of all existing tool implementations for robust testing and validation

### **Documentation and Code Quality**

- **Docstring Refactoring**: Refactored docstring in the `update_content` function to clarify parameter descriptions
- **Type Hint Improvements**: Enhanced type hints across multiple APIs for better documentation and IDE support
- **Testing Framework**: Removed test cases that incorrectly relied on `print` statement outputs, aligning them with the new logging standards

### **Bug Fixes & Improvements**

- **Bug #256**: Provided username instead of UUID in reservation details
- **Bug #296**: Updated `edge.py` to return raw timestamps for `created_at` and `updated_at` fields in `list_edge_functions`
- **Bug #293**: Enhanced subreddit functionality and resolved related implementation issues
- **Bug #281**: Fixed SAPConcur flight search issues with improved search algorithms
- **Google Meet Service**: Addressed significant technical debt, improving the service's overall stability and performance
- **Environment Variables**: Implemented a fallback mechanism for environment variables and updated tests
- **Gemini API Calls**: Added retry mechanism and fixed environment variable references

# [0.0.10]

## Release - 2025-07-30

### **Azure Service Enhacements**

- **Account Management**: Added `create_cosmos_db_account` functionality for creating and managing Cosmos DB accounts

### **Clock Service Major Enhancements**

- **Enhanced Alarm Management**: Improved alarm creation, modification, and deletion with better validation and error handling
- **Timer Functionality**: Added comprehensive timer API with start, stop, pause, and resume capabilities
- **Stopwatch Features**: Enhanced stopwatch functionality with precise time tracking and state management
- **Fetch Actions Support**: Added comprehensive fetch_actions functionality for all clock operations with proper action logging
- **Date Filtering**: Implemented advanced alarm filtering by date, start date, and end date for better organization
- **Improved Validation**: Enhanced input validation and error handling across all clock service operations

### **Authentication System Overhaul**

- **Global Authentication Framework**: Implemented comprehensive authentication system across all services
- **Service-Specific Configurations**: Added authentication configurations for all 50+ API services with configurable settings
- **MySQL Authentication**: Enhanced MySQL service with proper authentication mechanisms and user management
- **Authentication Manager**: Created centralized authentication management with proper validation and error handling
- **Security Improvements**: Added authentication flags and configurations for better security control

### **Shopify Order Modification Enhancements**

- **Advanced Order Modification**: Enhanced `modify_pending_order_items` function with improved variant_id support
- **Payment Method Validation**: Added comprehensive payment method validation to ensure customer association
- **Refund Logic**: Implemented sophisticated refund logic for line item updates with proper inventory management
- **Stock Management**: Enhanced stock checking and inventory validation for order modifications
- **Streamlined Validation**: Removed unnecessary parameters and improved validation process efficiency

### **GitHub Repository Management Improvements**

- **Root Directory Support**: Enhanced file creation operations to maintain proper root directory structure
- **Repository Content Management**: Improved `create_or_update_file` and `push_files` functions for better repository organization
- **File Content Handling**: Enhanced `get_file_contents` to properly list repository contents with root directory entries
- **Directory Structure Preservation**: Fixed issues where repositories created via API lacked proper root directory entries

### **Google Search Service Enhancements**

- **Live API/LLM Integration**: Google Search now supports real-time web search by interacting with a live API and/or LLM, providing up-to-date results beyond static database content.
- **Dynamic Content Retrieval**: Enhanced the search backend to fetch and process live web content, including titles, snippets, and URLs, at query time.
- **Relevance and Ranking**: Improved relevance scoring and ranking by leveraging LLM-based analysis for more accurate and context-aware search results.

### **SAPConcur Flight Search Improvements**

- **Connecting Flight Support**: Enhanced flight search functionality to support connecting flights with flexible date handling
- **Multi-Segment Flights**: Implemented support for flights with multiple segments departing up to 7 days apart
- **Availability Validation**: Added comprehensive availability checks for both segments in connecting flights
- **Flexible Date Handling**: Improved date handling logic for better flight search results and booking options

### **Device Settings Service Enhancements**

- **Battery Management**: Enhanced battery utilities with improved power management and status tracking
- **Storage Optimization**: Improved storage utilities with better space management and file organization
- **General Utilities**: Enhanced general utilities with improved device insight capabilities
- **Volume Control**: Added comprehensive volume control functionality with mute/unmute capabilities
- **Device Insights**: Implemented advanced device insight features for better device monitoring

### **Generic Reminders Service Updates**

- **Input Flexibility**: Enhanced recurring field input flexibility with case-insensitive day values
- **Improved Validation**: Added better validation for recurring reminder fields and date handling
- **Enhanced Models**: Updated reminder models with improved data structures and validation
- **Comprehensive Testing**: Added extensive test coverage for reminder creation and modification

### **Cursor Service Improvements**

- **LLM Model Updates**: Updated LLM model configuration in Qdrant for better performance
- **Test Optimization**: Removed redundant workspace root tests for improved test efficiency
- **Code Search Enhancement**: Improved codebase search functionality with better error handling
- **File Editing**: Enhanced file editing capabilities with improved validation and error handling

### **Gemini CLI and Terminal Enhancements**

- **Common File System**: Added default common directory support for Gemini CLI, Cursor, and Terminal
- **Shell API Alignment**: Improved shell API functionality with better alignment to terminal capabilities
- **Security Validation**: Enhanced shell command validation with configurable security system
- **File System Management**: Improved common file system management functions and dehydration process

### **WhatsApp and Contacts Integration**

- **Enhanced Integration**: Improved WhatsApp and Contacts integration with better data synchronization
- **Contact Management**: Enhanced contact listing and management across WhatsApp and Contacts services
- **Test Coverage**: Added comprehensive test coverage for WhatsApp-Contacts integration scenarios

### **Zendesk API Service Major Overhaul**

- **Complete User Management**: Enhanced `create_user`, `update_user`, `delete_user`, `list_users`, and `show_user` with full field support including organization ID, tags, photo attachments, and custom fields
- **Organization Management**: Improved `create_organization` and `update_organization` with new fields (`external_id`, `group_id`, `notes`, `details`, `shared_tickets`, `shared_comments`, `tags`)
- **Comment System**: Implemented full CRUD operations for comments (`create_comment`, `show_comment`, `update_comment`, `delete_comment`, `list_comment`) with attachment support
- **Attachment Management**: Added `create_attachment`, `show_attachment`, and `delete_attachment` functions with multi-attachment support
- **Audit & Search**: Implemented `list_audits`, `show_audit` functions and Zendesk search capabilities across entity types
- **Advanced Ticket Fields**: Added support for `attribute_value_ids`, `custom_status_id`, `requester`, `safe_update`, `ticket_form_id`, and voice comment features
- **Pydantic Validation**: Migrated all input validation to Pydantic models for better type safety and error handling
- **Enhanced Models**: Updated all Zendesk models with new fields and comprehensive validation rules
- **Import Structure**: Refactored import statements and migrated to relative imports across all Zendesk modules
- **Database Schema**: Enhanced ZendeskDefaultDB.json with new user and organization structures
- **Auto-generated IDs**: Implemented automatic ID generation for organization creation
- **Database Clearing**: Fixed user database clearing method in test setup/teardown
- **Photo Normalization**: Resolved photo field handling when both 'url' and 'content_url' are present
- **Ticket Status**: Fixed ticket status handling by removing deprecated 'resolved' status option
- **Test Coverage**: Resolved multiple failing test cases and added comprehensive validation scenarios
- **Comment Integration**: Fixed comment creation with new tickets and ticket updates
- **Code Quality**: Standardized import statements, added type annotations, and improved documentation
- **Test Infrastructure**: Enhanced BaseTestCaseWithErrorHandler imports and test organization
- **Validation Performance**: Optimized validation using Pydantic models across all operations
- **Files Modified**: 15+ core API files, 25+ test files, enhanced models and database schema

### **Bug Fixes & Improvements**

- **Bug #262**: Fixed Clock service fetch actions and tracking functionality
- **Bug #274**: Enhanced Clock service with improved action logging and validation
- **Bug #283**: Fixed validators to return exactly what was provided by users while maintaining data validity
- **Bug #257**: Enhanced reminders service with case-insensitive day values and improved input flexibility
- **Bug #264**: Fixed GitHub root directory handling and file creation operations
- **Bug #268-270-273**: Enhanced Shopify order modification with improved validation and refund logic
- **Bug #248**: Fixed various service-specific issues and improved error handling
- **Bug #256**: Enhanced error handling and validation across multiple services
- **Bug #259**: Improved test framework and error handling mechanisms
- **Bug #251**: Enhanced SAPConcur flight search with connecting flight support
- **Bug #271**: Supabase - Fixed list_organizations() internal API error in list_organizations()
- **Bug #272**: Supabase - Fixed list_projects() internal API error in list_projects()
- **WhatsApp Integration**: Fixed WhatsApp-Contacts integration test and enhanced cross-platform contact management

### **Technical Enhancements**

- **Requirements Update**: Updated project dependencies with latest package versions
- **Code Quality**: Enhanced code quality with improved error handling and validation
- **Test Coverage**: Added comprehensive test coverage across all new features and improvements
- **Documentation**: Updated documentation with enhanced feature descriptions and usage examples
- **Performance Optimization**: Improved performance across multiple services with better resource management

### **Error Formatting**

- Support for **service-based error formatting**:
- Each service (e.g., Gmail, Calendar) can now register a custom error formatter.
- If a service-specific formatter is not provided, a global default formatter will be used.
- Helps maintain consistent and context-aware error responses across services and modules.

### **Error Configuration**

- **Error Mode Configuration**: Implemented flexible error handling modes ("RAISE"/"ERROR_DICT") with `set_package_error_mode()`, `get_package_error_mode()`, `reset_package_error_mode()`, and `temporary_error_mode()` context manager. Priority hierarchy: context override > global override > environment variable > default (RAISE)
- **ErrorManager Class**: Added centralized ErrorManager with singleton pattern for error handling configuration management. Features include:
  - `set_error_mode()` and `reset_error_mode()` for global error mode control
  - `temporary_error_mode` property for context-based temporary overrides
  - Service-specific error mode overrides with `get_error_mode(service_name)`
  - Framework integration with JSON-based configuration support
  - Configuration rollback functionality for state restoration

---

## Release - 2025-07-23

### **Google Search Implementation**

- **Basic Web Search API**: Implemented Google Search API with web content search capabilities
- **Keyword-Based Search**: Added support for basic keyword matching and relevance scoring
- **Web Content Database**: Enhanced search functionality with stored web content including titles, snippets, URLs, and keywords
- **Relevance Scoring**: Implemented basic relevance scoring based on term matching in titles, snippets, content, and keywords

### **Slack Service Enhancements**

- **Current User ID Support**: Added `get_current_user_id` functionality to expose current user ID for better user context
- **History Filtering**: Enhanced conversation history with `exclude_user_id` parameter to filter out messages sent by specific users
- **Improved Message Filtering**: Fixed message filtering to properly return messages sent by the user ID
- **Enhanced Pagination**: Improved cursor-based pagination with proper base64 encoding and user-based cursors

### **Contact Integration System**

- **Cross-Platform Contact Management**: Implemented comprehensive contact integration between Contacts, Phone, Messages, and WhatsApp services
- **Unified Contact Database**: Created shared contact structure with WhatsApp, Phone, and Messages integration
- **Contact Creation Enhancement**: Updated `create_contact` to populate phone/messages related data automatically
- **WhatsApp Contact Sync**: Enhanced WhatsApp contact listing to properly display contacts created in Contacts API

### **Google Cloud Storage Improvements**

- **Bucket Insert Validation**: Enhanced bucket insert operations with comprehensive validation and data consistency checks
- **Bucket Request Support**: Added optional `bucket_request` parameter to patch/update methods for JSON-style bucket metadata
- **Enhanced Error Handling**: Improved validation and error handling for bucket operations with better type checking

### **SAPConcur Service Updates**

- **Flight Search Resolution**: Fixed SAPConcur search flight issues for improved flight booking functionality
- **Passenger Data Enhancement**: Enhanced passenger data handling in booking APIs with improved validation
- **Booking Insurance**: Added insurance field to bookings with binary support for cancellation policy information
- **Flight Availability**: Enhanced flight availability data structure in search functions for better results

### **Error Definitions and Configuration**

- **Comprehensive Error System**: Added extensive error definitions and error configuration across multiple services
- **Service-Specific Errors**: Implemented custom error definitions for Shopify, Spotify, Cursor, GitHub, Device Actions, Generic Media, Google Home, and Retail APIs
- **Enhanced Error Handling**: Improved error simulation and handling mechanisms across all services

### **AI Database Translation Module**

- **Cross-Platform Database Conversion**: Implemented comprehensive translation module for converting between different database formats (Cursor, Copilot, Gemini CLI, Terminal)
- **Bidirectional Translation**: Added support for translating between all combinations of database formats with proper metadata handling
- **File System Preservation**: Enhanced translation logic to preserve file system structures while adapting metadata for different platforms
- **Testing Framework**: Added comprehensive test suite for translation module with validation of all conversion paths

### **Shopify Service Enhancements**

- **Payment Methods Integration**: Enhanced customer API with payment methods and default payment method ID support in `shopify_get_customer_by_id`, `shopify_get_customers`, and `shopify_search_customers` functions
- **Payment Data Structures**: Added comprehensive payment method data structures including type, gateway, last four digits, brand, and default status
- **Load State Improvements**: Fixed Shopify load state error injection issues for improved stability and reliability

### **Development Tools Improvements**

- **FCSpec Error Handling**: Updated FCSpec.py to print error messages instead of raising errors for better debugging experience

---

## Release - 2025-07-18

### **Common Utils Package Implementation**

- **Shared Infrastructure**: Added comprehensive common_utils package with centralized error handling, logging, and testing utilities
- **Error Management**: Consolidated error simulation and handling across all services with standardized error definitions
- **Testing Framework**: Implemented unified base test cases and docstring testing utilities for consistent test coverage
- **Logging System**: Added centralized call logging and complexity tracking for better debugging and monitoring

### **Shopify Service Updates**

- **Order Status Restructuring**: Removed deprecated `status` field from orders in favor of `financial_status` and `fulfillment_status` to align with real Shopify API standards
- **Database Restructuring**: Major database schema updates with comprehensive order data restructuring
- **Test Coverage**: Updated test cases across cancel, close, reopen, and order count operations to reflect new order structure
- **Payment Information for Customer**: We added payment information when getting customer

### **Terminal and Cursor Services**

- **Git Directory Preservation**: Enhanced file system operations to properly preserve `.git` directories during database hydration and dehydration
- **Workspace Management**: Improved git handling in `update_db_file_system_from_temp` and `dehydrate_db_to_directory` functions
- **File Processing**: Streamlined file processing with better git directory restoration capabilities

### **Bug Fixes & Improvements**

- **Bug #200**: Fixed WhatsApp chat data handling to return chat objects directly instead of copies for better data integrity and multi-contact support.
- **Bug #196**: Resolved calendar ID handling issues for improved calendar operations
- **Bug #208**: Fixed Reddit search issues by correcting field mismatches, adding missing id and created_utc, and improving relevance scoring for accurate results and pagination.
- **Bug #206**: Fixed issues with Shopify utils crud operations saving datetime objects in DB
- **Bug #197**: SAPConcur - One-Stop Flight Search: Updated one-stop flight search to include flights with an intermediate stop, aligning with Tau bench data. For example, JFK to ATL and ATL to SEA flights are now included in JFK to SEA one-stop searches.
- **Bug #198**: Figma - find_node_in_tree: Addressed static analysis issues for find_node_in_tree, noting the absence of return type annotation and the requirement for nodes_list and node_id parameters.
- **Bug #199**: SAPConcur - Data Porting Script: Added comments to the "Tau Bench Data Porting" script to resolve data porting issues.
- **Bug #202**: SAPConcur - Gift Card Type: Implemented a new gift_card type.
- **Bug #204**: SAPConcur - User Details: Included "date of birth" as a parameter in user details.
- **Bug #207**: SAPConcur - Booking Insurance: Added an insurance field to bookings (binary), allowing for the presence of insurance to inform cancellation policies, consistent with Tau Bench requirements.
- **Bug #209**: Shopify load state apply error injection had to be removed after common utils update"
- **Bug #210**: `product_id` should be int per Shopify API, but kept as str throughout service for compatibility; now enforced to be str containing a valid int.
- **Bug #215**: Synced `ShopifyDefaultDB.json` from `RetailDefaultDB.json`, changing `fulfillment_status` from `'closed'` to `'fulfilled'`.
- **Bug #244**: Integration between Contacts and Whatsapp fixed. The contacts created in Contacts API are being correctly being listed in Whatsapp.

---

# [0.0.9]

## Release - 2025-07-17

### **Terminal and Cursor Enhancements**

- Added common file system support for Terminal and Cursor.
- Updated Cursor with the latest Terminal changes.
- Cursor and Terminal can now opperate on common file system by hydrating DB using the current state of file system and dehydrating DB after each command that modifies the file system

### **Gemini CLI Enhancements**

- **Feature Parity with Terminal API**: Enhanced gemini-cli’s run_shell_command to match the functionality of the terminal's run_command, including support for the description parameter (for command documentation) and directory parameter (for execution context), while retaining capabilities like background execution, internal commands (cd, pwd, env), and security validation.
- **Common File System**: Gemini CLI can now operate on common file system by hydrating DB using the current state of file system and dehydrating DB after each command that modifies the file system

### **Spotify Service Implementation**

- **Complete Music Streaming API**: Full-featured Spotify API simulation with user profiles, playlists, artists, albums, search, and discovery features
- **Social Features**: Follow/unfollow system for artists, users, and playlists with relationship management
- **Error Handling**: Comprehensive error simulation with 400+ error definitions and robust handling mechanisms
- **Testing Coverage**: 2,700+ test cases with comprehensive validation across all endpoints

### **Google Home Service Implementation**

- **Smart Home Control**: Complete device management, discovery, and remote control for smart home automation
- **Scheduling & Automation**: Advanced scheduling system with AI-powered automation generation and trait-based device control
- **Event Management**: Comprehensive event logging, search, and monitoring for home automation history
- **Testing Coverage**: 1,500+ test cases covering device operations, scheduling, and automation scenarios

### **Bug Fixes & Improvements**

- **Consistent File Representation**: Standardized file storage using content_lines with proper line endings for cross-system compatibility.
- **Checksum Fixes**: Fixed MD5 validation by correctly handling binary archives using base64 encoding/decoding.
- **Using Decorators at Function level**: Changed Gemini Common file decorator to implement it at function level
- **Configurable Documentation**: Added comprehensive alternate function call schemas (concise and medium detail) for all 58+ API services, providing flexible documentation options for different use cases and complexity levels.
- **Using Decorators at Function level**: Changed Gemini Common file decorator to implement it at function level

### **Reverted Changes**

- **WhatsApp Bug Fix #116 Reverted**: Reverted WhatsApp service database persistence and thread safety fixes due to reported issues

---

# [0.0.8]

## Release - 2025-07-16

### **Bug Fixes & Improvements**

- **Bug 192**: changed Copilot used Gemini model from preview version to official version;

## Release - 2025-07-14

### **MultiHop Support Enhancements**

- Enhanced binary file handling in hydration process for improved file conversion support
- Refactored counter functionality to better handle diverse file types during database hydration
- Added comprehensive binary file processing capabilities for MultiHop operations

### **Gmail Service Improvements**

- Reverted base64 encoding implementation to improve email content handling
- Enhanced email processing with better content preservation and formatting
- Improved email attachment handling and content extraction

### **Device Settings Service Updates**

- Added comprehensive fetch_actions functionality for all device setting endpoints
- Implemented action logging capabilities with enhanced database support
- Enhanced device settings management with better validation and error handling
- Improved test coverage for device settings operations

### **Shopify Service Enhancements**

- Added new functions for modifying pending orders with comprehensive validation
- Implemented order modification features for address, items, and payment transactions
- Enhanced Pydantic models for better data validation and error handling
- Added comprehensive unit tests for each modification function to ensure data integrity

### **Terminal Service Improvements**

- Added support for archiving operations with binary content handling
- Enhanced file compression and decompression capabilities
- Improved terminal command execution with better error handling
- Added comprehensive tests for archive functionality

### **Google Sheets Service Updates**

- Fixed append functionality for better data insertion and range handling
- Enhanced sheet data management with improved validation
- Added better error handling for sheet operations
- Improved range validation and data formatting

### **SAP Concur Service Refactoring**

- Refactored create trips functionality from utility to tool implementation
- Enhanced trip creation with better validation and error handling
- Improved SAP Concur API integration and response handling

### **Gemini CLI Service Enhancements**

- Fixed function map paths for improved CLI functionality
- Enhanced command execution with better path resolution
- Added comprehensive error handling for CLI operations
- Improved file system integration and workspace management

### **Google Docs Service Improvements**

- Fixed table extraction logic in Google Drive converter
- Enhanced document processing with better table handling
- Improved content extraction from complex document structures
- Added comprehensive support for table data conversion

### **State Management Improvements**

- Enhanced load/save state functionality across multiple services
- Added better state persistence and recovery mechanisms
- Improved database state management with comprehensive validation
- Enhanced error handling for state operations

### **Cursor Service Enhancements**

- Fixed milliseconds handling in cursor operations for better precision
- Enhanced cursor API functionality with improved time handling
- Added better validation for cursor-related operations
- Improved cursor service reliability and performance

### **Additional Bug Fixes & Improvements**

- **Bug #116**: Fixed WhatsApp service database persistence and thread safety issues by implementing AutoPersistDB class for automatic data saving.
- **Bug #117**: Fixed Copilot service error handling logic in get_errors function to prevent empty error list extensions.
- **Bug #184**: Resolved import issues in notifications API
- Fixed Google People service data handling and field names
- Fixed various service-specific issues across multiple APIs
- Enhanced test coverage and validation across all services
- Improved error handling and response formatting

### **Additional Technical Enhancements**

- Enhanced database initialization and utility functions across services
- Improved error handling to prevent nested command execution errors
- Added comprehensive logging and action tracking capabilities
- Enhanced test isolation and validation across all services
- Improved code quality with better validation and error handling

## Releases - 07-08-2025 to 07-12-2025

### **Messages Service Enhancements**

- Added comprehensive fetch_actions functionality for all message endpoints
- Implemented action logging capabilities with enhanced database support
- Added extensive test coverage for fetch_actions functionality with 390+ test cases
- Enhanced message models with new action-related data structures
- Improved utility functions for message processing and action handling

### **Generic Reminders Service Updates**

- Enhanced fetch_actions functionality for all reminder operations
- Added comprehensive action logging and database support
- Implemented extensive test coverage for fetch_actions with 269+ test cases
- Enhanced reminder models with action-related data structures
- Improved utility functions for reminder processing and validation

### **Notifications Service Improvements**

- Implemented get_replies functionality for notification management
- Added comprehensive test coverage for get_replies with 468+ test cases
- Enhanced notification models with reply-related data structures
- Improved utility functions for notification processing and reply handling
- Added fetch_actions support for all notification operations

### **Retail Service Database Enhancements**

- Refactored database initialization with improved default value handling
- Added utility functions for database clearing and default data loading
- Enhanced save_state function with formatted JSON output for better readability
- Renamed clear_db function to reset_db for improved clarity
- Added comprehensive database utility functions for better data management

### **Terminal Service Improvements**

- Enhanced command execution error handling to prevent nested CommandExecutionError
- Added comprehensive tests for workspace isolation issues
- Implemented tests for file permissions and persistence behavior
- Added tests for relative and absolute path hydration issues
- Improved error handling to ensure proper workspace isolation

### **API Version Comparison Tools**

- Implemented comprehensive API version comparison tool

### **Shopify Service Enhancements**

- Enhanced Shopify database with enriched data structures
- Improved test coverage and validation for Shopify operations
- Added comprehensive unit tests for database functionality
- Enhanced error handling and response formatting

### **Generic Tools Service**

- Implemented comprehensive Generic Tools service with code execution and LLM integration capabilities
- Added Python script validation and execution with Google Generative AI API integration
- Implemented file management utilities with create_file_part function for LLM file handling
- Added comprehensive docstring parsing and JSON schema generation utilities
- Enhanced code execution with proper error handling and file utilities module
- Added extensive test coverage for all generic tools functionality

## **Gemini CLI Service Implementation**

- Implemented comprehensive Gemini CLI service with file system and shell operations
- Added file management capabilities including read, write, and search operations
- Implemented shell command execution with proper error handling
- Added memory management functionality for CLI operations
- Enhanced service with comprehensive error simulation and custom error definitions
- Added extensive test coverage for all Gemini CLI functionality

## **Notes and Lists Service**

- Implemented comprehensive Notes and Lists service with full CRUD operations
- Added note creation, updating, and management functionality
- Implemented list creation, item management, and list operations
- Added search capabilities for notes and lists with advanced filtering
- Enhanced delete operations with proper validation and error handling
- Added comprehensive test suite covering all notes and lists functionality
- Implemented undo functionality for better user experience

### **Clock Service Enhancements**

- Added correct simulation code to resolve access problems
- Enhanced clock service initialization and functionality
- Improved error handling for clock operations
- Implemented comprehensive fetch_actions functionality for all clock service operations
- Added action logging capabilities with enhanced database support for alarms, timers, and stopwatches

### **Cursor API Improvements**

- Refactored cursor API to transition from ChromaDB to QdrantDB for better performance
- Removed ChromaDB configuration and introduced QdrantDB configuration
- Enhanced cursor API functionality with improved snippet bounds handling
- Introduced GeminiEmbeddingManager class for managing embeddings with caching capabilities
- Updated tests to improve error handling and test flexibility
- Enhanced embedding functions to utilize Qdrant for better search capabilities

### **Terminal Service Logging Enhancements**

- Added comprehensive logging functionality to terminal service
- Enhanced file permission handling to metadata functions
- Improved terminal logging capabilities with better error tracking
- Added corresponding unit tests for file permission handling

### **Device Settings Bug Fixes**

- Enhanced device settings API with improved error handling
- Added better validation for device settings operations
- Improved device settings functionality and reliability

### **Clock Service**

- Implemented comprehensive Clock service with alarm, timer, and stopwatch functionality
- Added alarm management with scheduling and notification capabilities
- Implemented timer and stopwatch APIs with precise time tracking
- Enhanced error handling and validation for all clock operations
- Added extensive test coverage for alarm, timer, and stopwatch functionality

### **Airline Service**

- Implemented comprehensive Airline service with flight booking and reservation management
- Added flight search capabilities for direct and one-stop flights
- Implemented reservation booking, cancellation, and update functionality
- Enhanced passenger and baggage management with detailed reservation tracking
- Added airport listing and user management with comprehensive test coverage
- Implemented certificate generation and human agent transfer capabilities

### **Retail Service Implementation**

- Implemented complete retail service with comprehensive order management capabilities
- Added order modification tools for address, items, and payment updates
- Implemented user management with email and name-based user identification
- Added product management with detailed product information and type listings
- Enhanced order processing with cancellation, exchange, and return functionality
- Implemented comprehensive test suite covering all retail operations

### **Contacts Integration Enhancement**

- Enhanced contacts integration across multiple services (Messages, Phone, WhatsApp)
- Improved contact management with aggregated contacts database
- Enhanced contact synchronization between different communication platforms
- Added comprehensive contact validation and error handling
- Updated default databases for better contact data consistency

### **Google Sheets A1 Range Validation**

- Enhanced Google Sheets A1 range validation for improved data integrity
- Made A1Range more robust with comprehensive validation logic
- Added extensive test coverage for A1 range functionality
- Improved error handling for invalid range specifications

### **MultiHop Support Improvements**

- Enhanced main.py to support parallel processing for file conversions
- Added file ignoring functionality in hydrate_db for Google Drive processing
- Added comprehensive base64 converter utility in GDrive Utils folder
- Bug fix in MultiHop Support with better content processing when tables are present in the documents

### **Device Actions & Settings**

- Enhanced device actions with comprehensive API coverage
- Improved device settings management with better utility functions
- Added extensive test coverage for device operations
- Enhanced error handling and validation for device-related operations
- Added comprehensive load/save state functionality for device settings service
- Implemented database state persistence with enhanced utility functions
- Added extensive test coverage for state management operations
- Enhanced device settings database with improved state handling capabilities

### **Jira Service Enhancements**

- Enhanced Jira documentation with improved docstrings
- Added comments functionality with proper documentation
- Improved Jira API testing with better validation
- Enhanced error handling and response formatting

### **Bug Fixes & Improvements**

- **Bug #177**: Fixed Google Sheets A1 range validation issues
- **Bug #102**: Enhanced error handling and validation across multiple services
- **Bug #87**: Improved Jira API functionality and documentation
- **Bug #178**: Fixed FileContentModel issues and enhanced database loading
- **Bug #175**: Enhanced error handling in run_command to remove nested CommandExecutionError
- Fixed workspace isolation issues in terminal service
- Improved file permissions and persistence behavior validation
- **Bug #179**: By default disabled debug statements in device_settings service.
- **Bug #181**: Standardize enum field usage to .value for dictionary keys and database operations
- **Bug #180**: Fixed device settings service issues and enhanced error handling
- **Bug #161**: Resolved various service-specific bugs and improved stability
- Fixed airline service naming issues and removed unwanted tau airline references
- Enhanced MySQL service functionality and error handling
- Improved Cursor service timing and millisecond handling
- Fixed simulation module issues across multiple services
- Enhanced terminal service workspace isolation and command execution

### **Technical Enhancements**

- Enhanced README.md with improved project structure documentation
- Improved code quality with removal of debug statements
- Enhanced error handling across multiple services
- Added comprehensive test coverage for new functionality
- Improved database management and utility functions
- Enhanced logging and action tracking capabilities
- Standardized error handling across all Simulation Engine modules
- Enhanced error simulation capabilities with improved error definitions
- Updated all services to use consistent error handling patterns
- Improved database initialization and management across multiple services
- Enhanced test coverage across multiple services
- Updated database schemas for better data consistency
- Improved logging and debugging capabilities
- Enhanced utility functions for better service integration

---

# [0.0.7.1] - 2025-07-07

## **MultiHop Support Enhancements**

- Refactored Google Slides converter to enhance text extraction capabilities
- Enhanced multihop hydrate DB tests to support varied content structures
- Improved MultiHop support for GDrive files with better content processing

## **Media Control Service**

- Implemented comprehensive Media Control API simulation with playback management
- Added media persistence to playlist functionality
- Enhanced playback control with improved error handling and state management
- Added unit tests for media control models and playback functions
- Implemented set_active_media_player function with proper error definitions

## **Generic Media Service**

- Added play and search APIs with error handling and media item management
- Enhanced play and search API tests with filtering capabilities
- Refactored media search and adaptation logic for better performance
- Added search engine module with multiple strategies and configurations
- Enhanced search strategies with unique document retrieval

## **Device Settings & Actions**

- Implemented device setting API with comprehensive utility functions
- Added installed apps and notification management APIs
- Enhanced app installation and uninstallation logic
- Added fetch_actions function for device_actions service
- Improved device insights with comprehensive enum system and expanded test coverage

## **Google People Service**

- Implemented Google People service with contact management capabilities
- Added comprehensive contact operations and data models

## **File Content Model Improvements**

- Updated FileContentModel and related models for Google Drive API
- Enhanced file conversion scripts for Google Drive, Sheets, and Slides
- Added support for .docx and .doc file parsing in gdrive_converter
- Implemented content extraction using python-docx with fallback to plain text

## **Notification System Enhancements**

- Added notification reading functionality with proper reply action initialization
- Implemented marking bundle as unread functionality
- Enhanced notification management with improved CRUD operations

## **Contacts Service**

- Implemented comprehensive contacts service with full CRUD operations
- Added pydantic validation for all contact functions
- Enhanced search_contacts functionality with proper validation

## **Bug Fixes & Improvements**

- **Bug #173**: Refactored set_customer_default_address function to ensure complete customer data usage
- Fixed failing tests across multiple services
- Enhanced test isolation and timestamp validation for device_setting
- Improved error handling for unmatched mock calls in test framework
- Fixed Jira docstring modifications and corrected documentation

## **Technical Enhancements**

- Refactored import paths to use absolute imports for better reliability
- Enhanced gsheets_converter and main script with logging and data serialization improvements
- Added A1 notation for range extraction in Google Sheets
- Improved database operations with proper UUID handling
- Enhanced embedding management and cache handling across search strategies
- Added `assertions_utils.py` utility file in Scripts folder with comprehensive comparison functions for strings, datetimes, and list operations

---

# [0.0.7] - 2025-07-03

## **MultiHop Support for GDrive Files**

- Introduced MultiHop-Support for Gdrive, GDocs, GSheets and GSlides APIs.
- Implemented `hydrate_db` function as a GDrive utility;

## **Phone API Simulation**

- Implemented a full-featured Phone API simulation, including models, error handling, database, and utility functions.
- Added a comprehensive test suite covering phone API components, call scenarios, and in-memory DB.
- Introduced `DBs/PhoneDefaultDB.json` with sample contacts and business data.

## **Slack Search Engine Integration**

- Added a modular search engine for Slack API simulation, including strategies, adapters, and configuration files.
- Expanded and updated unit tests for Slack API simulation.

## **Search Engine Performance Improvements**

- Integrated Google's text embedding model into `QdrantSearchStrategy` for improved semantic search performance.
- Implemented optimized caching with LRUCache and configurable memory management.
- Refactored `GeminiEmbeddingManager` for better cache handling and embedding efficiency.

## **Notification Support:**

- Added new services to handle and process notifications.

## **Message Phone:**

- Implemented support for Message Phone functionalities.

## **Device Settings:**

- Introduced new capabilities for managing and configuring device settings.

## **Device Actions:**

- Added support for executing various device actions.
- - Enhance app installation and uninstallation logic, add `fetch_actions` function to `utils.py` for `device_actions` service.

## **Bug Fixes**

- **Bug #164**: Updated `update_dynamic_data` function and improved search functions.
- **Bug #166**: Fixed SAPConcur `update_reservation_flights` baggage count removal issue.
- **Bug #167**: Enhanced order modification validation to prevent modifications of cancelled/closed orders.
- **Bug #168**: Added `list_returns` function to utils.py with corresponding unit tests.
- Improved error handling for unmatched mock calls in test framework.

---

# [0.0.6] - 2025-06-30

## 🔍 **Advanced Search Engine System**

- **Multi-strategy search architecture** across Gmail, Jira, and Google Drive APIs
- **Five search strategies**: Keyword (Whoosh), Semantic (Qdrant), Fuzzy (RapidFuzz), Hybrid, and Substring
- **Gmail search**: Full-text search across messages and drafts with advanced filtering
- **Jira search**: JQL (Jira Query Language) support with complex query operators
- **Google Drive search**: Content-based search across files and shared drives
- **Configurable scoring** and real-time indexing with database synchronization

## 📁 **Comprehensive Filesystem Support**

- **Gmail attachments**: Complete attachment system with 25MB file limit, MIME validation, and base64 encoding
- **Slack filesystem**: Full file management with 50MB uploads, external URLs, and channel organization
- **Jira attachments**: File attachment support for issues with content retrieval
- **Google Drive content management**: Advanced content storage with revision system and export caching

## 🗂️ **Google Drive Content & Revision Management**

- **Content operations**: Create, update, get, and export file content with 100MB limit
- **Revision system**: Create, list, and delete revisions with keep-forever protection
- **Export format caching**: Support for multiple formats (PDF, Word, etc.) with intelligent cache management
- **Content validation**: Checksums, encoding support, and comprehensive error handling

## 🛠️ **Technical Enhancements**

- **Enhanced error handling** with custom exception classes and comprehensive validation
- **Improved type hints** and Google-style documentation across all modules
- **Database schema improvements** with proper data structures and relationships
- **Extensive test coverage** with unit and integration tests for all new features

## 🐛 **Bug Fixes**

- Fixed variable validation issues (Bug #131)
- Added proper DateTimeEncoder (Bug #126)
- Resolved database extension creation (Bug #143)
- Fixed ticket ID handling consistency (Bug #162)
- Corrected expression evaluation problems (Bug #149)
- Enhanced attachment cleanup and reference counting

## 📚 **Code Quality & Documentation**

- **Extensive docstring improvements** with proper Args/Returns/Raises sections
- **Import statement refactoring** for better module organization
- **Removed deprecated code** and proof-of-concept scripts
- **Enhanced logging** and debugging capabilities across all APIs

---

# [0.0.5] - 2025-05-28

## **Tech Debt and Project Structure Improvements**

- **Project Structure Overhaul**: Migrated to relative imports across all API modules for better maintainability
- **Function Map Refactoring**: Updated function maps to use consistent import paths and aliases
- **Code Organization**: Consolidated imports and removed redundant code across multiple modules
- **Testing Infrastructure**: Enhanced test coverage and standardized test structures

## **Google Sheets API Enhancements**

- Enhanced `batchUpdate`, `batchGet`, and `batchGetByDataFilter` functions with comprehensive validation
- Improved `clear`, `copyTo`, and `append` functions with better input validation and error handling
- Updated default parameter handling for `valueRenderOption` and `dateTimeRenderOption`
- Added support for open-ended cell-to-column ranges (Issue #89 fix)

## **Google Calendar API Improvements**

- Comprehensive validation enhancements for `EventsResource`, `CalendarListResource`, and `AclResource`
- Improved event retrieval logic with proper primary calendar mapping
- Enhanced input validation for calendar and event existence checks
- Added comprehensive test coverage for time filtering and event handling

## **Shopify Service Enhancements**

- Added `list_exchanges` function to retrieve exchange records
- Enhanced `create_product` function with custom ID support and validation
- Added `modify_pending_order` function for order updates

## **Bug Fixes and Stability**

- **SapConcur**: Fixed project structure and relative imports
- **Gmail**: Enhanced system labels handling and database initialization
- **Terminal**: Improved git command handling and workspace isolation
- **Database**: Fixed default database path references from "DefaultDBs" to "DBs"

## **Development Tools**

- Enhanced AutoDoc functionality for better documentation generation
- Improved file utilities with better MIME type handling
- Updated GitHub workflows for better CI/CD pipeline management

---

# [0.0.4] - 2025-05-25

## **Comprehensive Input Validation Framework**

- **Multi-API Input Validation**: Implemented extensive input validation across 20+ APIs including Gmail, Google Docs, YouTube, Google Calendar, Slack, Jira, Google Sheets, and more
- **Pydantic Models**: Added hundreds of Pydantic validation models for robust type checking and data validation
- **Custom Error Handling**: Introduced comprehensive custom error classes with specific error messages for different validation scenarios
- **Test Coverage Enhancement**: Added 500+ test cases specifically for input validation scenarios

## **Gmail API Major Overhaul**

- Enhanced message handling with comprehensive validation for `insert`, `modify`, `batchModify`, `trash`, and `untrash` functions
- Improved draft management with validation for `create`, `update`, `delete`, and `get` operations
- Enhanced thread operations with proper input validation and error handling
- Upgraded label management with comprehensive CRUD operation validation

## **Google Docs API Improvements**

- Complete input validation for `batchUpdate`, `create`, and `get` functions
- Enhanced document management with proper error handling
- Improved test coverage for all document operations

## **YouTube API Enhancements**

- Comprehensive validation for `CommentThread`, `Channels`, and `ChannelSection` APIs
- Enhanced `list`, `insert`, and `delete` operations with proper input validation
- Improved error handling for video and channel management

## **Jira API Improvements**

- Enhanced project management with comprehensive validation
- Improved issue handling with better input validation
- Enhanced component and user management APIs
- Added comprehensive search functionality improvements

## **Service Implementations**

- **BigQuery Service**: Complete implementation with query execution and table management
- **Figma Service**: Comprehensive API implementation with design management capabilities
- **Stripe Service**: Full payment processing API with validation and error handling
- **GitHub Service**: Complete repository and issue management implementation
- **Puppeteer Service**: Browser automation capabilities with comprehensive testing

## **Database and Infrastructure**

- Enhanced database schemas across all services
- Improved error simulation and handling mechanisms
- Better test infrastructure with comprehensive coverage

---

# [0.0.3] - 2025-05-24

## **SapConcur Service Implementation**

- **Complete Travel Management System**: Implemented comprehensive SapConcur service for business travel management
- **Flight Booking Capabilities**: Added flight search, booking, reservation management, and cancellation features
- **User Management**: Implemented user details, payment methods, and membership handling
- **Extensive Database**: Integrated 200,000+ travel records with comprehensive data structure
- **Testing Coverage**: Added 18+ test modules covering all SapConcur functionality
- **Error Handling**: Implemented robust error simulation and custom error definitions

## **Flight Operations**

- Advanced flight search with direct and connecting flight options
- Booking management with confirmation and modification capabilities
- Baggage handling and passenger management
- Airport listings and travel route optimization

## **Business Travel Features**

- Corporate travel policy compliance
- Expense management integration
- Travel approval workflows
- Reporting and analytics capabilities

## **Data Migration**

- Tau-Bench data migration to SapConcur format
- Database optimization for large-scale travel data
- Performance improvements for search and booking operations

---

# [0.0.2] - 2025-05-23

## **Massive Input Validation Initiative**

- **Universal Input Validation**: Implemented comprehensive input validation across 25+ major API services
- **Pydantic Framework Integration**: Added robust Pydantic models for all API endpoints ensuring type safety and data integrity
- **Custom Error System**: Introduced standardized error handling with 100+ custom error classes
- **Comprehensive Testing**: Added 1000+ test cases for input validation scenarios

## **Major Service Implementations**

### **BigQuery Service**

- Complete Google BigQuery API implementation
- Query execution, table management, and data operations
- Comprehensive error handling and validation
- Full test coverage for all BigQuery operations

### **Figma Service**

- Complete Figma API implementation for design collaboration
- Node management, annotation operations, and document context handling
- Advanced design workflow support
- Comprehensive testing and error handling

### **Stripe Service**

- Full payment processing API implementation
- Customer management, payment methods, subscriptions
- Invoice handling, refunds, and billing operations
- Comprehensive financial transaction support

### **GitHub Service**

- Complete GitHub API implementation
- Repository management, issue tracking, pull requests
- Code scanning, workflow management
- Comprehensive version control operations

### **MongoDB Service**

- Database management and connection handling
- Collection operations and document management
- Advanced query capabilities
- Full testing coverage

### **MySQL Service**

- Database connectivity and management
- Query execution and transaction handling
- Schema management capabilities

## **Enhanced Existing Services**

### **Google Services Suite**

- **Gmail**: Enhanced message handling, improved threading, advanced label management
- **Google Calendar**: Comprehensive event management, calendar operations, ACL handling
- **Google Docs**: Document creation, editing, and collaboration features
- **Google Sheets**: Spreadsheet operations, data manipulation, formatting
- **Google Drive**: File management, sharing, and collaboration
- **Google Meet**: Meeting management and conference operations

### **Communication Platforms**

- **Slack**: Enhanced messaging, channel management, file sharing
- **Microsoft Teams**: Team collaboration and communication features
- **WhatsApp**: Messaging API with comprehensive validation

### **Social Media Platforms**

- **YouTube**: Video management, commenting, channel operations
- **Instagram**: Media posting, story management, engagement features
- **TikTok**: Content creation and management capabilities
- **LinkedIn**: Professional networking and content sharing

### **Project Management**

- **Jira**: Enhanced issue tracking, project management, workflow automation
- **Confluence**: Content management and collaboration
- **GitHub Actions**: CI/CD pipeline management

### **E-commerce Platforms**

- **Shopify**: Store management, product operations, order processing
- **Retail Services**: Comprehensive e-commerce functionality

## **Infrastructure Improvements**

- **Error Simulation Engine**: Advanced error simulation across all services
- **Database Schema Updates**: Enhanced database structures for all APIs
- **Testing Framework**: Comprehensive testing infrastructure with high coverage
- **Documentation**: Extensive API documentation and usage examples

## **Development Tools**

- **AutoDoc Enhancements**: Improved automatic documentation generation
- **Code Quality**: Enhanced code standards and validation
- **Performance Optimizations**: Improved response times and resource usage

---

# [0.0.1] - 2025-05-21

## **Initial Project Foundation**

- **Project Structure Establishment**: Created comprehensive API simulation framework
- **Database Migration**: Migrated default databases from `DefaultDBs` to `DBs` directory structure
- **Workflow Configuration**: Established GitHub Actions workflows for automated testing and coverage reporting
- **Utility Scripts**: Added essential automation and documentation tools

## **Core Infrastructure**

- **25+ API Services**: Initial implementation of major API services including:
  - Google Workspace Suite (Gmail, Drive, Calendar, Docs, Sheets, Meet)
  - Social Media APIs (YouTube, Instagram, TikTok, LinkedIn)
  - Communication Platforms (Slack, WhatsApp)
  - Project Management (Jira, Confluence)
  - E-commerce (Shopify)
  - Developer Tools (GitHub, Cursor)
  - Enterprise (Salesforce, Workday, HubSpot)

## **Database Foundation**

- **Comprehensive Default Databases**: Established 25+ service-specific databases with realistic data structures
- **Simulation Engine**: Core simulation framework for API behavior replication
- **Data Models**: Fundamental data structures and validation schemas

## **Development Tools**

- **AutoDoc System**: Automated documentation generation (`Scripts/AutoDoc.py`, `Utils/AutoDoc.py`)
- **Function Call Specifications**: Comprehensive API specification framework (`Scripts/FCSpec.py`, `Utils/FCSpec.py`)
- **Human Readable Documentation**: User-friendly documentation generation
- **Package Management**: Version control and distribution tools
- **Test Framework**: Basic testing infrastructure

## **GitHub Integration**

- **Automated Coverage**: Coverage reporting workflow configuration
- **Drive Synchronization**: Automated documentation sync to Google Drive
- **CI/CD Pipeline**: Continuous integration and deployment setup

## **Schema Foundation**

- **Removed Legacy Schemas**: Cleaned up 20+ legacy schema files for better organization
- **Centralized Configuration**: Consolidated API configurations and settings
- **Version Management**: Established version control system for API specifications
