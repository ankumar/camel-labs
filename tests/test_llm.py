"""
Tests for the LLM components of CaMeL.
"""

import pytest
from unittest.mock import Mock, patch
from camel.llm import PrivilegedLLM, QuarantinedLLM, LLMFactory, LLMResponse


class TestPrivilegedLLM:
    """Test the Privileged LLM."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.p_llm = PrivilegedLLM(model="gpt-4")
    
    def test_register_tool(self):
        schema = {
            "description": "Send an email",
            "params": "recipient: str, subject: str, body: str",
            "returns": "bool"
        }
        
        self.p_llm.register_tool("send_email", schema)
        assert "send_email" in self.p_llm.tool_schemas
        assert self.p_llm.tool_schemas["send_email"] == schema
    
    @patch('openai.OpenAI')
    def test_plan_and_generate_code(self, mock_openai):
        # Mock the OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = 'result = get_document("test.pdf")'
        
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        # Register a tool
        self.p_llm.register_tool("get_document", {"description": "Get a document"})
        
        # Test code generation
        response = self.p_llm.plan_and_generate_code("Get the test document")
        
        assert isinstance(response, LLMResponse)
        assert "get_document" in response.content
        assert response.metadata["query"] == "Get the test document"
    
    def test_system_prompt_includes_tools(self):
        # Register some tools
        self.p_llm.register_tool("send_email", {"description": "Send an email"})
        self.p_llm.register_tool("get_file", {"description": "Get a file"})
        
        system_prompt = self.p_llm._build_system_prompt()
        
        assert "send_email" in system_prompt
        assert "get_file" in system_prompt
        assert "query_quarantined_llm" in system_prompt


class TestQuarantinedLLM:
    """Test the Quarantined LLM."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.q_llm = QuarantinedLLM(model="gpt-3.5-turbo")
    
    @patch('openai.OpenAI')
    def test_query(self, mock_openai):
        # Mock the OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "bob@company.com"
        
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        # Test querying
        response = self.q_llm.query(
            "Extract the email address",
            "Contact Bob at bob@company.com",
            "email"
        )
        
        assert isinstance(response, LLMResponse)
        assert response.content == "bob@company.com"
        assert response.metadata["schema"] == "email"
    
    def test_validate_email_schema(self):
        # Valid email
        result = self.q_llm._validate_output("user@domain.com", "email")
        assert result == "user@domain.com"
        
        # Invalid email
        with pytest.raises(ValueError, match="does not match email schema"):
            self.q_llm._validate_output("not-an-email", "email")
    
    def test_validate_string_schema(self):
        # Valid string
        result = self.q_llm._validate_output("Hello World", "string")
        assert result == "Hello World"
        
        # String too long
        long_string = "x" * 1001
        with pytest.raises(ValueError, match="String output too long"):
            self.q_llm._validate_output(long_string, "string")
    
    def test_validate_filename_schema(self):
        # Valid filename
        result = self.q_llm._validate_output("document.pdf", "filename")
        assert result == "document.pdf"
        
        # Invalid filename with special characters
        with pytest.raises(ValueError, match="invalid filename characters"):
            self.q_llm._validate_output("doc<ument.pdf", "filename")


class TestLLMFactory:
    """Test the LLM factory."""
    
    def test_create_privileged_llm(self):
        p_llm = LLMFactory.create_privileged_llm("gpt-4", "test-key")
        assert isinstance(p_llm, PrivilegedLLM)
        assert p_llm.model == "gpt-4"
    
    def test_create_quarantined_llm(self):
        q_llm = LLMFactory.create_quarantined_llm("gpt-3.5-turbo", "test-key")
        assert isinstance(q_llm, QuarantinedLLM)
        assert q_llm.model == "gpt-3.5-turbo"


class TestLLMResponse:
    """Test the LLM response data class."""
    
    def test_llm_response_creation(self):
        response = LLMResponse(
            content="test content",
            reasoning="test reasoning",
            metadata={"key": "value"}
        )
        
        assert response.content == "test content"
        assert response.reasoning == "test reasoning"
        assert response.metadata == {"key": "value"}
    
    def test_llm_response_defaults(self):
        response = LLMResponse(content="test")
        
        assert response.content == "test"
        assert response.reasoning is None
        assert response.metadata is None
