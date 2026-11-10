import ast
import math
import operator
from typing import Any, Callable

MAX_SOURCE_CHARS = 8_000
MAX_AST_NODES = 250
MAX_STATEMENTS = 50
MAX_OUTPUT_CHARS = 16_000
MAX_TEXT_CHARS = 4_096
MAX_CONTAINER_ITEMS = 1_000
MAX_INTEGER_BITS = 2_048


class SafeEvaluationError(ValueError):
    pass


class SafePythonEvaluator:
    def __init__(self, memory: Any = None):
        self.variables: dict[str, Any] = {}
        self.output: list[str] = []
        self.output_size = 0
        self.memory = memory
        self.pending_memory: dict[str, Any] = {}
        self.deleted_memory: set[str] = set()
        self.binary_operators: dict[type[ast.operator], Callable[[Any, Any], Any]] = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
            ast.FloorDiv: operator.floordiv,
            ast.Mod: operator.mod,
            ast.Pow: operator.pow,
        }
        self.unary_operators: dict[type[ast.unaryop], Callable[[Any], Any]] = {
            ast.UAdd: operator.pos,
            ast.USub: operator.neg,
            ast.Not: operator.not_,
        }
        self.comparison_operators: dict[type[ast.cmpop], Callable[[Any, Any], bool]] = {
            ast.Eq: operator.eq,
            ast.NotEq: operator.ne,
            ast.Lt: operator.lt,
            ast.LtE: operator.le,
            ast.Gt: operator.gt,
            ast.GtE: operator.ge,
        }

    def evaluate(self, source: str) -> dict[str, Any]:
        if not isinstance(source, str):
            raise SafeEvaluationError("Code must be text.")
        if len(source) > MAX_SOURCE_CHARS:
            raise SafeEvaluationError(f"Code exceeds the {MAX_SOURCE_CHARS}-character limit.")
        try:
            tree = ast.parse(source, mode="exec")
        except (SyntaxError, ValueError, RecursionError) as error:
            raise SafeEvaluationError(f"Invalid supported Python syntax: {error}") from None

        node_count = sum(1 for _ in ast.walk(tree))
        if node_count > MAX_AST_NODES:
            raise SafeEvaluationError(f"Code exceeds the {MAX_AST_NODES}-node limit.")
        if len(tree.body) > MAX_STATEMENTS:
            raise SafeEvaluationError(f"Code exceeds the {MAX_STATEMENTS}-statement limit.")

        try:
            for statement in tree.body:
                self._statement(statement)
        except SafeEvaluationError:
            raise
        except (ArithmeticError, IndexError, KeyError, TypeError, ValueError, OverflowError, RecursionError) as error:
            raise SafeEvaluationError(f"Evaluation stopped safely: {error}") from None

        result = self.variables.get("result", self.variables.get("output"))
        result_text = str(result) if result is not None else None
        if result_text is not None and len(result_text) > MAX_TEXT_CHARS:
            raise SafeEvaluationError("Rendered result exceeds the safe output limit.")
        if self.memory is not None:
            for key in self.deleted_memory:
                self.memory.delete(key)
            for key, value in self.pending_memory.items():
                self.memory.set(key, value)
        return {
            "stdout": "".join(self.output),
            "return_value": result_text,
        }

    def _statement(self, node: ast.stmt) -> None:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            name = node.targets[0].id
            if name.startswith("_") or name in self._function_names():
                raise SafeEvaluationError("Assignment to private or reserved names is not supported.")
            self.variables[name] = self._checked(self._expression(node.value))
            return
        if isinstance(node, ast.Expr):
            self._expression(node.value)
            return
        raise SafeEvaluationError(f"Statement '{type(node).__name__}' is not supported.")

    def _expression(self, node: ast.expr) -> Any:
        if isinstance(node, ast.Constant):
            return self._checked(node.value)
        if isinstance(node, ast.Name):
            if node.id.startswith("_"):
                raise SafeEvaluationError("Private names are not supported.")
            if node.id in self.variables:
                return self.variables[node.id]
            if node.id in self._function_names():
                raise SafeEvaluationError("Safe functions can only be called directly.")
            raise SafeEvaluationError(f"Name '{node.id}' is not defined in the safe environment.")
        if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
            if len(node.elts) > MAX_CONTAINER_ITEMS:
                raise SafeEvaluationError("Container exceeds the item limit.")
            values = [self._expression(item) for item in node.elts]
            return self._checked(values if isinstance(node, ast.List) else tuple(values) if isinstance(node, ast.Tuple) else set(values))
        if isinstance(node, ast.Dict):
            if len(node.keys) > MAX_CONTAINER_ITEMS or any(key is None for key in node.keys):
                raise SafeEvaluationError("Dictionary unpacking is not supported or exceeds the item limit.")
            return self._checked({self._expression(key): self._expression(value) for key, value in zip(node.keys, node.values)})
        if isinstance(node, ast.BinOp) and type(node.op) in self.binary_operators:
            left, right = self._expression(node.left), self._expression(node.right)
            if isinstance(node.op, ast.Pow):
                if not self._is_number(left) or not self._is_number(right) or abs(right) > 16:
                    raise SafeEvaluationError("Power operations require numbers and an exponent between -16 and 16.")
            elif isinstance(node.op, ast.Mult) and (isinstance(left, (str, list, tuple)) or isinstance(right, (str, list, tuple))):
                repeated = right if isinstance(left, (str, list, tuple)) else left
                sequence = left if isinstance(left, (str, list, tuple)) else right
                max_size = MAX_TEXT_CHARS if isinstance(sequence, str) else MAX_CONTAINER_ITEMS
                if not isinstance(repeated, int) or repeated < 0 or repeated > MAX_CONTAINER_ITEMS or len(sequence) * repeated > max_size:
                    raise SafeEvaluationError("Sequence repetition is outside the safe limits.")
            elif not self._is_number(left) or not self._is_number(right):
                raise SafeEvaluationError("Arithmetic operators only accept numeric values (apart from bounded sequence repetition).");
            return self._checked(self.binary_operators[type(node.op)](left, right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in self.unary_operators:
            value = self._expression(node.operand)
            if not isinstance(node.op, ast.Not) and not self._is_number(value):
                raise SafeEvaluationError("Unary signs only accept numeric values.")
            return self._checked(self.unary_operators[type(node.op)](value))
        if isinstance(node, ast.BoolOp) and isinstance(node.op, (ast.And, ast.Or)):
            result = self._expression(node.values[0])
            for value_node in node.values[1:]:
                if (isinstance(node.op, ast.And) and not result) or (isinstance(node.op, ast.Or) and result):
                    break
                result = self._expression(value_node)
            return result
        if isinstance(node, ast.Compare):
            left = self._expression(node.left)
            for operation, comparator in zip(node.ops, node.comparators):
                if type(operation) not in self.comparison_operators:
                    raise SafeEvaluationError("This comparison operator is not supported.")
                right = self._expression(comparator)
                if not self.comparison_operators[type(operation)](left, right):
                    return False
                left = right
            return True
        if isinstance(node, ast.IfExp):
            return self._expression(node.body if self._expression(node.test) else node.orelse)
        if isinstance(node, ast.Subscript):
            container, key = self._expression(node.value), self._expression(node.slice)
            if not isinstance(container, (str, list, tuple, dict)) or not isinstance(key, (str, int)):
                raise SafeEvaluationError("Only direct indexing into small built-in containers is supported.")
            return self._checked(container[key])
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            name = node.func.id
            if node.keywords:
                raise SafeEvaluationError("Keyword arguments are not supported.")
            arguments = [self._expression(argument) for argument in node.args]
            return self._checked(self._call(name, arguments))
        raise SafeEvaluationError(f"Expression '{type(node).__name__}' is not supported.")

    def _call(self, name: str, arguments: list[Any]) -> Any:
        if name == "print":
            text = " ".join(self._bounded_repr(value) for value in arguments)
            self._append_output(text + "\n")
            return None
        if name == "len" and len(arguments) == 1 and isinstance(arguments[0], (str, list, tuple, dict, set)):
            return len(arguments[0])
        if name in {"sum", "min", "max", "sorted"} and len(arguments) == 1 and isinstance(arguments[0], (list, tuple, set)):
            values = list(arguments[0])
            if name == "sum":
                if not all(self._is_number(value) for value in values):
                    raise SafeEvaluationError("sum() accepts only numeric sequences.")
                return sum(values)
            if name == "min":
                return min(values)
            if name == "max":
                return max(values)
            return sorted(values)
        if name in {"min", "max"} and 1 <= len(arguments) <= MAX_CONTAINER_ITEMS:
            return min(arguments) if name == "min" else max(arguments)
        if name == "abs" and len(arguments) == 1 and self._is_number(arguments[0]):
            return abs(arguments[0])
        if name == "round" and len(arguments) in (1, 2) and self._is_number(arguments[0]) and (len(arguments) == 1 or isinstance(arguments[1], int) and abs(arguments[1]) <= 12):
            return round(*arguments)
        if name in {"memory_get", "memory_set", "memory_delete"}:
            return self._memory_call(name, arguments)
        raise SafeEvaluationError(f"Call to '{name}' is not permitted.")

    def _memory_call(self, name: str, arguments: list[Any]) -> Any:
        if self.memory is None:
            raise SafeEvaluationError("Shared memory is unavailable in this execution.")
        if name == "memory_get" and len(arguments) in (1, 2) and isinstance(arguments[0], str):
            key = arguments[0]
            if key in self.deleted_memory:
                return arguments[1] if len(arguments) == 2 else None
            if key in self.pending_memory:
                return self.pending_memory[key]
            return self.memory.get(key, arguments[1] if len(arguments) == 2 else None)
        if name == "memory_set" and len(arguments) == 2 and isinstance(arguments[0], str):
            self.deleted_memory.discard(arguments[0])
            self.pending_memory[arguments[0]] = self._checked(arguments[1])
            return None
        if name == "memory_delete" and len(arguments) == 1 and isinstance(arguments[0], str):
            self.pending_memory.pop(arguments[0], None)
            self.deleted_memory.add(arguments[0])
            return None
        raise SafeEvaluationError(f"Invalid arguments for {name}().")

    def _function_names(self) -> set[str]:
        return {"print", "len", "sum", "min", "max", "sorted", "abs", "round", "memory_get", "memory_set", "memory_delete"}

    def _checked(self, value: Any, depth: int = 0) -> Any:
        if depth > 16:
            raise SafeEvaluationError("Nested values exceed the depth limit.")
        if value is None or isinstance(value, bool):
            return value
        if isinstance(value, int):
            if value.bit_length() > MAX_INTEGER_BITS:
                raise SafeEvaluationError("Integer value exceeds the safe magnitude limit.")
            return value
        if isinstance(value, float):
            if not math.isfinite(value):
                raise SafeEvaluationError("Non-finite numbers are not supported.")
            return value
        if isinstance(value, str):
            if len(value) > MAX_TEXT_CHARS:
                raise SafeEvaluationError("Text value exceeds the safe length limit.")
            return value
        if isinstance(value, list):
            if len(value) > MAX_CONTAINER_ITEMS:
                raise SafeEvaluationError("Container exceeds the item limit.")
            return [self._checked(item, depth + 1) for item in value]
        if isinstance(value, tuple):
            if len(value) > MAX_CONTAINER_ITEMS:
                raise SafeEvaluationError("Container exceeds the item limit.")
            return tuple(self._checked(item, depth + 1) for item in value)
        if isinstance(value, set):
            if len(value) > MAX_CONTAINER_ITEMS:
                raise SafeEvaluationError("Container exceeds the item limit.")
            return {self._checked(item, depth + 1) for item in value}
        if isinstance(value, dict):
            if len(value) > MAX_CONTAINER_ITEMS:
                raise SafeEvaluationError("Container exceeds the item limit.")
            return {self._checked(key, depth + 1): self._checked(item, depth + 1) for key, item in value.items()}
        raise SafeEvaluationError("Only primitive values and bounded built-in containers are supported.")

    def _append_output(self, text: str) -> None:
        self.output_size += len(text)
        if self.output_size > MAX_OUTPUT_CHARS:
            raise SafeEvaluationError(f"Printed output exceeds the {MAX_OUTPUT_CHARS}-character limit.")
        self.output.append(text)

    def _bounded_repr(self, value: Any) -> str:
        text = repr(value)
        if len(text) > MAX_TEXT_CHARS:
            raise SafeEvaluationError("Rendered value exceeds the safe output limit.")
        return text

    @staticmethod
    def _is_number(value: Any) -> bool:
        return isinstance(value, (int, float)) and not isinstance(value, bool)
