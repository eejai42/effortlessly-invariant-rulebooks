#!/usr/bin/env python3
"""
UML Execution Substrate - Formula-to-OCL Compiler

This compiler:
1. Reads the rulebook (schema + formulas + data)
2. Generates class-diagram.puml (PlantUML class diagram - schema)
3. Generates objects.puml (PlantUML object diagram - instances)
4. Generates model.json (Structured model for OCL evaluation)
5. Generates constraints.ocl (OCL derive expressions for calculations)

The rulebook is the source of truth. UML/OCL is derived, not authored.
This script is 100% domain-agnostic - all field names come from the rulebook.
"""

import sys
import re
import json
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Union
from enum import Enum, auto

# Add project root to path for shared imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from orchestration.shared import load_rulebook, handle_clean_arg


# =============================================================================
# AST NODE TYPES (reused from OWL substrate)
# =============================================================================

@dataclass
class ASTNode:
    """Base class for AST nodes"""
    pass


@dataclass
class LiteralBool(ASTNode):
    value: bool


@dataclass
class LiteralInt(ASTNode):
    value: int


@dataclass
class LiteralString(ASTNode):
    value: str


@dataclass
class FieldRef(ASTNode):
    name: str  # Field name without {{ }}


@dataclass
class BinaryOp(ASTNode):
    op: str  # '=', '<>', '<', '<=', '>', '>='
    left: ASTNode
    right: ASTNode


@dataclass
class UnaryOp(ASTNode):
    op: str  # 'NOT'
    operand: ASTNode


@dataclass
class FuncCall(ASTNode):
    name: str  # 'AND', 'OR', 'IF', 'LOWER', 'FIND'
    args: List[ASTNode]


@dataclass
class Concat(ASTNode):
    parts: List[ASTNode]


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

    def parse(self) -> ASTNode:
        result = self.parse_concat()
        if self.current().type != TokenType.EOF:
            raise SyntaxError(f"Unexpected token {self.current()} after expression")
        return result

    def parse_concat(self) -> ASTNode:
        left = self.parse_comparison()
        parts = [left]
        while self.current().type == TokenType.AMPERSAND:
            self.consume(TokenType.AMPERSAND)
            right = self.parse_comparison()
            parts.append(right)
        if len(parts) == 1:
            return parts[0]
        return Concat(parts=parts)

    def parse_comparison(self) -> ASTNode:
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

    def parse_primary(self) -> ASTNode:
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


def parse_formula(formula_text: str) -> ASTNode:
    """Parse an Excel-dialect formula into an AST."""
    tokens = tokenize(formula_text)
    parser = Parser(tokens)
    return parser.parse()


# =============================================================================
# OCL EXPRESSION COMPILER
# =============================================================================

def field_to_ocl_attr(field_name: str) -> str:
    """Convert field name to OCL attribute (camelCase with self. prefix)."""
    if field_name:
        return 'self.' + field_name[0].lower() + field_name[1:]
    return 'self.unknown'


def escape_ocl_string(s: str) -> str:
    """Escape a string for OCL."""
    return s.replace("'", "\\'")


