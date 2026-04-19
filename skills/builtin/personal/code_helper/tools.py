"""Code Helper Skill - Tools definitions."""

TOOL_DEFINITIONS = [
    {
        "name": "analyze_code",
        "description": "分析代码结构，返回代码的基本信息",
        "parameters": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "要分析的代码内容",
                },
                "language": {
                    "type": "string",
                    "description": "编程语言，如python, javascript等",
                },
            },
            "required": ["code"],
        },
        "handler": "code_helper.handlers.handle_analyze_code",
        "permissions": ["read_code"],
        "timeout": 60,
    },
    {
        "name": "explain_code",
        "description": "解释代码逻辑和功能",
        "parameters": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "要解释的代码内容",
                },
                "level": {
                    "type": "string",
                    "description": "解释详细程度：brief, normal, detailed",
                    "default": "normal",
                },
            },
            "required": ["code"],
        },
        "handler": "code_helper.handlers.handle_explain_code",
        "permissions": ["read_code"],
        "timeout": 60,
    },
    {
        "name": "debug_code",
        "description": "调试代码，识别潜在问题和错误",
        "parameters": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "要调试的代码内容",
                },
                "error_message": {
                    "type": "string",
                    "description": "错误信息(如果有)",
                },
                "language": {
                    "type": "string",
                    "description": "编程语言",
                },
            },
            "required": ["code"],
        },
        "handler": "code_helper.handlers.handle_debug_code",
        "permissions": ["read_code"],
        "timeout": 120,
    },
    {
        "name": "generate_code",
        "description": "根据描述生成代码",
        "parameters": {
            "type": "object",
            "properties": {
                "description": {
                    "type": "string",
                    "description": "代码功能描述",
                },
                "language": {
                    "type": "string",
                    "description": "目标编程语言",
                    "default": "python",
                },
                "style": {
                    "type": "string",
                    "description": "代码风格：clean, verbose, minimal",
                    "default": "clean",
                },
                "context": {
                    "type": "string",
                    "description": "上下文信息(如现有代码片段)",
                },
            },
            "required": ["description"],
        },
        "handler": "code_helper.handlers.handle_generate_code",
        "permissions": ["write_code"],
        "timeout": 120,
    },
    {
        "name": "refactor_code",
        "description": "重构代码，优化结构和性能",
        "parameters": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "要重构的代码",
                },
                "goals": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "重构目标：optimize, clean, modular, document",
                },
                "language": {
                    "type": "string",
                    "description": "编程语言",
                },
            },
            "required": ["code"],
        },
        "handler": "code_helper.handlers.handle_refactor_code",
        "permissions": ["write_code"],
        "timeout": 120,
    },
    {
        "name": "search_api_docs",
        "description": "搜索API文档和库使用示例",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "搜索关键词或API名称",
                },
                "library": {
                    "type": "string",
                    "description": "库或框架名称，如fastapi, pandas",
                },
                "language": {
                    "type": "string",
                    "description": "编程语言",
                },
            },
            "required": ["query"],
        },
        "handler": "code_helper.handlers.handle_search_api_docs",
        "permissions": ["search_docs"],
        "timeout": 60,
    },
]