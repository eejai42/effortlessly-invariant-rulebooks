#!/usr/bin/env python3
"""
Shared Formula Parser for ERB Execution Substrates

This module provides a reusable formula parser that converts Excel-dialect
formulas (from effortless-rulebook.json) into an expression tree.

Each substrate then compiles the expression tree to its target language:
- Python: compile_to_python()
- JavaScript: compile_to_javascript()
- Go: compile_to_go()
- SPARQL: compile_to_sparql()
- COBOL: compile_to_cobol() / compile_to_cobol_condition()

Extracted from: execution-substrates/owl/inject-into-owl.py
"""

import re
from dataclasses import dataclass
from typing import List, Any
from enum import Enum, auto


# =============================================================================
# EXPRESSION NODE TYPES
# =============================================================================

@dataclass
class ExprNode:
    """Base class for expression nodes"""
    pass


@dataclass
class LiteralBool(ExprNode):
    value: bool


@dataclass
class LiteralInt(ExprNode):
    value: int


@dataclass
class LiteralString(ExprNode):
    value: str


@dataclass
class FieldRef(ExprNode):
    name: str  # Field name without {{ }}


@dataclass
class BinaryOp(ExprNode):
    op: str  # '=', '<>', '<', '<=', '>', '>='
    left: ExprNode
    right: ExprNode


@dataclass
class UnaryOp(ExprNode):
    op: str  # 'NOT'
    operand: ExprNode


@dataclass
class FuncCall(ExprNode):
    name: str  # 'AND', 'OR', 'IF', 'LOWER', 'FIND', 'CAST'
    args: List[ExprNode]


@dataclass
class Concat(ExprNode):
    parts: List[ExprNode]


# =============================================================================
# LEXER
# =============================================================================

class TokenType(Enum):
    STRING = auto()
    NUMBER = auto()
    FIELD_REF = auto()
    FUNC_NAME = auto()
    LPAREN = auto()
    RPAREN = auto()
    COMMA = auto()
    AMPERSAND = auto()
    EQUALS = auto()
    NOT_EQUALS = auto()
    LT = auto()
    LE = auto()
    GT = auto()
    GE = auto()
    EOF = auto()


@dataclass
class Token:
    type: TokenType
    value: Any
    pos: int


def tokenize(formula: str) -> List[Token]:
    """Tokenize an Excel-dialect formula."""
    tokens = []

    # Remove leading = if present
    if formula.startswith('='):
        formula = formula[1:]

    i = 0
    while i < len(formula):
        c = formula[i]

        # Skip whitespace
        if c in ' \t\n\r':
            i += 1
            continue

        # String literal
        if c == '"':
            j = i + 1
            while j < len(formula) and formula[j] != '"':
                if formula[j] == '\\':
                    j += 2
                else:
                    j += 1
            if j >= len(formula):
                raise SyntaxError(f"Unterminated string at position {i}")
            value = formula[i+1:j]
            tokens.append(Token(TokenType.STRING, value, i))
            i = j + 1
            continue

        # Field reference {{Name}}
        if formula[i:i+2] == '{{':
            j = formula.find('}}', i)
            if j == -1:
                raise SyntaxError(f"Unterminated field reference at position {i}")
            field_name = formula[i+2:j]
            tokens.append(Token(TokenType.FIELD_REF, field_name, i))
            i = j + 2
            continue

        # Number
        if c.isdigit() or (c == '-' and i + 1 < len(formula) and formula[i+1].isdigit()):
            j = i
            if c == '-':
                j += 1
            while j < len(formula) and formula[j].isdigit():
                j += 1
            value = int(formula[i:j])
            tokens.append(Token(TokenType.NUMBER, value, i))
            i = j
            continue

        # Operators
        if formula[i:i+2] == '<>':
            tokens.append(Token(TokenType.NOT_EQUALS, '<>', i))
            i += 2
            continue
        if formula[i:i+2] == '<=':
            tokens.append(Token(TokenType.LE, '<=', i))
            i += 2
            continue
        if formula[i:i+2] == '>=':
            tokens.append(Token(TokenType.GE, '>=', i))
            i += 2
            continue
        if c == '<':
            tokens.append(Token(TokenType.LT, '<', i))
            i += 1
            continue
        if c == '>':
            tokens.append(Token(TokenType.GT, '>', i))
            i += 1
            continue
        if c == '=':
            tokens.append(Token(TokenType.EQUALS, '=', i))
            i += 1
            continue
        if c == '&':
            tokens.append(Token(TokenType.AMPERSAND, '&', i))
            i += 1
            continue
        if c == '(':
            tokens.append(Token(TokenType.LPAREN, '(', i))
            i += 1
            continue
        if c == ')':
            tokens.append(Token(TokenType.RPAREN, ')', i))
            i += 1
            continue
        if c == ',':
            tokens.append(Token(TokenType.COMMA, ',', i))
            i += 1
            continue

        # Function names / identifiers
        if c.isalpha() or c == '_':
            j = i
            while j < len(formula) and (formula[j].isalnum() or formula[j] == '_'):
                j += 1
            name = formula[i:j].upper()
            tokens.append(Token(TokenType.FUNC_NAME, name, i))
            i = j
            continue

        raise SyntaxError(f"Unexpected character '{c}' at position {i}")

    tokens.append(Token(TokenType.EOF, None, len(formula)))
    return tokens


# =============================================================================
# PARSER
# =============================================================================

