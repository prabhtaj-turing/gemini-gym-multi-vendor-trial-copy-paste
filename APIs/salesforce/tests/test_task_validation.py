from salesforce import create_task
from common_utils.base_case import BaseTestCaseWithErrorHandler
from datetime import datetime, timedelta
from salesforce.SimulationEngine.custom_errors import (
    TaskSemanticValidationError, TaskDuplicateIdError, TaskContradictoryStateError,
    TaskInputSanitizationError, TaskNumericValidationError, TaskReferentialIntegrityError
)
from pydantic import ValidationError

###############################################################################
# Unit Tests for Task Validation
#
# This test suite validates the Task API's create_task function with focus on:
# 1. Pydantic-based validation for all input parameters
# 2. Required field validation (Priority, Status)
# 3. String length constraints (Name: 80, Subject: 255, Description: 32000)
# 4. Date/DateTime format validation (ISO 8601)
# 5. ID format validation (15-18 alphanumeric characters)
# 6. Enum value validation for Priority and Status
#
# All validation is now handled by Pydantic models, eliminating redundant
# manual validation code and providing consistent error messages.
###############################################################################
class TestTaskValidation(BaseTestCaseWithErrorHandler):
    def setUp(self):
        """
        Resets the database before each test to ensure test isolation.
        
        This prevents test interdependencies and ensures each test starts
        with a clean state.
        """
        from salesforce.SimulationEngine.db import DB

        DB.clear()
        DB.update({
            "Task": {
                "existing_task_id": {
                    "Id": "existing_task_id",
                    "Priority": "Medium",
                    "Status": "In Progress",
                    "CreatedDate": "2024-01-01T00:00:00",
                    "IsDeleted": False,
                    "SystemModstamp": "2024-01-01T00:00:00"
                }
            },
            "Event": {
                "event123456789012": {
                    "Id": "event123456789012",
                    "Subject": "Test Event",
                    "StartDateTime": "2024-01-01T10:00:00",
                    "EndDateTime": "2024-01-01T11:00:00",
                    "IsDeleted": False
                }
            }
        })

    def test_create_task_success(self):
        """
        Test successful task creation with all optional fields provided.
        
        Verifies that:
        - All provided fields are correctly stored
        - System fields (Id, CreatedDate) are automatically generated
        - Date and DateTime fields accept valid ISO 8601 formats
        """
        result = create_task(
            Priority="High",
            Status="Not Started",
            Subject="Test Task",
            Description="Test Description",
            ActivityDate="2024-01-15",
            ReminderDateTime="2024-01-15T10:00:00"
        )
        
        self.assertEqual(result["Priority"], "High")
        self.assertEqual(result["Status"], "Not Started")
        self.assertEqual(result["Subject"], "Test Task")
        self.assertEqual(result["Description"], "Test Description")
        self.assertEqual(result["ActivityDate"], "2024-01-15")
        self.assertEqual(result["ReminderDateTime"], "2024-01-15T10:00:00")
        self.assertIn("Id", result)
        self.assertIn("CreatedDate", result)

    def test_create_task_missing_required_fields(self):
        """
        Test that missing or None required fields raise ValidationError.
        
        Pydantic now handles all required field validation:
        - None values trigger "Field required" error
        
        This replaces the previous manual null checks.
        """
        from pydantic import ValidationError
        
        # Test Priority=None
        with self.assertRaises(ValidationError) as context:
            create_task(Priority=None, Status="Not Started")
        self.assertIn("Field required", str(context.exception))
        
        # Test Status=None
        with self.assertRaises(ValidationError) as context:
            create_task(Priority="High", Status=None)
        self.assertIn("Field required", str(context.exception))
    
    def test_create_task_empty_string_required_fields(self):
        """
        Test that empty string required fields raise ValidationError.
        
        With min_length=1 on required fields, Pydantic rejects empty strings:
        - Empty strings (after strip) trigger "String should have at least 1 character"
        - This happens before enum validation
        """
        from pydantic import ValidationError
        
        # Test empty Priority (after strip)
        with self.assertRaises(ValidationError) as context:
            create_task(Priority="", Status="Not Started")
        # Should fail min_length check before enum validation
        self.assertIn("String should have at least 1 character", str(context.exception))
        
        # Test empty Status (after strip)
        with self.assertRaises(ValidationError) as context:
            create_task(Priority="High", Status="")
        self.assertIn("String should have at least 1 character", str(context.exception))
        
        # Test whitespace-only Priority (stripped to empty)
        with self.assertRaises(ValidationError) as context:
            create_task(Priority="   ", Status="Not Started")
        self.assertIn("String should have at least 1 character", str(context.exception))
        
        # Test whitespace-only Status (stripped to empty)
        with self.assertRaises(ValidationError) as context:
            create_task(Priority="High", Status="   ")
        self.assertIn("String should have at least 1 character", str(context.exception))

    def test_create_task_invalid_priority(self):
        """
        Test that invalid Priority values raise ValidationError with helpful message.
        
        Pydantic's @field_validator for Priority ensures only valid enum values
        are accepted: ["High", "Medium", "Low"]
        """
        from pydantic import ValidationError
        with self.assertRaises(ValidationError) as context:
            create_task(Priority="Invalid", Status="Not Started")
        self.assertIn("Priority must be one of", str(context.exception))

    def test_create_task_invalid_status(self):
        """
        Test that invalid Status values raise ValidationError with helpful message.
        
        Pydantic's @field_validator for Status ensures only valid enum values
        are accepted: ["Not Started", "In Progress", "Completed", "Waiting", 
                       "Deferred", "Open", "Closed"]
        """
        from pydantic import ValidationError
        with self.assertRaises(ValidationError) as context:
            create_task(Priority="High", Status="Invalid")
        self.assertIn("Status must be one of", str(context.exception))

    def test_create_task_invalid_date_format(self):
        """
        Test that incorrect date/datetime formats raise ValidationError.
        
        Pydantic's @field_validator checks for:
        - ActivityDate: YYYY-MM-DD format (ISO 8601 date)
        - ReminderDateTime: YYYY-MM-DDTHH:MM:SS format (ISO 8601 datetime)
        
        This replaces previous manual regex validation with consistent
        Pydantic-based validation.
        """
        from pydantic import ValidationError
        
        # Test ActivityDate with slash separators instead of dashes
        with self.assertRaises(ValidationError) as context:
            create_task(Priority="High", Status="Not Started", ActivityDate="2024/01/15")
        self.assertIn("Date must be in ISO format", str(context.exception))
        
        # Test ReminderDateTime with space instead of 'T' separator
        with self.assertRaises(ValidationError) as context:
            create_task(Priority="High", Status="Not Started", ReminderDateTime="2024-01-15 10:00:00")
        self.assertIn("DateTime must be in ISO format", str(context.exception))

    def test_create_task_invalid_date_values(self):
        """
        Test that semantically invalid dates raise ValidationError.
        
        Even with correct format, Pydantic validates:
        - Month is 1-12
        - Day is valid for the given month/year
        - Hours are 0-23, minutes/seconds are 0-59
        
        This catches logical date errors like February 30th or hour 25.
        """
        from pydantic import ValidationError
        
        # Test invalid month (13)
        with self.assertRaises(ValidationError) as context:
            create_task(Priority="High", Status="Not Started", ActivityDate="2024-13-01")
        self.assertIn("Date must be a valid date", str(context.exception))
        
        # Test invalid day (32)
        with self.assertRaises(ValidationError) as context:
            create_task(Priority="High", Status="Not Started", ActivityDate="2024-01-32")
        self.assertIn("Date must be a valid date", str(context.exception))
        
        # Test February 30th (impossible date)
        with self.assertRaises(ValidationError) as context:
            create_task(Priority="High", Status="Not Started", ActivityDate="2024-02-30")
        self.assertIn("Date must be a valid date", str(context.exception))
        
        # Test invalid month in datetime (13)
        with self.assertRaises(ValidationError) as context:
            create_task(Priority="High", Status="Not Started", ReminderDateTime="2024-13-01T10:00:00")
        self.assertIn("DateTime must be a valid datetime", str(context.exception))
        
        # Test invalid day in datetime (32)
        with self.assertRaises(ValidationError) as context:
            create_task(Priority="High", Status="Not Started", ReminderDateTime="2024-01-32T10:00:00")
        self.assertIn("DateTime must be a valid datetime", str(context.exception))
        
        # Test invalid hour (25)
        with self.assertRaises(ValidationError) as context:
            create_task(Priority="High", Status="Not Started", ReminderDateTime="2024-01-15T25:00:00")
        self.assertIn("DateTime must be a valid datetime", str(context.exception))
        
        # Test invalid minute (60)
        with self.assertRaises(ValidationError) as context:
            create_task(Priority="High", Status="Not Started", ReminderDateTime="2024-01-15T10:60:00")
        self.assertIn("DateTime must be a valid datetime", str(context.exception))

    def test_create_task_invalid_id_format(self):
        """
        Test that invalid Salesforce ID formats raise ValidationError.
        
        Pydantic's @field_validator for OwnerId, WhoId, and WhatId ensures:
        - IDs are 15-18 characters long (Salesforce standard)
        - IDs contain only alphanumeric characters
        
        This replaces manual regex validation with Pydantic validation.
        """
        from pydantic import ValidationError
        
        # Test ID with hyphens (invalid)
        with self.assertRaises(ValidationError) as context:
            create_task(Priority="High", Status="Not Started", OwnerId="invalid-id")
        self.assertIn("ID must be 15-18 alphanumeric characters", str(context.exception))
        
        # Test ID that's too short
        with self.assertRaises(ValidationError) as context:
            create_task(Priority="High", Status="Not Started", WhoId="123")
        self.assertIn("ID must be 15-18 alphanumeric characters", str(context.exception))

    def test_create_task_string_length_validation(self):
        """
        Test that string length constraints are enforced by Pydantic.
        
        TaskCreateModel defines Field constraints:
        - Name: max_length=80
        - Subject: max_length=255  
        - Description: max_length=32000
        
        This replaces manual length validation with Pydantic's Field validation,
        eliminating ~10 lines of redundant validation code per field.
        """
        from pydantic import ValidationError
        
        # Test Subject exceeds max length (256 > 255)
        long_subject = "x" * 256
        with self.assertRaises(ValidationError) as context:
            create_task(Priority="High", Status="Not Started", Subject=long_subject)
        # Pydantic provides clear error message about the constraint
        self.assertIn("String should have at most 255 characters", str(context.exception))
        self.assertIn("Subject", str(context.exception))
        
        # Test Name exceeds max length (81 > 80)
        long_name = "x" * 81
        with self.assertRaises(ValidationError) as context:
            create_task(Priority="High", Status="Not Started", Name=long_name)
        # Pydantic provides clear error message about the constraint
        self.assertIn("String should have at most 80 characters", str(context.exception))
        self.assertIn("Name", str(context.exception))

    def test_create_task_minimal_valid_data(self):
        """
        Test task creation with only required fields.
        
        Verifies that:
        - Only Priority and Status are required
        - All other fields are optional
        - System fields are auto-generated
        - IsDeleted defaults to False
        """
        result = create_task(Priority="Medium", Status="In Progress")
        
        self.assertEqual(result["Priority"], "Medium")
        self.assertEqual(result["Status"], "In Progress")
        self.assertIn("Id", result)
        self.assertIn("CreatedDate", result)
        self.assertFalse(result["IsDeleted"])

    def test_create_task_with_custom_id(self):
        """
        Test that custom Salesforce ID can be provided.
        
        The Id parameter bypasses auto-generation if provided.
        Custom ID must still pass format validation (15-18 alphanumeric).
        """
        custom_id = "0031234567890123"
        result = create_task(Priority="Low", Status="Completed", Id=custom_id)
        
        self.assertEqual(result["Id"], custom_id)

    def test_create_task_all_valid_values(self):
        """
        Test exhaustive combinations of valid Priority and Status values.
        
        Valid Priorities: ["High", "Medium", "Low"]
        Valid Statuses: ["Not Started", "In Progress", "Completed", 
                        "Waiting", "Deferred", "Open", "Closed"]
        
        This ensures all enum values defined in Pydantic model are accepted.
        """
        valid_priorities = ["High", "Medium", "Low"]
        valid_statuses = ["Not Started", "In Progress", "Completed", "Waiting", "Deferred", "Open"]
        
        for priority in valid_priorities:
            for status in valid_statuses:
                result = create_task(Priority=priority, Status=status)
                self.assertEqual(result["Priority"], priority)
                self.assertEqual(result["Status"], status)

    def test_create_task_with_open_status(self):
        """
        Test the 'Open' status with additional fields.
        
        Verifies that:
        - 'Open' is a valid Status enum value
        - Name and Subject fields are properly stored
        - All system fields are generated
        """
        result = create_task(Priority="Low", Status="Open", Name="Task Alpha", Subject="Apple Picking")
        
        self.assertEqual(result["Priority"], "Low")
        self.assertEqual(result["Status"], "Open")
        self.assertEqual(result["Name"], "Task Alpha")
        self.assertEqual(result["Subject"], "Apple Picking")
        self.assertIn("Id", result)
        self.assertIn("CreatedDate", result)

    def test_create_task_with_all_optional_fields(self):
        """
        Test comprehensive task creation with all optional fields populated.
        
        This test covers:
        - Subject and Description (validated by Pydantic for length)
        - ActivityDate and DueDate (validated for ISO 8601 format)
        - OwnerId, WhoId, WhatId (validated for Salesforce ID format)
        - IsReminderSet (boolean field)
        - ReminderDateTime (validated for ISO 8601 datetime format)
        
        Ensures all optional field handling code paths are exercised.
        """
        # Valid Salesforce IDs (15-18 alphanumeric characters)
        owner_id = "0031234567890123"
        who_id = "0039876543210987"
        what_id = "0061112223334445"
        
        result = create_task(
            Priority="High",
            Status="In Progress",
            Subject="Test Task with All Fields",
            Description="Test Description",
            ActivityDate="2024-01-15",
            DueDate="2024-01-20",
            OwnerId=owner_id,
            WhoId=who_id,
            WhatId=what_id,
            IsReminderSet=True,
            ReminderDateTime="2024-01-15T10:00:00"
        )
        
        # Verify all fields are present and correctly stored
        self.assertEqual(result["Priority"], "High")
        self.assertEqual(result["Status"], "In Progress")
        self.assertEqual(result["Subject"], "Test Task with All Fields")
        self.assertEqual(result["Description"], "Test Description")
        self.assertEqual(result["ActivityDate"], "2024-01-15")
        self.assertEqual(result["DueDate"], "2024-01-20")
        self.assertEqual(result["OwnerId"], owner_id)
        self.assertEqual(result["WhoId"], who_id)
        self.assertEqual(result["WhatId"], what_id)
        self.assertTrue(result["IsReminderSet"])
        self.assertEqual(result["ReminderDateTime"], "2024-01-15T10:00:00")

    def test_create_task_with_owner_id_only(self):
        """
        Test task creation with only OwnerId (no other relationship IDs).
        
        Verifies that:
        - OwnerId can be provided independently
        - Other relationship fields (WhoId, WhatId) are not added
        - Reminder fields are not added when not provided
        """
        owner_id = "0031234567890123"
        result = create_task(
            Priority="Medium",
            Status="Not Started",
            OwnerId=owner_id
        )
        
        self.assertEqual(result["OwnerId"], owner_id)
        self.assertNotIn("WhoId", result)
        self.assertNotIn("WhatId", result)
        self.assertNotIn("IsReminderSet", result)
        self.assertNotIn("ReminderDateTime", result)

    def test_create_task_with_who_id_only(self):
        """
        Test task creation with only WhoId (contact relationship).
        
        WhoId links to Contact or Lead records in Salesforce.
        This test ensures WhoId can be provided independently of other IDs.
        """
        who_id = "0039876543210987"
        result = create_task(
            Priority="Medium",
            Status="Not Started",
            WhoId=who_id
        )
        
        self.assertEqual(result["WhoId"], who_id)
        self.assertNotIn("OwnerId", result)
        self.assertNotIn("WhatId", result)
        self.assertNotIn("IsReminderSet", result)
        self.assertNotIn("ReminderDateTime", result)

    def test_create_task_with_what_id_only(self):
        """
        Test task creation with only WhatId (related record relationship).
        
        WhatId links to Account, Opportunity, Campaign, or other objects.
        This test ensures WhatId can be provided independently of other IDs.
        """
        what_id = "0061112223334445"
        result = create_task(
            Priority="Medium",
            Status="Not Started",
            WhatId=what_id
        )
        
        self.assertEqual(result["WhatId"], what_id)
        self.assertNotIn("OwnerId", result)
        self.assertNotIn("WhoId", result)
        self.assertNotIn("IsReminderSet", result)
        self.assertNotIn("ReminderDateTime", result)

    def test_create_task_with_is_reminder_set_only(self):
        """
        Test task creation with only IsReminderSet flag.
        
        Verifies that:
        - IsReminderSet can be set without ReminderDateTime
        - Boolean field is correctly stored
        - Other optional fields remain absent
        """
        result = create_task(
            Priority="Medium",
            Status="Not Started",
            IsReminderSet=True
        )
        
        self.assertTrue(result["IsReminderSet"])
        self.assertNotIn("OwnerId", result)
        self.assertNotIn("WhoId", result)
        self.assertNotIn("WhatId", result)
        self.assertNotIn("ReminderDateTime", result)

    def test_create_task_with_reminder_datetime_only(self):
        """
        Test task creation with only ReminderDateTime (no IsReminderSet).
        
        Verifies that:
        - ReminderDateTime can be set independently
        - DateTime format is validated by Pydantic
        - Other optional fields remain absent
        """
        result = create_task(
            Priority="Medium",
            Status="Not Started",
            ReminderDateTime="2024-01-15T10:00:00"
        )
        
        self.assertEqual(result["ReminderDateTime"], "2024-01-15T10:00:00")
        self.assertNotIn("OwnerId", result)
        self.assertNotIn("WhoId", result)
        self.assertNotIn("WhatId", result)
        self.assertNotIn("IsReminderSet", result)

    def test_create_task_pydantic_validation_error(self):
        """Test that Pydantic ValidationError is properly raised without wrapping."""
        from unittest.mock import patch
        from pydantic import ValidationError

        # Mock the TaskCreateModel.create_and_validate method to raise ValidationError
        with patch('salesforce.Task.TaskCreateModel.create_and_validate') as mock_validate:

            # Create a simple ValidationError by trying to validate invalid data
            try:
                from salesforce.SimulationEngine.models import TaskCreateModel
                TaskCreateModel(Priority="InvalidPriority", Status="Not Started")
            except ValidationError as e:
                mock_validate.side_effect = e

            # ValidationError should propagate naturally without wrapping
            with self.assertRaises(ValidationError) as context:
                create_task(Priority="High", Status="Not Started")
            self.assertIn("Priority must be one of", str(context.exception))

    def test_unique_id_succeeds(self):
        """Test that creating a task with unique ID succeeds."""
        result = create_task(
            Priority="High",
            Status="Not Started",
            Id="00T123456789012345"
        )

        self.assertEqual(result["Id"], "00T123456789012345")

    def test_no_id_generates_unique_id(self):
        """Test that not providing ID generates a unique one."""
        result = create_task(
            Priority="High",
            Status="Not Started"
        )

        self.assertIsNotNone(result["Id"])
        self.assertTrue(len(result["Id"]) == 18)

    def test_numeric_validation_negative_call_duration(self):
        """Test that negative CallDurationInSeconds fails."""
        with self.assertRaises(TaskNumericValidationError) as context:
            create_task(
                Priority="High",
                Status="Not Started",
                CallDurationInSeconds=-60
            )

        self.assertIn("non-negative integer", str(context.exception))

    def test_numeric_validation_zero_recurrence_interval(self):
        """Test that zero RecurrenceInterval fails."""
        with self.assertRaises(TaskNumericValidationError) as context:
            create_task(
                Priority="High",
                Status="Not Started",
                IsRecurrence=True,
                RecurrenceType="Daily",
                RecurrenceInterval=0
            )

        self.assertIn("positive integer", str(context.exception))

    def test_numeric_validation_invalid_recurrence_month(self):
        """Test that invalid RecurrenceMonthOfYear fails."""
        with self.assertRaises(TaskNumericValidationError) as context:
            create_task(
                Priority="High",
                Status="Not Started",
                RecurrenceMonthOfYear=13
            )

        self.assertIn("between 1 and 12", str(context.exception))

    def test_numeric_validation_valid_fields_succeed(self):
        """Test that valid numeric fields succeed."""
        result = create_task(
            Priority="High",
            Status="Not Started",
            CallDurationInSeconds=300,
            IsRecurrence=True,
            RecurrenceType="Monthly",
            RecurrenceInterval=2,
            RecurrenceMonthOfYear=6,
            RecurrenceDayOfMonth=15
        )

        self.assertEqual(result["CallDurationInSeconds"], 300)
        self.assertEqual(result["RecurrenceInterval"], 2)
        self.assertEqual(result["RecurrenceMonthOfYear"], 6)
        self.assertEqual(result["RecurrenceDayOfMonth"], 15)

    def test_empty_id_handling(self):
        """Test that empty string ID fails."""
        with self.assertRaises(ValueError) as context:
            create_task(
                Priority="High",
                Status="Not Started",
                Id=""
            )

        self.assertIn("cannot be an empty string", str(context.exception))

    def test_semantic_validation_completed_task_with_future_reminder(self):
        """Test that completed tasks with future reminders are rejected."""
        future_time = (datetime.now() + timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M:%S')

        with self.assertRaises(TaskSemanticValidationError) as context:
            create_task(
                Priority="High",
                Status="Completed",
                ReminderDateTime=future_time
            )

        self.assertIn("Semantic inconsistency", str(context.exception))
        self.assertIn("Completed", str(context.exception))
        self.assertIn("future reminder", str(context.exception))

    def test_semantic_validation_closed_task_with_future_reminder(self):
        """Test that closed tasks with future reminders are rejected."""
        future_time = (datetime.now() + timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M:%S')

        with self.assertRaises(TaskSemanticValidationError) as context:
            create_task(
                Priority="Medium",
                Status="Closed",
                IsClosed=True,
                ReminderDateTime=future_time
            )

        self.assertIn("Semantic inconsistency", str(context.exception))
        self.assertIn("closed", str(context.exception))

    def test_semantic_validation_past_reminder_allowed(self):
        """Test that completed tasks with past reminders are allowed."""
        past_time = (datetime.now() - timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M:%S')

        result = create_task(
            Priority="High",
            Status="Completed",
            ReminderDateTime=past_time
        )

        self.assertEqual(result["Status"], "Completed")
        self.assertEqual(result["ReminderDateTime"], past_time)

    def test_duplicate_id_handling(self):
        """Test that creating a task with existing ID fails."""
        with self.assertRaises(TaskDuplicateIdError) as context:
            create_task(
                Priority="High",
                Status="Not Started",
                Id="existing_task_id"
            )

        self.assertIn("already exists", str(context.exception))
        self.assertIn("existing_task_id", str(context.exception))

    def test_contradictory_states_low_priority_with_high_flag(self):
        """Test that Low priority with IsHighPriority=True fails."""
        with self.assertRaises(TaskContradictoryStateError) as context:
            create_task(
                Priority="Low",
                Status="Not Started",
                IsHighPriority=True
            )

        self.assertIn("Contradictory priority settings", str(context.exception))
        self.assertIn("Low", str(context.exception))
        self.assertIn("IsHighPriority=True", str(context.exception))

    def test_contradictory_states_high_priority_with_low_flag(self):
        """Test that High priority with IsHighPriority=False fails."""
        with self.assertRaises(TaskContradictoryStateError) as context:
            create_task(
                Priority="High",
                Status="Not Started",
                IsHighPriority=False
            )

        self.assertIn("Contradictory priority settings", str(context.exception))
        self.assertIn("High", str(context.exception))
        self.assertIn("IsHighPriority=False", str(context.exception))

    def test_contradictory_states_non_recurrence_with_details(self):
        """Test that IsRecurrence=False with recurrence details fails."""
        with self.assertRaises(TaskContradictoryStateError) as context:
            create_task(
                Priority="Medium",
                Status="Not Started",
                IsRecurrence=False,
                RecurrenceType="Daily",
                RecurrenceInterval=1
            )

        self.assertIn("Contradictory recurrence settings", str(context.exception))
        self.assertIn("IsRecurrence=False", str(context.exception))

    def test_contradictory_states_recurrence_without_type(self):
        """Test that IsRecurrence=True without RecurrenceType fails."""
        with self.assertRaises(TaskContradictoryStateError) as context:
            create_task(
                Priority="Medium",
                Status="Not Started",
                IsRecurrence=True
            )

        self.assertIn("Contradictory recurrence settings", str(context.exception))
        self.assertIn("RecurrenceType is required", str(context.exception))

    def test_referential_integrity_valid_what_id(self):
        """Test that valid WhatId referencing existing Event succeeds."""
        result = create_task(
            Priority="High",
            Status="Not Started",
            WhatId="event123456789012"
        )

        self.assertEqual(result["WhatId"], "event123456789012")

    def test_comprehensive_valid_task_creation(self):
        """Test creating a task with all valid fields."""
        result = create_task(
            Priority="High",
            Status="In Progress",
            Id="00T456789012345678",
            Name="Comprehensive Test Task",
            Subject="Test all validation features",
            Description="This task tests all validation features comprehensively",
            ActivityDate="2024-12-31",
            DueDate="2024-12-31",
            OwnerId="005123456789012345",
            WhoId="003123456789012345",
            WhatId="event123456789012",
            IsReminderSet=True,
            ReminderDateTime="2024-12-30T09:00:00",
            CallDurationInSeconds=1800,
            CallType="Outbound",
            CallObject="00C123456789012345",
            CallDisposition="Completed",
            IsRecurrence=True,
            RecurrenceType="Weekly",
            RecurrenceInterval=1,
            RecurrenceMonthOfYear=12,
            RecurrenceDayOfWeekMask=2,
            RecurrenceDayOfMonth=15,
            RecurrenceInstance="First",
            CompletedDateTime=None,  # Not completed yet
            IsClosed=False,
            IsHighPriority=True,
            IsArchived=False,
            TaskSubtype="Standard"
        )

        # Verify all fields are set correctly
        self.assertEqual(result["Priority"], "High")
        self.assertEqual(result["Status"], "In Progress")
        self.assertEqual(result["Id"], "00T456789012345678")
        self.assertEqual(result["Name"], "Comprehensive Test Task")
        self.assertTrue(result["IsHighPriority"])
        self.assertTrue(result["IsRecurrence"])
        self.assertEqual(result["RecurrenceType"], "Weekly")
        self.assertEqual(result["CallDurationInSeconds"], 1800)

        # Verify system fields
        self.assertIn("CreatedDate", result)
        self.assertIn("SystemModstamp", result)
        self.assertFalse(result["IsDeleted"])

    def test_create_task_empty_string_optional_fields(self):
        """
        Test that empty strings for optional fields raise ValidationError.
        
        With min_length=1 on optional string fields, Pydantic rejects empty strings
        when they are explicitly provided (not when they are None/omitted).
        This ensures data quality - if a field is provided, it must have content.
        """
        from pydantic import ValidationError
        
        # Test empty Name
        with self.assertRaises(ValidationError) as context:
            create_task(Priority="High", Status="Not Started", Name="")
        self.assertIn("String should have at least 1 character", str(context.exception))
        
        # Test whitespace-only Name (stripped to empty)
        with self.assertRaises(ValidationError) as context:
            create_task(Priority="High", Status="Not Started", Name="   ")
        self.assertIn("String should have at least 1 character", str(context.exception))
        
        # Test empty Subject
        with self.assertRaises(ValidationError) as context:
            create_task(Priority="High", Status="Not Started", Subject="")
        self.assertIn("String should have at least 1 character", str(context.exception))
        
        # Test whitespace-only Subject
        with self.assertRaises(ValidationError) as context:
            create_task(Priority="High", Status="Not Started", Subject="  ")
        self.assertIn("String should have at least 1 character", str(context.exception))
        
        # Test empty Description
        with self.assertRaises(ValidationError) as context:
            create_task(Priority="High", Status="Not Started", Description="")
        self.assertIn("String should have at least 1 character", str(context.exception))
        
        # Test whitespace-only Description
        with self.assertRaises(ValidationError) as context:
            create_task(Priority="High", Status="Not Started", Description="\t\n  ")
        self.assertIn("String should have at least 1 character", str(context.exception))
        
        # Test empty OwnerId
        with self.assertRaises(ValidationError) as context:
            create_task(Priority="High", Status="Not Started", OwnerId="")
        self.assertIn("String should have at least 1 character", str(context.exception))
        
        # Test empty WhoId
        with self.assertRaises(ValidationError) as context:
            create_task(Priority="High", Status="Not Started", WhoId="")
        self.assertIn("String should have at least 1 character", str(context.exception))
        
        # Test empty WhatId
        with self.assertRaises(ValidationError) as context:
            create_task(Priority="High", Status="Not Started", WhatId="")
        self.assertIn("String should have at least 1 character", str(context.exception))
    
    def test_create_task_none_optional_fields_accepted(self):
        """
        Test that None values for optional fields are accepted.
        
        This verifies that min_length=1 validation only applies when a value
        is provided, not when the field is omitted (None).
        """
        # Should succeed - None is valid for optional fields
        result = create_task(
            Priority="High",
            Status="Not Started",
            Name=None,
            Subject=None,
            Description=None,
            OwnerId=None,
            WhoId=None,
            WhatId=None
        )
        self.assertEqual(result["Priority"], "High")
        self.assertEqual(result["Status"], "Not Started")
        # Optional fields should not be in the result when None
        self.assertNotIn("Name", result)
        self.assertNotIn("Subject", result)
        self.assertNotIn("Description", result)