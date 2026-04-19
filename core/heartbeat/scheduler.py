"""HEARTBEAT Scheduler - Proactive task scheduling and execution."""

import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional
import yaml
import re

from core.evolution.evolver import AutonomousEvolver, MemoryEvolver
from skills.manager import SkillManager
from core.memory.manager import MemoryManager
from core.logging import get_logger
from core.metrics import get_metrics, MetricNames
from config import get_settings

logger = get_logger("heartbeat")
metrics = get_metrics()


@dataclass
class HeartbeatTask:
    """A task to be executed by heartbeat scheduler."""
    name: str
    action: str
    schedule: str  # cron-like or interval
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    enabled: bool = True
    params: dict[str, Any] = {}


class HeartbeatConfig:
    """Configuration from HEARTBEAT.md file."""

    def __init__(self, config_path: str) -> None:
        self.config_path = Path(config_path)
        self.tasks: list[HeartbeatTask] = []
        self.interval: int = 300  # Default 5 minutes
        self.evolution_enabled: bool = True
        self.evolution_level: int = 1

    def load(self) -> None:
        """Load configuration from HEARTBEAT.md."""
        if not self.config_path.exists():
            self._create_default()
            return

        content = self.config_path.read_text(encoding="utf-8")

        # Parse frontmatter
        parts = content.split("---")
        if len(parts) >= 3:
            frontmatter = parts[1].strip()
            try:
                config = yaml.safe_load(frontmatter)
                self.interval = config.get("interval", 300)
                self.evolution_enabled = config.get("evolution_enabled", True)
                self.evolution_level = config.get("evolution_level", 1)
            except yaml.YAMLError:
                pass

        # Parse tasks from markdown
        task_pattern = r"- \[([ x])\] (.+?) :: (.+?) :: (.+)"
        matches = re.findall(task_pattern, content)

        for match in matches:
            enabled = match[0] != " "
            name = match[1]
            action = match[2]
            schedule = match[3]

            task = HeartbeatTask(
                name=name,
                action=action,
                schedule=schedule,
                enabled=enabled,
            )

            self._calculate_next_run(task)
            self.tasks.append(task)

    def _create_default(self) -> None:
        """Create default HEARTBEAT.md."""
        content = """---
interval: 300
evolution_enabled: true
evolution_level: 1
---

# HEARTBEAT 主动任务列表

Agent会定期执行以下任务：

## 定期任务

- [ ] 每日总结 :: generate_daily_summary :: daily
- [ ] 记忆整理 :: organize_memory :: weekly
- [ ] Skill检查 :: check_skill_updates :: weekly

## 进化检查

- [ ] 功能缺口识别 :: identify_evolution_gaps :: hourly
- [ ] 记忆进化分析 :: analyze_memory_evolution :: daily

---
最后更新: {datetime.now().strftime("%Y-%m-%d")}
"""

        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.config_path.write_text(content, encoding="utf-8")

    def _calculate_next_run(self, task: HeartbeatTask) -> None:
        """Calculate next run time based on schedule."""
        now = datetime.now()

        schedule = task.schedule.lower()

        if schedule == "daily":
            task.next_run = now + timedelta(days=1)

        elif schedule == "weekly":
            task.next_run = now + timedelta(weeks=1)

        elif schedule == "hourly":
            task.next_run = now + timedelta(hours=1)

        elif schedule.startswith("every_"):
            # Parse "every_N_minutes" format
            minutes = int(re.search(r"\d+", schedule).group() or "5")
            task.next_run = now + timedelta(minutes=minutes)

        else:
            # Default to interval
            task.next_run = now + timedelta(seconds=self.interval)


class HeartbeatScheduler:
    """Scheduler for proactive tasks."""

    def __init__(
        self,
        memory_manager: MemoryManager,
        skill_manager: SkillManager,
        autonomous_evolver: Optional[AutonomousEvolver] = None,
    ) -> None:
        self.settings = get_settings()
        self.memory_manager = memory_manager
        self.skill_manager = skill_manager
        self.autonomous_evolver = autonomous_evolver

        self.config: Optional[HeartbeatConfig] = None
        self._running = False
        self._task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        """Start the heartbeat scheduler."""
        tasks_path = self.settings.heartbeat.tasks_file

        self.config = HeartbeatConfig(tasks_path)
        self.config.load()

        self._running = True
        self._task = asyncio.create_task(self._run_loop())

        logger.info(
            "heartbeat_started",
            interval=self.config.interval,
            tasks=len(self.config.tasks),
        )

    async def stop(self) -> None:
        """Stop the heartbeat scheduler."""
        self._running = False

        if self._task:
            self._task.cancel()

            try:
                await self._task
            except asyncio.CancelledError:
                pass

        logger.info("heartbeat_stopped")

    async def _run_loop(self) -> None:
        """Main heartbeat loop."""
        while self._running:
            try:
                # Reload config
                if self.config:
                    self.config.load()

                # Execute tasks
                await self._execute_tasks()

                # Evolution check
                if self.config and self.config.evolution_enabled:
                    await self._evolution_check()

                # Wait for next heartbeat
                interval = self.config.interval if self.config else 300
                await asyncio.sleep(interval)

            except asyncio.CancelledError:
                break

            except Exception as e:
                logger.error("heartbeat_error", error=str(e))
                await asyncio.sleep(60)  # Wait before retry

    async def _execute_tasks(self) -> None:
        """Execute tasks that are due."""
        now = datetime.now()

        for task in self.config.tasks if self.config else []:
            if not task.enabled:
                continue

            if task.next_run and now >= task.next_run:
                await self._execute_task(task)

                # Update next run time
                task.last_run = now
                self.config._calculate_next_run(task)

    async def _execute_task(self, task: HeartbeatTask) -> None:
        """Execute a single task."""
        action = task.action

        logger.info(
            "heartbeat_task_executing",
            task_name=task.name,
            action=action,
        )

        try:
            if action == "generate_daily_summary":
                await self._generate_daily_summary()

            elif action == "organize_memory":
                await self._organize_memory()

            elif action == "check_skill_updates":
                await self._check_skill_updates()

            elif action == "identify_evolution_gaps":
                await self._identify_evolution_gaps()

            elif action == "analyze_memory_evolution":
                await self._analyze_memory_evolution()

            else:
                logger.warning("unknown_task_action", action=action)

        except Exception as e:
            logger.error(
                "heartbeat_task_failed",
                task_name=task.name,
                error=str(e),
            )

    async def _generate_daily_summary(self) -> None:
        """Generate daily activity summary."""
        # Read daily log
        today = datetime.now().strftime("%Y-%m-%d")
        log_path = Path(self.settings.memory.file_store.path) / "memory" / f"{today}.md"

        if log_path.exists():
            content = log_path.read_text(encoding="utf-8")

            # Generate summary
            summary = f"# 今日总结 ({today})\n\n"

            # Count sessions
            sessions = content.count("## Session")
            summary += f"- 共处理 {sessions} 个会话\n"

            # Write summary
            summary_path = log_path.parent / f"summary-{today}.md"
            summary_path.write_text(summary, encoding="utf-8")

            logger.info("daily_summary_generated", date=today)

    async def _organize_memory(self) -> None:
        """Organize and compress memory files."""
        # Archive old memories
        memory_path = Path(self.settings.memory.file_store.path) / "memory"

        if memory_path.exists():
            archive_path = memory_path / "archive"
            archive_path.mkdir(exist_ok=True)

            # Archive files older than 30 days
            now = datetime.now()
            threshold = now - timedelta(days=30)

            for file in memory_path.glob("*.md"):
                if file.name.startswith("summary") or file.name.startswith("archive"):
                    continue

                # Check file date from name
                date_match = re.match(r"(\d{4}-\d{2}-\d{2})", file.name)

                if date_match:
                    file_date = datetime.strptime(date_match.group(1), "%Y-%m-%d")

                    if file_date < threshold:
                        # Move to archive
                        file.rename(archive_path / file.name)
                        logger.info("memory_archived", file=file.name)

    async def _check_skill_updates(self) -> None:
        """Check for skill updates."""
        skills = await self.skill_manager.discover_skills()

        logger.info(
            "skill_check_complete",
            skills_count=len(skills),
        )

        # In production, would check remote registry for updates

    async def _identify_evolution_gaps(self) -> None:
        """Identify evolution gaps."""
        if self.autonomous_evolver:
            # Check for gaps (default user for autonomous evolution)
            gaps = await self.autonomous_evolver.identify_gaps("system")

            if gaps:
                logger.info(
                    "evolution_gaps_found",
                    gaps_count=len(gaps),
                )

                metrics.increment(MetricNames.EVOLUTION_EVENT_COUNT)

    async def _analyze_memory_evolution(self) -> None:
        """Analyze and apply memory evolution."""
        # This would analyze recent conversations and extract learnings
        logger.info("memory_evolution_analyzed")

    async def add_task(
        self,
        name: str,
        action: str,
        schedule: str,
    ) -> None:
        """Add a new heartbeat task."""
        task = HeartbeatTask(
            name=name,
            action=action,
            schedule=schedule,
        )

        if self.config:
            self.config._calculate_next_run(task)
            self.config.tasks.append(task)

            # Update HEARTBEAT.md
            self._update_heartbeat_md()

        logger.info("heartbeat_task_added", name=name)

    async def remove_task(self, task_name: str) -> bool:
        """Remove a heartbeat task."""
        if not self.config:
            return False

        for i, task in enumerate(self.config.tasks):
            if task.name == task_name:
                self.config.tasks.pop(i)
                self._update_heartbeat_md()

                logger.info("heartbeat_task_removed", name=task_name)

                return True

        return False

    def _update_heartbeat_md(self) -> None:
        """Update HEARTBEAT.md file with current tasks."""
        if not self.config:
            return

        content = f"""---
interval: {self.config.interval}
evolution_enabled: {self.config.evolution_enabled}
evolution_level: {self.config.evolution_level}
---

# HEARTBEAT 主动任务列表

Agent会定期执行以下任务：

## 定期任务

{chr(10).join([f"- [{'x' if t.enabled else ' '}] {t.name} :: {t.action} :: {t.schedule}" for t in self.config.tasks])}

---
最后更新: {datetime.now().strftime("%Y-%m-%d")}
"""

        self.config.config_path.write_text(content, encoding="utf-8")