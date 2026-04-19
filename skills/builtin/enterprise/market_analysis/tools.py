"""Market Analysis Skill - Tools definitions."""

TOOL_DEFINITIONS = [
    {
        "name": "analyze_competitors",
        "description": "分析竞争对手信息",
        "parameters": {
            "type": "object",
            "properties": {
                "competitors": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "竞争对手列表",
                },
                "category": {
                    "type": "string",
                    "description": "商品类别",
                },
                "metrics": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "对比指标：price, sales, rating, traffic",
                },
            },
            "required": ["competitors"],
        },
        "handler": "market_analysis.handlers.handle_analyze_competitors",
        "permissions": ["compare_competitors"],
        "timeout": 60,
    },
    {
        "name": "track_market_trend",
        "description": "追踪市场趋势",
        "parameters": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "description": "商品类别",
                },
                "time_range": {
                    "type": "string",
                    "description": "时间范围：week, month, quarter",
                    "default": "month",
                },
            },
            "required": ["category"],
        },
        "handler": "market_analysis.handlers.handle_track_market_trend",
        "permissions": ["track_trends"],
        "timeout": 60,
    },
    {
        "name": "suggest_pricing",
        "description": "定价策略建议",
        "parameters": {
            "type": "object",
            "properties": {
                "product_id": {
                    "type": "string",
                    "description": "商品ID",
                },
                "strategy": {
                    "type": "string",
                    "description": "策略类型：competitive, premium, value",
                    "default": "competitive",
                },
                "target_margin": {
                    "type": "number",
                    "description": "目标利润率",
                },
            },
            "required": ["product_id"],
        },
        "handler": "market_analysis.handlers.handle_suggest_pricing",
        "permissions": ["analyze_market"],
        "timeout": 30,
    },
]