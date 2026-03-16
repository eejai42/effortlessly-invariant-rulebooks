#!/usr/bin/env python3
"""
Take Test - UML Execution Substrate

Supports two modes:
1. Multi-entity (--multi-entity): Uses shared erb_calc.py for all entities
2. Legacy: Uses OCL interpreter for single test-answers.json

Scaffolding that:
1. Loads generated model (schema + instances)
2. Evaluates OCL expressions to compute derived values
3. Extracts results to test-answers.json

The computation happens in the OCL interpreter, not hardcoded here.
This script is 100% domain-agnostic - all field names come from the rulebook.
"""

import argparse
import glob as glob_module
import json
import os
import re
from pathlib import Path
import sys
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Union
from enum import Enum, auto

# Add project root to path for shared imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from orchestration.shared import load_rulebook, compute_aggregations, compute_lookups

# Add Python substrate directory to path for shared library
script_dir = Path(__file__).parent.resolve()
python_substrate_dir = script_dir / ".." / "python"
sys.path.insert(0, str(python_substrate_dir))


# =============================================================================
# OCL LEXER
# =============================================================================

class OCLTokenType(Enum):
    STRING = auto()
    NUMBER = auto()
    IDENTIFIER = auto()
    DOT = auto()
    LPAREN = auto()
    RPAREN = auto()
    PLUS = auto()
    MINUS = auto()
    STAR = auto()
    SLASH = auto()
    EQ = auto()
    NEQ = auto()
    LT = auto()
    LE = auto()
    GT = auto()
    GE = auto()
    AND = auto()
    OR = auto()
    NOT = auto()
    IF = auto()
    THEN = auto()
    ELSE = auto()
    ENDIF = auto()
    TRUE = auto()
    FALSE = auto()
    COMMA = auto()
    EOF = auto()


@dataclass
class OCLToken:
    type: OCLTokenType
    value: Any
    pos: int


