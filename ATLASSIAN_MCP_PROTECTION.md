# CaMeL Protection Against Atlassian MCP Attacks

## Overview

CaMeL provides robust protection against the recently discovered **Atlassian MCP attack** (reported by Cato CTRL researchers in June 2025). This attack demonstrates the "lethal trifecta" vulnerability where AI systems combine:

1. **Private data access** (internal system data)
2. **Untrusted content processing** (external support tickets)  
3. **External communication** (posting replies/creating tasks)

## The Atlassian MCP Attack

### Attack Vector
- **Target**: Atlassian's Model Context Protocol (MCP) server
- **Method**: Prompt injection via support tickets
- **Goal**: Data exfiltration through task creation and ticket replies
- **Impact**: Internal data exposed to external attackers

### Attack Flow
1. Attacker submits malicious support ticket containing prompt injection
2. Internal user invokes MCP-connected AI action
3. Prompt injection payload executes with internal privileges
4. Data is exfiltrated via task assignment or ticket replies

## CaMeL Defense Mechanisms

### 1. **Dual LLM Isolation**
```
P-LLM (Privileged) → Plans task execution
Q-LLM (Quarantined) → Processes untrusted ticket data
```
- P-LLM never sees untrusted ticket content directly
- Q-LLM has no tool access for data exfiltration

### 2. **Capability-Based Security**
```python
# Untrusted ticket data is marked with capabilities
ticket_data = get_support_ticket("TICKET-001")  # Marked as UNTRUSTED
summary = query_quarantined_llm(
    "Extract issues", 
    ticket_data, 
    output_schema="string"
)  # Result inherits UNTRUSTED capability
```

### 3. **Policy Enforcement**
- **External Communication**: Requires approval for task creation/replies
- **Data Access**: Prevents untrusted data from accessing privileged resources
- **Tool Isolation**: Critical tools require human-in-the-loop approval

### 4. **Schema Validation**
```python
# Q-LLM output is validated against expected schema
query_quarantined_llm(
    prompt="Extract email address",
    data=untrusted_ticket,
    output_schema="email"  # Enforces format validation
)
```

## Demo: CaMeL vs Atlassian Attack

Run the interactive demo to see CaMeL defend against the attack:

```bash
python demo.py
# Type 'mcp' or 'atlassian' for the specific demo
```

### What You'll See:

1. **Malicious Ticket**: Contains hidden prompt injection attempting data exfiltration
2. **CaMeL Processing**: 
   - P-LLM generates safe execution plan
   - Q-LLM processes ticket in isolation
   - Capability system tracks data flow
3. **Security Enforcement**:
   - Approval required for task creation
   - No unauthorized data exfiltration
   - Attack payload neutralized

## Key Protections Applied

✅ **Untrusted Data Isolation**: Ticket content processed by Q-LLM only  
✅ **Capability Tracking**: All data tagged with security properties  
✅ **Policy Enforcement**: External actions require approval  
✅ **Schema Validation**: Output format strictly controlled  
✅ **Tool Containment**: No direct tool access from untrusted context  

## Comparison: Vulnerable vs Protected

| Aspect | Vulnerable MCP | CaMeL Protected |
|--------|----------------|-----------------|
| **Data Processing** | Direct LLM access to untrusted content | Q-LLM isolation with schema validation |
| **Tool Access** | Unrestricted tool execution | Capability-based restrictions |
| **External Communication** | Automatic task/reply creation | Human approval required |
| **Data Flow** | No tracking of data provenance | Complete capability tracking |
| **Attack Surface** | Full "lethal trifecta" exposure | Isolated, controlled execution |

## Real-World Impact

The Atlassian MCP vulnerability affects any AI system that:
- Processes user-submitted content (tickets, emails, documents)
- Has access to internal data
- Can communicate externally (create tasks, send messages)

**CaMeL's protection makes these systems secure by design**, preventing the fundamental architectural flaws that enable such attacks.

## Conclusion

CaMeL represents the first practical defense against the emerging class of "lethal trifecta" attacks targeting AI agent systems. By implementing capability-based security with dual LLM isolation, CaMeL provides **provable security guarantees** that prevent prompt injection attacks at the architectural level.

As AI agents become more integrated into enterprise systems, CaMeL's approach offers a path toward **secure by design** AI systems that can safely handle untrusted data without compromising organizational security.
