"""Live Analytics Skill - Tools definitions."""

TOOL_DEFINITIONS = [
    {
        "name": "get_live_metrics",
        "description": "获取直播间实时数据指标",
        "parameters": {
            "type": "object",
            "properties": {
                "session_id": {
                    "type": "string",
                    "description": "直播场次ID",
                },
                "metrics": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "要获取的指标：viewers, engagement, sales, gifts",
                },
                "time_range": {
                    "type": "string",
                    "description": "时间范围：current, last_hour, last_session",
                    "default": "current",
                },
            },
            "required": ["session_id"],
        },
        "handler": "live_analytics.handlers.handle_get_live_metrics",
        "permissions": ["read_live_data"],
        "timeout": 30,
    },
    {
        "name": "analyze_audience",
        "description": "分析观众画像和行为",
        "parameters": {
            "type": "object",
            "properties": {
                "session_id": {
                    "type": "string",
                    "description": "直播场次ID",
                },
                "analysis_type": {
                    "type": "string",
                    "description": "分析类型：demographics, behavior, retention, engagement",
                },
            },
            "required": ["session_id", "analysis_type"],
        },
        "handler": "live_analytics.handlers.handle_analyze_audience",
        "permissions": ["analyze_audience"],
        "timeout": 60,
    },
    {
        "name": "calculate_conversion",
        "description": "计算直播转化率和ROI",
        "parameters": {
            "type": "object",
            "properties": {
                "session_id": {
                    "type": "string",
                    "description": "直播场次ID",
                },
                "metrics": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "要计算的指标：conversion_rate, roi, gmv, order_count",
                },
            },
            "required": ["session_id"],
        },
        "handler": "live_analytics.handlers.handle_calculate_conversion",
        "permissions": ["read_live_data"],
        "timeout": 30,
    },
    {
        "name": "generate_report",
        "description": "生成直播数据分析报告",
        "parameters": {
            "type": "object",
            "properties": {
                "session_id": {
                    "type": "string",
                    "description": "直播场次ID，支持多个ID用逗号分隔",
                },
                "report_type": {
                    "type": "string",
                    "description": "报告类型：summary, detailed, comparison",
                    "default": "summary",
                },
                "include_charts": {
                    "type": "boolean",
                    "description": "是否包含图表建议",
                    "default": true,
                },
            },
            "required": ["session_id"],
        },
        "handler": "live_analytics.handlers.handle_generate_report",
        "permissions": ["generate_report"],
        "timeout": 60,
    },
]