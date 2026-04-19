"""Study Assistant Skill - Handlers."""

from datetime import datetime, timedelta
from typing import Any
import json

from core.agent.types import ExecutionContext


# In-memory storage for MVP
_notes_store: dict[str, list[dict[str, Any]]] = {}
_plans_store: dict[str, dict[str, Any]] = {}
_progress_store: dict[str, list[dict[str, Any]]] = {}


async def handle_create_note(
    params: dict[str, Any],
    context: ExecutionContext,
) -> dict[str, Any]:
    """Handle create_note tool call."""
    title = params.get("title")
    content = params.get("content")
    category = params.get("category", "general")
    tags = params.get("tags", [])

    user_id = context.user_id

    try:
        note = {
            "id": f"note-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "title": title,
            "content": content,
            "category": category,
            "tags": tags,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }

        if user_id not in _notes_store:
            _notes_store[user_id] = []

        _notes_store[user_id].append(note)

        return {
            "success": True,
            "note": note,
            "message": f"笔记 '{title}' 已创建",
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


async def handle_organize_notes(
    params: dict[str, Any],
    context: ExecutionContext,
) -> dict[str, Any]:
    """Handle organize_notes tool call."""
    action = params.get("action")
    category = params.get("category")
    keyword = params.get("keyword")
    note_ids = params.get("note_ids", [])

    user_id = context.user_id

    try:
        user_notes = _notes_store.get(user_id, [])

        if action == "list":
            # List all notes or by category
            if category:
                filtered = [n for n in user_notes if n.get("category") == category]
            else:
                filtered = user_notes

            return {
                "success": True,
                "notes": filtered,
                "count": len(filtered),
            }

        elif action == "search":
            # Search notes by keyword
            if not keyword:
                return {
                    "success": False,
                    "error": "搜索需要提供关键词",
                }

            results = []
            for note in user_notes:
                if keyword.lower() in note.get("title", "").lower() or \
                   keyword.lower() in note.get("content", "").lower():
                    results.append(note)

            return {
                "success": True,
                "notes": results,
                "keyword": keyword,
                "count": len(results),
            }

        elif action == "merge":
            # Merge multiple notes
            if len(note_ids) < 2:
                return {
                    "success": False,
                    "error": "合并需要至少2个笔记",
                }

            notes_to_merge = []
            for note in user_notes:
                if note.get("id") in note_ids:
                    notes_to_merge.append(note)

            if len(notes_to_merge) < 2:
                return {
                    "success": False,
                    "error": "未找到指定的笔记",
                }

            # Create merged note
            merged_content = "\n\n---\n\n".join([
                f"## {n['title']}\n{n['content']}"
                for n in notes_to_merge
            ])

            merged_tags = []
            for n in notes_to_merge:
                merged_tags.extend(n.get("tags", []))
            merged_tags = list(set(merged_tags))

            merged_note = {
                "id": f"merged-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "title": f"合并笔记 ({len(notes_to_merge)}个)",
                "content": merged_content,
                "category": notes_to_merge[0].get("category", "general"),
                "tags": merged_tags,
                "merged_from": note_ids,
                "created_at": datetime.now().isoformat(),
            }

            _notes_store[user_id].append(merged_note)

            return {
                "success": True,
                "merged_note": merged_note,
                "original_count": len(notes_to_merge),
            }

        elif action == "categorize":
            # Auto categorize notes
            categories: dict[str, list] = {}

            for note in user_notes:
                cat = note.get("category", "general")
                if cat not in categories:
                    categories[cat] = []
                categories[cat].append(note)

            return {
                "success": True,
                "categories": {
                    cat: [n["id"] for n in notes]
                    for cat, notes in categories.items()
                },
                "total_notes": len(user_notes),
            }

        else:
            return {
                "success": False,
                "error": f"未知操作: {action}",
            }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


async def handle_create_study_plan(
    params: dict[str, Any],
    context: ExecutionContext,
) -> dict[str, Any]:
    """Handle create_study_plan tool call."""
    subject = params.get("subject")
    goal = params.get("goal")
    duration_days = params.get("duration_days", 30)
    daily_hours = params.get("daily_hours", 2)
    start_date = params.get("start_date", datetime.now().strftime("%Y-%m-%d"))

    user_id = context.user_id

    try:
        # Generate daily tasks
        start = datetime.strptime(start_date, "%Y-%m-%d")
        daily_tasks = []

        for day in range(duration_days):
            date = start + timedelta(days=day)
            daily_tasks.append({
                "day": day + 1,
                "date": date.strftime("%Y-%m-%d"),
                "hours": daily_hours,
                "tasks": [],
                "completed": False,
            })

        plan = {
            "id": f"plan-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "subject": subject,
            "goal": goal,
            "duration_days": duration_days,
            "daily_hours": daily_hours,
            "start_date": start_date,
            "end_date": (start + timedelta(days=duration_days - 1)).strftime("%Y-%m-%d"),
            "daily_tasks": daily_tasks,
            "total_hours": duration_days * daily_hours,
            "progress_hours": 0,
            "created_at": datetime.now().isoformat(),
        }

        _plans_store[user_id] = plan
        _progress_store[user_id] = []

        return {
            "success": True,
            "plan": plan,
            "message": f"学习计划 '{subject}' 已创建，共{duration_days}天",
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


async def handle_track_progress(
    params: dict[str, Any],
    context: ExecutionContext,
) -> dict[str, Any]:
    """Handle track_progress tool call."""
    plan_id = params.get("plan_id")
    date = params.get("date", datetime.now().strftime("%Y-%m-%d"))
    hours_spent = params.get("hours_spent", 0)
    completed_tasks = params.get("completed_tasks", [])
    notes = params.get("notes", "")

    user_id = context.user_id

    try:
        plan = _plans_store.get(user_id)

        if not plan or plan.get("id") != plan_id:
            return {
                "success": False,
                "error": "学习计划不存在",
            }

        # Record progress
        progress = {
            "date": date,
            "hours_spent": hours_spent,
            "completed_tasks": completed_tasks,
            "notes": notes,
            "recorded_at": datetime.now().isoformat(),
        }

        if user_id not in _progress_store:
            _progress_store[user_id] = []

        _progress_store[user_id].append(progress)

        # Update plan progress
        plan["progress_hours"] = sum(
            p.get("hours_spent", 0)
            for p in _progress_store[user_id]
        )

        # Calculate completion percentage
        completion = (plan["progress_hours"] / plan["total_hours"]) * 100

        return {
            "success": True,
            "progress": progress,
            "total_progress_hours": plan["progress_hours"],
            "completion_percentage": round(completion, 2),
            "remaining_hours": plan["total_hours"] - plan["progress_hours"],
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }