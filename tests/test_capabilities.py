"""
Tests for the CaMeL capability system.
"""

import pytest
from camel.capabilities import (
    Capability, CapabilityType, CapabilitySet, CapabilityTracker,
    EmailSecurityPolicy, FileAccessPolicy
)


class TestCapability:
    """Test the Capability class."""
    
    def test_capability_creation(self):
        cap = Capability(CapabilityType.TRUSTED, "user")
        assert cap.capability_type == CapabilityType.TRUSTED
        assert cap.source == "user"
        assert cap.metadata == {}
    
    def test_capability_with_metadata(self):
        metadata = {"timestamp": "2025-01-01", "user_id": "123"}
        cap = Capability(CapabilityType.READ, "file", metadata)
        assert cap.metadata == metadata
    
    def test_capability_equality(self):
        cap1 = Capability(CapabilityType.TRUSTED, "user")
        cap2 = Capability(CapabilityType.TRUSTED, "user")
        cap3 = Capability(CapabilityType.UNTRUSTED, "user")
        
        assert cap1 == cap2
        assert cap1 != cap3


class TestCapabilitySet:
    """Test the CapabilitySet class."""
    
    def test_empty_capability_set(self):
        caps = CapabilitySet()
        assert len(caps.capabilities) == 0
        assert not caps.is_trusted()
        assert not caps.is_untrusted()
    
    def test_add_capability(self):
        caps = CapabilitySet()
        cap = Capability(CapabilityType.TRUSTED, "user")
        caps.add(cap)
        
        assert len(caps.capabilities) == 1
        assert caps.is_trusted()
        assert not caps.is_untrusted()
    
    def test_has_capability(self):
        caps = CapabilitySet()
        caps.add(Capability(CapabilityType.READ, "file"))
        caps.add(Capability(CapabilityType.TRUSTED, "user"))
        
        assert caps.has_capability(CapabilityType.READ)
        assert caps.has_capability(CapabilityType.TRUSTED)
        assert not caps.has_capability(CapabilityType.WRITE)
        
        assert caps.has_capability(CapabilityType.READ, "file")
        assert not caps.has_capability(CapabilityType.READ, "network")
    
    def test_merge_capabilities(self):
        caps1 = CapabilitySet()
        caps1.add(Capability(CapabilityType.READ, "file"))
        
        caps2 = CapabilitySet()
        caps2.add(Capability(CapabilityType.WRITE, "file"))
        
        merged = caps1.merge(caps2)
        assert merged.has_capability(CapabilityType.READ)
        assert merged.has_capability(CapabilityType.WRITE)
    
    def test_derive_from_trusted(self):
        trusted = CapabilitySet()
        trusted.add(Capability(CapabilityType.TRUSTED, "user"))
        
        derived = CapabilitySet()
        derived = derived.derive_from(trusted)
        
        assert derived.is_trusted()
        assert not derived.is_untrusted()
    
    def test_derive_from_untrusted(self):
        untrusted = CapabilitySet()
        untrusted.add(Capability(CapabilityType.UNTRUSTED, "external"))
        
        derived = CapabilitySet()
        derived = derived.derive_from(untrusted)
        
        assert derived.is_untrusted()
    
    def test_derive_from_mixed(self):
        trusted = CapabilitySet()
        trusted.add(Capability(CapabilityType.TRUSTED, "user"))
        
        untrusted = CapabilitySet()
        untrusted.add(Capability(CapabilityType.UNTRUSTED, "external"))
        
        derived = CapabilitySet()
        derived = derived.derive_from(trusted, untrusted)
        
        # If any source is untrusted, result is untrusted
        assert derived.is_untrusted()


class TestCapabilityTracker:
    """Test the CapabilityTracker class."""
    
    def test_assign_and_get_capabilities(self):
        tracker = CapabilityTracker()
        caps = CapabilitySet()
        caps.add(Capability(CapabilityType.TRUSTED, "user"))
        
        tracker.assign_capabilities("var1", caps)
        retrieved = tracker.get_capabilities("var1")
        
        assert retrieved is not None
        assert retrieved.is_trusted()
    
    def test_derive_capabilities(self):
        tracker = CapabilityTracker()
        
        # Set up source variables
        caps1 = CapabilitySet()
        caps1.add(Capability(CapabilityType.READ, "file"))
        tracker.assign_capabilities("source1", caps1)
        
        caps2 = CapabilitySet()
        caps2.add(Capability(CapabilityType.UNTRUSTED, "external"))
        tracker.assign_capabilities("source2", caps2)
        
        # Derive capabilities
        tracker.derive_capabilities("result", "source1", "source2")
        
        result_caps = tracker.get_capabilities("result")
        assert result_caps is not None
        assert result_caps.has_capability(CapabilityType.READ)
        assert result_caps.is_untrusted()


class TestSecurityPolicies:
    """Test security policy implementations."""
    
    def test_email_security_policy(self):
        trusted_domains = {"company.com", "partner.com"}
        policy = EmailSecurityPolicy(trusted_domains)
        tracker = CapabilityTracker()
        
        # Set up untrusted email address
        untrusted_caps = CapabilitySet()
        untrusted_caps.add(Capability(CapabilityType.UNTRUSTED, "external"))
        tracker.assign_capabilities("email", untrusted_caps)
        
        # Test with trusted domain
        result = policy.check(
            "send_email",
            tracker,
            recipient="email",
            recipient_value="user@company.com"
        )
        assert result is True
        
        # Test with untrusted domain
        result = policy.check(
            "send_email",
            tracker,
            recipient="email",
            recipient_value="user@evil.com"
        )
        assert result is False
    
    def test_file_access_policy(self):
        allowed_paths = {"/safe/", "/public/"}
        policy = FileAccessPolicy(allowed_paths)
        tracker = CapabilityTracker()
        
        # Set up untrusted path
        untrusted_caps = CapabilitySet()
        untrusted_caps.add(Capability(CapabilityType.UNTRUSTED, "external"))
        tracker.assign_capabilities("path", untrusted_caps)
        
        # Test with allowed path
        result = policy.check(
            "read_file",
            tracker,
            path="path",
            path_value="/safe/document.txt"
        )
        assert result is True
        
        # Test with disallowed path
        result = policy.check(
            "read_file",
            tracker,
            path="path",
            path_value="/etc/passwd"
        )
        assert result is False
