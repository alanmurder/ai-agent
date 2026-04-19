"""Daily Planner Skill - Handlers."""

from datetime import datetime, timedelta
from typing import Any

from core.agent.types import ExecutionContext


# Simple in-memory storage for MVP
_events_store: dict[str, list[dict[str, Any]]] = {}


async def handle_create_event(
    params: dict[str, Any],
    context: ExecutionContext,
) -> dict[str, Any]:
    """Handle create_event tool call."""
    title = params.get("title")
    date = params.get("date")
    time = params.get("time")
    description = params.get("description", "")
    duration = params.get("duration_minutes", 60)

    user_id = context.user_id

    try:
        event = {
            "id": f"event-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "title": title,
            "date": date,
            "time": time,
            "description": description,
            "duration_minutes": duration,
            "created_at": datetime.now().isoformat(),
        }

        if user_id not in _events_store:
            _events_store[user_id] = []

        _events_store[user_id].append(event)

        return {
            "success": True,
            "event": event,
            "message": f"已创建日程: {title} ({date} {time})",
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


async def handle_list_events(
    params: dict[str, Any],
    context: ExecutionContext,
) -> dict[str, Any]:
    """Handle list_events tool call."""
    date = params.get("date", datetime.now().strftime("%Y-%m-%d"))
    days = params.get("days", 7)

    user_id = context.user_id

    try:
        user_events = _events_store.get(user_id, [])

        # Filter events in date range
        start_date = datetime.strptime(date, "%Y-%m-%d")
        end_date = start_date + timedelta(days=days)

        filtered = []

        for event in user_events:
            event_date = datetime.strptime(event["date"], "%Y-%m-%d")
            if start_date <= event_date <= end_date:
                filtered.append(event)

        # Sort by date and time
        filtered.sort(key=lambda e: (e["date"], e["time"]))

        return {
            "success": True,
            "events": filtered,
            "count": len(filtered),
            "date_range": f"{date} - {end_date.strftime('%Y-%m-%d')}",
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }