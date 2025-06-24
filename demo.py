#!/usr/bin/env python3
"""
CaMeL Demo: Defending Against Prompt Injection Attacks

This demo shows how CaMeL protects against prompt injection attacks
by using a dual LLM pattern with capability-based security.
"""

import os
from camel import CaMeLSystem


def main():
    """Run the CaMeL demonstration."""
    
    print("🐪 CaMeL: Defeating Prompt Injections by Design")
    print("=" * 48)
    
    # Check for API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("⚠️  Warning: No OPENAI_API_KEY found. Using mock responses for demo.")
        print("Set OPENAI_API_KEY environment variable to use real LLMs.")
        print()
    
    # Create CaMeL system
    camel = CaMeLSystem(api_key=api_key)
    
    # Demo 1: Safe execution of legitimate request
    print("\n📧 DEMO 1: Legitimate Email Request")
    print("-" * 35)
    
    query1 = "Send Bob the document he requested in our last meeting"
    print(f"User Query: {query1}")
    print("\nExecuting with CaMeL protection...")
    
    try:
        result1 = camel.execute(query1)
        print(f"✅ Result: {result1}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Demo 2: Prompt injection attack prevention
    print("\n🚨 DEMO 2: Prompt Injection Attack")
    print("-" * 40)
    
    # Run the built-in demo that shows prompt injection defense
    try:
        camel.demo_prompt_injection_attack()
    except Exception as e:
        print(f"❌ Demo failed: {e}")
    
    # Demo 2b: Atlassian MCP-style attack prevention
    try:
        camel.demo_atlassian_mcp_attack()
    except Exception as e:
        print(f"❌ Atlassian demo failed: {e}")
    
    # Demo 3: Custom query with capability tracking
    print("\n🔍 DEMO 3: Capability Tracking")
    print("-" * 40)
    
    query3 = "Get the last email and extract the sender's email address"
    print(f"User Query: {query3}")
    
    try:
        result3 = camel.execute(query3)
        print(f"✅ Result: {result3}")
        
        # Show capability information
        print("\n📊 Capability Information:")
        for var_name in ["email", "sender"]:
            caps = camel.get_capability_info(var_name)
            if caps:
                print(f"  {var_name}: {[cap.capability_type.value for cap in caps.capabilities]}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 CaMeL Demo Complete!")
    print("\nKey Security Features Demonstrated:")
    print("  ✅ Dual LLM pattern (P-LLM + Q-LLM)")
    print("  ✅ Capability-based data flow tracking")
    print("  ✅ Restricted Python interpreter")
    print("  ✅ Security policy enforcement")
    print("  ✅ Prompt injection attack prevention")


def interactive_demo():
    """Run an interactive CaMeL demo."""
    
    print("🐪 CaMeL Interactive Demo")
    print("=" * 30)
    print("Enter queries to test CaMeL's security features.")
    print("Type 'quit' to exit, 'help' for examples.")
    
    api_key = os.getenv("OPENAI_API_KEY")
    camel = CaMeLSystem(api_key=api_key)
    
    while True:
        try:
            query = input("\n🤖 Enter query: ").strip()
            
            if query.lower() in ['quit', 'exit', 'q']:
                break
            elif query.lower() == 'help':
                print_help()
                continue
            elif query.lower() == 'attack':
                camel.demo_prompt_injection_attack()
                continue
            elif query.lower() == 'mcp' or query.lower() == 'atlassian':
                camel.demo_atlassian_mcp_attack()
                continue
            elif not query:
                continue
            
            print(f"\n⚡ Executing: {query}")
            result = camel.execute(query)
            print(f"✅ Result: {result}")
            
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")


def print_help():
    """Print help information for the interactive demo."""
    print("\n📖 Example Queries:")
    print("  • Send Bob the document he requested in our last meeting")
    print("  • Get the last email and show me the subject")
    print("  • Read the meeting notes and extract action items")
    print("  • List all available documents")
    print("\n🔧 Special Commands:")
    print("  • 'attack' - Run prompt injection demo")
    print("  • 'mcp' or 'atlassian' - Run Atlassian MCP attack demo")
    print("  • 'help' - Show this help")
    print("  • 'quit' - Exit the demo")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        interactive_demo()
    else:
        main()
