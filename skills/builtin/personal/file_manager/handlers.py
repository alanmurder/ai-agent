"""File Manager Skill - Handlers."""

import os
from pathlib import Path
from typing import Any

from core.agent.types import ExecutionContext


async def handle_read_file(
    params: dict[str, Any],
    context: ExecutionContext,
) -> dict[str, Any]:
    """Handle read_file tool call."""
    path = params.get("path")
    encoding = params.get("encoding", "utf-8")

    try:
        file_path = Path(path)

        if not file_path.exists():
            return {
                "success": False,
                "error": f"文件不存在: {path}",
            }

        content = file_path.read_text(encoding=encoding)

        return {
            "success": True,
            "content": content,
            "path": str(file_path),
            "size": len(content),
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


async def handle_write_file(
    params: dict[str, Any],
    context: ExecutionContext,
) -> dict[str, Any]:
    """Handle write_file tool call."""
    path = params.get("path")
    content = params.get("content")
    encoding = params.get("encoding", "utf-8")
    mode = params.get("mode", "write")

    try:
        file_path = Path(path)

        # Ensure parent directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)

        if mode == "append":
            with open(file_path, "a", encoding=encoding) as f:
                f.write(content)
        else:
            file_path.write_text(content, encoding=encoding)

        return {
            "success": True,
            "path": str(file_path),
            "size": len(content),
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


async def handle_list_directory(
    params: dict[str, Any],
    context: ExecutionContext,
) -> dict[str, Any]:
    """Handle list_directory tool call."""
    path = params.get("path")
    recursive = params.get("recursive", False)

    try:
        dir_path = Path(path)

        if not dir_path.exists():
            return {
                "success": False,
                "error": f"目录不存在: {path}",
            }

        if not dir_path.is_dir():
            return {
                "success": False,
                "error": f"路径不是目录: {path}",
            }

        items = []

        if recursive:
            for item in dir_path.rglob("*"):
                items.append({
                    "path": str(item),
                    "name": item.name,
                    "type": "directory" if item.is_dir() else "file",
                    "size": item.stat().st_size if item.is_file() else None,
                })
        else:
            for item in dir_path.iterdir():
                items.append({
                    "path": str(item),
                    "name": item.name,
                    "type": "directory" if item.is_dir() else "file",
                    "size": item.stat().st_size if item.is_file() else None,
                })

        return {
            "success": True,
            "path": str(dir_path),
            "items": items,
            "count": len(items),
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }