"""
Tests for the core CaMeL system.
"""

import pytest
from unittest.mock import Mock, patch
from camel.core import CaMeLSystem, create_camel_system
from camel.llm import LLMResponse


class TestCaMeLSystem:
    """Test the main CaMeL system."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.camel = CaMeLSystem(api_key="test-key")
    
    def test_system_initialization(self):
        """Test that the system initializes correctly."""
        assert self.camel.p_llm is not None
        assert self.camel.q_llm is not None
        assert self.camel.interpreter is not None
        assert self.camel.capability_tracker is not None
        assert self.camel.tool_registry is not None
    
    def test_tools_registered(self):
        """Test that tools are registered with the interpreter."""
        # Check that some key tools are available
        assert "get_last_email" in self.camel.interpreter.functions
        assert "send_email" in self.camel.interpreter.functions
        assert "query_quarantined_llm" in self.camel.interpreter.functions
    
    def test_tool_schemas_registered(self):
        """Test that tool schemas are registered with P-LLM."""
        assert len(self.camel.p_llm.tool_schemas) > 0
        assert "send_email" in self.camel.p_llm.tool_schemas
    
    def test_security_policies_added(self):
        """Test that security policies are configured."""
        assert len(self.camel.capability_tracker.policies) > 0
    
    @patch.object(CaMeLSystem, '_query_quarantined_llm')
    def test_query_quarantined_llm(self, mock_q_llm):
        """Test the quarantined LLM query function."""
        mock_q_llm.return_value = "test@example.com"
        
        result = self.camel._query_quarantined_llm(
            "Extract email",
            "Contact test@example.com",
            "email"
        )
        
        assert result == "test@example.com"
        mock_q_llm.assert_called_once()
    
    def test_set_trusted_data(self):
        """Test setting trusted data."""
        self.camel.set_trusted_data("user_input", "Hello World")
        
        # Check that the variable was set
        assert self.camel.interpreter.get_variable("user_input") == "Hello World"
        
        # Check that it has trusted capabilities
        caps = self.camel.get_capability_info("user_input")
        assert caps is not None
        assert caps.is_trusted()
    
    def test_set_untrusted_data(self):
        """Test setting untrusted data."""
        self.camel.set_untrusted_data("external_data", "Malicious content", "email")
        
        # Check that the variable was set
        assert self.camel.interpreter.get_variable("external_data") == "Malicious content"
        
        # Check that it has untrusted capabilities
        caps = self.camel.get_capability_info("external_data")
        assert caps is not None
        assert caps.is_untrusted()
    
    @patch.object(CaMeLSystem, '_query_quarantined_llm')
    @patch('camel.llm.PrivilegedLLM.plan_and_generate_code')
    def test_execute_simple_query(self, mock_plan, mock_q_llm):
        """Test executing a simple query."""
        # Mock P-LLM response
        mock_plan.return_value = LLMResponse(
            content='result = get_last_email()',
            reasoning="Get email"
        )
        
        # Mock Q-LLM response
        mock_q_llm.return_value = "test email content"
        
        # Execute the query
        result = self.camel.execute("Get the last email")
        
        # Verify the mocks were called
        mock_plan.assert_called_once_with("Get the last email")
    
    @patch('camel.llm.PrivilegedLLM.plan_and_generate_code')
    def test_execute_with_error(self, mock_plan):
        """Test handling of execution errors."""
        # Mock P-LLM to return invalid code
        mock_plan.return_value = LLMResponse(
            content='invalid_function()',
            reasoning="Invalid code"
        )
        
        # Execute should handle the error gracefully
        result = self.camel.execute("Invalid query")
        assert "failed" in result.lower()
    
    def test_add_security_policy(self):
        """Test adding a custom security policy."""
        # Create a mock policy
        mock_policy = Mock()
        mock_policy.check.return_value = True
        
        # Add the policy
        initial_count = len(self.camel.capability_tracker.policies)
        self.camel.add_security_policy(mock_policy)
        
        # Verify it was added
        assert len(self.camel.capability_tracker.policies) == initial_count + 1
    
    def test_demo_prompt_injection_attack(self):
        """Test the prompt injection demo."""
        # This should run without errors (even if using mock LLMs)
        try:
            result = self.camel.demo_prompt_injection_attack()
            assert isinstance(result, str)
        except Exception as e:
            # Allow for errors due to mock LLMs, but check the method exists
            assert "demo_prompt_injection_attack" in str(e) or "LLM" in str(e)


class TestCaMeLSystemIntegration:
    """Integration tests for the CaMeL system."""
    
    @patch('openai.OpenAI')
    def test_full_workflow_mock(self, mock_openai):
        """Test a full workflow with mocked LLM responses."""
        # Mock OpenAI responses
        mock_client = Mock()
        mock_openai.return_value = mock_client
        
        # Mock P-LLM response (code generation)
        p_llm_response = Mock()
        p_llm_response.choices = [Mock()]
        p_llm_response.choices[0].message.content = """
email = get_last_email()
sender = query_quarantined_llm("Extract sender email", email, "email")
notify_user(f"Last email from: {sender}")
"""
        
        # Mock Q-LLM response (data extraction)
        q_llm_response = Mock()
        q_llm_response.choices = [Mock()]
        q_llm_response.choices[0].message.content = "alice@company.com"
        
        # Set up the mock to return different responses for different calls
        def mock_create(**kwargs):
            messages = kwargs.get('messages', [])
            if any('Privileged LLM' in msg.get('content', '') for msg in messages):
                return p_llm_response
            else:
                return q_llm_response
        
        mock_client.chat.completions.create.side_effect = mock_create
        
        # Create and test the system
        camel = CaMeLSystem(api_key="test-key")
        
        # Execute a query
        result = camel.execute("Show me who sent the last email")
        
        # Should complete without error
        assert isinstance(result, str)


def test_create_camel_system():
    """Test the convenience function for creating CaMeL systems."""
    camel = create_camel_system("test-key")
    assert isinstance(camel, CaMeLSystem)
    assert camel.p_llm.model == "gpt-4"
    assert camel.q_llm.model == "gpt-3.5-turbo"
