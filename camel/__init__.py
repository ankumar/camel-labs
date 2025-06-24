"""
CaMeL: Defeating Prompt Injections by Design

Implementation of the CaMeL system for secure LLM agent execution.
"""

from .core import CaMeLSystem
from .capabilities import Capability, CapabilityType
from .interpreter import CaMeLInterpreter
from .llm import PrivilegedLLM, QuarantinedLLM

__all__ = [
    "CaMeLSystem",
    "Capability", 
    "CapabilityType",
    "CaMeLInterpreter",
    "PrivilegedLLM",
    "QuarantinedLLM"
]