def ocl_tokenize(expr: str) -> List[OCLToken]:
    """Tokenize an OCL expression."""
    tokens = []
    i = 0

    keywords = {
        'and': OCLTokenType.AND,
        'or': OCLTokenType.OR,
        'not': OCLTokenType.NOT,
        'if': OCLTokenType.IF,
        'then': OCLTokenType.THEN,
        'else': OCLTokenType.ELSE,
        'endif': OCLTokenType.ENDIF,
        'true': OCLTokenType.TRUE,
        'false': OCLTokenType.FALSE,
    }

    while i < len(expr):
        c = expr[i]

        # Skip whitespace
        if c in ' \t\n\r':
            i += 1
            continue

        # String literal (single quotes in OCL)
        if c == "'":
            j = i + 1
            chars = []
            while j < len(expr) and expr[j] != "'":
                if expr[j] == '\\' and j + 1 < len(expr):
                    # Unescape: \' becomes ', \\ becomes \
                    next_char = expr[j + 1]
                    if next_char == "'":
                        chars.append("'")
                    elif next_char == "\\":
                        chars.append("\\")
                    else:
                        chars.append(next_char)
                    j += 2
                else:
                    chars.append(expr[j])
                    j += 1
            if j >= len(expr):
                raise SyntaxError(f"Unterminated string at position {i}")
            value = ''.join(chars)
            tokens.append(OCLToken(OCLTokenType.STRING, value, i))
            i = j + 1
            continue

        # Number
        if c.isdigit() or (c == '-' and i + 1 < len(expr) and expr[i+1].isdigit()):
            j = i
            if c == '-':
                j += 1
            while j < len(expr) and expr[j].isdigit():
                j += 1
            value = int(expr[i:j])
            tokens.append(OCLToken(OCLTokenType.NUMBER, value, i))
            i = j
            continue

        # Operators
        if expr[i:i+2] == '<>':
            tokens.append(OCLToken(OCLTokenType.NEQ, '<>', i))
            i += 2
            continue
        if expr[i:i+2] == '<=':
            tokens.append(OCLToken(OCLTokenType.LE, '<=', i))
            i += 2
            continue
        if expr[i:i+2] == '>=':
            tokens.append(OCLToken(OCLTokenType.GE, '>=', i))
            i += 2
            continue
        if c == '<':
            tokens.append(OCLToken(OCLTokenType.LT, '<', i))
            i += 1
            continue
        if c == '>':
            tokens.append(OCLToken(OCLTokenType.GT, '>', i))
            i += 1
            continue
        if c == '=':
            tokens.append(OCLToken(OCLTokenType.EQ, '=', i))
            i += 1
            continue
        if c == '+':
            tokens.append(OCLToken(OCLTokenType.PLUS, '+', i))
            i += 1
            continue
        if c == '-':
            tokens.append(OCLToken(OCLTokenType.MINUS, '-', i))
            i += 1
            continue
        if c == '*':
            tokens.append(OCLToken(OCLTokenType.STAR, '*', i))
            i += 1
            continue
        if c == '/':
            tokens.append(OCLToken(OCLTokenType.SLASH, '/', i))
            i += 1
            continue
        if c == '(':
            tokens.append(OCLToken(OCLTokenType.LPAREN, '(', i))
            i += 1
            continue
        if c == ')':
            tokens.append(OCLToken(OCLTokenType.RPAREN, ')', i))
            i += 1
            continue
        if c == '.':
            tokens.append(OCLToken(OCLTokenType.DOT, '.', i))
            i += 1
            continue
        if c == ',':
            tokens.append(OCLToken(OCLTokenType.COMMA, ',', i))
            i += 1
            continue

        # Identifiers and keywords
        if c.isalpha() or c == '_':
            j = i
            while j < len(expr) and (expr[j].isalnum() or expr[j] == '_'):
                j += 1
            name = expr[i:j]
            lower_name = name.lower()

            if lower_name in keywords:
                tokens.append(OCLToken(keywords[lower_name], name, i))
            else:
                tokens.append(OCLToken(OCLTokenType.IDENTIFIER, name, i))
            i = j
            continue

        raise SyntaxError(f"Unexpected character '{c}' at position {i}")

    tokens.append(OCLToken(OCLTokenType.EOF, None, len(expr)))
    return tokens


# =============================================================================
# OCL EXPRESSION NODES
# =============================================================================

@dataclass
class OCLNode:
    pass


@dataclass
class OCLLiteralBool(OCLNode):
    value: bool


@dataclass
class OCLLiteralInt(OCLNode):
    value: int


@dataclass
class OCLLiteralString(OCLNode):
    value: str


@dataclass
class OCLSelfAttr(OCLNode):
    attr: str


@dataclass
class OCLBinaryExpr(OCLNode):
    op: str
    left: OCLNode
    right: OCLNode


@dataclass
class OCLUnaryExpr(OCLNode):
    op: str
    operand: OCLNode


@dataclass
class OCLIfExpr(OCLNode):
    cond: OCLNode
    then_branch: OCLNode
    else_branch: OCLNode


@dataclass
class OCLMethodCall(OCLNode):
    obj: OCLNode
    method: str
    args: List[OCLNode]


# =============================================================================
# OCL PARSER
# =============================================================================

