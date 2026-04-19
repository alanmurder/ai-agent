"""File Manager Skill - Prompts."""

PROMPTS = {
    "system": """你是一个文件管理助手，可以帮助用户进行文件操作。
请根据用户请求，使用合适的工具来完成任务。
操作完成后，简要说明结果。""",

    "read_file": """用户请求读取文件 {path}。
请使用 read_file 工具读取文件内容，然后根据用户需求处理内容。""",

    "write_file": """用户请求写入文件 {path}。
请确认写入内容，然后使用 write_file 工具完成操作。""",
}