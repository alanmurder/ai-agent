"""Skill Evolution Module - Level 1 & 2 & 3 Evolution mechanisms."""

from datetime import datetime
from pathlib import Path
from typing import Any, Optional
import yaml

from skills.types import Skill, SkillDraft, SkillFeedback
from skills.loader import SkillLoader
from skills.manager import SkillManager
from core.memory.types import ExtractedItem
from core.logging import get_logger
from core.metrics import get_metrics, MetricNames

logger = get_logger("evolution")
metrics = get_metrics()


class MemoryEvolver:
    """Level 1: Memory evolution - automatically learn from interactions."""

    def __init__(self, memory_manager: Any) -> None:
        self.memory_manager = memory_manager

    async def analyze_conversation(
        self,
        conversation: list[dict[str, str]],
        user_id: str,
    ) -> list[ExtractedItem]:
        """Analyze conversation and extract information to remember."""
        extracted = []

        for message in conversation:
            content = message.get("content", "")
            role = message.get("role", "")

            if role != "user":
                continue

            # Extract preferences
            preferences = self._extract_preferences(content)
            for pref in preferences:
                extracted.append(ExtractedItem(
                    type="preference",
                    content=pref,
                    confidence=0.8,
                ))

            # Extract facts
            facts = self._extract_facts(content)
            for fact in facts:
                extracted.append(ExtractedItem(
                    type="fact",
                    content=fact,
                    confidence=0.9,
                ))

            # Extract patterns
            patterns = self._extract_patterns(content)
            for pattern in patterns:
                extracted.append(ExtractedItem(
                    type="pattern",
                    content=pattern,
                    confidence=0.7,
                ))

        metrics.increment(MetricNames.EVOLUTION_EVENT_COUNT, len(extracted))

        return extracted

    async def apply_extractions(
        self,
        extractions: list[ExtractedItem],
        user_id: str,
    ) -> dict[str, int]:
        """Apply extracted information to user's memory."""
        applied = {"preferences": 0, "facts": 0, "patterns": 0}

        for item in extractions:
            if item.type == "preference":
                await self._update_soul_md(user_id, item.content)
                applied["preferences"] += 1

            elif item.type == "fact":
                await self._update_memory_md(user_id, item.content)
                applied["facts"] += 1

            elif item.type == "pattern":
                await self._record_pattern(user_id, item.content)
                applied["patterns"] += 1

        logger.info(
            "memory_evolution_applied",
            user_id=user_id,
            items=applied,
        )

        return applied

    def _extract_preferences(self, content: str) -> list[str]:
        """Extract user preferences from content."""
        preferences = []

        # Chinese patterns
        patterns = [
            r"我喜欢(.+)",
            r"我偏好(.+)",
            r"我更喜欢(.+)",
            r"我希望(.+)",
            r"我想要(.+)",
        ]

        # English patterns
        patterns.extend([
            r"I prefer (.+)",
            r"I like (.+)",
            r"I want (.+)",
            r"I would like (.+)",
        ])

        import re
        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                if match and len(match) > 2:
                    preferences.append(match.strip())

        return preferences

    def _extract_facts(self, content: str) -> list[str]:
        """Extract important facts from content."""
        facts = []

        import re

        # Name patterns
        name_patterns = [
            r"我叫(.+)",
            r"我是(.+)",
            r"我的名字是(.+)",
            r"my name is (.+)",
        ]

        for pattern in name_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                if match and len(match) > 1:
                    facts.append(f"名字: {match.strip()}")

        return facts

    def _extract_patterns(self, content: str) -> list[str]:
        """Extract usage patterns from content."""
        patterns = []

        import re

        # Frequency patterns
        freq_patterns = [
            r"经常(.+)",
            r"总是(.+)",
            r"通常(.+)",
            r"always (.+)",
            r"usually (.+)",
        ]

        for pattern in freq_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                if match and len(match) > 2:
                    patterns.append(f"使用模式: {match.strip()}")

        return patterns

    async def _update_soul_md(self, user_id: str, content: str) -> None:
        """Update SOUL.md with preference."""
        await self.memory_manager.update_memory(
            user_id=user_id,
            key="偏好",
            value=content,
        )

    async def _update_memory_md(self, user_id: str, content: str) -> None:
        """Update MEMORY.md with fact."""
        await self.memory_manager.update_memory(
            user_id=user_id,
            key="信息",
            value=content,
        )

    async def _record_pattern(self, user_id: str, content: str) -> None:
        """Record usage pattern."""
        await self.memory_manager.update_memory(
            user_id=user_id,
            key="模式",
            value=content,
        )


