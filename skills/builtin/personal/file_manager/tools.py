"""File Manager Skill - Tools definitions."""

TOOL_DEFINITIONS = [
    {
        "name": "read_file",
        "description": "读取指定路径的文件内容",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "文件路径",
                },
                "encoding": {
                    "type": "string",
                    "description": "文件编码，默认utf-8",
                    "default": "utf-8",
                },
            },
            "required": ["path"],
        },
        "handler": "file_manager.handlers.handle_read_file",
        "permissions": ["read_file"],
        "timeout": 30,
    },
    {
        "name": "write_file",
        "description": "写入内容到指定文件",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "文件路径",
                },
                "content": {
                    "type": "string",
                    "description": "要写入的内容",
                },
                "encoding": {
                    "type": "string",
                    "description": "文件编码，默认utf-8",
                    "default": "utf-8",
                },
                "mode": {
                    "type": "string",
                    "description": "写入模式，write或append",
                    "default": "write",
                },
            },
            "required": ["path", "content"],
        },
        "handler": "file_manager.handlers.handle_write_file",
        "permissions": ["write_file"],
        "timeout": 30,
    },
    {
        "name": "list_directory",
        "description": "列出目录内容",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "目录路径",
                },
                "recursive": {
                    "type": "boolean",
                    "description": "是否递归列出",
                    "default": False,
                },
            },
            "required": ["path"],
        },
        "handler": "file_manager.handlers.handle_list_directory",
        "permissions": ["list_directory"],
        "timeout": 30,
    },
]