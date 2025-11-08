"""
Test cases for counter-based retry logic implementation.
Tests the DI compliance for retry mechanisms with fallback states.
"""

import sys
import os
import unittest
from datetime import datetime
from unittest.mock import patch

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common_utils.base_case import BaseTestCaseWithErrorHandler
from ces_flights.SimulationEngine.utils import (
    RetryCounter, 
    ConversationStateManager, 
    validate_retry_logic,
    create_conversation_state_manager
)
from ces_flights.SimulationEngine.custom_errors import ValidationError


class TestRetryCounter(BaseTestCaseWithErrorHandler):
    """Test the RetryCounter class functionality."""
    
    def setUp(self):
        """Set up mocks to prevent DB writes."""
        self.save_patcher = patch('SimulationEngine.db._save_state_to_file')
        self.mock_save = self.save_patcher.start()
    
    def tearDown(self):
        """Clean up mocks."""
        self.save_patcher.stop()
    
    def test_retry_counter_initialization(self):
        """Test retry counter initializes with empty counters."""
        counter = RetryCounter()
        self.assertEqual(counter.counters, {})
        self.assertEqual(counter.max_retries, 2)
    
    def test_increment_counter(self):
        """Test counter increment functionality."""
        counter = RetryCounter()
        
        # First increment
        count = counter.increment_counter("test_action")
        self.assertEqual(count, 1)
        self.assertEqual(counter.get_counter("test_action"), 1)
        
        # Second increment
        count = counter.increment_counter("test_action")
        self.assertEqual(count, 2)
        self.assertEqual(counter.get_counter("test_action"), 2)
    
    def test_multiple_counters(self):
        """Test multiple independent counters."""
        counter = RetryCounter()
        
        counter.increment_counter("action1")
        counter.increment_counter("action2")
        counter.increment_counter("action1")
        
        self.assertEqual(counter.get_counter("action1"), 2)
        self.assertEqual(counter.get_counter("action2"), 1)
        self.assertEqual(counter.get_counter("action3"), 0)
    
    def test_reset_counter(self):
        """Test counter reset functionality."""
        counter = RetryCounter()
        
        counter.increment_counter("test_action")
        counter.increment_counter("test_action")
        self.assertEqual(counter.get_counter("test_action"), 2)
        
        counter.reset_counter("test_action")
        self.assertEqual(counter.get_counter("test_action"), 0)
    
    def test_max_retries_check(self):
        """Test max retries exceeded check."""
        counter = RetryCounter()
        
        # Within limit
        counter.increment_counter("test_action")
        counter.increment_counter("test_action")
        self.assertFalse(counter.has_exceeded_max_retries("test_action", 2))
        
        # Exceeded limit
        counter.increment_counter("test_action")
        self.assertTrue(counter.has_exceeded_max_retries("test_action", 2))
    
    def test_should_fallback(self):
        """Test fallback decision logic."""
        counter = RetryCounter()
        
        # Should not fallback
        counter.increment_counter("test_action")
        self.assertFalse(counter.should_fallback("test_action", 2))
        
        # Should fallback
        counter.increment_counter("test_action")
        counter.increment_counter("test_action")
        self.assertTrue(counter.should_fallback("test_action", 2))


class TestConversationStateManager(BaseTestCaseWithErrorHandler):
    """Test the ConversationStateManager class functionality."""
    
    def setUp(self):
        """Set up mocks to prevent DB writes."""
        self.save_patcher = patch('SimulationEngine.db._save_state_to_file')
        self.mock_save = self.save_patcher.start()
    
    def tearDown(self):
        """Clean up mocks."""
        self.save_patcher.stop()
    
    def test_state_manager_initialization(self):
        """Test state manager initializes with default values."""
        manager = ConversationStateManager()
        
        self.assertEqual(manager.current_state, "main")
        self.assertEqual(manager.env_vars, {})
        self.assertEqual(manager.conversation_history, [])
        self.assertIsNotNone(manager.session_id)
    
    def test_custom_session_id(self):
        """Test state manager with custom session ID."""
        custom_id = "test_session_123"
        manager = ConversationStateManager(session_id=custom_id)
        
        self.assertEqual(manager.session_id, custom_id)
    
    def test_state_transition(self):
        """Test state transition functionality."""
        manager = ConversationStateManager()
        
        manager.transition_to("collect_origin", "User wants to book flight")
        
        self.assertEqual(manager.current_state, "collect_origin")
        self.assertEqual(len(manager.conversation_history), 1)
        
        transition_log = manager.conversation_history[0]
        self.assertEqual(transition_log["from_state"], "main")
        self.assertEqual(transition_log["to_state"], "collect_origin")
        self.assertEqual(transition_log["reason"], "User wants to book flight")
    
    def test_env_var_management(self):
        """Test environment variable management."""
        manager = ConversationStateManager()
        
        manager.update_env_var("origin", "New York, NY")
        manager.update_env_var("destination", "Los Angeles, CA")
        
        self.assertEqual(manager.get_env_var("origin"), "New York, NY")
        self.assertEqual(manager.get_env_var("destination"), "Los Angeles, CA")
        self.assertEqual(manager.get_env_var("nonexistent", "default"), "default")
    
    def test_retry_logic_within_limits(self):
        """Test retry logic when within retry limits."""
        manager = ConversationStateManager()
        
        # First attempt
        should_continue, next_state = manager.handle_retry_logic("collect_origin", 2, "escalate")
        self.assertTrue(should_continue)
        self.assertEqual(next_state, "main")
        self.assertEqual(manager.get_retry_count("collect_origin"), 1)
        
        # Second attempt
        should_continue, next_state = manager.handle_retry_logic("collect_origin", 2, "escalate")
        self.assertTrue(should_continue)
        self.assertEqual(next_state, "main")
        self.assertEqual(manager.get_retry_count("collect_origin"), 2)
    
    def test_retry_logic_exceeds_limits(self):
        """Test retry logic when exceeding retry limits."""
        manager = ConversationStateManager()
        
        # First two attempts (within limit)
        manager.handle_retry_logic("collect_origin", 2, "escalate")
        manager.handle_retry_logic("collect_origin", 2, "escalate")
        
        # Third attempt (exceeds limit)
        should_continue, next_state = manager.handle_retry_logic("collect_origin", 2, "escalate")
        self.assertFalse(should_continue)
        self.assertEqual(next_state, "escalate")
        self.assertEqual(manager.current_state, "escalate")
        self.assertEqual(manager.get_retry_count("collect_origin"), 0)  # Reset after fallback
    
    def test_retry_counter_reset_on_success(self):
        """Test retry counter reset on successful completion."""
        manager = ConversationStateManager()
        
        # Increment counter
        manager.handle_retry_logic("collect_origin", 2, "escalate")
        self.assertEqual(manager.get_retry_count("collect_origin"), 1)
        
        # Reset on success
        manager.reset_retry_counter("collect_origin")
        self.assertEqual(manager.get_retry_count("collect_origin"), 0)
    
    def test_is_first_attempt(self):
        """Test first attempt detection."""
        manager = ConversationStateManager()
        
        self.assertFalse(manager.is_first_attempt("new_action"))  # No attempts yet
        
        manager.handle_retry_logic("new_action", 2, "escalate")
        self.assertTrue(manager.is_first_attempt("new_action"))
        
        manager.handle_retry_logic("new_action", 2, "escalate")
        self.assertFalse(manager.is_first_attempt("new_action"))
    
    def test_conversation_context(self):
        """Test conversation context retrieval."""
        manager = ConversationStateManager()
        
        manager.update_env_var("origin", "New York, NY")
        manager.transition_to("collect_destination", "Moving to next step")
        manager.handle_retry_logic("test_action", 2, "escalate")
        
        context = manager.get_conversation_context()
        
        self.assertEqual(context["current_state"], "collect_destination")
        self.assertEqual(context["env_vars"]["origin"], "New York, NY")
        self.assertEqual(context["retry_counts"]["test_action"], 1)
        self.assertEqual(len(context["conversation_history"]), 1)


