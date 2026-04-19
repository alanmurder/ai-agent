"""Customer Service Skill - Handlers."""

from datetime import datetime, timedelta
from typing import Any
import random

from core.agent.types import ExecutionContext


# Mock data stores
_orders_store: dict[str, dict[str, Any]] = {}
_refunds_store: dict[str, list[dict[str, Any]]] = {}


def _generate_mock_order(order_id: str) -> dict[str, Any]:
    """Generate mock order."""
    return {
        "id": order_id,
        "customer_id": f"customer-{random.randint(1000, 9999)}",
        "products": [
            {"name": f"商品-{random.randint(1, 10)}", "price": round(random.uniform(50, 200), 2), "quantity": random.randint(1, 3)}
        ],
        "total_amount": round(random.uniform(100, 500), 2),
        "status": random.choice(["pending", "paid", "shipped", "delivered", "cancelled"]),
        "created_at": (datetime.now() - timedelta(days=random.randint(0, 7))).isoformat(),
        "payment_method": random.choice(["支付宝", "微信支付", "银行卡"]),
        "shipping_address": "测试地址",
    }


async def handle_query_order(
    params: dict[str, Any],
    context: ExecutionContext,
) -> dict[str, Any]:
    """Handle query_order tool call."""
    order_id = params.get("order_id")
    customer_id = params.get("customer_id")

    try:
        if order_id:
            if order_id not in _orders_store:
                _orders_store[order_id] = _generate_mock_order(order_id)

            order = _orders_store[order_id]

            return {
                "success": True,
                "order": order,
                "message": f"订单 {order_id} 当前状态: {order['status']}",
            }

        elif customer_id:
            # Find orders for customer
            customer_orders = [
                o for o in _orders_store.values()
                if o.get("customer_id") == customer_id
            ]

            if not customer_orders:
                # Generate some mock orders
                for i in range(3):
                    oid = f"order-{random.randint(10000, 99999)}"
                    order = _generate_mock_order(oid)
                    order["customer_id"] = customer_id
                    _orders_store[oid] = order
                    customer_orders.append(order)

            return {
                "success": True,
                "customer_id": customer_id,
                "orders": customer_orders,
                "total_orders": len(customer_orders),
            }

        else:
            return {
                "success": False,
                "error": "请提供订单ID或客户ID",
            }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


async def handle_handle_refund(
    params: dict[str, Any],
    context: ExecutionContext,
) -> dict[str, Any]:
    """Handle handle_refund tool call."""
    order_id = params.get("order_id")
    reason = params.get("reason")
    amount = params.get("amount")
    refund_type = params.get("type", "refund_only")

    try:
        if order_id not in _orders_store:
            _orders_store[order_id] = _generate_mock_order(order_id)

        order = _orders_store[order_id]

        # Calculate refund amount
        if amount is None:
            amount = order["total_amount"]

        # Create refund record
        refund = {
            "id": f"refund-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "order_id": order_id,
            "amount": amount,
            "reason": reason,
            "type": refund_type,
            "status": "processing",
            "created_at": datetime.now().isoformat(),
            "estimated_completion": (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d"),
        }

        if order_id not in _refunds_store:
            _refunds_store[order_id] = []

        _refunds_store[order_id].append(refund)

        # Update order status
        order["status"] = "refunding"

        return {
            "success": True,
            "refund": refund,
            "order_id": order_id,
            "refund_amount": amount,
            "message": f"退款申请已提交，预计{refund['estimated_completion']}完成",
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


async def handle_auto_reply(
    params: dict[str, Any],
    context: ExecutionContext,
) -> dict[str, Any]:
    """Handle auto_reply tool call."""
    customer_id = params.get("customer_id")
    message_type = params.get("message_type")
    ctx = params.get("context", "")

    try:
        # Generate appropriate reply
        replies = {
            "greeting": "您好！欢迎来到我们的直播间，有什么可以帮助您的吗？",
            "order_query": "请提供您的订单号，我帮您查询订单状态。如果是最近下单，一般在24小时内发货。",
            "refund_request": "关于退款申请，请在订单详情页面提交退款申请，我们会在3个工作日内处理。如有特殊情况请联系客服。",
            "complaint": "非常抱歉给您带来不便！请详细描述您的问题，我们会尽快为您解决。",
            "product_question": "关于商品详情，请查看商品页面说明。如有具体问题，请详细描述，我来为您解答。",
        }

        reply = replies.get(message_type, "感谢您的咨询，请详细描述您的问题，我会尽快回复。")

        # Add context-specific info
        if ctx:
            reply += f"\n\n关于 '{ctx}' 的补充说明：建议您联系客服获取详细帮助。"

        return {
            "success": True,
            "customer_id": customer_id,
            "message_type": message_type,
            "reply": reply,
            "generated_at": datetime.now().isoformat(),
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }