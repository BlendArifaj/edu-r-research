from __future__ import annotations

import ast
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

SERVICE_SUFFIXES = ("Service", "Repository", "Builder")
HTTP_METHODS = {"get", "post", "put", "patch", "delete"}


@dataclass
class StaticEvidence:
    modules: list[str] = field(default_factory=list)
    classes: list[dict[str, Any]] = field(default_factory=list)
    module_imports: list[dict[str, str]] = field(default_factory=list)
    class_dependencies: list[dict[str, str]] = field(default_factory=list)
    calls: list[dict[str, str]] = field(default_factory=list)
    entity_mentions: list[dict[str, str]] = field(default_factory=list)
    tablenames: dict[str, str] = field(default_factory=dict)
    endpoints: list[dict[str, Any]] = field(default_factory=list)
    attr_types: dict[str, dict[str, str]] = field(default_factory=dict)


def _module_name(root: Path, path: Path) -> str:
    relative = path.relative_to(root)
    parts = list(relative.with_suffix("").parts)
    if parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(["app", *parts]) if parts else "app"


def _is_component(name: str) -> bool:
    return name.endswith(SERVICE_SUFFIXES)


def analyze_app(app_root: Path) -> StaticEvidence:
    evidence = StaticEvidence()
    entity_names = _collect_tablenames(app_root, evidence)
    for path in sorted(app_root.rglob("*.py")):
        if path.name == "__init__.py" and path.parent == app_root:
            continue
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
        module = _module_name(app_root, path)
        evidence.modules.append(module)
        visitor = _ModuleVisitor(module, path, entity_names)
        visitor.visit(tree)
        evidence.module_imports.extend(visitor.imports)
        evidence.classes.extend(visitor.classes)
        evidence.class_dependencies.extend(visitor.class_deps)
        evidence.calls.extend(visitor.calls)
        evidence.entity_mentions.extend(visitor.entity_mentions)
        evidence.endpoints.extend(visitor.endpoints)
        evidence.attr_types[visitor.current_class or module] = visitor.attr_types
        for class_name, attrs in visitor.class_attr_types.items():
            evidence.attr_types[class_name] = attrs
    _resolve_self_calls(evidence)
    return evidence


def _collect_tablenames(app_root: Path, evidence: StaticEvidence) -> set[str]:
    names: set[str] = set()
    models_root = app_root / "models"
    if not models_root.exists():
        return names
    for path in models_root.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            table = _tablename_of(node)
            if table:
                evidence.tablenames[node.name] = table
                names.add(node.name)
    return names


def _tablename_of(node: ast.ClassDef) -> str | None:
    for stmt in node.body:
        if not isinstance(stmt, ast.Assign):
            continue
        for target in stmt.targets:
            if isinstance(target, ast.Name) and target.id == "__tablename__":
                if isinstance(stmt.value, ast.Constant) and isinstance(stmt.value.value, str):
                    return stmt.value.value
    return None