class OCLParser:
    """Parser for OCL expressions."""

    def __init__(self, tokens: List[OCLToken]):
        self.tokens = tokens
        self.pos = 0

    def current(self) -> OCLToken:
        return self.tokens[self.pos]

    def consume(self, expected: OCLTokenType = None) -> OCLToken:
        tok = self.current()
        if expected and tok.type != expected:
            raise SyntaxError(f"Expected {expected}, got {tok.type} at position {tok.pos}")
        self.pos += 1
        return tok

    def peek(self) -> OCLToken:
        if self.pos + 1 < len(self.tokens):
            return self.tokens[self.pos + 1]
        return self.tokens[-1]

    def parse(self) -> OCLNode:
        return self.parse_or()

    def parse_or(self) -> OCLNode:
        left = self.parse_and()
        while self.current().type == OCLTokenType.OR:
            self.consume()
            right = self.parse_and()
            left = OCLBinaryExpr(op='or', left=left, right=right)
        return left

    def parse_and(self) -> OCLNode:
        left = self.parse_not()
        while self.current().type == OCLTokenType.AND:
            self.consume()
            right = self.parse_not()
            left = OCLBinaryExpr(op='and', left=left, right=right)
        return left

    def parse_not(self) -> OCLNode:
        if self.current().type == OCLTokenType.NOT:
            self.consume()
            operand = self.parse_not()
            return OCLUnaryExpr(op='not', operand=operand)
        return self.parse_comparison()

    def parse_comparison(self) -> OCLNode:
        left = self.parse_additive()
        op_types = {
            OCLTokenType.EQ: '=',
            OCLTokenType.NEQ: '<>',
            OCLTokenType.LT: '<',
            OCLTokenType.LE: '<=',
            OCLTokenType.GT: '>',
            OCLTokenType.GE: '>=',
        }
        if self.current().type in op_types:
            op = op_types[self.current().type]
            self.consume()
            right = self.parse_additive()
            return OCLBinaryExpr(op=op, left=left, right=right)
        return left

    def parse_additive(self) -> OCLNode:
        left = self.parse_multiplicative()
        while self.current().type in (OCLTokenType.PLUS, OCLTokenType.MINUS):
            op = '+' if self.current().type == OCLTokenType.PLUS else '-'
            self.consume()
            right = self.parse_multiplicative()
            left = OCLBinaryExpr(op=op, left=left, right=right)
        return left

    def parse_multiplicative(self) -> OCLNode:
        left = self.parse_postfix()
        while self.current().type in (OCLTokenType.STAR, OCLTokenType.SLASH):
            op = '*' if self.current().type == OCLTokenType.STAR else '/'
            self.consume()
            right = self.parse_postfix()
            left = OCLBinaryExpr(op=op, left=left, right=right)
        return left

    def parse_postfix(self) -> OCLNode:
        node = self.parse_primary()

        while self.current().type == OCLTokenType.DOT:
            self.consume()
            name_tok = self.consume(OCLTokenType.IDENTIFIER)
            method_name = name_tok.value

            if self.current().type == OCLTokenType.LPAREN:
                self.consume()
                args = []
                if self.current().type != OCLTokenType.RPAREN:
                    args.append(self.parse_or())
                    while self.current().type == OCLTokenType.COMMA:
                        self.consume()
                        args.append(self.parse_or())
                self.consume(OCLTokenType.RPAREN)
                node = OCLMethodCall(obj=node, method=method_name, args=args)
            else:
                node = OCLMethodCall(obj=node, method=method_name, args=[])

        return node

    def parse_primary(self) -> OCLNode:
        tok = self.current()

        if tok.type == OCLTokenType.TRUE:
            self.consume()
            return OCLLiteralBool(value=True)

        if tok.type == OCLTokenType.FALSE:
            self.consume()
            return OCLLiteralBool(value=False)

        if tok.type == OCLTokenType.NUMBER:
            self.consume()
            return OCLLiteralInt(value=tok.value)

        if tok.type == OCLTokenType.STRING:
            self.consume()
            return OCLLiteralString(value=tok.value)

        if tok.type == OCLTokenType.IDENTIFIER:
            name = tok.value
            self.consume()

            if name.lower() == 'self' and self.current().type == OCLTokenType.DOT:
                self.consume()
                attr_tok = self.consume(OCLTokenType.IDENTIFIER)
                return OCLSelfAttr(attr=attr_tok.value)

            return OCLSelfAttr(attr=name)

        if tok.type == OCLTokenType.LPAREN:
            self.consume()
            node = self.parse_or()
            self.consume(OCLTokenType.RPAREN)
            return node

        if tok.type == OCLTokenType.IF:
            self.consume()
            cond = self.parse_or()
            self.consume(OCLTokenType.THEN)
            then_branch = self.parse_or()
            self.consume(OCLTokenType.ELSE)
            else_branch = self.parse_or()
            self.consume(OCLTokenType.ENDIF)
            return OCLIfExpr(cond=cond, then_branch=then_branch, else_branch=else_branch)

        raise SyntaxError(f"Unexpected token {tok.type} at position {tok.pos}")


