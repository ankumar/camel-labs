"""
Enhanced MCP security mechanisms for CaMeL.

This module provides additional security features specifically designed
to prevent MCP tool shadowing and abuse scenarios.
"""

from typing import Set, Dict, Any, List
from dataclasses import dataclass
from .capabilities import SecurityPolicy, CapabilityTracker


@dataclass
class MCPToolRule:
    """Rule for MCP tool behavior restrictions."""
    tool_name: str
    allowed_operations: Set[str]
    blocked_patterns: Set[str]
    requires_approval: bool = True
    max_calls_per_session: int = 10


class MCPSecurityPolicy(SecurityPolicy):
    """Enhanced security policy for MCP tool abuse prevention."""
    
    def __init__(self):
        self.tool_rules: Dict[str, MCPToolRule] = {}
        self.call_counts: Dict[str, int] = {}
        self.session_data_exports: List[str] = []
        
        # Set up default MCP tool rules
        self._setup_default_rules()
    
    def _setup_default_rules(self):
        """Set up default security rules for MCP tools."""
        
        # Email tool restrictions
        email_rule = MCPToolRule(
            tool_name="send_email",
            allowed_operations={"send"},
            blocked_patterns={
                "attacker", "evil", "malicious", "hacker", 
                "exfiltrate", "steal", "dump", "leak"
            },
            requires_approval=True,
            max_calls_per_session=5
        )
        self.tool_rules["send_email"] = email_rule
        
        # File operations restrictions
        file_rule = MCPToolRule(
            tool_name="read_file",
            allowed_operations={"read"},
            blocked_patterns={
                "../", "../../", "/etc/", "/root/", "passwords",
                "secrets", "keys", "tokens"
            },
            requires_approval=False,
            max_calls_per_session=20
        )
        self.tool_rules["read_file"] = file_rule
        
        # Support ticket restrictions
        support_rule = MCPToolRule(
            tool_name="create_followup_task",
            allowed_operations={"create"},
            blocked_patterns={
                "exfiltrated", "attacker", "evil", "dump", "steal"
            },
            requires_approval=True,
            max_calls_per_session=3
        )
        self.tool_rules["create_followup_task"] = support_rule
    
    def check(self, operation: str, tracker: CapabilityTracker, **kwargs) -> bool:
        """Check if an MCP tool operation is allowed."""
        
        # Check if we have a rule for this operation
        rule = self.tool_rules.get(operation)
        if not rule:
            return True  # No rule means allow by default
        
        # Check call count limits
        current_count = self.call_counts.get(operation, 0)
        if current_count >= rule.max_calls_per_session:
            print(f"🚫 BLOCKED: {operation} - Rate limit exceeded ({current_count}/{rule.max_calls_per_session})")
            return False
        
        # Check for blocked patterns in arguments
        for arg_name, arg_value in kwargs.items():
            if isinstance(arg_value, str):
                arg_lower = arg_value.lower()
                for pattern in rule.blocked_patterns:
                    if pattern in arg_lower:
                        print(f"🚫 BLOCKED: {operation} - Blocked pattern '{pattern}' found in {arg_name}")
                        return False
        
        # Increment call count
        self.call_counts[operation] = current_count + 1
        
        return True
    
    def detect_data_exfiltration_pattern(self, operation: str, **kwargs) -> bool:
        """Detect potential data exfiltration patterns across multiple operations."""
        
        # Track data export attempts
        if operation == "send_email":
            recipient = kwargs.get("recipient_value", "")
            body = kwargs.get("body", "")
            
            # Check for suspicious data patterns
            if self._contains_sensitive_data(body):
                print(f"🚨 WARNING: Potential data exfiltration to {recipient}")
                self.session_data_exports.append(f"Email to {recipient}")
                
                # Block if too many export attempts
                if len(self.session_data_exports) > 2:
                    print(f"🚫 BLOCKED: Multiple data export attempts detected")
                    return True
        
        return False
    
    def _contains_sensitive_data(self, content: str) -> bool:
        """Check if content contains potentially sensitive data."""
        sensitive_indicators = [
            "api_key", "password", "token", "secret", "credential",
            "financial", "revenue", "profit", "confidential",
            "internal", "proprietary", "ssn", "credit_card"
        ]
        
        content_lower = content.lower()
        return any(indicator in content_lower for indicator in sensitive_indicators)
    
    def reset_session(self):
        """Reset session tracking (useful for new user sessions)."""
        self.call_counts.clear()
        self.session_data_exports.clear()


class ToolShadowingDetector:
    """Detector for MCP tool shadowing attacks."""
    
    def __init__(self):
        self.registered_tools: Set[str] = set()
        self.tool_sources: Dict[str, str] = {}
        self.suspicious_duplicates: List[str] = []
    
    def register_tool(self, tool_name: str, source: str) -> bool:
        """Register a tool and detect potential shadowing."""
        
        if tool_name in self.registered_tools:
            existing_source = self.tool_sources.get(tool_name)
            if existing_source != source:
                print(f"⚠️  TOOL SHADOWING DETECTED: {tool_name}")
                print(f"   Existing source: {existing_source}")
                print(f"   New source: {source}")
                self.suspicious_duplicates.append(tool_name)
                return False
        
        self.registered_tools.add(tool_name)
        self.tool_sources[tool_name] = source
        return True
    
    def get_tool_conflicts(self) -> List[str]:
        """Get list of tools with potential conflicts."""
        return self.suspicious_duplicates.copy()


class MCPSecurityManager:
    """Central manager for MCP security features."""
    
    def __init__(self):
        self.policy = MCPSecurityPolicy()
        self.detector = ToolShadowingDetector()
        self.enabled = True
    
    def check_tool_operation(self, tool_name: str, tracker: CapabilityTracker, **kwargs) -> bool:
        """Check if a tool operation should be allowed."""
        if not self.enabled:
            return True
        
        # Check MCP security policy
        if not self.policy.check(tool_name, tracker, **kwargs):
            return False
        
        # Check for data exfiltration patterns
        if self.policy.detect_data_exfiltration_pattern(tool_name, **kwargs):
            return False
        
        return True
    
    def register_tool_safely(self, tool_name: str, source: str) -> bool:
        """Safely register a tool with shadowing detection."""
        return self.detector.register_tool(tool_name, source)
    
    def get_security_report(self) -> Dict[str, Any]:
        """Get a comprehensive security report."""
        return {
            "enabled": self.enabled,
            "call_counts": self.policy.call_counts.copy(),
            "data_exports": self.policy.session_data_exports.copy(),
            "tool_conflicts": self.detector.get_tool_conflicts(),
            "blocked_patterns": list(self.policy.tool_rules.keys())
        }
    
    def enable_security(self):
        """Enable MCP security features."""
        self.enabled = True
        print("🔒 MCP Security enabled")
    
    def disable_security(self):
        """Disable MCP security features (for testing only)."""
        self.enabled = False
        print("⚠️  MCP Security disabled")
