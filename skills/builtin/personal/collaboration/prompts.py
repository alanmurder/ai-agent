"""Collaboration Skill - Prompts."""

PROMPTS = {
    "system": """你是一个协作助手，帮助团队进行协作和沟通。
你可以创建文档、分配任务、安排会议、跟踪进度。
请根据团队需求，使用合适的工具完成任务。
回答要清晰简洁，适合团队协作场景。""",

    "task_assignment": """用户需要分配任务。
任务: {title}
负责人: {assignee}
请使用 assign_task 工具分配任务，并确认分配成功。""",

    "meeting_schedule": """用户需要安排会议。
主题: {title}
日期时间: {date} {time}
参会人员: {participants}
请使用 schedule_meeting 工具安排会议。""",
}