def parse_ocl(expr: str) -> OCLNode:
    """Parse an OCL expression into an expression tree."""
    tokens = ocl_tokenize(expr)
    parser = OCLParser(tokens)
    return parser.parse()


# =============================================================================
# OCL INTERPRETER
# =============================================================================

class OCLInterpreter:
    """Minimal OCL interpreter for ERB formula subset."""

    def __init__(self, instance: Dict[str, Any]):
        self.instance = instance
        self.attr_lookup = {}
        for key, value in instance.items():
            # Register both the original key and a normalized version (no underscores)
            # This allows snake_case JSON keys to match camelCase OCL references
            self.attr_lookup[key.lower()] = value
            normalized = key.lower().replace('_', '')
            self.attr_lookup[normalized] = value

    def evaluate(self, expr: str) -> Any:
        expr = parse_ocl(expr)
        return self.eval_node(expr)

    def eval_node(self, node: OCLNode) -> Any:
        if isinstance(node, OCLLiteralBool):
            return node.value

        if isinstance(node, OCLLiteralInt):
            return node.value

        if isinstance(node, OCLLiteralString):
            return node.value

        if isinstance(node, OCLSelfAttr):
            # Try exact match (lowered), then normalized (no underscores)
            attr_lower = node.attr.lower()
            if attr_lower in self.attr_lookup:
                return self.attr_lookup[attr_lower]
            # Try without underscores for cross-format matching
            attr_normalized = attr_lower.replace('_', '')
            return self.attr_lookup.get(attr_normalized)

        if isinstance(node, OCLUnaryExpr):
            if node.op == 'not':
                operand = self.eval_node(node.operand)
                return not bool(operand) if operand is not None else None
            raise ValueError(f"Unknown unary op: {node.op}")

        if isinstance(node, OCLBinaryExpr):
            left = self.eval_node(node.left)
            right = self.eval_node(node.right)
            return self.apply_binary_op(node.op, left, right)

        if isinstance(node, OCLIfExpr):
            cond = self.eval_node(node.cond)
            if cond:
                return self.eval_node(node.then_branch)
            else:
                return self.eval_node(node.else_branch)

        if isinstance(node, OCLMethodCall):
            obj = self.eval_node(node.obj)
            return self.apply_method(obj, node.method, node.args)

        raise ValueError(f"Unknown node type: {type(node)}")

    def apply_binary_op(self, op: str, left: Any, right: Any) -> Any:
        if op == '+':
            if isinstance(left, str) or isinstance(right, str):
                left_str = '' if left is None else str(left)
                right_str = '' if right is None else str(right)
                return left_str + right_str
            left_num = 0 if left is None else left
            right_num = 0 if right is None else right
            return left_num + right_num

        if op == '-':
            left_num = 0 if left is None else left
            right_num = 0 if right is None else right
            return left_num - right_num

        if op == '*':
            left_num = 0 if left is None else left
            right_num = 0 if right is None else right
            return left_num * right_num

        if op == '/':
            left_num = 0 if left is None else left
            right_num = 1 if right is None or right == 0 else right
            return left_num / right_num

        if op == '=':
            return left == right

        if op == '<>':
            return left != right

        if op == '<':
            if left is None or right is None:
                return False
            return left < right

        if op == '<=':
            if left is None or right is None:
                return False
            return left <= right

        if op == '>':
            if left is None or right is None:
                return False
            return left > right

        if op == '>=':
            if left is None or right is None:
                return False
            return left >= right

        if op == 'and':
            return bool(left) and bool(right)

        if op == 'or':
            return bool(left) or bool(right)

        raise ValueError(f"Unknown binary op: {op}")

    def apply_method(self, obj: Any, method: str, args: List[OCLNode]) -> Any:
        method_lower = method.lower()

        if method_lower == 'tolower':
            return str(obj).lower() if obj is not None else ''

        if method_lower == 'toupper':
            return str(obj).upper() if obj is not None else ''

        if method_lower == 'indexof':
            if not args:
                raise ValueError("indexOf requires 1 argument")
            needle = self.eval_node(args[0])
            if obj is None:
                return -1
            return str(obj).find(str(needle))

        if method_lower == 'substring':
            if len(args) < 2:
                raise ValueError("substring requires 2 arguments")
            start = self.eval_node(args[0])
            end = self.eval_node(args[1])
            if obj is None:
                return ''
            return str(obj)[start:end]

        if method_lower == 'size':
            if obj is None:
                return 0
            return len(str(obj))

        if method_lower == 'replace':
            if len(args) < 2:
                raise ValueError("replace requires 2 arguments")
            old_text = self.eval_node(args[0])
            new_text = self.eval_node(args[1])
            if obj is None:
                return ''
            return str(obj).replace(str(old_text) if old_text else '', str(new_text) if new_text else '')

        raise ValueError(f"Unknown method: {method}")


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def camel_to_snake(name: str) -> str:
    """Convert CamelCase to snake_case for output compatibility."""
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    s2 = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
    # Normalize consecutive underscores to single underscore
    return re.sub('_+', '_', s2)


