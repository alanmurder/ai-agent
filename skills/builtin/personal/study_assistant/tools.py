"""Study Assistant Skill - Tools definitions."""

TOOL_DEFINITIONS = [
    {
        "name": "create_note",
        "description": "创建学习笔记",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "笔记标题",
                },
                "content": {
                    "type": "string",
                    "description": "笔记内容",
                },
                "category": {
                    "type": "string",
                    "description": "笔记分类，如programming, mathematics, language等",
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "笔记标签",
                },
            },
            "required": ["title", "content"],
        },
        "handler": "study_assistant.handlers.handle_create_note",
        "permissions": ["manage_notes"],
        "timeout": 30,
    },
    {
        "name": "organize_notes",
        "description": "整理和搜索笔记",
        "parameters": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "操作类型：list, search, merge, categorize",
                },
                "category": {
                    "type": "string",
                    "description": "按分类筛选",
                },
                "keyword": {
                    "type": "string",
                    "description": "搜索关键词",
                },
                "note_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "要合并的笔记ID列表",
                },
            },
            "required": ["action"],
        },
        "handler": "study_assistant.handlers.handle_organize_notes",
        "permissions": ["manage_notes"],
        "timeout": 30,
    },
    {
        "name": "create_study_plan",
        "description": "创建学习计划",
        "parameters": {
            "type": "object",
            "properties": {
                "subject": {
                    "type": "string",
                    "description": "学习科目",
                },
                "goal": {
                    "type": "string",
                    "description": "学习目标",
                },
                "duration_days": {
                    "type": "integer",
                    "description": "计划天数",
                    "default": 30,
                },
                "daily_hours": {
                    "type": "integer",
                    "description": "每天学习小时数",
                    "default": 2,
                },
                "start_date": {
                    "type": "string",
                    "description": "开始日期，格式YYYY-MM-DD",
                },
            },
            "required": ["subject", "goal"],
        },
        "handler": "study_assistant.handlers.handle_create_study_plan",
        "permissions": ["create_plan"],
        "timeout": 30,
    },
    {
        "name": "track_progress",
        "description": "跟踪学习进度",
        "parameters": {
            "type": "object",
            "properties": {
                "plan_id": {
                    "type": "string",
                    "description": "学习计划ID",
                },
                "date": {
                    "type": "string",
                    "description": "记录日期",
                },
                "hours_spent": {
                    "type": "number",
                    "description": "学习时长(小时)",
                },
                "completed_tasks": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "完成的任务",
                },
                "notes": {
                    "type": "string",
                    "description": "学习笔记",
                },
            },
            "required": ["plan_id", "hours_spent"],
        },
        "handler": "study_assistant.handlers.handle_track_progress",
        "permissions": ["create_plan"],
        "timeout": 30,
    },
]