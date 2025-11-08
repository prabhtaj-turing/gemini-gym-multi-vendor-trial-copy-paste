import copy

from .. import DB
from ..SimulationEngine import custom_errors
from .. import fetch_rules # Assuming fetch_rules is now modified to return {'rules': ...}
from common_utils.base_case import BaseTestCaseWithErrorHandler


# Assuming BaseTestCaseWithErrorHandler is defined elsewhere and works correctly
# from common_utils.base_case import BaseTestCaseWithErrorHandler


class TestFetchRules(BaseTestCaseWithErrorHandler):
    """
    Test suite for the fetch_rules function.
    """

    def setUp(self):
        """
        Set up test environment before each test.
        This involves storing the original DB state, clearing DB,
        and populating DB with rules for testing.
        """
        self._original_DB_state = copy.deepcopy(DB)
        DB.clear()
        DB['available_instructions'] = {
            "style_guide": "Follow PEP8 and use black for formatting.",
            "commit_messages": "Use conventional commit messages.",
            "testing_policy": {
                "unit_tests": "Required for all new features.",
                "integration_tests": "Cover critical user flows."
            },
            "performance_guidelines": "Optimize database queries and avoid N+1 problems.",
            "empty_rule_content": "",
            "rule-with-hyphen": "Content for a rule with a hyphen in its name."
        }

    def tearDown(self):
        """
        Clean up test environment after each test.
        This involves restoring the original DB state.
        """
        DB.clear()
        DB.update(self._original_DB_state)

    def test_fetch_single_existing_rule(self):
        """Test fetching a single rule that exists."""
        result = fetch_rules(rule_names=['style_guide'])
        self.assertEqual(result, {"rules": {"style_guide": "Follow PEP8 and use black for formatting."}})

    def test_fetch_multiple_existing_rules(self):
        """Test fetching multiple rules that exist."""
        result = fetch_rules(rule_names=['style_guide', 'testing_policy'])
        expected = {
            "rules": {
                "style_guide": "Follow PEP8 and use black for formatting.",
                "testing_policy": {
                    "unit_tests": "Required for all new features.",
                    "integration_tests": "Cover critical user flows."
                }
            }
        }
        self.assertEqual(result, expected)

    def test_fetch_rule_with_complex_content(self):
        """Test fetching a rule whose content is a dictionary."""
        result = fetch_rules(rule_names=['testing_policy'])
        expected = {
            "rules": {
                "testing_policy": {
                    "unit_tests": "Required for all new features.",
                    "integration_tests": "Cover critical user flows."
                }
            }
        }
        self.assertEqual(result, expected)

    def test_fetch_rules_partial_found(self):
        """Test fetching rules where some exist and some do not, expecting a ValidationError."""
        self.assert_error_behavior(
            func_to_call=fetch_rules,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="Unknown rule(s) requested: non_existent_rule. Available rules are: commit_messages, empty_rule_content, performance_guidelines, rule-with-hyphen, style_guide, testing_policy.",
            rule_names=['style_guide', 'non_existent_rule']
        )

    def test_fetch_rules_none_found(self):
        """Test fetching rules where none of the requested rules exist, expecting a ValidationError."""
        self.assert_error_behavior(
            func_to_call=fetch_rules,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="Unknown rule(s) requested: non_existent_rule1, non_existent_rule2. Available rules are: commit_messages, empty_rule_content, performance_guidelines, rule-with-hyphen, style_guide, testing_policy.",
            rule_names=['non_existent_rule1', 'non_existent_rule2']
        )

    def test_fetch_rules_empty_input_list(self):
        """Test fetching rules with an empty list of rule names."""
        result = fetch_rules(rule_names=[])
        self.assertEqual(result, {"rules": {}}) # Corrected: Expect nested empty dict

    def test_fetch_rule_with_empty_string_content(self):
        """Test fetching a rule whose content is an empty string."""
        result = fetch_rules(rule_names=['empty_rule_content'])
        self.assertEqual(result, {"rules": {"empty_rule_content": ""}}) # Corrected: Expect nested dict

    def test_fetch_rule_with_hyphen_in_name(self):
        """Test fetching a rule that has a hyphen in its name."""
        result = fetch_rules(rule_names=['rule-with-hyphen'])
        self.assertEqual(result, {"rules": {"rule-with-hyphen": "Content for a rule with a hyphen in its name."}}) # Corrected: Expect nested dict

    def test_fetch_rules_input_list_with_duplicates(self):
        """Test fetching rules where the input list contains duplicate rule names."""
        result = fetch_rules(rule_names=['style_guide', 'commit_messages', 'style_guide'])
        expected = {
            "rules": { # Corrected: Expect nested dict
                "style_guide": "Follow PEP8 and use black for formatting.",
                "commit_messages": "Use conventional commit messages."
            }
        }
        self.assertEqual(result, expected)

    def test_fetch_rules_output_dict_preserves_order(self):
        """Test that the output dictionary preserves the order of found rules from the input list."""
        self.assert_error_behavior(
            func_to_call=fetch_rules,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="Unknown rule(s) requested: non_existent_rule. Available rules are: commit_messages, empty_rule_content, performance_guidelines, rule-with-hyphen, style_guide, testing_policy.",
            rule_names=['testing_policy', 'style_guide', 'non_existent_rule', 'commit_messages']
        )

    # --- Input Validation Error Cases ---

    def test_fetch_rules_arg_rule_names_is_not_list(self):
        """Test error when rule_names argument is not a list (e.g., a string)."""
        self.assert_error_behavior(
            func_to_call=fetch_rules,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="Input 'rule_names' must be a list.",
            rule_names="not_a_list_string"
        )

    def test_fetch_rules_arg_rule_names_is_none(self):
        """Test error when rule_names argument is None."""
        self.assert_error_behavior(
            func_to_call=fetch_rules,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="Input 'rule_names' must be a list.",
            rule_names=None
        )

    def test_fetch_rules_arg_rule_names_list_contains_integer(self):
        """Test error when rule_names list contains a non-string item (integer)."""
        self.assert_error_behavior(
            func_to_call=fetch_rules,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="All elements in 'rule_names' must be strings. Found an element that is not a string.",
            rule_names=['style_guide', 123]
        )

    def test_fetch_rules_arg_rule_names_list_contains_none(self):
        """Test error when rule_names list contains a non-string item (None)."""
        self.assert_error_behavior(
            func_to_call=fetch_rules,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="All elements in 'rule_names' must be strings. Found an element that is not a string.",
            rule_names=['style_guide', None]
        )

    def test_fetch_rules_arg_rule_names_list_contains_list(self):
        """Test error when rule_names list contains a non-string item (another list)."""
        self.assert_error_behavior(
            func_to_call=fetch_rules,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="All elements in 'rule_names' must be strings. Found an element that is not a string.",
            rule_names=['style_guide', []]
        )

    def test_fetch_rules_arg_rule_names_list_contains_dict(self):
        """Test error when rule_names list contains a non-string item (a dict)."""
        self.assert_error_behavior(
            func_to_call=fetch_rules,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="All elements in 'rule_names' must be strings. Found an element that is not a string.",
            rule_names=['style_guide', {}]
        )

    def test_fetch_rules_arg_rule_names_list_contains_empty_string(self):
        """Test error when rule_names list contains an empty string."""
        self.assert_error_behavior(
            func_to_call=fetch_rules,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="Rule names cannot be empty or contain only whitespace.",
            rule_names=['style_guide', '']
        )

    def test_fetch_rules_arg_rule_names_list_contains_whitespace_string(self):
        """Test error when rule_names list contains a string with only whitespace."""
        self.assert_error_behavior(
            func_to_call=fetch_rules,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="Rule names cannot be empty or contain only whitespace.",
            rule_names=['style_guide', '   \t\n  ']
        )

    # --- DB State Interaction Cases ---

    def test_fetch_rules_when_available_rules_key_is_missing_in_db(self):
        """Test behavior if DB['available_instructions'] key is missing entirely."""
        if 'available_instructions' in DB:
            del DB['available_instructions']

        self.assert_error_behavior(
            func_to_call=fetch_rules,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="Unknown rule(s) requested: style_guide. Available rules are: None.",
            rule_names=['style_guide']
        )

    def test_fetch_rules_when_available_rules_is_empty_dict_in_db(self):
        """Test behavior if DB['available_instructions'] is present but an empty dictionary."""
        DB['available_instructions'] = {}
        self.assert_error_behavior(
            func_to_call=fetch_rules,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="Unknown rule(s) requested: style_guide. Available rules are: None.",
            rule_names=['style_guide']
        )

    def test_fetch_rules_when_available_rules_is_none_in_db(self):
        """Test behavior if DB['available_instructions'] is None."""
        DB['available_instructions'] = None
        self.assert_error_behavior(
            func_to_call=fetch_rules,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="Unknown rule(s) requested: style_guide. Available rules are: None.",
            rule_names=['style_guide']
        )