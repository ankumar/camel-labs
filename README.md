# 🐪 CaMeL: Defeating Prompt Injections by Design

Implementation of the CaMeL (short for **CA**pabilities for **M**achin**E** **L**earning) system from the paper ["Defeating Prompt Injections by Design" by Debenedetti et al. (2025).](https://arxiv.org/pdf/2503.18813)

- CaMeL is short for CApabilities for MachinE Learning.
- Note that here the term capability refers to the standard security definition, and not the standard machine learning measurement of how capable models are.

## Overview

CaMeL is a robust defense against prompt injection attacks that creates a protective system layer around Large Language Models (LLMs). It works by:

1. **Dual LLM Pattern**: Uses a Privileged LLM (P-LLM) for planning and a Quarantined LLM (Q-LLM) for processing untrusted data
2. **Custom Python Interpreter**: Executes restricted Python code with capability enforcement
3. **Capability System**: Tracks data flow and enforces security policies based on data provenance
4. **Policy Enforcement**: Prevents unauthorized actions and data exfiltration

## Key Features

- **Provable Security**: Provides strong guarantees against prompt injection attacks
- **Data Flow Tracking**: Monitors how untrusted data flows through the system  
- **Capability-Based Security**: Uses capabilities to control what operations can be performed on different data
- **Custom Python DSL**: Restricted Python interpreter for safe code execution
- **Tool Integration**: Secure interface for external tools (email, file access, APIs)
- **Atlassian MCP Protection**: Defends against the latest "lethal trifecta" attacks targeting AI agent systems

## Architecture

```
User Query → P-LLM → Python Code → CaMeL Interpreter → Secure Execution
                                        ↓
                                  Q-LLM (for untrusted data)
```

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```python
from camel import CaMeLSystem

# Initialize the system
camel = CaMeLSystem()

# Execute a user query safely
result = camel.execute("Send Bob the document he requested in our last meeting")
```

## Security Guarantees

- **Control Flow Isolation**: Untrusted data cannot affect control flow
- **Data Exfiltration Prevention**: Capabilities prevent unauthorized data exfiltration  
- **Policy Enforcement**: Custom interpreter enforces security policies
- **LLM Isolation**: Dual LLM pattern isolates planning from data processing
- **Lethal Trifecta Protection**: Defends against attacks combining private data access, untrusted content, and external communication

## License

MIT License
