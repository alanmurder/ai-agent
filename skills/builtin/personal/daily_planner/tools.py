"""Daily Planner Skill - Tools definitions."""

TOOL_DEFINITIONS = [
    {
        "name": "create_event",
        "description": "创建日程事件",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "事件标题",
                },
                "date": {
                    "type": "string",
                    "description": "日期，格式YYYY-MM-DD",
                },
                "time": {
                    "type": "string",
                    "description": "时间，格式HH:MM",
                },
                "description": {
                    "type": "string",
                    "description": "事件描述",
                },
                "duration_minutes": {
                    "type": "integer",
                    "description": "持续时间(分钟)",
                    "default": 60,
                },
            },
            "required": ["title", "date", "time"],
        },
        "handler": "daily_planner.handlers.handle_create_event",
        "permissions": ["write_schedule"],
        "timeout": 30,
    },
    {
        "name": "list_events",
        "description": "查询日程列表",
        "parameters": {
            "type": "object",
            "properties": {
                "date": {
                    "type": "string",
                    "description": "日期，格式YYYY-MM-DD，留空返回今日",
                },
                "days": {
                    "type": "integer",
                    "description": "查询天数",
                    "default": 7,
                },
            },
            "required": [],
        },
        "handler": "daily_planner.handlers.handle_list_events",
        "permissions": ["read_schedule"],
        "timeout": 30,
    },
]