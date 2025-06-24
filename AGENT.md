# CaMeL Implementation - Agent Documentation

## Project Overview

This is a complete implementation of CaMeL (CApabilities for MachinE Learning), a robust defense system against prompt injection attacks as described in the paper "Defeating Prompt Injections by Design" by Debenedetti et al. (2025).

## Architecture

### Core Components

1. **Dual LLM Pattern**
   - **Privileged LLM (P-LLM)**: Plans tasks and generates CaMeL code
   - **Quarantined LLM (Q-LLM)**: Processes untrusted data safely

2. **Capability System**
   - Tracks data provenance and security properties
   - Enforces security policies based on data flow
   - Prevents unauthorized data exfiltration

3. **Custom Python Interpreter**
   - Executes restricted Python with AST validation
   - Enforces capability-based security
   - Blocks dangerous constructs (imports, exec, etc.)

4. **Tool Registry**
   - Secure interface for external tools
   - Capability enforcement for tool operations
   - Built-in approval mechanisms

## Key Security Features

- **Prompt Injection Defense**: Untrusted data cannot affect control flow
- **Data Flow Tracking**: All data tagged with security capabilities
- **Policy Enforcement**: Configurable security policies for different operations
- **Tool Isolation**: External tools operate under strict capability constraints

## Usage

### Basic Setup
```python
from camel import CaMeLSystem

# Initialize with OpenAI API key
camel = CaMeLSystem(api_key="your-api-key")

# Execute user queries safely
result = camel.execute("Send Bob the document he requested")
```

### Running Examples
```bash
# Basic example (no API key needed)
python example.py

# Interactive demo with real LLMs
export OPENAI_API_KEY="your-key"
python demo.py

# Interactive mode
python demo.py --interactive
```

### Testing
```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test module
python -m pytest tests/test_capabilities.py -v
```

## File Structure

```
├── camel/
│   ├── __init__.py          # Main exports
│   ├── core.py              # CaMeL system integration
│   ├── capabilities.py      # Capability system
│   ├── interpreter.py       # Custom Python interpreter
│   ├── llm.py              # Dual LLM implementation
│   └── tools.py            # Example tools with security
├── tests/                   # Comprehensive test suite
├── demo.py                 # Interactive demonstration
├── example.py              # Basic usage example
└── README.md               # Project documentation
```

## Development Commands

### Installation
```bash
pip install -r requirements.txt
```

### Code Quality
- All tests pass: `python -m pytest tests/ -v`
- Type checking: Static typing used throughout
- Security focus: Capability-based access control

## Implementation Notes

### Security Guarantees
- **Control Flow Isolation**: Untrusted data cannot affect program control flow
- **Data Provenance**: All data tagged with source and security properties  
- **Policy Enforcement**: Configurable security policies prevent unauthorized operations
- **Tool Containment**: External tools operate under strict capability constraints

### Performance Considerations
- P-LLM can use powerful models (GPT-4) for planning
- Q-LLM can use smaller/local models for data processing
- Custom interpreter adds minimal overhead
- Capability tracking is lightweight

### Extensibility
- Easy to add new tools with capability enforcement
- Configurable security policies
- Pluggable LLM backends
- Custom capability types supported

## Paper Implementation Fidelity

This implementation closely follows the CaMeL paper:
- ✅ Dual LLM pattern with P-LLM and Q-LLM
- ✅ Capability-based security system
- ✅ Custom Python interpreter with AST restrictions
- ✅ Data flow tracking and policy enforcement
- ✅ Protection against prompt injection attacks
- ✅ Tool integration with security constraints

## Security Testing

The system includes protection against:
- Direct prompt injection in user queries
- Indirect prompt injection via external data sources
- Tool abuse through capability constraints
- Data exfiltration via policy enforcement
- Code injection via AST validation

Test with: `python demo.py` and try the prompt injection demo.
