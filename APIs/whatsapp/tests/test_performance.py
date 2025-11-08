import unittest
import time
import psutil
import os
import gc
import tempfile
import threading
import concurrent.futures
from unittest.mock import patch, mock_open

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from common_utils.base_case import BaseTestCaseWithErrorHandler
from ..SimulationEngine.db import DB
from .. import (get_chat, 
                get_last_interaction, 
                get_message_context, 
                list_chats, 
                list_messages, 
                search_contacts, 
                send_file, 
                send_message)

class TestWhatsAppPerformance(BaseTestCaseWithErrorHandler):
    """Performance tests for WhatsApp API operations."""

    def setUp(self):
        """Set up test environment with performance monitoring."""
        super().setUp()
        self.process = psutil.Process(os.getpid())
        
        # Set up test data
        self.test_contact = '1111111111@s.whatsapp.net'
        self.test_group = '2222222222@g.us'
        
        # Set up current user JID
        DB['current_user_jid'] = '9999999999@s.whatsapp.net'
        
        # Add test contact to DB
        DB['contacts'][f"people/{self.test_contact}"] = {
            "resourceName": f"people/{self.test_contact}",
            "names": [{"givenName": "Test", "familyName": "Contact"}],
            "phoneNumbers": [{"value": "1234567890", "type": "mobile", "primary": True}],
            "whatsapp": {
                "jid": self.test_contact,
                "name_in_address_book": "Test Contact",
                "profile_name": "TestProfile",
                "phone_number": "1234567890",
                "is_whatsapp_user": True
            }
        }
        
        # Add test chat
        DB['chats'][self.test_contact] = {
            'chat_jid': self.test_contact,
            'name': 'Test Contact',
            'is_group': False,
            'messages': [],
            'last_active_timestamp': None,
            'unread_count': 0,
            'is_archived': False,
            'is_pinned': False
        }
        
        # Create temporary directory for test files
        self.temp_dir = tempfile.mkdtemp()
        self.test_file_path = os.path.join(self.temp_dir, 'test_file.txt')
        
        # Create test file
        with open(self.test_file_path, 'wb') as f:
            f.write(b'Test file content for performance testing')

    def tearDown(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir)
        super().tearDown()

    def test_memory_usage_message_operations(self):
        """Test memory usage during multiple message operations."""
        initial_memory = self.process.memory_info().rss
        
        # Perform multiple message operations
        for i in range(50):
            send_message(recipient=self.test_contact, message=f"Performance test message {i}")
            list_messages(chat_jid=self.test_contact, limit=10, include_context=False)
        
        # Force garbage collection
        gc.collect()
        
        final_memory = self.process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Should not increase by more than 5MB
        self.assertLess(memory_increase, 5 * 1024 * 1024, 
                       f"Memory increase {memory_increase / 1024 / 1024:.2f}MB exceeds 5MB limit")

    def test_message_send_response_time(self):
        """Test message sending response time."""
        start_time = time.time()
        
        result = send_message(recipient=self.test_contact, message="Performance test message")
        
        execution_time = time.time() - start_time
        
        # Should complete within 500ms
        self.assertLess(execution_time, 0.5, 
                       f"Message send took {execution_time:.3f}s, should be < 0.5s")
        self.assertTrue(result.get('success'))

    def test_list_messages_performance(self):
        """Test listing messages performance with large datasets."""
        # Setup large dataset
        for i in range(100):
            send_message(recipient=self.test_contact, message=f"Message {i}")
        
        start_time = time.time()
        result = list_messages(chat_jid=self.test_contact, limit=50, include_context=False)
        execution_time = time.time() - start_time
        
        # Should complete within 1 second
        self.assertLess(execution_time, 1.0, 
                       f"List messages took {execution_time:.3f}s, should be < 1.0s")
        self.assertEqual(len(result['results']), 50)

    def test_file_send_performance(self):
        """Test file sending performance."""
        start_time = time.time()
        
        with patch('os.path.exists', return_value=True), \
             patch('os.path.isfile', return_value=True), \
             patch('mimetypes.guess_type', return_value=('text/plain', None)), \
             patch('os.path.getsize', return_value=1024), \
             patch('os.path.basename', return_value='test_file.txt'):
            
            result = send_file(
                recipient=self.test_contact,
                media_path=self.test_file_path,
                caption="Performance test file"
            )
        
        execution_time = time.time() - start_time
        
        # Should complete within 2 seconds
        self.assertLess(execution_time, 2.0, 
                       f"File send took {execution_time:.3f}s, should be < 2.0s")
        self.assertTrue(result.get('success'))

    def test_concurrent_message_sending(self):
        """Test performance under concurrent load."""
        def send_message_worker(recipient, message):
            return send_message(recipient=recipient, message=message)
        
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [
                executor.submit(send_message_worker, self.test_contact, f"Concurrent message {i}")
                for i in range(20)
            ]
            results = [future.result() for future in futures]
        
        execution_time = time.time() - start_time
        
        # Should complete within 5 seconds
        self.assertLess(execution_time, 5.0, 
                       f"Concurrent operations took {execution_time:.3f}s, should be < 5.0s")
        self.assertTrue(all(result.get('success') for result in results))

    def test_chat_operations_performance(self):
        """Test chat listing and retrieval performance."""
        # Setup multiple chats
        for i in range(10):
            chat_jid = f'chat{i}@s.whatsapp.net'
            DB['chats'][chat_jid] = {
                'chat_jid': chat_jid,
                'name': f'Chat {i}',
                'is_group': False,
                'messages': [],
                'last_active_timestamp': None,
                'unread_count': 0,
                'is_archived': False,
                'is_pinned': False
            }
        
        start_time = time.time()
        
        # List all chats
        chats_result = list_chats(limit=20)
        
        # Get details for each chat
        for chat in chats_result['chats'][:5]:
            get_chat(chat_jid=chat['chat_jid'])
        
        execution_time = time.time() - start_time
        
        # Should complete within 2 seconds
        self.assertLess(execution_time, 2.0, 
                       f"Chat operations took {execution_time:.3f}s, should be < 2.0s")

    def test_search_operations_performance(self):
        """Test contact search performance."""
        # Setup multiple contacts
        for i in range(20):
            contact_jid = f'contact{i}@s.whatsapp.net'
            DB['contacts'][f"people/{contact_jid}"] = {
                "resourceName": f"people/{contact_jid}",
                "names": [{"givenName": f"Contact{i}", "familyName": "Test"}],
                "phoneNumbers": [{"value": f"123456789{i}", "type": "mobile", "primary": True}],
                "whatsapp": {
                    "jid": contact_jid,
                    "name_in_address_book": f"Contact {i}",
                    "profile_name": f"Profile{i}",
                    "phone_number": f"123456789{i}",
                    "is_whatsapp_user": True
                }
            }
        
        start_time = time.time()
        
        # Perform multiple searches
        for i in range(10):
            search_contacts(query=f"Contact{i}")
        
        execution_time = time.time() - start_time
        
        # Should complete within 1 second
        self.assertLess(execution_time, 1.0, 
                       f"Search operations took {execution_time:.3f}s, should be < 1.0s")

    def test_message_context_performance(self):
        """Test message context retrieval performance."""
        # Send a message first
        message_result = send_message(recipient=self.test_contact, message="Context test message")
        message_id = message_result.get('message_id')
        
        start_time = time.time()
        
        # Get message context multiple times
        for i in range(10):
            context_result = get_message_context(message_id)
            self.assertIn('target_message', context_result)
        
        execution_time = time.time() - start_time
        
        # Should complete within 1 second
        self.assertLess(execution_time, 1.0, 
                       f"Context operations took {execution_time:.3f}s, should be < 1.0s")

    def test_last_interaction_performance(self):
        """Test last interaction retrieval performance."""
        # Send multiple messages
        for i in range(10):
            send_message(recipient=self.test_contact, message=f"Interaction test {i}")
        
        start_time = time.time()
        
        # Get last interaction multiple times
        for i in range(10):
            interaction_result = get_last_interaction(jid=self.test_contact)
            self.assertIn('message_id', interaction_result)
        
        execution_time = time.time() - start_time
        
        # Should complete within 1 second
        self.assertLess(execution_time, 1.0, 
                       f"Last interaction operations took {execution_time:.3f}s, should be < 1.0s")

    def test_memory_cleanup_after_operations(self):
        """Test that memory is properly cleaned up after operations."""
        initial_memory = self.process.memory_info().rss
        
        # Perform intensive operations
        for i in range(100):
            send_message(recipient=self.test_contact, message=f"Memory test {i}")
            list_messages(chat_jid=self.test_contact, limit=20, include_context=False)
            get_chat(chat_jid=self.test_contact)
        
        # Force garbage collection
        gc.collect()
        
        # Wait a bit for cleanup
        time.sleep(0.1)
        
        final_memory = self.process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory should not grow excessively
        self.assertLess(memory_increase, 10 * 1024 * 1024, 
                       f"Memory increase {memory_increase / 1024 / 1024:.2f}MB exceeds 10MB limit")

    def test_large_file_performance(self):
        """Test performance with large file operations."""
        # Create a larger test file
        large_file_path = os.path.join(self.temp_dir, 'large_test_file.dat')
        with open(large_file_path, 'wb') as f:
            f.write(b'0' * (5 * 1024 * 1024))  # 5MB file
        
        start_time = time.time()
        
        with patch('os.path.exists', return_value=True), \
             patch('os.path.isfile', return_value=True), \
             patch('mimetypes.guess_type', return_value=('application/octet-stream', None)), \
             patch('os.path.getsize', return_value=5 * 1024 * 1024), \
             patch('os.path.basename', return_value='large_test_file.dat'):
            
            result = send_file(
                recipient=self.test_contact,
                media_path=large_file_path,
                caption="Large file test"
            )
        
        execution_time = time.time() - start_time
        
        # Should complete within 3 seconds for 5MB file
        self.assertLess(execution_time, 3.0, 
                       f"Large file operation took {execution_time:.3f}s, should be < 3.0s")
        self.assertTrue(result.get('success'))

    def test_mixed_operations_performance(self):
        """Test performance with mixed operations simulating real usage."""
        start_time = time.time()
        
        # Simulate typical user workflow
        for i in range(10):
            # Send message
            message_result = send_message(recipient=self.test_contact, message=f"Mixed test {i}")
            message_id = message_result.get('message_id')
            
            # List messages
            list_messages(chat_jid=self.test_contact, limit=10, include_context=False)
            
            # Get message context
            get_message_context(message_id)
            
            # Get chat details
            get_chat(chat_jid=self.test_contact)
            
            # Get last interaction
            get_last_interaction(jid=self.test_contact)
        
        execution_time = time.time() - start_time
        
        # Should complete within 5 seconds
        self.assertLess(execution_time, 5.0, 
                       f"Mixed operations took {execution_time:.3f}s, should be < 5.0s")


if __name__ == '__main__':
    unittest.main()