class SkillEvolver:
    """Level 2: Skill evolution - create and optimize skills."""

    def __init__(self, skill_manager: SkillManager) -> None:
        self.skill_manager = skill_manager

    async def assist_skill_creation(
        self,
        user_request: str,
        user_id: str,
    ) -> SkillDraft:
        """Help user create a new skill based on their request."""
        # Analyze the request
        requirement = await self._analyze_requirement(user_request)

        # Generate skill skeleton
        skill_md = self._generate_skill_md(requirement)
        tools_code = self._generate_tools_code(requirement)
        handlers_code = self._generate_handlers_code(requirement)

        draft = SkillDraft(
            name=requirement.get("name", "custom_skill"),
            skill_md=skill_md,
            tools=tools_code,
            handlers=handlers_code,
            config=requirement,
        )

        logger.info(
            "skill_draft_created",
            user_id=user_id,
            skill_name=draft.name,
        )

        return draft

    async def optimize_skill(
        self,
        skill_name: str,
        feedback: SkillFeedback,
    ) -> dict[str, Any]:
        """Optimize skill based on usage feedback."""
        skill = await self.skill_manager.get_skill(skill_name)

        if not skill:
            return {"success": False, "error": "Skill not found"}

        optimizations = []

        if feedback.slow_execution:
            # Suggest performance optimizations
            optimizations.append({
                "type": "performance",
                "suggestions": [
                    "Consider caching frequently accessed data",
                    "Reduce unnecessary API calls",
                    "Optimize database queries",
                ],
            })

        if feedback.low_accuracy:
            # Suggest accuracy improvements
            optimizations.append({
                "type": "accuracy",
                "suggestions": [
                    "Improve prompt templates",
                    "Add more context examples",
                    "Implement fallback strategies",
                ],
            })

        for suggestion in feedback.user_suggestions:
            optimizations.append({
                "type": "user_suggestion",
                "suggestion": suggestion,
            })

        metrics.increment(MetricNames.EVOLUTION_EVENT_COUNT)

        logger.info(
            "skill_optimization_suggested",
            skill_name=skill_name,
            optimizations=len(optimizations),
        )

        return {
            "success": True,
            "skill_name": skill_name,
            "optimizations": optimizations,
            "feedback_metrics": feedback.metrics,
        }

    async def _analyze_requirement(self, request: str) -> dict[str, Any]:
        """Analyze user request to determine skill requirements."""
        # Extract key information
        requirement = {
            "name": "custom_skill",
            "description": request[:100],
            "category": "custom",
            "tools_needed": [],
        }

        # Simple keyword analysis
        if "文件" in request or "file" in request.lower():
            requirement["tools_needed"].append("file_operations")
            requirement["category"] = "system"

        if "搜索" in request or "search" in request.lower():
            requirement["tools_needed"].append("search")

        if "分析" in request or "analyze" in request.lower():
            requirement["tools_needed"].append("analysis")

        return requirement

    def _generate_skill_md(self, requirement: dict[str, Any]) -> str:
        """Generate SKILL.md content."""
        name = requirement.get("name", "custom_skill")
        description = requirement.get("description", "")

        content = f"""---
name: {name}
version: 1.0.0
category: custom
description: {description}
author: user
dependencies: []
permissions: []
tags:
  - custom
  - user_created
enabled: true
priority: 50
---

## 功能描述

用户自定义技能。

## 使用场景

根据用户需求定制。

## 工具列表

- `execute`: 执行自定义任务
"""
        return content

    def _generate_tools_code(self, requirement: dict[str, Any]) -> str:
        """Generate tools.py content."""
        content = '''"""Custom Skill - Tools definitions."""

TOOL_DEFINITIONS = [
    {
        "name": "execute",
        "description": "执行自定义任务",
        "parameters": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "要执行的动作",
                },
                "params": {
                    "type": "object",
                    "description": "动作参数",
                },
            },
            "required": ["action"],
        },
        "handler": "handlers.handle_execute",
        "timeout": 60,
    },
]
'''
        return content

    def _generate_handlers_code(self, requirement: dict[str, Any]) -> str:
        """Generate handlers.py content."""
        content = '''"""Custom Skill - Handlers."""

from typing import Any
from core.agent.types import ExecutionContext


async def handle_execute(
    params: dict[str, Any],
    context: ExecutionContext,
) -> dict[str, Any]:
    """Handle execute tool call."""
    action = params.get("action")
    action_params = params.get("params", {})

    # Implement custom logic here
    return {
        "success": True,
        "action": action,
        "result": "Custom action executed",
    }
'''
        return content

    async def save_skill_draft(
        self,
        draft: SkillDraft,
        extensions_path: str,
        user_id: str,
    ) -> dict[str, Any]:
        """Save skill draft to extensions directory."""
        skill_dir = Path(extensions_path) / draft.name
        skill_dir.mkdir(parents=True, exist_ok=True)

        # Write files
        (skill_dir / "SKILL.md").write_text(draft.skill_md, encoding="utf-8")
        (skill_dir / "tools.py").write_text(draft.tools, encoding="utf-8")
        (skill_dir / "handlers.py").write_text(draft.handlers, encoding="utf-8")

        # Create prompts.py
        prompts_content = '''"""Custom Skill - Prompts."""

PROMPTS = {
    "system": "这是一个用户自定义的技能。请根据用户的需求执行相应的任务。",
}
'''
        (skill_dir / "prompts.py").write_text(prompts_content, encoding="utf-8")

        metrics.increment(MetricNames.SKILL_CREATION_COUNT)

        logger.info(
            "skill_draft_saved",
            skill_name=draft.name,
            user_id=user_id,
            path=str(skill_dir),
        )

        return {
            "success": True,
            "skill_name": draft.name,
            "path": str(skill_dir),
            "message": f"技能 '{draft.name}' 已保存",
        }


