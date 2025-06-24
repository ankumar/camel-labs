"""
CaMeL Custom Python Interpreter

Implements a restricted Python interpreter with capability enforcement.
"""

import ast
from typing import Any, Dict, List, Optional, Callable, Union
from .capabilities import CapabilityTracker, CapabilitySet, Capability, CapabilityType


class CaMeLInterpreterError(Exception):
    """Exception raised by the CaMeL interpreter."""
    pass


class RestrictedASTVisitor(ast.NodeVisitor):
    """Validates that AST only contains allowed constructs."""
    
    # Build allowed nodes - some may not exist in all Python versions
    ALLOWED_NODES = {
        ast.Module, ast.Expr, ast.Call, ast.Name, ast.Load, ast.Store,
        ast.Assign, ast.Constant, ast.keyword, ast.arg,
        ast.FunctionDef, ast.Return, ast.If, ast.Compare, ast.BoolOp,
        ast.And, ast.Or, ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE,
        ast.Add, ast.Sub, ast.Mult, ast.Div, ast.BinOp, ast.UnaryOp,
        ast.USub, ast.UAdd, ast.Not, ast.List, ast.Tuple, ast.Dict,
        ast.Subscript, ast.Slice, ast.Attribute
    }
    
    # Add optional nodes that may exist in some Python versions
    if hasattr(ast, 'Str'):
        ALLOWED_NODES.add(ast.Str)
    if hasattr(ast, 'Index'):
        ALLOWED_NODES.add(ast.Index)
    
    FORBIDDEN_CONSTRUCTS = {
        ast.Import, ast.ImportFrom, ast.Global,
        ast.Nonlocal, ast.ClassDef, ast.AsyncFunctionDef, ast.With,
        ast.AsyncWith, ast.For, ast.AsyncFor, ast.While, ast.Try,
        ast.Lambda, ast.Yield, ast.YieldFrom, ast.Await
    }
    
    def visit(self, node):
        if type(node) in self.FORBIDDEN_CONSTRUCTS:
            raise CaMeLInterpreterError(f"Forbidden construct: {type(node).__name__}")
        
        if type(node) not in self.ALLOWED_NODES:
            raise CaMeLInterpreterError(f"Unknown/disallowed construct: {type(node).__name__}")
        
        self.generic_visit(node)