class Parser:
    """Recursive descent parser for Excel-dialect formulas."""

    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0

    def current(self) -> Token:
        return self.tokens[self.pos]

    def consume(self, expected: TokenType = None) -> Token:
        tok = self.current()
        if expected and tok.type != expected:
            raise SyntaxError(f"Expected {expected}, got {tok.type} at position {tok.pos}")
        self.pos += 1
        return tok

    def parse(self) -> ExprNode:
        result = self.parse_concat()
        if self.current().type != TokenType.EOF:
            raise SyntaxError(f"Unexpected token {self.current()} after expression")
        return result

    def parse_concat(self) -> ExprNode:
        left = self.parse_comparison()
        parts = [left]
        while self.current().type == TokenType.AMPERSAND:
            self.consume(TokenType.AMPERSAND)
            right = self.parse_comparison()
            parts.append(right)
        if len(parts) == 1:
            return parts[0]
        return Concat(parts=parts)

    def parse_comparison(self) -> ExprNode:
        left = self.parse_primary()
        op_map = {
            TokenType.EQUALS: '=',
            TokenType.NOT_EQUALS: '<>',
            TokenType.LT: '<',
            TokenType.LE: '<=',
            TokenType.GT: '>',
            TokenType.GE: '>=',
        }
        if self.current().type in op_map:
            op = op_map[self.current().type]
            self.consume()
            right = self.parse_primary()
            return BinaryOp(op=op, left=left, right=right)
        return left

    def parse_primary(self) -> ExprNode:
        tok = self.current()

        if tok.type == TokenType.STRING:
            self.consume()
            return LiteralString(value=tok.value)

        if tok.type == TokenType.NUMBER:
            self.consume()
            return LiteralInt(value=tok.value)

        if tok.type == TokenType.FIELD_REF:
            self.consume()
            return FieldRef(name=tok.value)

        if tok.type == TokenType.FUNC_NAME:
            name = tok.value.upper()
            self.consume()

            if name == 'TRUE':
                if self.current().type == TokenType.LPAREN:
                    self.consume(TokenType.LPAREN)
                    self.consume(TokenType.RPAREN)
                return LiteralBool(value=True)

            if name == 'FALSE':
                if self.current().type == TokenType.LPAREN:
                    self.consume(TokenType.LPAREN)
                    self.consume(TokenType.RPAREN)
                return LiteralBool(value=False)

            self.consume(TokenType.LPAREN)
            args = []
            if self.current().type != TokenType.RPAREN:
                args.append(self.parse_concat())
                while self.current().type == TokenType.COMMA:
                    self.consume(TokenType.COMMA)
                    args.append(self.parse_concat())
            self.consume(TokenType.RPAREN)

            if name == 'NOT' and len(args) == 1:
                return UnaryOp(op='NOT', operand=args[0])

            return FuncCall(name=name, args=args)

        if tok.type == TokenType.LPAREN:
            self.consume(TokenType.LPAREN)
            expr = self.parse_concat()
            self.consume(TokenType.RPAREN)
            return expr

        raise SyntaxError(f"Unexpected token {tok.type} at position {tok.pos}")


