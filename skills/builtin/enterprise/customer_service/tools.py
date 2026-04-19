"""Customer Service Skill - Tools definitions."""

TOOL_DEFINITIONS = [
    {
        "name": "query_order",
        "description": "查询订单信息和状态",
        "parameters": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "string",
                    "description": "订单ID",
                },
                "customer_id": {
                    "type": "string",
                    "description": "客户ID",
                },
            },
            "required": [],
        },
        "handler": "customer_service.handlers.handle_query_order",
        "permissions": ["read_order"],
        "timeout": 30,
    },
    {
        "name": "handle_refund",
        "description": "处理退款申请",
        "parameters": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "string",
                    "description": "订单ID",
                },
                "reason": {
                    "type": "string",
                    "description": "退款原因",
                },
                "amount": {
                    "type": "number",
                    "description": "退款金额，留空则全额退款",
                },
                "type": {
                    "type": "string",
                    "description": "退款类型：refund_only, return_refund",
                    "default": "refund_only",
                },
            },
            "required": ["order_id", "reason"],
        },
        "handler": "customer_service.handlers.handle_handle_refund",
        "permissions": ["handle_refund"],
        "timeout": 60,
    },
    {
        "name": "auto_reply",
        "description": "自动回复客户咨询",
        "parameters": {
            "type": "object",
            "properties": {
                "customer_id": {
                    "type": "string",
                    "description": "客户ID",
                },
                "message_type": {
                    "type": "string",
                    "description": "消息类型：greeting, order_query, refund_request, complaint",
                },
                "context": {
                    "type": "string",
                    "description": "上下文信息",
                },
            },
            "required": ["customer_id", "message_type"],
        },
        "handler": "customer_service.handlers.handle_auto_reply",
        "permissions": ["respond_customer"],
        "timeout": 30,
    },
]