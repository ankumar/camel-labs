# 🐪 CaMeL: Defeating Prompt Injections by Design

Implementation of the CaMeL (short for **CA**pabilities for **M**achin**E** **L**earning) system from the paper ["Defeating Prompt Injections by Design" by Debenedetti et al. (2025).](https://arxiv.org/pdf/2503.18813)

- CaMeL is short for CApabilities for MachinE Learning.
- Here the term **capability** refers to the standard security definition, and not the standard machine learning measurement of how capable models are.

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