def parse_formula(formula_text: str) -> ExprNode:
    """Parse an Excel-dialect formula into an expression tree."""
    tokens = tokenize(formula_text)
    parser = Parser(tokens)
    return parser.parse()


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def to_snake_case(name: str) -> str:
    """Convert PascalCase/CamelCase to snake_case.

    Examples:
        HasLinearDecodingPressure -> has_linear_decoding_pressure
        StableOntologyReference -> stable_ontology_reference
        Bio_HockettScore -> bio_hockett_score
        Name -> name
    """
    # Use [^_] to avoid doubling underscores when input already has them
    s1 = re.sub('([^_])([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def to_camel_case(name: str) -> str:
    """Convert PascalCase to camelCase.

    Examples:
        HasLinearDecodingPressure -> hasLinearDecodingPressure
        Name -> name
    """
    if not name:
        return name
    return name[0].lower() + name[1:]


def to_pascal_case(snake_name: str) -> str:
    """Convert snake_case to PascalCase.

    Examples:
        has_linear_decoding_pressure -> HasLinearDecodingPressure
        name -> Name
    """
    return ''.join(word.capitalize() for word in snake_name.split('_'))


def get_field_dependencies(expr: ExprNode) -> List[str]:
    """Extract all field references from an expression tree.

    Returns a list of field names (PascalCase as they appear in formulas).
    Used for DAG ordering and dependency tracking.
    """
    deps = []

    def visit(node: ExprNode):
        if isinstance(node, FieldRef):
            if node.name not in deps:
                deps.append(node.name)
        elif isinstance(node, BinaryOp):
            visit(node.left)
            visit(node.right)
        elif isinstance(node, UnaryOp):
            visit(node.operand)
        elif isinstance(node, FuncCall):
            for arg in node.args:
                visit(arg)
        elif isinstance(node, Concat):
            for part in node.parts:
                visit(part)

    visit(expr)
    return deps


# =============================================================================
# PYTHON CODE GENERATOR
# =============================================================================

def _is_boolean_expr(expr: ExprNode) -> bool:
    """Check if an expression node produces a boolean result."""
    if isinstance(expr, LiteralBool):
        return True
    if isinstance(expr, UnaryOp) and expr.op == 'NOT':
        return True
    if isinstance(expr, BinaryOp):
        return True  # Comparisons return bool
    if isinstance(expr, FuncCall) and expr.name in ('AND', 'OR', 'NOT'):
        return True
    return False


def _compile_and_arg(expr: ExprNode) -> str:
    """Compile an AND/OR argument with appropriate boolean coercion."""
    compiled = compile_to_python(expr)
    # If it's already a boolean expression, don't wrap with 'is True'
    if _is_boolean_expr(expr):
        return compiled
    # Field references need 'is True' for None handling
    return f'({compiled} is True)'


def compile_to_python(expr: ExprNode) -> str:
    """Compile an expression tree to a Python expression.

    Handles None values by using 'is True' and 'is not True' patterns.
    Field references are converted to snake_case variable names.
    """
    if isinstance(expr, LiteralBool):
        return 'True' if expr.value else 'False'

    if isinstance(expr, LiteralInt):
        return str(expr.value)

    if isinstance(expr, LiteralString):
        return repr(expr.value)

    if isinstance(expr, FieldRef):
        return to_snake_case(expr.name)

    if isinstance(expr, UnaryOp):
        if expr.op == 'NOT':
            operand = compile_to_python(expr.operand)
            # For field refs, use 'is not True' for None safety
            if isinstance(expr.operand, FieldRef):
                return f'({operand} is not True)'
            # For other expressions, use regular not
            return f'(not {operand})'
        raise ValueError(f"Unknown unary op: {expr.op}")

    if isinstance(expr, BinaryOp):
        left = compile_to_python(expr.left)
        right = compile_to_python(expr.right)
        op_map = {'=': '==', '<>': '!=', '<': '<', '<=': '<=', '>': '>', '>=': '>='}
        return f'({left} {op_map[expr.op]} {right})'

    if isinstance(expr, FuncCall):
        if expr.name == 'AND':
            parts = [_compile_and_arg(arg) for arg in expr.args]
            return '(' + ' and '.join(parts) + ')'

        if expr.name == 'OR':
            parts = [_compile_and_arg(arg) for arg in expr.args]
            return '(' + ' or '.join(parts) + ')'

        if expr.name == 'IF':
            if len(expr.args) < 2:
                raise ValueError("IF requires at least 2 arguments")
            cond = compile_to_python(expr.args[0])
            then_val = compile_to_python(expr.args[1])
            else_val = compile_to_python(expr.args[2]) if len(expr.args) > 2 else 'None'
            return f'({then_val} if {cond} else {else_val})'

        if expr.name == 'NOT':
            if len(expr.args) != 1:
                raise ValueError("NOT requires 1 argument")
            operand = compile_to_python(expr.args[0])
            return f'({operand} is not True)'

        if expr.name == 'LOWER':
            if len(expr.args) != 1:
                raise ValueError("LOWER requires 1 argument")
            arg = compile_to_python(expr.args[0])
            return f'(({arg} or "").lower())'

        if expr.name == 'FIND':
            if len(expr.args) != 2:
                raise ValueError("FIND requires 2 arguments")
            needle = compile_to_python(expr.args[0])
            haystack = compile_to_python(expr.args[1])
            return f'({needle} in ({haystack} or ""))'

        if expr.name == 'CAST':
            # CAST(x AS TEXT) -> str(x) if x else ""
            if len(expr.args) >= 1:
                arg = compile_to_python(expr.args[0])
                return f'(str({arg}) if {arg} else "")'
            raise ValueError("CAST requires at least 1 argument")

        if expr.name == 'SUM':
            # SUM(a, b, c) -> (a + b + c)
            # Typically used as SUM(IF(cond,1,0), IF(cond,1,0), ...)
            if not expr.args:
                return '0'
            parts = [compile_to_python(arg) for arg in expr.args]
            return '(' + ' + '.join(parts) + ')'

        if expr.name == 'SUBSTITUTE':
            # SUBSTITUTE(text, old_text, new_text) -> text.replace(old_text, new_text)
            if len(expr.args) != 3:
                raise ValueError("SUBSTITUTE requires 3 arguments")
            text = compile_to_python(expr.args[0])
            old_text = compile_to_python(expr.args[1])
            new_text = compile_to_python(expr.args[2])
            return f'(({text} or "").replace({old_text}, {new_text}))'

        raise ValueError(f"Unknown function: {expr.name}")

    if isinstance(expr, Concat):
        # Use string concatenation to avoid nested f-string issues
        parts = []
        for part in expr.parts:
            if isinstance(part, LiteralString):
                parts.append(repr(part.value))
            elif isinstance(part, FieldRef):
                var = compile_to_python(part)
                parts.append(f'str({var} or "")')
            else:
                # Complex expression - wrap in str() with None handling
                expr = compile_to_python(part)
                parts.append(f'str({expr} if {expr} is not None else "")')
        return '(' + ' + '.join(parts) + ')'

    raise ValueError(f"Unknown expression node type: {type(expr)}")


# =============================================================================
# JAVASCRIPT CODE GENERATOR
# =============================================================================

def compile_to_javascript(expr: ExprNode, obj_name: str = 'candidate') -> str:
    """Compile an expression tree to a JavaScript expression.

    Uses explicit === true / !== true for proper null handling.
    Field references use camelCase with object prefix.
    """
    if isinstance(expr, LiteralBool):
        return 'true' if expr.value else 'false'

    if isinstance(expr, LiteralInt):
        return str(expr.value)

    if isinstance(expr, LiteralString):
        escaped = expr.value.replace('\\', '\\\\').replace("'", "\\'")
        return f"'{escaped}'"

    if isinstance(expr, FieldRef):
        return f'{obj_name}.{to_camel_case(expr.name)}'

    if isinstance(expr, UnaryOp):
        if expr.op == 'NOT':
            operand = compile_to_javascript(expr.operand, obj_name)
            return f'({operand} !== true)'
        raise ValueError(f"Unknown unary op: {expr.op}")

    if isinstance(expr, BinaryOp):
        left = compile_to_javascript(expr.left, obj_name)
        right = compile_to_javascript(expr.right, obj_name)
        op_map = {'=': '===', '<>': '!==', '<': '<', '<=': '<=', '>': '>', '>=': '>='}
        return f'({left} {op_map[expr.op]} {right})'

    if isinstance(expr, FuncCall):
        if expr.name == 'AND':
            parts = [f'({compile_to_javascript(arg, obj_name)} === true)' for arg in expr.args]
            return '(' + ' && '.join(parts) + ')'

        if expr.name == 'OR':
            parts = [f'({compile_to_javascript(arg, obj_name)} === true)' for arg in expr.args]
            return '(' + ' || '.join(parts) + ')'

        if expr.name == 'IF':
            if len(expr.args) < 2:
                raise ValueError("IF requires at least 2 arguments")
            cond = compile_to_javascript(expr.args[0], obj_name)
            then_val = compile_to_javascript(expr.args[1], obj_name)
            else_val = compile_to_javascript(expr.args[2], obj_name) if len(expr.args) > 2 else 'null'
            return f'({cond} ? {then_val} : {else_val})'

        if expr.name == 'NOT':
            if len(expr.args) != 1:
                raise ValueError("NOT requires 1 argument")
            operand = compile_to_javascript(expr.args[0], obj_name)
            return f'({operand} !== true)'

        if expr.name == 'LOWER':
            if len(expr.args) != 1:
                raise ValueError("LOWER requires 1 argument")
            arg = compile_to_javascript(expr.args[0], obj_name)
            return f'(({arg} || "").toLowerCase())'

        if expr.name == 'FIND':
            if len(expr.args) != 2:
                raise ValueError("FIND requires 2 arguments")
            needle = compile_to_javascript(expr.args[0], obj_name)
            haystack = compile_to_javascript(expr.args[1], obj_name)
            return f'(({haystack} || "").includes({needle}))'

        if expr.name == 'CAST':
            if len(expr.args) >= 1:
                arg = compile_to_javascript(expr.args[0], obj_name)
                return f'({arg} ? String({arg}) : "")'
            raise ValueError("CAST requires at least 1 argument")

        if expr.name == 'SUM':
            # SUM(a, b, c) -> (a + b + c)
            if not expr.args:
                return '0'
            parts = [compile_to_javascript(arg, obj_name) for arg in expr.args]
            return '(' + ' + '.join(parts) + ')'

        raise ValueError(f"Unknown function: {expr.name}")

    if isinstance(expr, Concat):
        parts = []
        for part in expr.parts:
            if isinstance(part, LiteralString):
                escaped = part.value.replace('\\', '\\\\').replace('`', '\\`').replace('$', '\\$')
                parts.append(escaped)
            else:
                var = compile_to_javascript(part, obj_name)
                parts.append('${' + f'{var} || ""' + '}')
        return '`' + ''.join(parts) + '`'

    raise ValueError(f"Unknown expression node type: {type(expr)}")


# =============================================================================
# GO CODE GENERATOR
# =============================================================================

def _compile_to_go_int(expr: ExprNode, struct_name: str, field_types: dict) -> str:
    """Compile an expression node to a Go expression that returns an int.

    This is used for SUM arguments where IF(cond, 1, 0) should return int, not string.
    """
    if isinstance(expr, LiteralInt):
        return str(expr.value)

    if isinstance(expr, FuncCall) and expr.name == 'IF':
        # IF(cond, then, else) -> func() int { if cond { return then }; return else }()
        if len(expr.args) < 2:
            raise ValueError("IF requires at least 2 arguments")
        cond = compile_to_go(expr.args[0], struct_name, field_types)
        then_val = _compile_to_go_int(expr.args[1], struct_name, field_types)
        else_val = _compile_to_go_int(expr.args[2], struct_name, field_types) if len(expr.args) > 2 else '0'
        # Wrap condition in boolVal if it's a field ref
        if isinstance(expr.args[0], FieldRef):
            cond = f'boolVal({cond})'
        return f'func() int {{ if {cond} {{ return {then_val} }}; return {else_val} }}()'

    # For other expressions, fall back to the regular compiler
    # (shouldn't happen in practice for SUM(IF(...), IF(...)))
    return compile_to_go(expr, struct_name, field_types)


def compile_to_go(expr: ExprNode, struct_name: str = 'lc', field_types: dict = None) -> str:
    """Compile an expression tree to a Go expression.

    Uses boolVal() helper for nil-safe boolean access.
    Field references use PascalCase struct field names.

    Args:
        expr: The expression node to compile
        struct_name: Variable name for the struct (e.g., 'tc' for tc.FieldName)
        field_types: Optional dict mapping field names to their datatypes
                     (e.g., {'OrderNumber': 'integer', 'Name': 'string'})
    """
    if field_types is None:
        field_types = {}

    if isinstance(expr, LiteralBool):
        return 'true' if expr.value else 'false'

    if isinstance(expr, LiteralInt):
        return str(expr.value)

    if isinstance(expr, LiteralString):
        escaped = expr.value.replace('\\', '\\\\').replace('"', '\\"')
        return f'"{escaped}"'

    if isinstance(expr, FieldRef):
        # Go struct fields are PascalCase
        field_name = expr.name  # Already PascalCase in rulebook
        return f'{struct_name}.{field_name}'

    if isinstance(expr, UnaryOp):
        if expr.op == 'NOT':
            operand = compile_to_go(expr.operand, struct_name, field_types)
            # Wrap in boolVal for nil-safe access
            if isinstance(expr.operand, FieldRef):
                return f'!boolVal({operand})'
            return f'!({operand})'
        raise ValueError(f"Unknown unary op: {expr.op}")

    if isinstance(expr, BinaryOp):
        # Handle comparisons involving field refs (pointer fields in Go)
        if isinstance(expr.left, FieldRef) and isinstance(expr.right, FieldRef):
            # Both sides are field refs - wrap both in boolVal for nil-safe comparison
            left = compile_to_go(expr.left, struct_name, field_types)
            right = compile_to_go(expr.right, struct_name, field_types)
            op_map = {'=': '==', '<>': '!=', '<': '<', '<=': '<=', '>': '>', '>=': '>='}
            return f'(boolVal({left}) {op_map[expr.op]} boolVal({right}))'

        if isinstance(expr.left, FieldRef) and isinstance(expr.right, LiteralInt):
            # Field ref compared to integer - need nil check and dereference
            left_field = expr.left.name
            right = compile_to_go(expr.right, struct_name, field_types)
            op_go = {'=': '==', '<>': '!=', '<': '<', '<=': '<=', '>': '>', '>=': '>='}[expr.op]
            if expr.op == '=':
                return f'({struct_name}.{left_field} != nil && *{struct_name}.{left_field} == {right})'
            elif expr.op == '<>':
                return f'({struct_name}.{left_field} == nil || *{struct_name}.{left_field} != {right})'
            else:
                # For <, <=, >, >= - nil is treated as false (0 comparison semantics)
                return f'({struct_name}.{left_field} != nil && *{struct_name}.{left_field} {op_go} {right})'

        if isinstance(expr.left, FieldRef) and isinstance(expr.right, LiteralBool):
            # Field ref compared to boolean literal - use boolVal for nil-safe access
            left = compile_to_go(expr.left, struct_name, field_types)
            right = compile_to_go(expr.right, struct_name, field_types)
            op_map = {'=': '==', '<>': '!='}
            return f'(boolVal({left}) {op_map[expr.op]} {right})'

        if isinstance(expr.left, FieldRef) and isinstance(expr.right, LiteralString):
            # Field ref compared to string literal - use stringVal for nil-safe access
            left = compile_to_go(expr.left, struct_name, field_types)
            right = compile_to_go(expr.right, struct_name, field_types)
            op_map = {'=': '==', '<>': '!='}
            return f'(stringVal({left}) {op_map[expr.op]} {right})'

        if isinstance(expr.left, LiteralString) and isinstance(expr.right, FieldRef):
            # String literal compared to field ref - use stringVal for nil-safe access
            left = compile_to_go(expr.left, struct_name, field_types)
            right = compile_to_go(expr.right, struct_name, field_types)
            op_map = {'=': '==', '<>': '!='}
            return f'({left} {op_map[expr.op]} stringVal({right}))'

        left = compile_to_go(expr.left, struct_name, field_types)
        right = compile_to_go(expr.right, struct_name, field_types)
        op_map = {'=': '==', '<>': '!=', '<': '<', '<=': '<=', '>': '>', '>=': '>='}
        return f'({left} {op_map[expr.op]} {right})'

    if isinstance(expr, FuncCall):
        if expr.name == 'AND':
            parts = []
            for arg in expr.args:
                compiled = compile_to_go(arg, struct_name, field_types)
                if isinstance(arg, FieldRef):
                    parts.append(f'boolVal({compiled})')
                elif isinstance(arg, UnaryOp) and arg.op == 'NOT':
                    # NOT already handles boolVal
                    parts.append(compiled)
                elif isinstance(arg, BinaryOp):
                    # Binary ops handle their own nil checks
                    parts.append(compiled)
                else:
                    parts.append(compiled)
            return '(' + ' && '.join(parts) + ')'

        if expr.name == 'OR':
            parts = []
            for arg in expr.args:
                compiled = compile_to_go(arg, struct_name, field_types)
                if isinstance(arg, FieldRef):
                    parts.append(f'boolVal({compiled})')
                else:
                    parts.append(compiled)
            return '(' + ' || '.join(parts) + ')'

        if expr.name == 'IF':
            if len(expr.args) < 2:
                raise ValueError("IF requires at least 2 arguments")
            cond = compile_to_go(expr.args[0], struct_name, field_types)
            then_val = compile_to_go(expr.args[1], struct_name, field_types)
            else_val = compile_to_go(expr.args[2], struct_name, field_types) if len(expr.args) > 2 else '""'
            # Go doesn't have ternary - generate inline func
            return f'func() string {{ if {cond} {{ return {then_val} }}; return {else_val} }}()'

        if expr.name == 'NOT':
            if len(expr.args) != 1:
                raise ValueError("NOT requires 1 argument")
            operand = compile_to_go(expr.args[0], struct_name, field_types)
            if isinstance(expr.args[0], FieldRef):
                return f'!boolVal({operand})'
            return f'!({operand})'

        if expr.name == 'LOWER':
            if len(expr.args) != 1:
                raise ValueError("LOWER requires 1 argument")
            arg = compile_to_go(expr.args[0], struct_name, field_types)
            return f'strings.ToLower(stringVal({arg}))'

        if expr.name == 'FIND':
            if len(expr.args) != 2:
                raise ValueError("FIND requires 2 arguments")
            needle = compile_to_go(expr.args[0], struct_name, field_types)
            haystack = compile_to_go(expr.args[1], struct_name, field_types)
            return f'strings.Contains(stringVal({haystack}), {needle})'

        if expr.name == 'CAST':
            if len(expr.args) >= 1:
                arg = compile_to_go(expr.args[0], struct_name, field_types)
                if isinstance(expr.args[0], FieldRef):
                    # Check field type for appropriate conversion
                    field_type = field_types.get(expr.args[0].name, 'boolean').lower()
                    if field_type == 'integer':
                        return f'intToString({arg})'
                    elif field_type == 'boolean':
                        return f'boolToString(boolVal({arg}))'
                    else:
                        return f'stringVal({arg})'
                return f'fmt.Sprintf("%v", {arg})'
            raise ValueError("CAST requires at least 1 argument")

        if expr.name == 'SUM':
            # SUM(a, b, c) -> (a + b + c)
            # Typically used as SUM(IF(cond,1,0), IF(cond,1,0), ...)
            # For Go, we need IF to return int, not string
            if not expr.args:
                return '0'
            parts = []
            for arg in expr.args:
                parts.append(_compile_to_go_int(arg, struct_name, field_types))
            return '(' + ' + '.join(parts) + ')'

        if expr.name == 'SUBSTITUTE':
            # SUBSTITUTE(text, old_text, new_text) -> strings.ReplaceAll(text, old_text, new_text)
            if len(expr.args) != 3:
                raise ValueError("SUBSTITUTE requires 3 arguments")
            text = compile_to_go(expr.args[0], struct_name, field_types)
            old_text = compile_to_go(expr.args[1], struct_name, field_types)
            new_text = compile_to_go(expr.args[2], struct_name, field_types)
            # Wrap field refs in stringVal for nil-safe access
            if isinstance(expr.args[0], FieldRef):
                text = f'stringVal({text})'
            return f'strings.ReplaceAll({text}, {old_text}, {new_text})'

        raise ValueError(f"Unknown function: {expr.name}")

    if isinstance(expr, Concat):
        parts = []
        for part in expr.parts:
            if isinstance(part, LiteralString):
                escaped = part.value.replace('\\', '\\\\').replace('"', '\\"')
                parts.append(f'"{escaped}"')
            else:
                var = compile_to_go(part, struct_name, field_types)
                if isinstance(part, FieldRef):
                    # Check field type to use appropriate conversion
                    field_type = field_types.get(part.name, 'string').lower()
                    if field_type == 'integer':
                        parts.append(f'intToString({var})')
                    elif field_type == 'boolean':
                        parts.append(f'boolToString(boolVal({var}))')
                    else:
                        parts.append(f'stringVal({var})')
                else:
                    parts.append(var)
        if len(parts) == 1:
            return parts[0]
        return ' + '.join(parts)

    raise ValueError(f"Unknown expression node type: {type(expr)}")


# =============================================================================
# CANONICAL EVALUATOR
# =============================================================================
# Direct formula evaluation for generating answer keys from the rulebook.
# This evaluator is the source of truth - all substrates must match its output.

def evaluate(formula: str, context: dict) -> any:
    """
    Evaluate a formula directly given field values.

    This is the canonical evaluator - the single source of truth for formula
    semantics. Answer keys are generated using this evaluator, and all
    execution substrates (Python, Go, Postgres, etc.) must produce identical
    results to pass conformance testing.

    Args:
        formula: An Excel-dialect formula string (e.g., "=IF({{Name}}=\"\", \"Unknown\", {{Name}})")
        context: A dict mapping field names (PascalCase) to their values

    Returns:
        The evaluated result (bool, int, str, or None)

    Example:
        >>> evaluate('={{FirstName}} & " " & {{LastName}}', {'FirstName': 'John', 'LastName': 'Doe'})
        'John Doe'
    """
    expr = parse_formula(formula)
    return _eval_expr(expr, context)


def _eval_expr(node: ExprNode, ctx: dict) -> any:
    """
    Recursively evaluate an expression node given a context dict.

    Implements Excel-style semantics:
    - None/null values propagate sensibly
    - Empty string vs None distinction preserved
    - Boolean coercion follows Excel conventions
    """
    if isinstance(node, LiteralBool):
        return node.value

    if isinstance(node, LiteralInt):
        return node.value

    if isinstance(node, LiteralString):
        return node.value

    if isinstance(node, FieldRef):
        # Field names in formulas are PascalCase
        return ctx.get(node.name)

    if isinstance(node, UnaryOp):
        if node.op == 'NOT':
            operand = _eval_expr(node.operand, ctx)
            # None is treated as False for NOT
            if operand is None:
                return True
            return not bool(operand)
        raise ValueError(f"Unknown unary op: {node.op}")

    if isinstance(node, BinaryOp):
        left = _eval_expr(node.left, ctx)
        right = _eval_expr(node.right, ctx)

        if node.op == '=':
            return left == right
        if node.op == '<>':
            return left != right
        if node.op == '<':
            # Handle None comparisons
            if left is None or right is None:
                return False
            return left < right
        if node.op == '<=':
            if left is None or right is None:
                return False
            return left <= right
        if node.op == '>':
            if left is None or right is None:
                return False
            return left > right
        if node.op == '>=':
            if left is None or right is None:
                return False
            return left >= right
        raise ValueError(f"Unknown binary op: {node.op}")

    if isinstance(node, FuncCall):
        return _eval_func(node, ctx)

    if isinstance(node, Concat):
        parts = []
        for part in node.parts:
            val = _eval_expr(part, ctx)
            # Convert None to empty string for concatenation
            parts.append(str(val) if val is not None else '')
        return ''.join(parts)

    raise ValueError(f"Unknown expression node type: {type(node)}")


def _eval_func(node: FuncCall, ctx: dict) -> any:
    """Evaluate a function call expression node."""
    name = node.name
    args = node.args

    if name == 'AND':
        for arg in args:
            val = _eval_expr(arg, ctx)
            # None or False fails AND
            if val is None or val is False or val == 0:
                return False
        return True

    if name == 'OR':
        for arg in args:
            val = _eval_expr(arg, ctx)
            # Any truthy value passes OR
            if val is True or (val is not None and val != False and val != 0):
                return True
        return False

    if name == 'NOT':
        if len(args) != 1:
            raise ValueError("NOT requires 1 argument")
        val = _eval_expr(args[0], ctx)
        if val is None:
            return True
        return not bool(val)

    if name == 'IF':
        if len(args) < 2:
            raise ValueError("IF requires at least 2 arguments")
        cond = _eval_expr(args[0], ctx)
        # Condition is truthy if not None/False/0/""
        is_true = cond is not None and cond is not False and cond != 0 and cond != ""
        if is_true:
            return _eval_expr(args[1], ctx)
        elif len(args) > 2:
            return _eval_expr(args[2], ctx)
        else:
            return None

    if name == 'LOWER':
        if len(args) != 1:
            raise ValueError("LOWER requires 1 argument")
        val = _eval_expr(args[0], ctx)
        if val is None:
            return ''
        return str(val).lower()

    if name == 'UPPER':
        if len(args) != 1:
            raise ValueError("UPPER requires 1 argument")
        val = _eval_expr(args[0], ctx)
        if val is None:
            return ''
        return str(val).upper()

    if name == 'FIND':
        if len(args) != 2:
            raise ValueError("FIND requires 2 arguments")
        needle = _eval_expr(args[0], ctx)
        haystack = _eval_expr(args[1], ctx)
        if needle is None or haystack is None:
            return False
        return str(needle) in str(haystack)

    if name == 'CAST':
        if len(args) < 1:
            raise ValueError("CAST requires at least 1 argument")
        val = _eval_expr(args[0], ctx)
        if val is None:
            return ''
        return str(val)

    if name == 'SUM':
        total = 0
        for arg in args:
            val = _eval_expr(arg, ctx)
            if val is not None and isinstance(val, (int, float)):
                total += val
        return total

    if name == 'SUBSTITUTE':
        if len(args) != 3:
            raise ValueError("SUBSTITUTE requires 3 arguments")
        text = _eval_expr(args[0], ctx)
        old_text = _eval_expr(args[1], ctx)
        new_text = _eval_expr(args[2], ctx)
        if text is None:
            return ''
        return str(text).replace(str(old_text or ''), str(new_text or ''))

    if name == 'LEFT':
        if len(args) != 2:
            raise ValueError("LEFT requires 2 arguments")
        text = _eval_expr(args[0], ctx)
        num = _eval_expr(args[1], ctx)
        if text is None:
            return ''
        return str(text)[:int(num)]

    if name == 'RIGHT':
        if len(args) != 2:
            raise ValueError("RIGHT requires 2 arguments")
        text = _eval_expr(args[0], ctx)
        num = _eval_expr(args[1], ctx)
        if text is None:
            return ''
        n = int(num)
        return str(text)[-n:] if n > 0 else ''

    if name == 'LEN':
        if len(args) != 1:
            raise ValueError("LEN requires 1 argument")
        val = _eval_expr(args[0], ctx)
        if val is None:
            return 0
        return len(str(val))

    if name == 'CONCAT':
        parts = []
        for arg in args:
            val = _eval_expr(arg, ctx)
            parts.append(str(val) if val is not None else '')
        return ''.join(parts)

    if name == 'COUNT':
        # COUNT of non-null values
        count = 0
        for arg in args:
            val = _eval_expr(arg, ctx)
            if val is not None:
                count += 1
        return count

    if name == 'AVERAGE':
        total = 0
        count = 0
        for arg in args:
            val = _eval_expr(arg, ctx)
            if val is not None and isinstance(val, (int, float)):
                total += val
                count += 1
        return total / count if count > 0 else None

    if name == 'MIN':
        values = []
        for arg in args:
            val = _eval_expr(arg, ctx)
            if val is not None and isinstance(val, (int, float)):
                values.append(val)
        return min(values) if values else None

    if name == 'MAX':
        values = []
        for arg in args:
            val = _eval_expr(arg, ctx)
            if val is not None and isinstance(val, (int, float)):
                values.append(val)
        return max(values) if values else None

    raise ValueError(f"Unknown function: {name}")


def evaluate_field(formula: str, record: dict, field_name_mapping: dict = None) -> any:
    """
    Convenience function to evaluate a formula against a record.

    Args:
        formula: The formula string
        record: A dict with snake_case field names (as stored in JSON)
        field_name_mapping: Optional dict mapping snake_case -> PascalCase
                           If None, attempts to convert automatically

    Returns:
        The evaluated result
    """
    # Build context with PascalCase keys (as used in formulas)
    context = {}
    for key, value in record.items():
        # Convert snake_case to PascalCase for the context
        pascal_key = to_pascal_case(key)
        context[pascal_key] = value
        # Also keep original key in case formula uses it directly
        context[key] = value

    return evaluate(formula, context)


# =============================================================================
# COBOL CODE GENERATOR (GnuCOBOL free-format)
# =============================================================================

def to_cobol_name(name: str) -> str:
    """Convert PascalCase/snake_case to COBOL name (uppercase with hyphens).

    Examples:
        ChosenLanguageCandidate -> CHOSEN-LANGUAGE-CANDIDATE
        Bio_HockettScore -> BIO-HOCKETT-SCORE
    """
    snake = to_snake_case(name)
    return snake.upper().replace('_', '-')


def compile_to_cobol_condition(expr: ExprNode, record_var: str) -> str:
    """Compile a boolean expression to a COBOL condition string for use after IF."""
    if isinstance(expr, LiteralBool):
        return '"true"' if expr.value else '"false"'

    if isinstance(expr, FieldRef):
        cobol_field = f"{record_var}-{to_cobol_name(expr.name)}"
        return f"{cobol_field} = 'true'"

    if isinstance(expr, UnaryOp):
        if expr.op == 'NOT':
            inner = compile_to_cobol_condition(expr.operand, record_var)
            return f"NOT ({inner})"
        raise ValueError(f"Unknown unary op: {expr.op}")

    if isinstance(expr, BinaryOp):
        left = expr.left
        right = expr.right
        if isinstance(left, FieldRef) and isinstance(right, LiteralBool):
            cobol_field = f"{record_var}-{to_cobol_name(left.name)}"
            if right.value:
                return f"{cobol_field} = 'true'"
            return f"{cobol_field} = 'false'"
        if isinstance(left, FieldRef) and isinstance(right, LiteralInt):
            cobol_field = f"{record_var}-{to_cobol_name(left.name)}"
            return f"{cobol_field} {expr.op} {right.value}"
        if isinstance(left, FieldRef) and isinstance(right, LiteralString):
            cobol_field = f"{record_var}-{to_cobol_name(left.name)}"
            esc = right.value.replace("'", "''")
            op = "=" if expr.op == "=" else " NOT ="
            return f"{cobol_field} {op} '{esc}'"
        if isinstance(left, LiteralString) and isinstance(right, FieldRef):
            cobol_field = f"{record_var}-{to_cobol_name(right.name)}"
            esc = left.value.replace("'", "''")
            op = "=" if expr.op == "=" else " NOT ="
            return f"'{esc}' {op} {cobol_field}"
        if isinstance(left, FieldRef) and isinstance(right, FieldRef):
            lf = f"{record_var}-{to_cobol_name(left.name)}"
            rf = f"{record_var}-{to_cobol_name(right.name)}"
            op = "=" if expr.op == "=" else " NOT ="
            return f"{lf} {op} {rf}"
        left_s = compile_to_cobol_value_expr(left, record_var)
        right_s = compile_to_cobol_value_expr(right, record_var)
        op_map = {'=': '=', '<>': ' NOT =', '<': '<', '<=': '< =', '>': '>', '>=': '> ='}
        return f"{left_s} {op_map[expr.op]} {right_s}"

    if isinstance(expr, FuncCall):
        if expr.name == 'AND':
            parts = [compile_to_cobol_condition(a, record_var) for a in expr.args]
            return " AND ".join(f"({p})" for p in parts)
        if expr.name == 'OR':
            parts = [compile_to_cobol_condition(a, record_var) for a in expr.args]
            return " OR ".join(f"({p})" for p in parts)
        if expr.name == 'NOT' and len(expr.args) == 1:
            return "NOT (" + compile_to_cobol_condition(expr.args[0], record_var) + ")"
        if expr.name == 'FIND':
            compile_to_cobol_value_expr(expr.args[0], record_var)
            compile_to_cobol_value_expr(expr.args[1], record_var)
            return "WS-FIND-RESULT = 'true'"  # caller sets WS-FIND-RESULT via paragraph

    raise ValueError(f"Cannot compile node to COBOL condition: {type(expr)}")


def compile_to_cobol_value_expr(expr: ExprNode, record_var: str) -> str:
    """Compile to a single COBOL value expression (literal or identifier) for MOVE or IF."""
    if isinstance(expr, LiteralBool):
        return '"true"' if expr.value else '"false"'
    if isinstance(expr, LiteralInt):
        return str(expr.value)
    if isinstance(expr, LiteralString):
        esc = expr.value.replace("'", "''")
        return f"'{esc}'"
    if isinstance(expr, FieldRef):
        return f"{record_var}-{to_cobol_name(expr.name)}"
    raise ValueError(f"Not a simple value expression: {type(expr)}")


def compile_to_cobol(
    expr: ExprNode,
    result_var: str,
    record_var: str,
    field_types: dict = None,
    temp_prefix: str = "WS-TEMP",
    temp_counter: list = None,
) -> List[str]:
    """Compile an expression tree to COBOL statements that leave the result in result_var.

    Uses free-format COBOL (GnuCOBOL -free). temp_counter is a list with one int [n];
    the generator uses temp_prefix-n for complex subexpressions and increments the int.
    """
    if field_types is None:
        field_types = {}
    if temp_counter is None:
        temp_counter = [0]

    def next_temp():
        temp_counter[0] += 1
        return f"{temp_prefix}-{temp_counter[0]}"

    if isinstance(expr, LiteralBool):
        val = '"true"' if expr.value else '"false"'
        return [f"MOVE {val} TO {result_var}"]

    if isinstance(expr, LiteralInt):
        return [f"MOVE {expr.value} TO {result_var}"]

    if isinstance(expr, LiteralString):
        esc = expr.value.replace("'", "''")
        return [f"MOVE '{esc}' TO {result_var}"]

    if isinstance(expr, FieldRef):
        src = f"{record_var}-{to_cobol_name(expr.name)}"
        return [f"MOVE {src} TO {result_var}"]

    if isinstance(expr, UnaryOp):
        if expr.op == 'NOT':
            cond = compile_to_cobol_condition(expr.operand, record_var)
            return [
                f"IF {cond}",
                f"   MOVE \"false\" TO {result_var}",
                "ELSE",
                f"   MOVE \"true\" TO {result_var}",
                "END-IF",
            ]
        raise ValueError(f"Unknown unary op: {expr.op}")

    if isinstance(expr, BinaryOp):
        try:
            left_s = compile_to_cobol_value_expr(expr.left, record_var)
        except ValueError:
            left_s = next_temp()
            lines_left = compile_to_cobol(expr.left, left_s, record_var, field_types, temp_prefix, temp_counter)
        else:
            lines_left = []
        try:
            right_s = compile_to_cobol_value_expr(expr.right, record_var)
        except ValueError:
            right_s = next_temp()
            lines_right = compile_to_cobol(expr.right, right_s, record_var, field_types, temp_prefix, temp_counter)
        else:
            lines_right = []
        op_map = {'=': '=', '<>': ' NOT =', '<': '<', '<=': '< =', '>': '>', '>=': '> ='}
        op = op_map.get(expr.op, expr.op)
        return (
            lines_left + lines_right +
            [
                f"IF {left_s} {op} {right_s}",
                f"   MOVE \"true\" TO {result_var}",
                "ELSE",
                f"   MOVE \"false\" TO {result_var}",
                "END-IF",
            ]
        )

    if isinstance(expr, FuncCall):
        if expr.name == 'AND':
            conds = [compile_to_cobol_condition(a, record_var) for a in expr.args]
            combined = " AND ".join(f"({c})" for c in conds)
            return [
                f"IF {combined}",
                f"   MOVE \"true\" TO {result_var}",
                "ELSE",
                f"   MOVE \"false\" TO {result_var}",
                "END-IF",
            ]
        if expr.name == 'OR':
            conds = [compile_to_cobol_condition(a, record_var) for a in expr.args]
            combined = " OR ".join(f"({c})" for c in conds)
            return [
                f"IF {combined}",
                f"   MOVE \"true\" TO {result_var}",
                "ELSE",
                f"   MOVE \"false\" TO {result_var}",
                "END-IF",
            ]
        if expr.name == 'IF':
            if len(expr.args) < 2:
                raise ValueError("IF requires at least 2 arguments")
            cond = compile_to_cobol_condition(expr.args[0], record_var)
            then_expr = expr.args[1]
            else_expr = expr.args[2] if len(expr.args) > 2 else LiteralString(value="")
            then_lines = compile_to_cobol(then_expr, result_var, record_var, field_types, temp_prefix, temp_counter)
            else_lines = compile_to_cobol(else_expr, result_var, record_var, field_types, temp_prefix, temp_counter)
            return [f"IF {cond}"] + ["   " + ln for ln in then_lines] + ["ELSE"] + ["   " + ln for ln in else_lines] + ["END-IF"]
        if expr.name == 'NOT':
            if len(expr.args) != 1:
                raise ValueError("NOT requires 1 argument")
            cond = compile_to_cobol_condition(expr.args[0], record_var)
            return [
                f"IF NOT ({cond})",
                f"   MOVE \"true\" TO {result_var}",
                "ELSE",
                f"   MOVE \"false\" TO {result_var}",
                "END-IF",
            ]
        if expr.name == 'LOWER':
            if len(expr.args) != 1:
                raise ValueError("LOWER requires 1 argument")
            arg = compile_to_cobol_value_expr(expr.args[0], record_var)
            return [f"MOVE FUNCTION LOWER-CASE({arg}) TO {result_var}"]
        if expr.name == 'FIND':
            if len(expr.args) != 2:
                raise ValueError("FIND requires 2 arguments")
            needle = compile_to_cobol_value_expr(expr.args[0], record_var)
            haystack = compile_to_cobol_value_expr(expr.args[1], record_var)
            return [
                f"MOVE {needle} TO WS-FIND-NEEDLE",
                f"MOVE {haystack} TO WS-FIND-HAYSTACK",
                "PERFORM FIND-CONTAINS",
                f"MOVE WS-FIND-RESULT TO {result_var}",
            ]
        if expr.name == 'CAST':
            if len(expr.args) < 1:
                raise ValueError("CAST requires at least 1 argument")
            arg_expr = expr.args[0]
            if isinstance(arg_expr, FieldRef):
                field_type = field_types.get(arg_expr.name, 'string').lower()
                src = f"{record_var}-{to_cobol_name(arg_expr.name)}"
                if field_type == 'integer':
                    return [f"MOVE {src} TO {result_var}"]
                if field_type == 'boolean':
                    return [f"MOVE {src} TO {result_var}"]
            return compile_to_cobol(arg_expr, result_var, record_var, field_types, temp_prefix, temp_counter)
        if expr.name == 'SUM':
            if not expr.args:
                return [f"MOVE 0 TO {result_var}"]
            t = next_temp()
            lines = [f"MOVE 0 TO {result_var}"]
            for arg in expr.args:
                arg_lines = compile_to_cobol(arg, t, record_var, field_types, temp_prefix, temp_counter)
                lines.extend(arg_lines)
                lines.append(f"ADD {t} TO {result_var}")
            return lines
        if expr.name == 'CONCAT':
            return compile_to_cobol(Concat(parts=list(expr.args)), result_var, record_var, field_types, temp_prefix, temp_counter)
        raise ValueError(f"Unknown function: {expr.name}")

    if isinstance(expr, Concat):
        parts = []
        for part in expr.parts:
            if isinstance(part, LiteralString):
                esc = part.value.replace("'", "''")
                parts.append(("'%s'" % esc, None))
            elif isinstance(part, FieldRef):
                fname = f"{record_var}-{to_cobol_name(part.name)}"
                parts.append((fname, None))
            else:
                t = next_temp()
                sub = compile_to_cobol(part, t, record_var, field_types, temp_prefix, temp_counter)
                parts.append((t, sub))
        lines = []
        for _, sub in parts:
            if sub is not None:
                lines.extend(sub)
        str_parts = [val + " DELIMITED BY SIZE" for val, _ in parts]
        lines.append(f"STRING {' '.join(str_parts)} INTO {result_var}")
        return lines

    raise ValueError(f"Unknown expression node type: {type(expr)}")