def snake_to_pascal(name: str) -> str:
    """Convert snake_case to PascalCase for OCL class lookup."""
    return ''.join(word.capitalize() for word in name.split('_'))


def parse_ocl_file(ocl_text: str) -> Dict[str, Dict[str, str]]:
    """Parse OCL constraints file into a dictionary of class -> {attr: expr}."""
    constraints = {}
    current_class = None

    for line in ocl_text.split('\n'):
        line = line.strip()

        if not line or line.startswith('--'):
            continue

        if line.startswith('context '):
            current_class = line[8:].strip()
            if current_class not in constraints:
                constraints[current_class] = {}
            continue

        if line.startswith('derive '):
            if current_class is None:
                continue
            rest = line[7:].strip()
            colon_idx = rest.find(':')
            if colon_idx == -1:
                continue
            attr_name = rest[:colon_idx].strip()
            ocl_expr = rest[colon_idx + 1:].strip()
            constraints[current_class][attr_name] = ocl_expr

    return constraints


def topological_sort_constraints(class_constraints: Dict[str, str]) -> List[tuple]:
    """Topologically sort derived attributes by their dependencies."""
    attr_names = set(class_constraints.keys())
    dependencies = {}

    for attr_name, ocl_expr in class_constraints.items():
        deps = set()
        expr_lower = ocl_expr.lower()
        for other_attr in attr_names:
            if other_attr == attr_name:
                continue
            if f'self.{other_attr.lower()}' in expr_lower:
                deps.add(other_attr)
        dependencies[attr_name] = deps

    in_degree = {attr: 0 for attr in attr_names}
    for attr, deps in dependencies.items():
        for dep in deps:
            if dep in in_degree:
                in_degree[attr] += 1

    queue = [attr for attr, degree in in_degree.items() if degree == 0]
    result = []

    while queue:
        queue.sort()
        attr = queue.pop(0)
        result.append((attr, class_constraints[attr]))

        for other_attr, deps in dependencies.items():
            if attr in deps:
                in_degree[other_attr] -= 1
                if in_degree[other_attr] == 0:
                    queue.append(other_attr)

    if len(result) != len(attr_names):
        return list(class_constraints.items())

    return result


