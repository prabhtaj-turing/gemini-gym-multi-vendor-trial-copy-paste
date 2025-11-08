import copy
import unittest

from whatsapp.SimulationEngine import custom_errors
from whatsapp.SimulationEngine.db import DB
from common_utils.base_case import BaseTestCaseWithErrorHandler
from .. import get_chat

class TestGetChat(BaseTestCaseWithErrorHandler):

    def setUp(self):
        self._original_DB_state = copy.deepcopy(DB)
        DB.clear()
        self.user_jid1 = '1111111111@s.whatsapp.net'
        self.user_jid2 = '2222222222@s.whatsapp.net'
        self.user_jid3 = '3333333333@s.whatsapp.net'
        self.group_jid1 = 'group1_id@g.us'
        self.group_jid2 = 'group2_id@g.us'
        self.message1_user1_chat = {'message_id': 'msg1_user1', 'chat_jid': self.user_jid1,
                                    'sender_jid': self.user_jid1, 'sender_name': 'User One',
                                    'timestamp': '2023-01-01T10:00:00Z', 'text_content': 'Hello from user1',
                                    'is_outgoing': True, 'media_info': None, 'quoted_message_info': None,
                                    'reaction': None, 'status': 'sent', 'forwarded': False}
        self.message2_user1_chat = {'message_id': 'msg2_user1', 'chat_jid': self.user_jid1,
                                    'sender_jid': 'other@s.whatsapp.net', 'sender_name': 'Other User',
                                    'timestamp': '2023-01-01T10:05:00Z', 'text_content': 'Hi user1',
                                    'is_outgoing': False, 'media_info': None, 'quoted_message_info': None,
                                    'reaction': '', 'status': 'read', 'forwarded': False}
        self.message3_user1_chat_latest = {'message_id': 'msg3_user1', 'chat_jid': self.user_jid1,
                                           'sender_jid': self.user_jid1, 'sender_name': 'User One',
                                           'timestamp': '2023-01-01T10:10:00Z',
                                           'text_content': 'Latest message with media', 'is_outgoing': True,
                                           'media_info': {'media_type': 'image', 'file_name': 'photo.jpg',
                                                          'caption': 'A nice photo', 'mime_type': 'image/jpeg'},
                                           'quoted_message_info': {'quoted_message_id': 'msg2_user1',
                                                                   'quoted_sender_jid': 'other@s.whatsapp.net',
                                                                   'quoted_text_preview': 'Hi user1'}, 'reaction': None,
                                           'status': 'delivered', 'forwarded': True}
        self.message0_user1_chat_older = {'message_id': 'msg0_user1', 'chat_jid': self.user_jid1,
                                          'sender_jid': 'other@s.whatsapp.net', 'sender_name': 'Other User',
                                          'timestamp': '2022-12-31T23:59:59Z', 'text_content': 'An older message',
                                          'is_outgoing': False, 'media_info': None, 'quoted_message_info': None,
                                          'reaction': None, 'status': 'read', 'forwarded': False}
        self.chat_user1 = {'chat_jid': self.user_jid1, 'name': 'User One Chat', 'is_group': False,
                           'last_active_timestamp': '2023-01-01T10:10:00Z', 'unread_count': 1, 'is_archived': False,
                           'is_pinned': False, 'is_muted_until': None,
                           'messages': [self.message1_user1_chat, self.message2_user1_chat,
                                        self.message0_user1_chat_older, self.message3_user1_chat_latest]}
        self.chat_user2_archived_muted = {'chat_jid': self.user_jid2, 'name': 'User Two Archived', 'is_group': False,
                                          'last_active_timestamp': '2023-01-02T12:00:00Z', 'unread_count': 0,
                                          'is_archived': True, 'is_pinned': False, 'is_muted_until': 'indefinitely',
                                          'messages': []}
        self.chat_user3_no_messages = {'chat_jid': self.user_jid3, 'name': None, 'is_group': False,
                                       'last_active_timestamp': '2023-01-02T13:00:00Z', 'unread_count': 0,
                                       'is_archived': False, 'is_pinned': False, 'is_muted_until': None, 'messages': []}
        self.chat_user4_messages_not_list = {'chat_jid': '4444444444@s.whatsapp.net', 'name': 'User Four Bad Messages',
                                             'is_group': False, 'last_active_timestamp': '2023-01-02T14:00:00Z',
                                             'unread_count': 0, 'is_archived': False, 'is_pinned': False,
                                             'is_muted_until': None, 'messages': 'this is not a list'}
        self.group1_participant1 = {'jid': self.user_jid1, 'name_in_address_book': 'Admin User',
                                    'profile_name': 'Admin Profile', 'is_admin': True}
        self.group1_participant2 = {'jid': self.user_jid2, 'name_in_address_book': 'Member User',
                                    'profile_name': 'Member Profile', 'is_admin': False}
        self.message1_group1_chat = {'message_id': 'msg1_group1', 'chat_jid': self.group_jid1,
                                     'sender_jid': self.user_jid1, 'sender_name': 'Admin User',
                                     'timestamp': '2023-01-03T11:00:00Z', 'text_content': 'Group message 1',
                                     'is_outgoing': False, 'media_info': None, 'quoted_message_info': None,
                                     'reaction': None, 'status': 'delivered', 'forwarded': False}
        self.message2_group1_chat_latest = {'message_id': 'msg2_group1', 'chat_jid': self.group_jid1,
                                            'sender_jid': self.user_jid2, 'sender_name': 'Member User',
                                            'timestamp': '2023-01-03T11:05:00Z',
                                            'text_content': 'Group message 2 latest', 'is_outgoing': False,
                                            'media_info': None, 'quoted_message_info': None, 'reaction': None,
                                            'status': 'read', 'forwarded': False}
        self.chat_group1_full_metadata = {'chat_jid': self.group_jid1, 'name': 'Test Group 1', 'is_group': True,
                                          'last_active_timestamp': '2023-01-03T11:05:00Z', 'unread_count': 5,
                                          'is_archived': False, 'is_pinned': True,
                                          'is_muted_until': '2024-12-31T23:59:59Z',
                                          'group_metadata': {'group_description': 'A test group with full data.',
                                                             'creation_timestamp': '2023-01-01T00:00:00Z',
                                                             'owner_jid': self.user_jid1, 'participants_count': 2,
                                                             'participants': [self.group1_participant1,
                                                                              self.group1_participant2]},
                                          'messages': [self.message1_group1_chat, self.message2_group1_chat_latest]}
        self.chat_group2_null_metadata = {'chat_jid': self.group_jid2, 'name': 'Group With Null Meta', 'is_group': True,
                                          'last_active_timestamp': '2023-01-04T00:00:00Z', 'unread_count': 0,
                                          'is_archived': False, 'is_pinned': False, 'is_muted_until': None,
                                          'group_metadata': None, 'messages': []}
        self.chat_group3_minimal_metadata = {'chat_jid': 'group3_id@g.us', 'name': 'Minimal Group', 'is_group': True,
                                             'last_active_timestamp': '2023-01-05T00:00:00Z', 'unread_count': 0,
                                             'is_archived': False, 'is_pinned': False, 'is_muted_until': None,
                                             'group_metadata': {'group_description': None, 'creation_timestamp': None,
                                                                'owner_jid': None, 'participants_count': 0,
                                                                'participants': []}, 'messages': []}
        DB['chats'] = {self.user_jid1: self.chat_user1, self.user_jid2: self.chat_user2_archived_muted,
                       self.user_jid3: self.chat_user3_no_messages,
                       '4444444444@s.whatsapp.net': self.chat_user4_messages_not_list,
                       self.group_jid1: self.chat_group1_full_metadata, self.group_jid2: self.chat_group2_null_metadata,
                       'group3_id@g.us': self.chat_group3_minimal_metadata}
        DB['contacts'] = {}
        DB['actions'] = []

    def tearDown(self):
        DB.clear()
        DB.update(self._original_DB_state)

    def test_get_individual_chat_with_last_message(self):
        chat = get_chat(self.user_jid1, include_last_message=True)
        self.assertEqual(chat['chat_jid'], self.user_jid1)
        self.assertEqual(chat['name'], 'User One Chat')
        self.assertFalse(chat['is_group'])
        self.assertIsNone(chat['group_metadata'])
        self.assertEqual(chat['unread_count'], 1)
        self.assertFalse(chat['is_archived'])
        self.assertIsNone(chat['is_muted_until'])
        self.assertIsNotNone(chat['last_message'])
        self.assertEqual(chat['last_message']['message_id'], self.message3_user1_chat_latest['message_id'])
        self.assertEqual(chat['last_message']['text_content'], self.message3_user1_chat_latest['text_content'])
        self.assertEqual(chat['last_message'], self.message3_user1_chat_latest)

    def test_get_individual_chat_without_last_message(self):
        chat = get_chat(self.user_jid1, include_last_message=False)
        self.assertEqual(chat['chat_jid'], self.user_jid1)
        self.assertEqual(chat['name'], 'User One Chat')
        self.assertIsNone(chat['last_message'])

    def test_get_group_chat_with_last_message(self):
        chat = get_chat(self.group_jid1, include_last_message=True)
        self.assertEqual(chat['chat_jid'], self.group_jid1)
        self.assertEqual(chat['name'], 'Test Group 1')
        self.assertTrue(chat['is_group'])
        self.assertIsNotNone(chat['group_metadata'])
        self.assertEqual(chat['group_metadata']['group_description'], 'A test group with full data.')
        self.assertEqual(chat['group_metadata']['owner_jid'], self.user_jid1)
        self.assertEqual(chat['group_metadata']['participants_count'], 2)
        self.assertEqual(len(chat['group_metadata']['participants']), 2)
        self.assertEqual(chat['unread_count'], 5)
        self.assertFalse(chat['is_archived'])
        self.assertEqual(chat['is_muted_until'], '2024-12-31T23:59:59Z')
        self.assertIsNotNone(chat['last_message'])
        self.assertEqual(chat['last_message']['message_id'], self.message2_group1_chat_latest['message_id'])
        self.assertEqual(chat['last_message'], self.message2_group1_chat_latest)

    def test_get_group_chat_without_last_message(self):
        chat = get_chat(self.group_jid1, include_last_message=False)
        self.assertEqual(chat['chat_jid'], self.group_jid1)
        self.assertTrue(chat['is_group'])
        self.assertIsNotNone(chat['group_metadata'])
        self.assertIsNone(chat['last_message'])

    def test_get_chat_with_no_messages_include_last_message_true(self):
        chat = get_chat(self.user_jid3, include_last_message=True)
        self.assertEqual(chat['chat_jid'], self.user_jid3)
        self.assertIsNone(chat['name'])
        self.assertFalse(chat['is_group'])
        self.assertIsNone(chat['group_metadata'])
        self.assertIsNone(chat['last_message'])

    def test_get_chat_archived_and_muted_indefinitely(self):
        chat = get_chat(self.user_jid2, include_last_message=True)
        self.assertEqual(chat['chat_jid'], self.user_jid2)
        self.assertEqual(chat['name'], 'User Two Archived')
        self.assertTrue(chat['is_archived'])
        self.assertEqual(chat['is_muted_until'], 'indefinitely')
        self.assertIsNone(chat['last_message'])

    def test_get_group_chat_with_null_group_metadata_in_db(self):
        chat = get_chat(self.group_jid2, include_last_message=True)
        self.assertEqual(chat['chat_jid'], self.group_jid2)
        self.assertEqual(chat['name'], 'Group With Null Meta')
        self.assertTrue(chat['is_group'])
        self.assertIsNone(chat['group_metadata'])
        self.assertIsNone(chat['last_message'])

    def test_get_group_chat_with_minimal_group_metadata_fields(self):
        chat = get_chat('group3_id@g.us', include_last_message=False)
        self.assertEqual(chat['chat_jid'], 'group3_id@g.us')
        self.assertTrue(chat['is_group'])
        self.assertIsNotNone(chat['group_metadata'])
        group_meta = chat['group_metadata']
        self.assertIsNone(group_meta['group_description'])
        self.assertIsNone(group_meta['creation_timestamp'])
        self.assertIsNone(group_meta['owner_jid'])
        self.assertEqual(group_meta['participants_count'], 0)
        self.assertEqual(group_meta['participants'], [])
        self.assertIsNone(chat['last_message'])

    def test_get_chat_messages_in_db_not_a_list(self):
        chat_jid_bad_messages = '4444444444@s.whatsapp.net'
        chat = get_chat(chat_jid_bad_messages, include_last_message=True)
        self.assertEqual(chat['chat_jid'], chat_jid_bad_messages)
        self.assertIsNone(chat['last_message'], 'Last message should be None if DB messages field is not a list')

    def test_get_chat_not_found_error(self):
        self.assert_error_behavior(func_to_call=get_chat, expected_exception_type=custom_errors.ChatNotFoundError,
                                   expected_message='The specified chat could not be found.',
                                   chat_jid='nonexistent@s.whatsapp.net')

    def test_get_chat_invalid_jid_format_error_user_scheme(self):
        self.assert_error_behavior(func_to_call=get_chat, expected_exception_type=custom_errors.InvalidJIDError,
                                   expected_message='The provided JID has an invalid format.',
                                   chat_jid='12345@example.com')

    def test_get_chat_invalid_jid_format_error_no_at_sign(self):
        self.assert_error_behavior(func_to_call=get_chat, expected_exception_type=custom_errors.InvalidJIDError,
                                   expected_message='The provided JID has an invalid format.', chat_jid='invalidjid')

    def test_get_chat_invalid_jid_format_error_empty_string(self):
        self.assert_error_behavior(func_to_call=get_chat, expected_exception_type=custom_errors.InvalidJIDError,
                                   expected_message='The provided JID has an invalid format.', chat_jid='')

    def test_get_chat_validation_error_chat_jid_not_string(self):
        expected_message = "1 validation error for GetChatArguments\nchat_jid\n  Input should be a valid string [type=string_type, input_value=12345, input_type=int]\n    For further information visit https://errors.pydantic.dev/2.11/v/string_type"
        self.assert_error_behavior(func_to_call=get_chat, expected_exception_type=custom_errors.InvalidInputError,
                                   expected_message=expected_message,
                                   chat_jid=12345)

    def test_get_chat_validation_error_include_last_message_not_bool(self):
        expected_message = "1 validation error for GetChatArguments\ninclude_last_message\n  Input should be a valid boolean, unable to interpret input [type=bool_parsing, input_value='true_string', input_type=str]\n    For further information visit https://errors.pydantic.dev/2.11/v/bool_parsing"
        self.assert_error_behavior(func_to_call=get_chat, expected_exception_type=custom_errors.InvalidInputError,
                                   expected_message=expected_message,
                                   chat_jid=self.user_jid1, include_last_message='true_string')

    def test_get_chat_db_chats_not_dict(self):
        DB['chats'] = 'this is not a dictionary'
        self.assert_error_behavior(func_to_call=get_chat, expected_exception_type=custom_errors.ChatNotFoundError,
                                   expected_message='The specified chat could not be found.',
                                   chat_jid=self.user_jid1)

    def test_get_chat_db_chat_entry_not_dict(self):
        DB['chats'][self.user_jid1] = 'this is not a dictionary'
        self.assert_error_behavior(func_to_call=get_chat, expected_exception_type=custom_errors.ChatNotFoundError,
                                   expected_message='The specified chat could not be found.',
                                   chat_jid=self.user_jid1)


if __name__ == '__main__':
    unittest.main()