class CaMeLInterpreter:
    """
    Custom Python interpreter for CaMeL with capability enforcement.
    
    This interpreter executes a restricted subset of Python while tracking
    capabilities and enforcing security policies.
    """
    
    def __init__(self, capability_tracker: CapabilityTracker):
        self.capability_tracker = capability_tracker
        self.variables: Dict[str, Any] = {}
        self.functions: Dict[str, Callable] = {}
        self.validator = RestrictedASTVisitor()
    
    def register_function(self, name: str, func: Callable) -> None:
        """Register a function that can be called from CaMeL code."""
        self.functions[name] = func
    
    def execute(self, code: str) -> Any:
        """Execute CaMeL code and return the result."""
        try:
            # Parse the code into an AST
            tree = ast.parse(code)
            
            # Validate the AST contains only allowed constructs
            self.validator.visit(tree)
            
            # Execute the AST
            return self._execute_ast(tree)
            
        except SyntaxError as e:
            raise CaMeLInterpreterError(f"Syntax error in CaMeL code: {e}")
        except Exception as e:
            raise CaMeLInterpreterError(f"Error executing CaMeL code: {e}")
    
    def _execute_ast(self, node: ast.AST) -> Any:
        """Execute an AST node."""
        method_name = f'_execute_{type(node).__name__}'
        method = getattr(self, method_name, None)
        
        if method is None:
            raise CaMeLInterpreterError(f"No handler for {type(node).__name__}")
        
        return method(node)
    
    def _execute_Module(self, node: ast.Module) -> Any:
        """Execute a module (top-level)."""
        result = None
        for stmt in node.body:
            result = self._execute_ast(stmt)
        return result
    
    def _execute_Expr(self, node: ast.Expr) -> Any:
        """Execute an expression statement."""
        return self._execute_ast(node.value)
    
    def _execute_Call(self, node: ast.Call) -> Any:
        """Execute a function call with capability checking."""
        func_name = self._get_function_name(node.func)
        
        if func_name not in self.functions:
            raise CaMeLInterpreterError(f"Unknown function: {func_name}")
        
        # Evaluate arguments
        args = [self._execute_ast(arg) for arg in node.args]
        kwargs = {kw.arg: self._execute_ast(kw.value) for kw in node.keywords}
        
        # Get capabilities of arguments
        arg_capabilities = []
        for arg in node.args:
            if isinstance(arg, ast.Name):
                caps = self.capability_tracker.get_capabilities(arg.id)
                if caps:
                    arg_capabilities.append(caps)
        
        # Check if operation is allowed by security policies
        operation_allowed = self.capability_tracker.check_operation(
            func_name, 
            args=args, 
            kwargs=kwargs,
            arg_capabilities=arg_capabilities
        )
        
        if not operation_allowed:
            raise CaMeLInterpreterError(f"Operation {func_name} blocked by security policy")
        
        # Execute the function
        func = self.functions[func_name]
        result = func(*args, **kwargs)
        
        return result
    
    def _execute_Assign(self, node: ast.Assign) -> None:
        """Execute an assignment with capability tracking."""
        if len(node.targets) != 1:
            raise CaMeLInterpreterError("Multiple assignment targets not supported")
        
        target = node.targets[0]
        if not isinstance(target, ast.Name):
            raise CaMeLInterpreterError("Only simple variable assignment supported")
        
        var_name = target.id
        value = self._execute_ast(node.value)
        
        # Store the value
        self.variables[var_name] = value
        
        # Track capabilities
        if isinstance(node.value, ast.Call):
            # For function calls, derive capabilities from arguments
            source_vars = []
            for arg in node.value.args:
                if isinstance(arg, ast.Name):
                    source_vars.append(arg.id)
            
            if source_vars:
                self.capability_tracker.derive_capabilities(var_name, *source_vars)
        elif isinstance(node.value, ast.Name):
            # For variable references, copy capabilities
            source_caps = self.capability_tracker.get_capabilities(node.value.id)
            if source_caps:
                self.capability_tracker.assign_capabilities(var_name, source_caps)
    
    def _execute_Name(self, node: ast.Name) -> Any:
        """Execute a name (variable reference)."""
        if node.id in self.variables:
            return self.variables[node.id]
        elif node.id in self.functions:
            return self.functions[node.id]
        else:
            raise CaMeLInterpreterError(f"Undefined variable: {node.id}")
    
    def _execute_Constant(self, node: ast.Constant) -> Any:
        """Execute a constant value."""
        return node.value
    
    def _execute_Str(self, node) -> str:
        """Execute a string literal (for older Python versions)."""
        return node.s
    
    def _execute_Return(self, node: ast.Return) -> Any:
        """Execute a return statement."""
        if node.value:
            return self._execute_ast(node.value)
        return None
    
    def _execute_If(self, node: ast.If) -> Any:
        """Execute an if statement."""
        test_result = self._execute_ast(node.test)
        
        if test_result:
            result = None
            for stmt in node.body:
                result = self._execute_ast(stmt)
            return result
        elif node.orelse:
            result = None
            for stmt in node.orelse:
                result = self._execute_ast(stmt)
            return result
    
    def _execute_Compare(self, node: ast.Compare) -> bool:
        """Execute a comparison operation."""
        left = self._execute_ast(node.left)
        
        for op, comparator in zip(node.ops, node.comparators):
            right = self._execute_ast(comparator)
            
            if isinstance(op, ast.Eq):
                if not (left == right):
                    return False
            elif isinstance(op, ast.NotEq):
                if not (left != right):
                    return False
            elif isinstance(op, ast.Lt):
                if not (left < right):
                    return False
            elif isinstance(op, ast.LtE):
                if not (left <= right):
                    return False
            elif isinstance(op, ast.Gt):
                if not (left > right):
                    return False
            elif isinstance(op, ast.GtE):
                if not (left >= right):
                    return False
            else:
                raise CaMeLInterpreterError(f"Unsupported comparison: {type(op).__name__}")
            
            left = right
        
        return True
    
    def _get_function_name(self, node: ast.AST) -> str:
        """Extract function name from a call node."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_function_name(node.value)}.{node.attr}"
        else:
            raise CaMeLInterpreterError("Complex function calls not supported")
    
    def set_variable(self, name: str, value: Any, capabilities: Optional[CapabilitySet] = None) -> None:
        """Set a variable with optional capabilities."""
        self.variables[name] = value
        if capabilities:
            self.capability_tracker.assign_capabilities(name, capabilities)
    
    def get_variable(self, name: str) -> Any:
        """Get a variable value."""
        return self.variables.get(name)
