"""Study Assistant Skill - Prompts."""

PROMPTS = {
    "system": """你是一个学习助手，帮助用户进行学习和知识管理。
你可以创建笔记、整理知识、制定学习计划、跟踪学习进度。
请根据用户需求，使用合适的工具来完成任务。
回答要简洁明了，适合学习场景。""",

    "note_creation": """用户想要创建笔记。
标题: {title}
内容: {content}
请使用 create_note 工具保存笔记，并确认保存成功。""",

    "study_plan": """用户想要制定学习计划。
科目: {subject}
目标: {goal}
天数: {duration_days}
请使用 create_study_plan 工具生成详细的学习计划。""",
}