class AutonomousEvolver:
    """Level 3: Autonomous evolution - self-improving capabilities."""

    def __init__(
        self,
        skill_manager: SkillManager,
        model_router: Any,
        extensions_path: str,
    ) -> None:
        self.skill_manager = skill_manager
        self.model_router = model_router
        self.extensions_path = extensions_path
        self._request_history: dict[str, list[dict[str, Any]]] = {}
        self._failed_requests: dict[str, list[dict[str, Any]]] = {}

    async def identify_gaps(self, user_id: str) -> list[dict[str, Any]]:
        """Identify functionality gaps from usage patterns."""
        gaps = []

        # Analyze failed requests
        failed = self._failed_requests.get(user_id, [])

        for request in failed:
            reason = request.get("reason")

            if reason == "missing_skill":
                gaps.append({
                    "type": "new_skill",
                    "description": request.get("needed_capability"),
                    "priority": "high",
                    "source": "failed_request",
                })

            elif reason == "missing_tool":
                gaps.append({
                    "type": "new_tool",
                    "description": request.get("needed_tool"),
                    "priority": "medium",
                    "skill_context": request.get("skill_name"),
                })

        # Analyze skill coverage
        available_skills = await self.skill_manager.discover_skills()

        # Check if commonly requested functionality is covered
        common_requests = [
            ("数据分析", "analysis"),
            ("文件处理", "file_manager"),
            ("日程管理", "daily_planner"),
            ("代码辅助", "code_helper"),
        ]

        for request_type, expected_skill in common_requests:
            covered = any(s.name == expected_skill for s in available_skills)

            if not covered:
                gaps.append({
                    "type": "missing_common_skill",
                    "description": request_type,
                    "expected_skill": expected_skill,
                    "priority": "medium",
                })

        metrics.increment(MetricNames.AUTONOMOUS_CREATION_COUNT)

        logger.info(
            "gaps_identified",
            user_id=user_id,
            gaps_count=len(gaps),
        )

        return gaps

    async def autonomous_create_skill(
        self,
        gap: dict[str, Any],
        user_id: str,
    ) -> dict[str, Any]:
        """Autonomously create a new skill to fill a gap."""
        description = gap.get("description")

        if gap.get("type") not in ["new_skill", "missing_common_skill"]:
            return {
                "success": False,
                "error": "Cannot autonomously create this type of gap",
            }

        try:
            # Analyze what skill is needed
            spec = await self._analyze_capability_need(description)

            # Generate skill code using model
            skill_code = await self._generate_skill_code(spec)

            # Create sandbox and test
            sandbox_result = await self._test_in_sandbox(skill_code)

            if not sandbox_result.get("success"):
                return {
                    "success": False,
                    "error": "Sandbox test failed",
                    "details": sandbox_result,
                }

            # Security audit
            security_result = await self._security_audit(skill_code)

            if not security_result.get("safe"):
                return {
                    "success": False,
                    "error": "Security audit failed",
                    "details": security_result,
                }

            # Deploy the skill
            skill = await self._deploy_skill(skill_code, user_id)

            metrics.increment(MetricNames.AUTONOMOUS_CREATION_COUNT)

            logger.info(
                "skill_autonomously_created",
                skill_name=skill.get("name"),
                user_id=user_id,
            )

            return {
                "success": True,
                "skill": skill,
                "message": f"技能 '{skill.get('name')}' 已自动创建并部署",
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }

    async def _analyze_capability_need(self, description: str) -> dict[str, Any]:
        """Analyze what capability is needed."""
        spec = {
            "name": description.lower().replace(" ", "_"),
            "description": description,
            "tools_needed": [],
            "category": "custom",
        }

        # Analyze keywords
        keywords_analysis = {
            "分析": {"category": "analysis", "tools_needed": ["analyze", "report"]},
            "搜索": {"category": "search", "tools_needed": ["search", "filter"]},
            "处理": {"category": "processing", "tools_needed": ["process", "transform"]},
            "管理": {"category": "management", "tools_needed": ["manage", "update"]},
            "查询": {"category": "query", "tools_needed": ["query", "list"]},
        }

        for keyword, config in keywords_analysis.items():
            if keyword in description:
                spec["category"] = config["category"]
                spec["tools_needed"] = config["tools_needed"]

        return spec

    async def _generate_skill_code(self, spec: dict[str, Any]) -> dict[str, Any]:
        """Generate skill code based on spec."""
        name = spec.get("name", "custom_skill")
        description = spec.get("description", "")
        tools_needed = spec.get("tools_needed", ["execute"])

        # Generate SKILL.md
        skill_md = f"""---
name: {name}
version: 1.0.0
category: {spec.get('category', 'custom')}
description: {description}
author: autonomous
dependencies: []
permissions: []
tags:
  - autonomous_created
  - custom
enabled: true
priority: 50
---

## 功能描述

{description}

## 使用场景

自动识别并创建的功能。

## 工具列表

{chr(10).join([f"- `{t}`: 相关工具" for t in tools_needed])}
"""

        # Generate tools.py
        tools_definitions = []

        for tool_name in tools_needed:
            tools_definitions.append(f'''    {{
        "name": "{tool_name}",
        "description": "执行{tool_name}操作",
        "parameters": {{
            "type": "object",
            "properties": {{
                "input": {{
                    "type": "string",
                    "description": "输入内容",
                }},
            }},
            "required": ["input"],
        }},
        "handler": "handlers.handle_{tool_name}",
        "timeout": 60,
    },''')

        tools_py = f'''"""{name} Skill - Tools definitions."""

TOOL_DEFINITIONS = [
{chr(10).join(tools_definitions)}
]
'''

        # Generate handlers.py
        handlers_list = []

        for tool_name in tools_needed:
            handlers_list.append(f'''
async def handle_{tool_name}(
    params: dict[str, Any],
    context: ExecutionContext,
) -> dict[str, Any]:
    """Handle {tool_name} tool call."""
    input_data = params.get("input")

    # Auto-generated handler - customize as needed
    return {{
        "success": True,
        "tool": "{tool_name}",
        "input": input_data,
        "result": "Auto-generated result",
    }}
''')

        handlers_py = f'''"""{name} Skill - Handlers."""

from typing import Any
from core.agent.types import ExecutionContext

{chr(10).join(handlers_list)}
'''

        return {
            "name": name,
            "skill_md": skill_md,
            "tools_py": tools_py,
            "handlers_py": handlers_py,
        }

    async def _test_in_sandbox(self, skill_code: dict[str, Any]) -> dict[str, Any]:
        """Test skill code in sandbox."""
        # MVP: Basic syntax check
        try:
            # Check if Python code is valid syntax
            import ast

            ast.parse(skill_code.get("tools_py", ""))
            ast.parse(skill_code.get("handlers_py", ""))

            return {
                "success": True,
                "tests_passed": ["syntax_check"],
                "message": "Sandbox tests passed",
            }

        except SyntaxError as e:
            return {
                "success": False,
                "error": f"Syntax error: {e}",
            }

    async def _security_audit(self, skill_code: dict[str, Any]) -> dict[str, Any]:
        """Perform security audit on skill code."""
        code = skill_code.get("handlers_py", "")

        # Check for dangerous patterns
        dangerous_patterns = [
            "eval(",
            "exec(",
            "os.system(",
            "subprocess.call(",
            "__import__",
            "open(",
        ]

        issues = []

        for pattern in dangerous_patterns:
            if pattern in code:
                issues.append(f"Found dangerous pattern: {pattern}")

        if issues:
            return {
                "safe": False,
                "issues": issues,
                "recommendation": "Remove dangerous code patterns",
            }

        return {
            "safe": True,
            "issues": [],
            "message": "Security audit passed",
        }

    async def _deploy_skill(
        self,
        skill_code: dict[str, Any],
        user_id: str,
    ) -> dict[str, Any]:
        """Deploy skill to extensions directory."""
        name = skill_code.get("name", "custom_skill")

        skill_dir = Path(self.extensions_path) / name
        skill_dir.mkdir(parents=True, exist_ok=True)

        # Write skill files
        (skill_dir / "SKILL.md").write_text(skill_code.get("skill_md", ""), encoding="utf-8")
        (skill_dir / "tools.py").write_text(skill_code.get("tools_py", ""), encoding="utf-8")
        (skill_dir / "handlers.py").write_text(skill_code.get("handlers_py", ""), encoding="utf-8")

        # Create prompts.py
        prompts = '''"""Auto-generated Skill - Prompts."""

PROMPTS = {
    "system": "这是一个自动创建的技能。",
}
'''
        (skill_dir / "prompts.py").write_text(prompts, encoding="utf-8")

        return {
            "name": name,
            "path": str(skill_dir),
            "created_by": "autonomous",
            "user_id": user_id,
        }

    def record_request(
        self,
        user_id: str,
        request: str,
        success: bool,
        reason: Optional[str] = None,
    ) -> None:
        """Record request for gap analysis."""
        record = {
            "request": request,
            "success": success,
            "reason": reason,
            "timestamp": datetime.now().isoformat(),
        }

        if user_id not in self._request_history:
            self._request_history[user_id] = []

        self._request_history[user_id].append(record)

        if not success:
            if user_id not in self._failed_requests:
                self._failed_requests[user_id] = []

            self._failed_requests[user_id].append(record)