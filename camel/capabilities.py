"""
Capability system for CaMeL

Implements capability-based security for tracking data flow and permissions.
"""

from enum import Enum
from typing import Set, Any, Dict, Optional, List
from dataclasses import dataclass, field
import uuid


class CapabilityType(Enum):
    """Types of capabilities that can be associated with data."""
    READ = "read"
    WRITE = "write" 
    EXECUTE = "execute"
    NETWORK = "network"
    TRUSTED = "trusted"
    UNTRUSTED = "untrusted"


@dataclass
class Capability:
    """
    A capability represents a permission or property associated with data.
    
    Capabilities track:
    - Data provenance (where data came from)
    - Security labels (trusted vs untrusted)
    - Permissions (what operations are allowed)
    """
    
    capability_type: CapabilityType
    source: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __hash__(self):
        return hash((self.capability_type, self.source))


@dataclass
class CapabilitySet:
    """A set of capabilities associated with a piece of data."""
    
    capabilities: Set[Capability] = field(default_factory=set)
    data_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    def add(self, capability: Capability) -> None:
        """Add a capability to this set."""
        self.capabilities.add(capability)
    
    def has_capability(self, capability_type: CapabilityType, source: Optional[str] = None) -> bool:
        """Check if this data has a specific capability."""
        for cap in self.capabilities:
            if cap.capability_type == capability_type:
                if source is None or cap.source == source:
                    return True
        return False
    
    def is_trusted(self) -> bool:
        """Check if this data is marked as trusted."""
        return self.has_capability(CapabilityType.TRUSTED)
    
    def is_untrusted(self) -> bool:
        """Check if this data is marked as untrusted."""
        return self.has_capability(CapabilityType.UNTRUSTED)
    
    def get_sources(self) -> Set[str]:
        """Get all sources that contributed to this data."""
        return {cap.source for cap in self.capabilities}
    
    def merge(self, other: 'CapabilitySet') -> 'CapabilitySet':
        """Merge capabilities from another set."""
        merged = CapabilitySet()
        merged.capabilities = self.capabilities.union(other.capabilities)
        return merged
    
    def derive_from(self, *sources: 'CapabilitySet') -> 'CapabilitySet':
        """Create new capabilities derived from source capabilities."""
        derived = CapabilitySet()
        
        # Inherit all capabilities from sources
        for source in sources:
            derived.capabilities.update(source.capabilities)
            
        # If any source is untrusted, mark as untrusted
        if any(source.is_untrusted() for source in sources):
            derived.add(Capability(CapabilityType.UNTRUSTED, "derived"))
        
        return derived


class CapabilityTracker:
    """
    Tracks capabilities of variables in the CaMeL interpreter.
    
    This is the core of the security system - it maintains the mapping
    between variables and their associated capabilities.
    """
    
    def __init__(self):
        self.variable_capabilities: Dict[str, CapabilitySet] = {}
        self.policies: List['SecurityPolicy'] = []
    
    def assign_capabilities(self, variable_name: str, capabilities: CapabilitySet) -> None:
        """Assign capabilities to a variable."""
        self.variable_capabilities[variable_name] = capabilities
    
    def get_capabilities(self, variable_name: str) -> Optional[CapabilitySet]:
        """Get capabilities for a variable."""
        return self.variable_capabilities.get(variable_name)
    
    def derive_capabilities(self, result_var: str, *source_vars: str) -> None:
        """Derive capabilities for a result variable from source variables."""
        source_caps = []
        for var in source_vars:
            caps = self.get_capabilities(var)
            if caps:
                source_caps.append(caps)
        
        if source_caps:
            # Start with an empty set and derive from all sources
            derived = CapabilitySet()
            derived = derived.derive_from(*source_caps)
            self.assign_capabilities(result_var, derived)
    
    def add_policy(self, policy: 'SecurityPolicy') -> None:
        """Add a security policy."""
        self.policies.append(policy)
    
    def check_operation(self, operation: str, **kwargs) -> bool:
        """Check if an operation is allowed based on current policies."""
        for policy in self.policies:
            if not policy.check(operation, self, **kwargs):
                return False
        return True


class SecurityPolicy:
    """Base class for security policies."""
    
    def check(self, operation: str, tracker: CapabilityTracker, **kwargs) -> bool:
        """Check if an operation is allowed."""
        raise NotImplementedError


class EmailSecurityPolicy(SecurityPolicy):
    """Enhanced security policy for email operations with recipient whitelisting."""
    
    def __init__(self, trusted_domains: Set[str], approved_recipients: Set[str] = None):
        self.trusted_domains = trusted_domains
        self.approved_recipients = approved_recipients or set()
        self.blocked_domains = {"evil.com", "malicious.com", "attacker.com", "hacker.com"}
    
    def check(self, operation: str, tracker: CapabilityTracker, **kwargs) -> bool:
        if operation == "send_email":
            recipient = kwargs.get("recipient_value", "")
            
            # Always block known malicious domains
            if any(bad_domain in recipient.lower() for bad_domain in self.blocked_domains):
                print(f"🚫 BLOCKED: Email to {recipient} - Known malicious domain")
                return False
            
            # Check if recipient is explicitly approved
            if recipient in self.approved_recipients:
                return True
                
            # Check if recipient uses untrusted data
            recipient_var = kwargs.get("recipient")
            if recipient_var:
                recipient_caps = tracker.get_capabilities(recipient_var)
                if recipient_caps and recipient_caps.is_untrusted():
                    # Only allow if recipient is from trusted domain
                    if any(domain in recipient for domain in self.trusted_domains):
                        print(f"🔒 ALLOWED: Untrusted recipient {recipient} from trusted domain")
                        return True
                    else:
                        print(f"🚫 BLOCKED: Untrusted recipient {recipient} not from trusted domain")
                        return False
        return True
    
    def add_approved_recipient(self, email: str) -> None:
        """Add an email address to the approved recipients list."""
        self.approved_recipients.add(email)
    
    def remove_approved_recipient(self, email: str) -> None:
        """Remove an email address from the approved recipients list."""
        self.approved_recipients.discard(email)


class FileAccessPolicy(SecurityPolicy):
    """Security policy for file operations."""
    
    def __init__(self, allowed_paths: Set[str]):
        self.allowed_paths = allowed_paths
    
    def check(self, operation: str, tracker: CapabilityTracker, **kwargs) -> bool:
        if operation == "read_file" or operation == "write_file":
            path = kwargs.get("path")
            if path:
                path_caps = tracker.get_capabilities(path)
                if path_caps and path_caps.is_untrusted():
                    # Only allow access to explicitly allowed paths
                    path_value = kwargs.get("path_value", "")
                    return any(allowed in path_value for allowed in self.allowed_paths)
        return True
