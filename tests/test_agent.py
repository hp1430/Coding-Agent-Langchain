import unittest
from unittest.mock import patch

from agent import build_agent
from tools.shell import rewrite_command


class BuildAgentCompatibilityTests(unittest.TestCase):
    @patch("agent.build_client_model")
    @patch("agent.create_agent")
    @patch("agent.make_checkpointer")
    def test_groq_skips_structured_response_format(self, mock_checkpointer, mock_create_agent, mock_build_client_model):
        mock_build_client_model.return_value = (
            object(),
            type("Provider", (), {"name": "Groq"})(),
        )

        build_agent(checkpointer=None)

        _, kwargs = mock_create_agent.call_args
        self.assertNotIn("response_format", kwargs)

    @patch("agent.build_client_model")
    @patch("agent.create_agent")
    @patch("agent.make_checkpointer")
    def test_non_groq_keeps_structured_response_format(self, mock_checkpointer, mock_create_agent, mock_build_client_model):
        mock_build_client_model.return_value = (
            object(),
            type("Provider", (), {"name": "OpenAI"})(),
        )

        build_agent(checkpointer=None)

        _, kwargs = mock_create_agent.call_args
        self.assertIn("response_format", kwargs)

    @patch("tools.shell.sys.executable", "C:\\Users\\demo\\AppData\\Local\\Programs\\Python\\Python311\\python.exe")
    def test_rewrite_command_handles_windows_executable_path(self):
        result = rewrite_command("python ping_pong.py")
        self.assertEqual(
            result,
            r'"C:\Users\demo\AppData\Local\Programs\Python\Python311\python.exe" ping_pong.py',
        )


if __name__ == "__main__":
    unittest.main()
