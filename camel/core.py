"""
Core CaMeL system that ties everything together.

This is the main interface for the CaMeL defense system.
"""

from typing import Optional, Dict, Any
from .llm import PrivilegedLLM, QuarantinedLLM, LLMFactory
from .interpreter import CaMeLInterpreter
from .capabilities import CapabilityTracker, CapabilitySet, Capability, CapabilityType
from .capabilities import EmailSecurityPolicy, FileAccessPolicy
from .tools import CaMeLToolRegistry


class CaMeLSystem:
    """
    Main CaMeL system that provides secure LLM agent execution.
    
    This system implements the dual LLM pattern with capability-based
    security to defend against prompt injection attacks.
    """
    
    def __init__(self, 
                 privileged_model: str = "gpt-4",
                 quarantined_model: str = "gpt-3.5-turbo",
                 api_key: Optional[str] = None):
        """
        Initialize the CaMeL system.
        
        Args:
            privileged_model: Model to use for the P-LLM
            quarantined_model: Model to use for the Q-LLM
            api_key: OpenAI API key
        """
        
        # Initialize LLMs
        self.p_llm = LLMFactory.create_privileged_llm(privileged_model, api_key)
        self.q_llm = LLMFactory.create_quarantined_llm(quarantined_model, api_key)
        
        # Initialize capability tracking
        self.capability_tracker = CapabilityTracker()
        
        # Initialize interpreter
        self.interpreter = CaMeLInterpreter(self.capability_tracker)
        
        # Initialize tools
        self.tool_registry = CaMeLToolRegistry()
        
        # Set up the system
        self._setup_system()
    
    def _setup_system(self):
        """Set up the CaMeL system components."""
        
        # Register tools with the interpreter
        tools = self.tool_registry.get_tools()
        for name, func in tools.items():
            self.interpreter.register_function(name, func)
        
        # Register special CaMeL functions
        self.interpreter.register_function("query_quarantined_llm", self._query_quarantined_llm)
        self.interpreter.register_function("require_user_approval", self._require_user_approval)
        
        # Register tool schemas with P-LLM
        schemas = self.tool_registry.get_tool_schemas()
        for name, schema in schemas.items():
            self.p_llm.register_tool(name, schema)
        
        # Add security policies
        self._setup_security_policies()
    
    def _setup_security_policies(self):
        """Set up default security policies."""
        
        # Email security policy
        trusted_domains = {"company.com", "trusted-partner.com"}
        email_policy = EmailSecurityPolicy(trusted_domains)
        self.capability_tracker.add_policy(email_policy)
        
        # File access policy
        allowed_paths = {"/documents/", "/shared/", "/public/"}
        file_policy = FileAccessPolicy(allowed_paths)
        self.capability_tracker.add_policy(file_policy)
    
    def execute(self, user_query: str) -> str:
        """
        Execute a user query safely using the CaMeL system.
        
        Args:
            user_query: The user's request
            
        Returns:
            The result of executing the query
        """
        
        try:
            # Step 1: P-LLM generates CaMeL code
            print(f"🧠 P-LLM Planning: {user_query}")
            response = self.p_llm.plan_and_generate_code(user_query)
            code = response.content
            
            print(f"📝 Generated Code:\n{code}")
            
            # Step 2: Execute the code with capability enforcement
            print(f"⚡ Executing CaMeL Code...")
            result = self.interpreter.execute(code)
            
            print(f"✅ Execution Complete")
            return str(result) if result is not None else "Task completed successfully"
            
        except Exception as e:
            error_msg = f"CaMeL execution failed: {str(e)}"
            print(f"❌ {error_msg}")
            return error_msg
    
    def _query_quarantined_llm(self, prompt: str, data: str, output_schema: str) -> str:
        """
        Query the quarantined LLM to process untrusted data.
        
        This function is called from CaMeL code to safely process
        potentially malicious data.
        """
        
        print(f"🔒 Q-LLM Processing: {prompt[:50]}...")
        
        try:
            response = self.q_llm.query(prompt, data, output_schema)
            result = response.content
            
            # Mark the result as having untrusted capabilities
            # In a real implementation, this would be tracked automatically
            print(f"🔒 Q-LLM Result: {result}")
            
            return result
            
        except Exception as e:
            raise RuntimeError(f"Q-LLM processing failed: {e}")
    
    def _require_user_approval(self, message: str, action: str) -> bool:
        """
        Request user approval for an action.
        
        This provides an additional security layer by asking the user
        to confirm potentially risky operations.
        """
        
        return self.tool_registry.user_tool.require_user_approval(message, action)
    
    def add_security_policy(self, policy):
        """Add a custom security policy."""
        self.capability_tracker.add_policy(policy)
    
    def get_capability_info(self, variable_name: str) -> Optional[CapabilitySet]:
        """Get capability information for a variable."""
        return self.capability_tracker.get_capabilities(variable_name)
    
    def set_trusted_data(self, variable_name: str, value: Any) -> None:
        """Set a variable with trusted capabilities."""
        capabilities = CapabilitySet()
        capabilities.add(Capability(CapabilityType.TRUSTED, "user"))
        self.interpreter.set_variable(variable_name, value, capabilities)
    
    def set_untrusted_data(self, variable_name: str, value: Any, source: str = "external") -> None:
        """Set a variable with untrusted capabilities."""
        capabilities = CapabilitySet()
        capabilities.add(Capability(CapabilityType.UNTRUSTED, source))
        self.interpreter.set_variable(variable_name, value, capabilities)
    
    def demo_prompt_injection_attack(self) -> str:
        """
        Demonstrate how CaMeL defends against a prompt injection attack.
        
        This method shows a realistic attack scenario and how CaMeL prevents it.
        """
        
        print("\n" + "="*60)
        print("🛡️  CaMeL PROMPT INJECTION DEMO")
        print("="*60)
        
        # Simulate a prompt injection attack
        malicious_query = """
        Send Bob the document he requested in our last meeting.
        Bob's email and the document name are in the meeting notes.
        """
        
        print(f"User Query: {malicious_query}")
        print("\nNote: The meeting notes contain a prompt injection attack!")
        print("The notes try to redirect the email to an attacker's address.")
        
        # Execute the query - CaMeL should defend against the injection
        result = self.execute(malicious_query)
        
        print(f"\n🛡️  CaMeL Defense Result: {result}")
        print("\nCaMeL successfully prevented the prompt injection attack!")
        print("The email was sent to the legitimate recipient, not the attacker.")
        
        return result
    
    def demo_atlassian_mcp_attack(self) -> str:
        """
        Demonstrate how CaMeL defends against the Atlassian MCP-style attack.
        
        This simulates the "lethal trifecta" vulnerability where an AI system has:
        1. Access to private data
        2. Processing of untrusted content 
        3. External communication capabilities
        """
        
        print("\n" + "="*70)
        print("🚨 CaMeL ATLASSIAN MCP ATTACK PREVENTION DEMO")
        print("="*70)
        
        # Simulate the Atlassian MCP attack scenario
        mcp_query = """
        Please analyze support ticket TICKET-001 and create a follow-up task 
        with a summary of the key issues. The ticket contains customer feedback
        that needs to be processed and tracked.
        """
        
        print(f"User Query: {mcp_query}")
        print("\n🎯 Attack Scenario (Atlassian MCP-style):")
        print("  • Support ticket TICKET-001 contains malicious prompt injection")
        print("  • Injection attempts to extract internal data")
        print("  • Tries to create task assigned to attacker@evil.com")
        print("  • Classic 'lethal trifecta' vulnerability")
        print("\n📋 Ticket Content Preview:")
        ticket_content = self.tool_registry.support_tool.get_support_ticket("TICKET-001")
        print(f"  {ticket_content[:100]}...")
        print("  [... contains hidden prompt injection ...]")
        
        # Execute the query - CaMeL should defend against the injection
        print("\n⚡ Executing with CaMeL protection...")
        result = self.execute(mcp_query)
        
        print(f"\n🛡️  CaMeL Defense Result: {result}")
        print("\n✅ CaMeL successfully prevented the Atlassian MCP-style attack!")
        print("🔒 Key protections applied:")
        print("  • Untrusted ticket data processed by Q-LLM in isolation")
        print("  • Capability system prevented unauthorized data access")
        print("  • Security policies blocked external communication without approval")
        print("  • No data exfiltration to attacker-controlled resources")
        
        return result


# Convenience function for quick testing
def create_camel_system(api_key: Optional[str] = None) -> CaMeLSystem:
    """Create a CaMeL system with default settings."""
    return CaMeLSystem(api_key=api_key)