# =============================================================================
# MULTI-ENTITY MODE (uses shared erb_calc.py)
# =============================================================================

def process_entity(input_path: str, output_path: str, entity_name: str,
                   all_constraints: Dict[str, Dict[str, str]],
                   rulebook: dict = None, project_root: Path = None) -> int:
    """Process a single entity file using OCL interpreter."""
    with open(input_path, 'r', encoding='utf-8') as f:
        records = json.load(f)

    if rulebook is not None and project_root is not None:
        # Compute lookup fields first (INDEX/MATCH)
        records = compute_lookups(records, entity_name, rulebook, project_root)
        # Then compute aggregation fields (COUNTIFS, SUMIFS)
        records = compute_aggregations(records, entity_name, rulebook, project_root)

    # Convert entity name to PascalCase for OCL class lookup
    class_name = snake_to_pascal(entity_name)
    class_constraints = all_constraints.get(class_name, {})

    if not class_constraints:
        print(f"   Warning: No OCL constraints found for class '{class_name}'")

    # Sort constraints by dependency order
    sorted_constraints = topological_sort_constraints(class_constraints)

    computed_records = []
    for record in records:
        # Create interpreter with current record values
        interpreter = OCLInterpreter(record)

        # Evaluate each derived attribute in dependency order
        for attr_name, ocl_expr in sorted_constraints:
            snake_key = camel_to_snake(attr_name)
            try:
                value = interpreter.evaluate(ocl_expr)
                record[snake_key] = value
                # Update interpreter's lookup so dependent fields can see this value
                interpreter.attr_lookup[attr_name.lower()] = value
            except Exception as e:
                print(f"   Warning: Error evaluating {attr_name}: {e}")
                record[snake_key] = None

        computed_records.append(record)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(computed_records, f, indent=2)

    return len(computed_records)


def run_multi_entity():
    """Process all entity files from shared testing/blank-tests/ directory using OCL."""
    # Use shared blank-tests directory at project root
    project_root = script_dir.parent.parent
    blank_tests_dir = project_root / "testing" / "blank-tests"
    test_answers_dir = script_dir / "test-answers"

    if not blank_tests_dir.is_dir():
        print(f"Error: {blank_tests_dir} not found")
        sys.exit(1)

    # Load rulebook for aggregation computation
    try:
        rulebook = load_rulebook()
    except FileNotFoundError as e:
        print(f"Warning: Could not load rulebook for aggregations: {e}")
        rulebook = None

    # Load OCL constraints
    ocl_path = script_dir / "constraints.ocl"
    if not ocl_path.exists():
        print(f"Error: {ocl_path} not found")
        print("Run: python inject-into-uml.py first")
        sys.exit(1)

    ocl_text = ocl_path.read_text()
    all_constraints = parse_ocl_file(ocl_text)
    total_ocl_constraints = sum(len(v) for v in all_constraints.values())

    test_answers_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("UML Execution Substrate - Multi-Entity Test Execution (OCL)")
    print("=" * 70)
    print()
    print(f"Loaded {total_ocl_constraints} OCL constraints from constraints.ocl")
    print()

    total_records = 0
    entity_count = 0

    for input_path in sorted(glob_module.glob(str(blank_tests_dir / "*.json"))):
        filename = os.path.basename(input_path)

        if filename.startswith('_'):
            continue

        entity = filename.replace('.json', '')
        output_path = test_answers_dir / filename

        count = process_entity(input_path, str(output_path), entity, all_constraints,
                               rulebook, project_root)
        total_records += count
        entity_count += 1

        print(f"  -> {entity}: {count} records (via OCL)")

    print(f"\nUML substrate: Processed {entity_count} entities, {total_records} total records")
    print("=" * 70)


# =============================================================================
# LEGACY MODE (uses OCL interpreter)
# =============================================================================

# =============================================================================
# MAIN
# =============================================================================

def main():
    run_multi_entity()


if __name__ == "__main__":
    main()