class TestValidateRetryLogic(BaseTestCaseWithErrorHandler):
    """Test the validate_retry_logic function."""
    
    def setUp(self):
        """Set up mocks to prevent DB writes."""
        self.save_patcher = patch('SimulationEngine.db._save_state_to_file')
        self.mock_save = self.save_patcher.start()
    
    def tearDown(self):
        """Clean up mocks."""
        self.save_patcher.stop()
    
    def test_validate_retry_logic_within_limits(self):
        """Test retry validation when within limits."""
        manager = ConversationStateManager()
        
        should_continue, next_state = validate_retry_logic("test_action", manager, 2, "escalate")
        
        self.assertTrue(should_continue)
        self.assertEqual(next_state, "main")
        self.assertEqual(manager.get_retry_count("test_action"), 1)
    
    def test_validate_retry_logic_exceeds_limits(self):
        """Test retry validation when exceeding limits."""
        manager = ConversationStateManager()
        
        # Exceed retry limit
        validate_retry_logic("test_action", manager, 2, "escalate")
        validate_retry_logic("test_action", manager, 2, "escalate")
        should_continue, next_state = validate_retry_logic("test_action", manager, 2, "escalate")
        
        self.assertFalse(should_continue)
        self.assertEqual(next_state, "escalate")
        self.assertEqual(manager.current_state, "escalate")
    
    def test_validate_retry_logic_custom_fallback(self):
        """Test retry validation with custom fallback state."""
        manager = ConversationStateManager()
        
        # Exceed retry limit with custom fallback
        validate_retry_logic("test_action", manager, 1, "fail")
        should_continue, next_state = validate_retry_logic("test_action", manager, 1, "fail")
        
        self.assertFalse(should_continue)
        self.assertEqual(next_state, "fail")
        self.assertEqual(manager.current_state, "fail")


class TestCreateConversationStateManager(BaseTestCaseWithErrorHandler):
    """Test the create_conversation_state_manager function."""
    
    def setUp(self):
        """Set up mocks to prevent DB writes."""
        self.save_patcher = patch('SimulationEngine.db._save_state_to_file')
        self.mock_save = self.save_patcher.start()
    
    def tearDown(self):
        """Clean up mocks."""
        self.save_patcher.stop()
    
    def test_create_state_manager(self):
        """Test creating a new state manager."""
        manager = create_conversation_state_manager()
        
        self.assertIsInstance(manager, ConversationStateManager)
        self.assertEqual(manager.current_state, "main")
        self.assertIsNotNone(manager.session_id)


