"""Product Manager Skill - Handlers."""

from datetime import datetime
from typing import Any
import random

from core.agent.types import ExecutionContext


# Mock product data for MVP
_products_store: dict[str, dict[str, Any]] = {}


def _generate_mock_product(product_id: str) -> dict[str, Any]:
    """Generate mock product data."""
    return {
        "id": product_id,
        "name": f"商品-{product_id}",
        "category": random.choice(["服装", "美妆", "食品", "家居", "数码"]),
        "price": round(random.uniform(50, 500), 2),
        "original_price": round(random.uniform(80, 600), 2),
        "inventory": random.randint(10, 1000),
        "sales": random.randint(0, 500),
        "status": random.choice(["active", "inactive", "pending"]),
        "platforms": {
            "taobao": {"price": round(random.uniform(50, 500), 2), "inventory": random.randint(10, 500)},
            "jd": {"price": round(random.uniform(50, 500), 2), "inventory": random.randint(10, 500)},
            "pdd": {"price": round(random.uniform(45, 480), 2), "inventory": random.randint(10, 500)},
        },
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }


async def handle_get_product_info(
    params: dict[str, Any],
    context: ExecutionContext,
) -> dict[str, Any]:
    """Handle get_product_info tool call."""
    product_id = params.get("product_id")
    include_inventory = params.get("include_inventory", True)

    try:
        if product_id not in _products_store:
            _products_store[product_id] = _generate_mock_product(product_id)

        product = _products_store[product_id]

        result = {
            "id": product["id"],
            "name": product["name"],
            "category": product["category"],
            "price": product["price"],
            "original_price": product["original_price"],
            "status": product["status"],
            "sales": product["sales"],
        }

        if include_inventory:
            result["inventory"] = product["inventory"]
            result["platforms"] = product["platforms"]

        return {
            "success": True,
            "product": result,
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


async def handle_update_product(
    params: dict[str, Any],
    context: ExecutionContext,
) -> dict[str, Any]:
    """Handle update_product tool call."""
    product_id = params.get("product_id")
    updates = params.get("updates")

    try:
        if product_id not in _products_store:
            _products_store[product_id] = _generate_mock_product(product_id)

        product = _products_store[product_id]

        # Apply updates
        for key, value in updates.items():
            if key in product:
                product[key] = value

        product["updated_at"] = datetime.now().isoformat()

        return {
            "success": True,
            "product_id": product_id,
            "updated_fields": list(updates.keys()),
            "message": f"商品 {product_id} 已更新",
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


async def handle_sync_inventory(
    params: dict[str, Any],
    context: ExecutionContext,
) -> dict[str, Any]:
    """Handle sync_inventory tool call."""
    product_id = params.get("product_id")
    platform = params.get("platform", "all")
    action = params.get("action", "sync")

    try:
        if product_id:
            if product_id not in _products_store:
                _products_store[product_id] = _generate_mock_product(product_id)

            product = _products_store[product_id]

            if action == "sync":
                # Simulate sync
                for p_name, p_data in product["platforms"].items():
                    p_data["inventory"] = product["inventory"]

                return {
                    "success": True,
                    "product_id": product_id,
                    "action": "synced",
                    "inventory": product["inventory"],
                    "platforms_synced": list(product["platforms"].keys()),
                }

            elif action == "check":
                differences = []
                for p_name, p_data in product["platforms"].items():
                    if p_data["inventory"] != product["inventory"]:
                        differences.append({
                            "platform": p_name,
                            "local": product["inventory"],
                            "platform_value": p_data["inventory"],
                        })

                return {
                    "success": True,
                    "product_id": product_id,
                    "local_inventory": product["inventory"],
                    "differences": differences,
                    "sync_needed": len(differences) > 0,
                }

        else:
            # Sync all products
            synced_count = len(_products_store)

            return {
                "success": True,
                "action": "sync_all",
                "products_synced": synced_count,
                "message": f"已同步 {synced_count} 个商品的库存",
            }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


async def handle_adjust_price(
    params: dict[str, Any],
    context: ExecutionContext,
) -> dict[str, Any]:
    """Handle adjust_price tool call."""
    product_id = params.get("product_id")
    new_price = params.get("new_price")
    reason = params.get("reason", "manual_adjustment")
    platforms = params.get("apply_to_platforms", ["all"])

    try:
        if product_id not in _products_store:
            _products_store[product_id] = _generate_mock_product(product_id)

        product = _products_store[product_id]
        old_price = product["price"]

        product["price"] = new_price
        product["updated_at"] = datetime.now().isoformat()

        # Apply to platforms
        applied_platforms = []

        if "all" in platforms:
            for p_name, p_data in product["platforms"].items():
                p_data["price"] = new_price
                applied_platforms.append(p_name)
        else:
            for p_name in platforms:
                if p_name in product["platforms"]:
                    product["platforms"][p_name]["price"] = new_price
                    applied_platforms.append(p_name)

        return {
            "success": True,
            "product_id": product_id,
            "old_price": old_price,
            "new_price": new_price,
            "change": round(new_price - old_price, 2),
            "reason": reason,
            "platforms_applied": applied_platforms,
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }