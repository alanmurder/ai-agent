"""Code Helper Skill - Handlers."""

import re
from typing import Any

from core.agent.types import ExecutionContext


def _count_lines(code: str) -> int:
    """Count lines of code."""
    return len(code.strip().split("\n"))


def _detect_language(code: str) -> str:
    """Detect programming language."""
    if "def " in code or "import " in code:
        return "python"
    elif "function " in code or "const " in code or "let " in code:
        return "javascript"
    elif "func " in code or "package " in code:
        return "go"
    elif "class " in code and "{" in code:
        return "java"
    return "unknown"


async def handle_analyze_code(
    params: dict[str, Any],
    context: ExecutionContext,
) -> dict[str, Any]:
    """Handle analyze_code tool call."""
    code = params.get("code")
    language = params.get("language") or _detect_language(code)

    try:
        lines = _count_lines(code)

        # Simple analysis
        functions = []
        if language == "python":
            functions = re.findall(r"def\s+(\w+)\s*\(", code)
        elif language == "javascript":
            functions = re.findall(r"function\s+(\w+)\s*\(", code)

        return {
            "success": True,
            "language": language,
            "lines": lines,
            "functions": functions,
            "complexity": "low" if lines < 50 else "medium" if lines < 200 else "high",
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


async def handle_explain_code(
    params: dict[str, Any],
    context: ExecutionContext,
) -> dict[str, Any]:
    """Handle explain_code tool call."""
    code = params.get("code")
    level = params.get("level", "normal")

    try:
        language = _detect_language(code)
        lines = _count_lines(code)

        # Return analysis for model to generate explanation
        return {
            "success": True,
            "code": code,
            "language": language,
            "lines": lines,
            "level": level,
            "request_explanation": True,
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


async def handle_debug_code(
    params: dict[str, Any],
    context: ExecutionContext,
) -> dict[str, Any]:
    """Handle debug_code tool call."""
    code = params.get("code")
    error_message = params.get("error_message", "")
    language = params.get("language") or _detect_language(code)

    try:
        lines = _count_lines(code)

        # Identify common issues
        issues = []

        # Check for syntax errors
        if language == "python":
            # Check indentation
            if code.strip() and not code.startswith("    ") and "def " in code:
                issues.append({"type": "indentation", "severity": "warning"})

            # Check for missing imports
            used_modules = re.findall(r"(\w+)\.\w+", code)
            imported_modules = re.findall(r"import\s+(\w+)", code)
            for mod in used_modules:
                if mod not in imported_modules and mod not in ["self", "len", "str", "int", "list", "dict"]:
                    issues.append({
                        "type": "missing_import",
                        "module": mod,
                        "severity": "warning"
                    })

        # Check for common patterns
        if "TODO" in code or "FIXME" in code:
            issues.append({"type": "todo_marker", "severity": "info"})

        return {
            "success": True,
            "code": code,
            "language": language,
            "lines": lines,
            "error_message": error_message,
            "issues": issues,
            "request_debug_analysis": True,
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


async def handle_generate_code(
    params: dict[str, Any],
    context: ExecutionContext,
) -> dict[str, Any]:
    """Handle generate_code tool call."""
    description = params.get("description")
    language = params.get("language", "python")
    style = params.get("style", "clean")
    context_code = params.get("context", "")

    try:
        # Return request for code generation
        return {
            "success": True,
            "description": description,
            "language": language,
            "style": style,
            "context": context_code,
            "request_code_generation": True,
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


async def handle_refactor_code(
    params: dict[str, Any],
    context: ExecutionContext,
) -> dict[str, Any]:
    """Handle refactor_code tool call."""
    code = params.get("code")
    goals = params.get("goals", ["clean"])
    language = params.get("language") or _detect_language(code)

    try:
        lines = _count_lines(code)
        functions = []

        if language == "python":
            functions = re.findall(r"def\s+(\w+)\s*\(", code)

        # Return analysis for model to generate refactored code
        return {
            "success": True,
            "code": code,
            "language": language,
            "lines": lines,
            "functions": functions,
            "goals": goals,
            "request_refactoring": True,
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


async def handle_search_api_docs(
    params: dict[str, Any],
    context: ExecutionContext,
) -> dict[str, Any]:
    """Handle search_api_docs tool call."""
    query = params.get("query")
    library = params.get("library", "")
    language = params.get("language", "")

    try:
        # Return request for API documentation search
        # The model will generate the documentation response
        return {
            "success": True,
            "query": query,
            "library": library,
            "language": language,
            "request_api_docs": True,
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }