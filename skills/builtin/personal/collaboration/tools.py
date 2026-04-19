"""Collaboration Skill - Tools definitions."""

TOOL_DEFINITIONS = [
    {
        "name": "create_document",
        "description": "创建协作文档",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "文档标题",
                },
                "content": {
                    "type": "string",
                    "description": "文档内容",
                },
                "type": {
                    "type": "string",
                    "description": "文档类型：report, plan, notes, meeting",
                    "default": "notes",
                },
                "collaborators": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "协作者列表",
                },
            },
            "required": ["title", "content"],
        },
        "handler": "collaboration.handlers.handle_create_document",
        "permissions": ["manage_documents"],
        "timeout": 30,
    },
    {
        "name": "assign_task",
        "description": "分配任务给团队成员",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "任务标题",
                },
                "description": {
                    "type": "string",
                    "description": "任务描述",
                },
                "assignee": {
                    "type": "string",
                    "description": "任务负责人",
                },
                "priority": {
                    "type": "string",
                    "description": "优先级：high, medium, low",
                    "default": "medium",
                },
                "due_date": {
                    "type": "string",
                    "description": "截止日期，格式YYYY-MM-DD",
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "任务标签",
                },
            },
            "required": ["title", "assignee"],
        },
        "handler": "collaboration.handlers.handle_assign_task",
        "permissions": ["assign_tasks"],
        "timeout": 30,
    },
    {
        "name": "schedule_meeting",
        "description": "安排会议",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "会议主题",
                },
                "date": {
                    "type": "string",
                    "description": "会议日期，格式YYYY-MM-DD",
                },
                "time": {
                    "type": "string",
                    "description": "会议时间，格式HH:MM",
                },
                "duration_minutes": {
                    "type": "integer",
                    "description": "会议时长(分钟)",
                    "default": 60,
                },
                "participants": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "参会人员",
                },
                "location": {
                    "type": "string",
                    "description": "会议地点或在线会议链接",
                },
                "agenda": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "会议议程",
                },
            },
            "required": ["title", "date", "time"],
        },
        "handler": "collaboration.handlers.handle_schedule_meeting",
        "permissions": ["schedule_meeting"],
        "timeout": 30,
    },
    {
        "name": "list_tasks",
        "description": "查询任务列表",
        "parameters": {
            "type": "object",
            "properties": {
                "assignee": {
                    "type": "string",
                    "description": "按负责人筛选",
                },
                "status": {
                    "type": "string",
                    "description": "按状态筛选：pending, in_progress, completed",
                },
                "priority": {
                    "type": "string",
                    "description": "按优先级筛选",
                },
            },
            "required": [],
        },
        "handler": "collaboration.handlers.handle_list_tasks",
        "permissions": ["assign_tasks"],
        "timeout": 30,
    },
    {
        "name": "update_task_status",
        "description": "更新任务状态",
        "parameters": {
            "type": "object",
            "properties": {
                "task_id": {
                    "type": "string",
                    "description": "任务ID",
                },
                "status": {
                    "type": "string",
                    "description": "新状态：pending, in_progress, completed",
                },
                "progress": {
                    "type": "integer",
                    "description": "进度百分比(0-100)",
                },
                "notes": {
                    "type": "string",
                    "description": "备注说明",
                },
            },
            "required": ["task_id", "status"],
        },
        "handler": "collaboration.handlers.handle_update_task_status",
        "permissions": ["assign_tasks"],
        "timeout": 30,
    },
]