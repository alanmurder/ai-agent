"""Product Manager Skill - Tools definitions."""

TOOL_DEFINITIONS = [
    {
        "name": "get_product_info",
        "description": "查询商品详细信息",
        "parameters": {
            "type": "object",
            "properties": {
                "product_id": {
                    "type": "string",
                    "description": "商品ID",
                },
                "include_inventory": {
                    "type": "boolean",
                    "description": "是否包含库存信息",
                    "default": True,
                },
            },
            "required": ["product_id"],
        },
        "handler": "product_manager.handlers.handle_get_product_info",
        "permissions": ["read_product"],
        "timeout": 30,
    },
    {
        "name": "update_product",
        "description": "更新商品信息",
        "parameters": {
            "type": "object",
            "properties": {
                "product_id": {
                    "type": "string",
                    "description": "商品ID",
                },
                "updates": {
                    "type": "object",
                    "description": "要更新的字段",
                },
            },
            "required": ["product_id", "updates"],
        },
        "handler": "product_manager.handlers.handle_update_product",
        "permissions": ["write_product"],
        "timeout": 30,
    },
    {
        "name": "sync_inventory",
        "description": "同步库存数据",
        "parameters": {
            "type": "object",
            "properties": {
                "product_id": {
                    "type": "string",
                    "description": "商品ID，留空则同步所有",
                },
                "platform": {
                    "type": "string",
                    "description": "平台：taobao, jd, pdd, douyin",
                },
                "action": {
                    "type": "string",
                    "description": "操作：sync, check, update",
                    "default": "sync",
                },
            },
            "required": [],
        },
        "handler": "product_manager.handlers.handle_sync_inventory",
        "permissions": ["manage_inventory"],
        "timeout": 60,
    },
    {
        "name": "adjust_price",
        "description": "调整商品价格",
        "parameters": {
            "type": "object",
            "properties": {
                "product_id": {
                    "type": "string",
                    "description": "商品ID",
                },
                "new_price": {
                    "type": "number",
                    "description": "新价格",
                },
                "reason": {
                    "type": "string",
                    "description": "调整原因",
                },
                "apply_to_platforms": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "应用到的平台",
                },
            },
            "required": ["product_id", "new_price"],
        },
        "handler": "product_manager.handlers.handle_adjust_price",
        "permissions": ["update_price"],
        "timeout": 30,
    },
]