def compile_to_ocl(ast: ASTNode) -> str:
    """Compile an AST node to an OCL expression."""

    if isinstance(ast, LiteralBool):
        return 'true' if ast.value else 'false'

    if isinstance(ast, LiteralInt):
        return str(ast.value)

    if isinstance(ast, LiteralString):
        escaped = escape_ocl_string(ast.value)
        return f"'{escaped}'"

    if isinstance(ast, FieldRef):
        return field_to_ocl_attr(ast.name)

    if isinstance(ast, UnaryOp):
        if ast.op == 'NOT':
            operand = compile_to_ocl(ast.operand)
            return f'not ({operand})'
        raise ValueError(f"Unknown unary op: {ast.op}")

    if isinstance(ast, BinaryOp):
        left = compile_to_ocl(ast.left)
        right = compile_to_ocl(ast.right)
        op_map = {'=': '=', '<>': '<>', '<': '<', '<=': '<=', '>': '>', '>=': '>='}
        ocl_op = op_map.get(ast.op, '=')
        return f'({left} {ocl_op} {right})'

    if isinstance(ast, FuncCall):
        if ast.name == 'AND':
            parts = [compile_to_ocl(arg) for arg in ast.args]
            return '(' + ' and '.join(parts) + ')'

        if ast.name == 'OR':
            parts = [compile_to_ocl(arg) for arg in ast.args]
            return '(' + ' or '.join(parts) + ')'

        if ast.name == 'IF':
            if len(ast.args) < 2:
                raise ValueError("IF requires at least 2 arguments")
            cond = compile_to_ocl(ast.args[0])
            then_val = compile_to_ocl(ast.args[1])
            else_val = compile_to_ocl(ast.args[2]) if len(ast.args) > 2 else "''"
            return f'if {cond} then {then_val} else {else_val} endif'

        if ast.name == 'NOT':
            if len(ast.args) != 1:
                raise ValueError("NOT requires 1 argument")
            operand = compile_to_ocl(ast.args[0])
            return f'not ({operand})'

        if ast.name == 'LOWER':
            if len(ast.args) != 1:
                raise ValueError("LOWER requires 1 argument")
            arg = compile_to_ocl(ast.args[0])
            return f'{arg}.toLower()'

        if ast.name == 'FIND':
            if len(ast.args) != 2:
                raise ValueError("FIND requires 2 arguments")
            needle = compile_to_ocl(ast.args[0])
            haystack = compile_to_ocl(ast.args[1])
            return f'{haystack}.indexOf({needle})'

        if ast.name == 'SUM':
            # SUM of values - use arithmetic addition
            parts = [compile_to_ocl(arg) for arg in ast.args]
            return '(' + ' + '.join(parts) + ')'

        if ast.name == 'SUBSTITUTE':
            # SUBSTITUTE(text, old_text, new_text) -> text.replace(old_text, new_text)
            if len(ast.args) != 3:
                raise ValueError("SUBSTITUTE requires 3 arguments")
            text = compile_to_ocl(ast.args[0])
            old_text = compile_to_ocl(ast.args[1])
            new_text = compile_to_ocl(ast.args[2])
            return f'{text}.replace({old_text}, {new_text})'

        raise ValueError(f"Unknown function: {ast.name}")

    if isinstance(ast, Concat):
        parts = [compile_to_ocl(part) for part in ast.parts]
        return ' + '.join(parts)

    raise ValueError(f"Unknown AST node type: {type(ast)}")


# =============================================================================
# UML/PLANTUML GENERATORS
# =============================================================================

def datatype_to_uml(datatype: str) -> str:
    """Convert rulebook datatype to UML type."""
    dt = datatype.lower()
    if dt == 'boolean':
        return 'Boolean'
    elif dt == 'integer':
        return 'Integer'
    else:
        return 'String'


def format_value(value: Any) -> str:
    """Format a value for PlantUML object diagram."""
    if value is None:
        return 'null'
    if isinstance(value, bool):
        return 'true' if value else 'false'
    if isinstance(value, (int, float)):
        return str(value)
    # String - quote and escape
    s = str(value)
    if len(s) > 30:
        s = s[:27] + '...'
    return f'"{s}"'


def generate_class_diagram(tables: Dict[str, Any]) -> str:
    """Generate PlantUML class diagram from rulebook schema."""
    lines = ['@startuml', 'skinparam classAttributeIconSize 0', '']

    for table_name, table_def in sorted(tables.items()):
        if table_name.startswith('_') or table_name.startswith('$'):
            continue

        schema = table_def.get('schema', [])
        if not schema:
            continue

        # Add entity description as a note if available
        entity_description = table_def.get('Description', '')
        if entity_description:
            lines.append(f'note top of {table_name}')
            lines.append(f'  {entity_description}')
            lines.append('end note')
            lines.append('')

        lines.append(f'class {table_name} {{')

        # Raw attributes
        for col in schema:
            if col.get('type') != 'calculated':
                uml_type = datatype_to_uml(col.get('datatype', 'string'))
                desc = col.get('Description', '')
                if desc:
                    lines.append(f'  +{col["name"]}: {uml_type} -- {desc}')
                else:
                    lines.append(f'  +{col["name"]}: {uml_type}')

        lines.append('  --')

        # Derived attributes (calculated)
        for col in schema:
            if col.get('type') == 'calculated':
                uml_type = datatype_to_uml(col.get('datatype', 'string'))
                desc = col.get('Description', '')
                if desc:
                    lines.append(f'  /{col["name"]}: {uml_type}  {{derived}} -- {desc}')
                else:
                    lines.append(f'  /{col["name"]}: {uml_type}  {{derived}}')

        lines.append('}')
        lines.append('')

    lines.append('@enduml')
    return '\n'.join(lines)


def generate_object_diagram(tables: Dict[str, Any]) -> str:
    """Generate PlantUML object diagram from rulebook data."""
    lines = ['@startuml', '']

    for table_name, table_def in sorted(tables.items()):
        if table_name.startswith('_') or table_name.startswith('$'):
            continue

        schema = table_def.get('schema', [])
        data = table_def.get('data', [])

        if not schema or not data:
            continue

        # Build column info for filtering
        col_info = {}
        for col in schema:
            col_name = col.get('name', '')
            col_info[col_name] = col.get('type', 'raw')

        for i, row in enumerate(data):
            obj_name = f'{table_name}_{i}'
            display_name = row.get('Name', obj_name)
            lines.append(f'object "{display_name}" as {obj_name} {{')

            for col in schema:
                if col.get('type') == 'calculated':
                    continue  # OCL will compute these

                col_name = col.get('name', '')
                value = row.get(col_name)
                if value is not None:
                    lines.append(f'  {col_name} = {format_value(value)}')

            lines.append('}')
            lines.append('')

    lines.append('@enduml')
    return '\n'.join(lines)


def generate_model_json(tables: Dict[str, Any]) -> str:
    """Generate JSON model for OCL evaluation."""
    model = {
        "classes": {},
        "instances": []
    }

    for table_name, table_def in sorted(tables.items()):
        if table_name.startswith('_') or table_name.startswith('$'):
            continue

        schema = table_def.get('schema', [])
        data = table_def.get('data', [])

        if not schema:
            continue

        # Schema
        model["classes"][table_name] = {
            "attributes": [],
            "derived": []
        }

        for col in schema:
            attr = {
                "name": col.get('name', ''),
                "type": col.get('datatype', 'string')
            }
            if col.get('formula'):
                attr["formula"] = col.get('formula')
                model["classes"][table_name]["derived"].append(attr)
            else:
                model["classes"][table_name]["attributes"].append(attr)

        # Instances
        for i, row in enumerate(data):
            instance = {
                "class": table_name,
                "id": f"{table_name}_{i}",
                "values": {}
            }
            for col in schema:
                if col.get('type') != 'calculated':
                    col_name = col.get('name', '')
                    instance["values"][col_name] = row.get(col_name)

            model["instances"].append(instance)

    return json.dumps(model, indent=2)


def generate_ocl_constraints(tables: Dict[str, Any]) -> str:
    """Compile formulas to OCL derive expressions."""
    lines = ['-- OCL Constraints for ERB', '-- Generated from effortless-rulebook.json', '']

    for table_name, table_def in sorted(tables.items()):
        if table_name.startswith('_') or table_name.startswith('$'):
            continue

        schema = table_def.get('schema', [])
        if not schema:
            continue

        # Check if this table has any calculated fields
        has_derived = any(col.get('formula') for col in schema)
        if not has_derived:
            continue

        # Add entity description as a comment if available
        entity_description = table_def.get('Description', '')
        if entity_description:
            lines.append(f'-- {entity_description}')
        lines.append(f'context {table_name}')
        lines.append('')

        for col in schema:
            formula = col.get('formula')
            if not formula:
                continue

            col_name = col.get('name', '')
            col_description = col.get('Description', '')

            try:
                ast = parse_formula(formula)
                ocl_expr = compile_to_ocl(ast)

                # Add field description if available
                if col_description:
                    lines.append(f'-- {col_description}')
                lines.append(f'-- Formula: {formula.replace(chr(10), " ")}')
                lines.append(f'derive {col_name}: {ocl_expr}')
                lines.append('')

            except Exception as e:
                if col_description:
                    lines.append(f'-- {col_description}')
                lines.append(f'-- Formula for {col_name} - parse error: {e}')
                lines.append(f'-- Original: {formula.replace(chr(10), " ")}')
                lines.append('')

    return '\n'.join(lines)


# =============================================================================
# MAIN
# =============================================================================

def main():
    # Define generated files for this substrate
    GENERATED_FILES = [
        'class-diagram.puml',
        'objects.puml',
        'model.json',
        'constraints.ocl',
        'test-answers.json',
        'test-results.md',
    ]

    # Handle --clean argument
    if handle_clean_arg(GENERATED_FILES, "UML substrate: Removes generated PlantUML diagrams, model, and OCL constraints"):
        return

    script_dir = Path(__file__).resolve().parent

    print("=" * 70)
    print("UML Execution Substrate - Formula-to-OCL Compiler")
    print("=" * 70)
    print()

    # Load the rulebook
    print("Loading rulebook...")
    try:
        rulebook = load_rulebook()
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    # Filter to just table definitions (exclude metadata keys)
    tables = {k: v for k, v in rulebook.items()
              if isinstance(v, dict) and 'schema' in v}

    print(f"Found {len(tables)} tables: {', '.join(tables.keys())}")

    # Count calculated fields
    total_calc = 0
    for table_name, table_def in tables.items():
        for col in table_def.get('schema', []):
            if col.get('formula'):
                total_calc += 1
    print(f"Found {total_calc} calculated fields to compile")

    print("\n" + "-" * 70)

    # Generate class-diagram.puml (PlantUML schema)
    print("\nGenerating class-diagram.puml (PlantUML class diagram)...")
    class_diagram_content = generate_class_diagram(tables)
    class_diagram_path = script_dir / "class-diagram.puml"
    class_diagram_path.write_text(class_diagram_content, encoding='utf-8')
    print(f"   Wrote: {class_diagram_path} ({len(class_diagram_content)} bytes)")

    # Generate objects.puml (PlantUML object diagram)
    print("\nGenerating objects.puml (PlantUML object diagram)...")
    objects_content = generate_object_diagram(tables)
    objects_path = script_dir / "objects.puml"
    objects_path.write_text(objects_content, encoding='utf-8')
    print(f"   Wrote: {objects_path} ({len(objects_content)} bytes)")

    # Generate model.json (structured model for OCL evaluation)
    print("\nGenerating model.json (structured model)...")
    model_content = generate_model_json(tables)
    model_path = script_dir / "model.json"
    model_path.write_text(model_content, encoding='utf-8')
    print(f"   Wrote: {model_path} ({len(model_content)} bytes)")

    # Generate constraints.ocl (OCL derive expressions)
    print("\nGenerating constraints.ocl (OCL derive expressions)...")
    ocl_content = generate_ocl_constraints(tables)
    ocl_path = script_dir / "constraints.ocl"
    ocl_path.write_text(ocl_content, encoding='utf-8')
    print(f"   Wrote: {ocl_path} ({len(ocl_content)} bytes)")

    print("\n" + "=" * 70)
    print("Generation complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
