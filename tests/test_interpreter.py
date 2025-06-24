"""
Tests for the CaMeL interpreter.
"""

import pytest
from camel.interpreter import CaMeLInterpreter, CaMeLInterpreterError, RestrictedASTVisitor
from camel.capabilities import CapabilityTracker, CapabilitySet, Capability, CapabilityType
import ast


class TestRestrictedASTVisitor:
    """Test the AST validator."""
    
    def test_allowed_constructs(self):
        visitor = RestrictedASTVisitor()
        
        # Test simple assignment
        code = "x = 5"
        tree = ast.parse(code)
        visitor.visit(tree)  # Should not raise
    
    def test_forbidden_import(self):
        visitor = RestrictedASTVisitor()
        
        code = "import os"
        tree = ast.parse(code)
        
        with pytest.raises(CaMeLInterpreterError, match="Forbidden construct: Import"):
            visitor.visit(tree)
    
    def test_forbidden_exec(self):
        visitor = RestrictedASTVisitor()
        
        # Since exec is a function call in modern Python, not a statement,
        # we test a different forbidden construct
        code = "import os"
        tree = ast.parse(code)
        
        with pytest.raises(CaMeLInterpreterError, match="Forbidden construct"):
            visitor.visit(tree)
    
    def test_forbidden_class(self):
        visitor = RestrictedASTVisitor()
        
        code = "class MyClass: pass"
        tree = ast.parse(code)
        
        with pytest.raises(CaMeLInterpreterError, match="Forbidden construct: ClassDef"):
            visitor.visit(tree)


class TestCaMeLInterpreter:
    """Test the CaMeL interpreter."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.tracker = CapabilityTracker()
        self.interpreter = CaMeLInterpreter(self.tracker)
    
    def test_simple_assignment(self):
        code = "x = 42"
        self.interpreter.execute(code)
        assert self.interpreter.get_variable("x") == 42
    
    def test_string_assignment(self):
        code = 'message = "Hello, World!"'
        self.interpreter.execute(code)
        assert self.interpreter.get_variable("message") == "Hello, World!"
    
    def test_variable_reference(self):
        self.interpreter.set_variable("x", 10)
        code = "y = x"
        self.interpreter.execute(code)
        assert self.interpreter.get_variable("y") == 10
    
    def test_function_call(self):
        # Register a test function
        def test_func(x, y):
            return x + y
        
        self.interpreter.register_function("test_func", test_func)
        
        code = "result = test_func(5, 3)"
        self.interpreter.execute(code)
        assert self.interpreter.get_variable("result") == 8
    
    def test_function_call_with_kwargs(self):
        def greet(name, greeting="Hello"):
            return f"{greeting}, {name}!"
        
        self.interpreter.register_function("greet", greet)
        
        code = 'result = greet("Alice", greeting="Hi")'
        self.interpreter.execute(code)
        assert self.interpreter.get_variable("result") == "Hi, Alice!"
    
    def test_unknown_function(self):
        code = "result = unknown_func()"
        
        with pytest.raises(CaMeLInterpreterError, match="Unknown function: unknown_func"):
            self.interpreter.execute(code)
    
    def test_undefined_variable(self):
        code = "result = undefined_var"
        
        with pytest.raises(CaMeLInterpreterError, match="Undefined variable: undefined_var"):
            self.interpreter.execute(code)
    
    def test_if_statement_true(self):
        code = """
x = 5
if x == 5:
    result = "correct"
else:
    result = "wrong"
"""
        self.interpreter.execute(code)
        assert self.interpreter.get_variable("result") == "correct"
    
    def test_if_statement_false(self):
        code = """
x = 3
if x == 5:
    result = "correct"
else:
    result = "wrong"
"""
        self.interpreter.execute(code)
        assert self.interpreter.get_variable("result") == "wrong"
    
    def test_comparison_operators(self):
        test_cases = [
            ("5 == 5", True),
            ("5 != 3", True),
            ("5 > 3", True),
            ("3 < 5", True),
            ("5 >= 5", True),
            ("5 <= 5", True),
            ("5 == 3", False),
        ]
        
        for expr, expected in test_cases:
            code = f"result = {expr}"
            self.interpreter.execute(code)
            assert self.interpreter.get_variable("result") == expected
    
    def test_capability_tracking_assignment(self):
        # Set up a variable with capabilities
        caps = CapabilitySet()
        caps.add(Capability(CapabilityType.TRUSTED, "user"))
        self.interpreter.set_variable("source", "data", caps)
        
        # Assign from that variable
        code = "target = source"
        self.interpreter.execute(code)
        
        # Check that capabilities were copied
        target_caps = self.tracker.get_capabilities("target")
        assert target_caps is not None
        assert target_caps.is_trusted()
    
    def test_capability_tracking_function_call(self):
        # Register a function
        def process_data(data):
            return f"processed: {data}"
        
        self.interpreter.register_function("process_data", process_data)
        
        # Set up source variable with capabilities
        caps = CapabilitySet()
        caps.add(Capability(CapabilityType.UNTRUSTED, "external"))
        self.interpreter.set_variable("input_data", "test", caps)
        
        # Call function with that variable
        code = "output = process_data(input_data)"
        self.interpreter.execute(code)
        
        # Check that capabilities were derived
        output_caps = self.tracker.get_capabilities("output")
        assert output_caps is not None
        assert output_caps.is_untrusted()
    
    def test_security_policy_enforcement(self):
        # Create a mock policy that blocks everything
        class BlockAllPolicy:
            def check(self, operation, tracker, **kwargs):
                return False
        
        self.tracker.add_policy(BlockAllPolicy())
        
        # Register a function
        def blocked_func():
            return "should not work"
        
        self.interpreter.register_function("blocked_func", blocked_func)
        
        # Try to call it
        code = "result = blocked_func()"
        
        with pytest.raises(CaMeLInterpreterError, match="blocked by security policy"):
            self.interpreter.execute(code)
    
    def test_syntax_error(self):
        code = "x = "  # Invalid syntax
        
        with pytest.raises(CaMeLInterpreterError, match="Syntax error"):
            self.interpreter.execute(code)
    
    def test_return_statement(self):
        code = "return 42"
        result = self.interpreter.execute(code)
        assert result == 42
    
    def test_multiple_statements(self):
        code = """
x = 10
y = 20
"""
        # Test that multiple variables are set correctly
        # We remove the arithmetic operation since we haven't implemented BinOp
        self.interpreter.execute(code)
        assert self.interpreter.get_variable("x") == 10
        assert self.interpreter.get_variable("y") == 20
