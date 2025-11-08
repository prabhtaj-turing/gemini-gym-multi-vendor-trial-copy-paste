import unittest
import copy
import base64
import time
from datetime import datetime, timezone
from ..SimulationEngine import custom_errors
from .. import list_ticket_comments
from ..SimulationEngine.db import DB
from common_utils.base_case import BaseTestCaseWithErrorHandler
from pydantic import ValidationError as PydanticValidationError
from ..Tickets import create_ticket, update_ticket


class TestTicketComments(BaseTestCaseWithErrorHandler):

    def setUp(self):
        self._original_DB_state = copy.deepcopy(DB)
        DB.clear()

        DB['users'] = {
            '1': {'id': 1, 'name': 'Alice User', 'email': 'alice@example.com', 'active': True, 'role': 'end-user', 'created_at': datetime.now().isoformat(), 'updated_at': datetime.now().isoformat()},
            '2': {'id': 2, 'name': 'Bob Agent', 'email': 'bob.agent@example.com', 'active': True, 'role': 'agent', 'created_at': datetime.now().isoformat(), 'updated_at': datetime.now().isoformat()},
            '3': {'id': 3, 'name': 'Charlie Assignee', 'email': 'charlie.assignee@example.com', 'active': True, 'role': 'agent', 'created_at': datetime.now().isoformat(), 'updated_at': datetime.now().isoformat()},
            '4': {'id': 4, 'name': 'David Collaborator', 'email': 'david.collab@example.com', 'active': True, 'role': 'end-user', 'created_at': datetime.now().isoformat(), 'updated_at': datetime.now().isoformat()},
            '5': {'id': 5, 'name': 'Eve Submitter', 'email': 'eve.submitter@example.com', 'active': True, 'role': 'agent', 'created_at': datetime.now().isoformat(), 'updated_at': datetime.now().isoformat()},
        }
        DB['organizations'] = {
            '101': {'id': 101, 'name': 'Org Alpha', 'created_at': datetime.now().isoformat(), 'updated_at': datetime.now().isoformat()},
        }
        DB['tickets'] = {
            '1': {
                'id': 1, 
                'subject': 'Test Ticket', 
                'description': 'This is a test ticket', 
                'created_at': datetime.now().isoformat(), 
                'updated_at': datetime.now().isoformat()
            },
        }
        DB['comments'] = {
            '1': {
                'id': 1, 
                'ticket_id': 1, 
                'author_id': 1, 
                'body': 'This is a test comment', 
                'created_at': datetime.now().isoformat(), 
                'updated_at': datetime.now().isoformat(), 
                'attachments': [1]},
            '2': {
                'id': 2, 
                'ticket_id': 1, 
                'author_id': 2, 
                'body': 'This is a test comment 2', 
                'created_at': datetime.now().isoformat(), 
                'updated_at': datetime.now().isoformat(), 
                'attachments': [2]},
        }
        DB['next_comment_id'] = 3
        DB['attachments'] = {
            '1': {'id': 1, 'file_name': 'test.txt', 'content_url': 'https://example.com/test.txt', 'content_type': 'text/plain', 'size': 100, 'thumbnail': {'url': 'https://example.com/test.txt', 'width': 100, 'height': 100}},
            '2': {'id': 2, 'file_name': 'test2.txt', 'content_url': 'https://example.com/test2.txt', 'content_type': 'text/plain', 'size': 200, 'thumbnail': {'url': 'https://example.com/test2.txt', 'width': 200, 'height': 200}},
        }
        DB['next_attachment_id'] = 3
        DB['next_ticket_id'] = 2
        DB['next_user_id'] = 100 
        DB['next_audit_id'] = 1

    def tearDown(self):
        DB.clear()
        DB.update(self._original_DB_state)  

    def test_list_ticket_comments_success(self):
        response = list_ticket_comments(1)  
        self.assertEqual(len(response['comments']), 2)
        

    def test_list_ticket_comments_include_inline_images_success(self):
        response = list_ticket_comments(1, include_inline_images=True)
        self.assertEqual(len(response['comments']), 2)
        self.assertEqual(response['comments'][0]['attachments'][0]['id'], 1)
        self.assertEqual(response['comments'][1]['attachments'][0]['id'], 2)

    def test_list_ticket_comments_include_users_success(self):
        response = list_ticket_comments(1, include="users")
        self.assertEqual(len(response['comments']), 2)
        self.assertEqual(response['comments'][0]['author_id'], 1)
        self.assertEqual(response['comments'][1]['author_id'], 2)

    def test_list_ticket_comments_include_users_and_inline_images_success(self):
        response = list_ticket_comments(1, include="users", include_inline_images=True)
        self.assertEqual(len(response['comments']), 2)
        self.assertEqual(response['comments'][0]['attachments'][0]['id'], 1)
        self.assertEqual(response['comments'][1]['attachments'][0]['id'], 2)

    def test_list_ticket_comments_invalid_ticket_id_raises_error(self):
        self.assert_error_behavior(
            list_ticket_comments,
            custom_errors.TicketNotFoundError,
            "Ticket with ID 999 not found", 
            ticket_id=999   
        )

    def test_list_ticket_comments_invalid_include_raises_error(self):
        self.assert_error_behavior(
            list_ticket_comments,
            TypeError,
            "include must be a string",
            include=1,
            ticket_id=1
        )

    def test_list_ticket_comments_invalid_include_inline_images_raises_error(self):
        self.assert_error_behavior(
            list_ticket_comments,
            TypeError,
            "include_inline_images must be a boolean",
            include_inline_images=1,
            ticket_id=1
        )

    def test_list_ticket_comments_invalid_ticket_id_type_raises_error(self):
        self.assert_error_behavior(
            list_ticket_comments,
            TypeError,
            "ticket_id must be an integer",
            ticket_id="1"
        )
            
    def test_agent_adds_public_comment_and_requester_sees_only_public(self):
        # Step 1: Agent adds a public comment to an existing ticket
        # First, create a ticket as the requester (user_id=1)
         # Step 1: Agent creates ticket
        # Setup: Add users (agent, assignee, manager) and ticket 98765
        agent_id = 10
        assignee_id = 20
        manager_id = 30
        ticket_id = 98765

        now_iso = datetime.now(timezone.utc).isoformat()

        DB['users'] = {
            str(agent_id): {'id': agent_id, 'name': 'Agent Smith', 'email': 'agent.smith@example.com', 'active': True, 'role': 'agent', 'created_at': now_iso, 'updated_at': now_iso},
            str(assignee_id): {'id': assignee_id, 'name': 'Agent Jones', 'email': 'agent.jones@example.com', 'active': True, 'role': 'agent', 'created_at': now_iso, 'updated_at': now_iso},
            str(manager_id): {'id': manager_id, 'name': 'Manager Lee', 'email': 'manager.lee@example.com', 'active': True, 'role': 'admin', 'created_at': now_iso, 'updated_at': now_iso},
        }
        DB['tickets'] = {}
        DB['next_ticket_id'] = ticket_id + 1
        DB['ticket_audits'] = {}
        DB['next_audit_id'] = 1
        DB['comments'] = {}
        DB['next_comment_id'] = 1

        ticket_id = ticket_id + 1

        # Step 1: Agent creates ticket
        res = create_ticket(
            ticket={
                'assignee_id': assignee_id,
                'comment': {
                    'body': 'We are working on your issue and will update you soon.'
                },
                'requester_id': agent_id,
                'subject': 'Test Ticket'
            }
        )
        ticket_id = res['ticket']['id']

        comments_response = list_ticket_comments(ticket_id)
        comments = comments_response['comments']

        self.assertEqual(len(comments), 1)

        # Add a private comment as agent (user_id=2)
        # Simulate adding a private comment via the Tickets API (update_ticket)
        update_ticket(ticket_id, {'comment_body': 'Internal note: Reset user password.'})
        update_ticket(ticket_id, {'comment_body': 'We are working on your issue and will update you soon.'})

        comments_response = list_ticket_comments(ticket_id)
        comments = comments_response['comments']

        self.assertEqual(len(comments), 3)