class _ModuleVisitor(ast.NodeVisitor):
    def __init__(self, module: str, path: Path, entity_names: set[str]) -> None:
        self.module = module
        self.path = path
        self.entity_names = entity_names
        self.imports: list[dict[str, str]] = []
        self.classes: list[dict[str, Any]] = []
        self.class_deps: list[dict[str, str]] = []
        self.calls: list[dict[str, str]] = []
        self.entity_mentions: list[dict[str, str]] = []
        self.endpoints: list[dict[str, Any]] = []
        self.current_class: str | None = None
        self.current_function: str | None = None
        self.attr_types: dict[str, str] = {}
        self.class_attr_types: dict[str, dict[str, str]] = {}
        self._imported_names: dict[str, str] = {}

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        module = node.module or ""
        for alias in node.names:
            name = alias.asname or alias.name
            self._imported_names[name] = f"{module}.{alias.name}" if module else alias.name
            self.imports.append(
                {"from_module": self.module, "imported_module": module, "name": alias.name}
            )
        self.generic_visit(node)

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            self.imports.append(
                {
                    "from_module": self.module,
                    "imported_module": alias.name,
                    "name": alias.asname or alias.name,
                }
            )
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        previous = self.current_class
        self.current_class = node.name
        self.class_attr_types.setdefault(node.name, {})
        self.classes.append(
            {
                "name": node.name,
                "module": self.module,
                "file": str(self.path),
                "is_component": _is_component(node.name),
            }
        )
        for base in node.bases:
            base_name = _expr_name(base)
            if base_name:
                self.class_deps.append({"from_class": node.name, "to_class": base_name})
        self.generic_visit(node)
        self.current_class = previous

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        previous = self.current_function
        self.current_function = node.name
        endpoint = _endpoint_from_decorators(node)
        if endpoint:
            endpoint.update(
                {
                    "function": node.name,
                    "module": self.module,
                    "file": str(self.path),
                    "class_name": self.current_class,
                }
            )
            self.endpoints.append(endpoint)
        self.generic_visit(node)
        self.current_function = previous

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_Assign(self, node: ast.Assign) -> None:
        if self.current_class and self.current_function == "__init__":
            for target in node.targets:
                if (
                    isinstance(target, ast.Attribute)
                    and isinstance(target.value, ast.Name)
                    and target.value.id == "self"
                ):
                    callee = _call_callee(node.value)
                    if callee:
                        self.class_attr_types[self.current_class][target.attr] = callee
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        attr, method = _self_call_parts(node)
        caller = self.current_class or self.module
        if attr:
            self.calls.append(
                {
                    "from_component": caller,
                    "to_name": attr,
                    "function": self.current_function or "",
                    "method": method or "",
                }
            )
        if attr in self.entity_names and self.current_class:
            self.entity_mentions.append(
                {"component": self.current_class, "entity": attr, "kind": "constructor"}
            )
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name) -> None:
        if node.id in self.entity_names and self.current_class:
            self.entity_mentions.append(
                {"component": self.current_class, "entity": node.id, "kind": "name"}
            )
        if (
            self.endpoints
            and self.current_function
            and node.id.endswith("Service")
            and self.endpoints[-1].get("function") == self.current_function
        ):
            services = self.endpoints[-1].setdefault("services", [])
            if node.id not in services:
                services.append(node.id)


def _expr_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None


def _self_call_parts(node: ast.Call) -> tuple[str | None, str | None]:
    func = node.func
    if isinstance(func, ast.Attribute):
        method = func.attr
        value = func.value
        if (
            isinstance(value, ast.Attribute)
            and isinstance(value.value, ast.Name)
            and value.value.id == "self"
        ):
            return value.attr, method
        if isinstance(value, ast.Name):
            return value.id, method
        return None, method
    if isinstance(func, ast.Name):
        return func.id, None
    return None, None


def _call_callee(node: ast.AST) -> str | None:
    if isinstance(node, ast.Call):
        return _call_callee(node.func)
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None


def _endpoint_from_decorators(node: ast.FunctionDef) -> dict[str, Any] | None:
    for deco in node.decorator_list:
        if not isinstance(deco, ast.Call) or not isinstance(deco.func, ast.Attribute):
            continue
        method = deco.func.attr.lower()
        if method not in HTTP_METHODS:
            continue
        path = ""
        if deco.args and isinstance(deco.args[0], ast.Constant):
            path = str(deco.args[0].value)
        return {"http_method": method.upper(), "path": path, "services": []}
    return None


def _resolve_self_calls(evidence: StaticEvidence) -> None:
    resolved: list[dict[str, str]] = []
    for call in evidence.calls:
        target = evidence.attr_types.get(call["from_component"], {}).get(call["to_name"])
        if target:
            resolved.append(
                {
                    "from_component": call["from_component"],
                    "to_component": target,
                    "function": call["function"],
                    "via_attr": call["to_name"],
                    "method": call.get("method", ""),
                }
            )
        elif _is_component(call["to_name"]):
            resolved.append(
                {
                    "from_component": call["from_component"],
                    "to_component": call["to_name"],
                    "function": call["function"],
                    "via_attr": "",
                    "method": call.get("method", ""),
                }
            )
    evidence.calls = resolved
