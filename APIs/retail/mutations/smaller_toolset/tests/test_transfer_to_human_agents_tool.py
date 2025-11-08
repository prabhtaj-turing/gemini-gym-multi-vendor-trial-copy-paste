import unittest
from unittest.mock import patch
from retail.mutations.smaller_toolset.transfer_to_human_agents_tool import escalate_to_human_support

class TestTransferToHumanAgentsTool(unittest.TestCase):

    @patch('retail.mutations.smaller_toolset.transfer_to_human_agents_tool.transfer_to_human_agents')
    def test_escalate_to_human_support(self, mock_transfer):
        mock_transfer.return_value = "Your request has been escalated to a human agent."
        result = escalate_to_human_support(problem_description="The user is having trouble with their order.")
        mock_transfer.assert_called_once_with(summary="The user is having trouble with their order.")
        self.assertEqual(result, {"message": "Your request has been escalated to a human agent."})

