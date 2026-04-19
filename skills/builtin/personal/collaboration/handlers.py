"""Collaboration Skill - Handlers."""

from datetime import datetime, timedelta
from typing import Any

from core.agent.types import ExecutionContext


# In-memory storage for MVP
_documents_store: dict[str, list[dict[str, Any]]] = {}
_tasks_store: dict[str, list[dict[str, Any]]] = {}
_meetings_store: dict[str, list[dict[str, Any]]] = {}


async def handle_create_document(
    params: dict[str, Any],
    context: ExecutionContext,
) -> dict[str, Any]:
    """Handle create_document tool call."""
    title = params.get("title")
    content = params.get("content")
    doc_type = params.get("type", "notes")
    collaborators = params.get("collaborators", [])

    user_id = context.user_id

    try:
        document = {
            "id": f"doc-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "title": title,
            "content": content,
            "type": doc_type,
            "owner": user_id,
            "collaborators": collaborators,
            "version": 1,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }

        if user_id not in _documents_store:
            _documents_store[user_id] = []

        _documents_store[user_id].append(document)

        return {
            "success": True,
            "document": document,
            "message": f"文档 '{title}' 已创建",
            "share_link": f"/docs/{document['id']}",
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


async def handle_assign_task(
    params: dict[str, Any],
    context: ExecutionContext,
) -> dict[str, Any]:
    """Handle assign_task tool call."""
    title = params.get("title")
    description = params.get("description", "")
    assignee = params.get("assignee")
    priority = params.get("priority", "medium")
    due_date = params.get("due_date")
    tags = params.get("tags", [])

    user_id = context.user_id

    try:
        task = {
            "id": f"task-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "title": title,
            "description": description,
            "assignee": assignee,
            "assigner": user_id,
            "priority": priority,
            "due_date": due_date,
            "tags": tags,
            "status": "pending",
            "progress": 0,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }

        if user_id not in _tasks_store:
            _tasks_store[user_id] = []

        _tasks_store[user_id].append(task)

        return {
            "success": True,
            "task": task,
            "message": f"任务 '{title}' 已分配给 {assignee}",
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


async def handle_schedule_meeting(
    params: dict[str, Any],
    context: ExecutionContext,
) -> dict[str, Any]:
    """Handle schedule_meeting tool call."""
    title = params.get("title")
    date = params.get("date")
    time = params.get("time")
    duration = params.get("duration_minutes", 60)
    participants = params.get("participants", [])
    location = params.get("location", "待定")
    agenda = params.get("agenda", [])

    user_id = context.user_id

    try:
        meeting = {
            "id": f"meeting-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "title": title,
            "date": date,
            "time": time,
            "duration_minutes": duration,
            "participants": participants,
            "location": location,
            "agenda": agenda,
            "organizer": user_id,
            "status": "scheduled",
            "created_at": datetime.now().isoformat(),
        }

        if user_id not in _meetings_store:
            _meetings_store[user_id] = []

        _meetings_store[user_id].append(meeting)

        # Calculate end time
        start_dt = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
        end_dt = start_dt + timedelta(minutes=duration)

        return {
            "success": True,
            "meeting": meeting,
            "message": f"会议 '{title}' 已安排在 {date} {time}",
            "end_time": end_dt.strftime("%H:%M"),
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


async def handle_list_tasks(
    params: dict[str, Any],
    context: ExecutionContext,
) -> dict[str, Any]:
    """Handle list_tasks tool call."""
    assignee = params.get("assignee")
    status = params.get("status")
    priority = params.get("priority")

    user_id = context.user_id

    try:
        all_tasks = _tasks_store.get(user_id, [])

        # Apply filters
        filtered = all_tasks

        if assignee:
            filtered = [t for t in filtered if t.get("assignee") == assignee]

        if status:
            filtered = [t for t in filtered if t.get("status") == status]

        if priority:
            filtered = [t for t in filtered if t.get("priority") == priority]

        # Sort by priority and due date
        priority_order = {"high": 0, "medium": 1, "low": 2}
        filtered.sort(key=lambda t: (
            priority_order.get(t.get("priority", "medium"), 1),
            t.get("due_date", "9999-99-99")
        ))

        return {
            "success": True,
            "tasks": filtered,
            "total_count": len(filtered),
            "by_status": {
                "pending": len([t for t in filtered if t["status"] == "pending"]),
                "in_progress": len([t for t in filtered if t["status"] == "in_progress"]),
                "completed": len([t for t in filtered if t["status"] == "completed"]),
            },
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


async def handle_update_task_status(
    params: dict[str, Any],
    context: ExecutionContext,
) -> dict[str, Any]:
    """Handle update_task_status tool call."""
    task_id = params.get("task_id")
    status = params.get("status")
    progress = params.get("progress")
    notes = params.get("notes", "")

    user_id = context.user_id

    try:
        all_tasks = _tasks_store.get(user_id, [])

        # Find task
        task = None
        for t in all_tasks:
            if t.get("id") == task_id:
                task = t
                break

        if not task:
            return {
                "success": False,
                "error": "任务不存在",
            }

        # Update status
        task["status"] = status

        if progress is not None:
            task["progress"] = min(100, max(0, progress))

        task["notes"] = notes
        task["updated_at"] = datetime.now().isoformat()

        return {
            "success": True,
            "task": task,
            "message": f"任务 '{task['title']}' 状态已更新为 {status}",
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }