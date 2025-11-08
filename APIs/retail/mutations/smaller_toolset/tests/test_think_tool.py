import unittest
from unittest.mock import patch
from retail.mutations.smaller_toolset.think_tool import log_thought

class TestThinkTool(unittest.TestCase):

    @patch('retail.mutations.smaller_toolset.think_tool.think')
    def test_log_thought(self, mock_think):
        mock_think.return_value = {"status": "Thought logged"}
        result = log_thought(thought="This is a test thought.")
        mock_think.assert_called_once_with(thought="This is a test thought.")
        self.assertEqual(result, {"status": "Thought logged"})

    @patch('retail.mutations.smaller_toolset.think_tool.think')
    def test_log_thought_error(self, mock_think):
        mock_think.side_effect = Exception("Invalid thought")
        with self.assertRaises(Exception) as context:
            log_thought(thought="This is a test thought.")
        self.assertEqual(str(context.exception), "Invalid thought")