class TestRetryLogicIntegration(BaseTestCaseWithErrorHandler):
    """Integration tests for retry logic with DI scenarios."""
    
    def setUp(self):
        """Set up mocks to prevent DB writes."""
        self.save_patcher = patch('SimulationEngine.db._save_state_to_file')
        self.mock_save = self.save_patcher.start()
    
    def tearDown(self):
        """Clean up mocks."""
        self.save_patcher.stop()
    
    def test_di_retry_pattern_origin_collection(self):
        """Test DI retry pattern for origin city collection."""
        manager = ConversationStateManager()
        
        # Simulate failed attempts to collect origin
        should_continue, _ = manager.handle_retry_logic("collect_origin", 2, "escalate_to_agent")
        self.assertTrue(should_continue)
        self.assertEqual(manager.get_retry_count("collect_origin"), 1)
        
        should_continue, _ = manager.handle_retry_logic("collect_origin", 2, "escalate_to_agent")
        self.assertTrue(should_continue)
        self.assertEqual(manager.get_retry_count("collect_origin"), 2)
        
        # Third attempt should trigger escalation
        should_continue, next_state = manager.handle_retry_logic("collect_origin", 2, "escalate_to_agent")
        self.assertFalse(should_continue)
        self.assertEqual(next_state, "escalate_to_agent")
        self.assertEqual(manager.current_state, "escalate_to_agent")
    
    def test_di_retry_pattern_destination_collection(self):
        """Test DI retry pattern for destination city collection."""
        manager = ConversationStateManager()
        
        # Simulate failed attempts to collect destination
        for i in range(2):
            should_continue, _ = manager.handle_retry_logic("collect_destination", 2, "escalate_to_agent")
            self.assertTrue(should_continue)
        
        # Third attempt should trigger escalation
        should_continue, next_state = manager.handle_retry_logic("collect_destination", 2, "escalate_to_agent")
        self.assertFalse(should_continue)
        self.assertEqual(next_state, "escalate_to_agent")
    
    def test_di_retry_pattern_date_collection(self):
        """Test DI retry pattern for date collection."""
        manager = ConversationStateManager()
        
        # Simulate failed attempts to collect dates
        for i in range(2):
            should_continue, _ = manager.handle_retry_logic("collect_dates", 2, "escalate_to_agent")
            self.assertTrue(should_continue)
        
        # Third attempt should trigger escalation
        should_continue, next_state = manager.handle_retry_logic("collect_dates", 2, "escalate_to_agent")
        self.assertFalse(should_continue)
        self.assertEqual(next_state, "escalate_to_agent")
    
    def test_di_retry_pattern_passenger_collection(self):
        """Test DI retry pattern for passenger count collection."""
        manager = ConversationStateManager()
        
        # Simulate failed attempts to collect passenger info
        for i in range(2):
            should_continue, _ = manager.handle_retry_logic("collect_passengers", 2, "escalate_to_agent")
            self.assertTrue(should_continue)
        
        # Third attempt should trigger escalation
        should_continue, next_state = manager.handle_retry_logic("collect_passengers", 2, "escalate_to_agent")
        self.assertFalse(should_continue)
        self.assertEqual(next_state, "escalate_to_agent")
    
    def test_multiple_retry_actions_independence(self):
        """Test that multiple retry actions are independent."""
        manager = ConversationStateManager()
        
        # Test different actions independently
        manager.handle_retry_logic("collect_origin", 2, "escalate")
        manager.handle_retry_logic("collect_destination", 2, "escalate")
        manager.handle_retry_logic("collect_origin", 2, "escalate")
        
        self.assertEqual(manager.get_retry_count("collect_origin"), 2)
        self.assertEqual(manager.get_retry_count("collect_destination"), 1)
        
        # Reset one action
        manager.reset_retry_counter("collect_origin")
        self.assertEqual(manager.get_retry_count("collect_origin"), 0)
        self.assertEqual(manager.get_retry_count("collect_destination"), 1)  # Unchanged
    
    def test_retry_logic_with_state_transitions(self):
        """Test retry logic combined with state transitions."""
        manager = ConversationStateManager()
        
        # Start in main state
        self.assertEqual(manager.current_state, "main")
        
        # Transition to collect_origin and test retry
        manager.transition_to("collect_origin", "Starting origin collection")
        should_continue, _ = manager.handle_retry_logic("collect_origin", 2, "escalate")
        
        self.assertEqual(manager.current_state, "collect_origin")
        self.assertTrue(should_continue)
        
        # Exceed retry limit and test fallback
        manager.handle_retry_logic("collect_origin", 2, "escalate")
        should_continue, next_state = manager.handle_retry_logic("collect_origin", 2, "escalate")
        
        self.assertFalse(should_continue)
        self.assertEqual(next_state, "escalate")
        self.assertEqual(manager.current_state, "escalate")


if __name__ == "__main__":
    unittest.main()