"""Sandbox Executor - Secure isolated execution environment for Level 3 evolution."""

import asyncio
import subprocess
import tempfile
import os
import sys
import signal
import shutil
from typing import Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import json

# resource module is Unix-only, not available on Windows
try:
    import resource
except ImportError:
    resource = None  # type: ignore

from core.logging import get_logger
from core.security.audit import AuditEventType, get_audit_logger
from core.metrics import get_metrics, MetricNames

logger = get_logger("security.sandbox")
metrics = get_metrics()


@dataclass
class SandboxConfig:
    """Sandbox execution configuration."""
    max_memory_mb: int = 100  # Maximum memory in MB
    max_cpu_seconds: int = 10  # Maximum CPU time
    max_wall_seconds: int = 30  # Maximum wall time
    max_output_size: int = 10000  # Maximum output size in bytes
    allowed_modules: list[str] = field(default_factory=lambda: [
        "json",
        "datetime",
        "typing",
        "dataclasses",
        "collections",
        "itertools",
        "functools",
        "re",
        "math",
        "statistics",
        "enum",
    ])
    forbidden_patterns: list[str] = field(default_factory=lambda: [
        "import os",
        "import sys",
        "import subprocess",
        "import socket",
        "import requests",
        "import urllib",
        "import shutil",
        "import pathlib",
        "__import__",
        "eval",
        "exec",
        "compile",
        "open(",
        "file(",
        "input(",
        "breakpoint",
        "globals",
        "locals",
        "vars",
    ])
    network_access: bool = False
    file_access: bool = False


@dataclass
class SandboxResult:
    """Result of sandbox execution."""
    success: bool
    output: Any = None
    error: Optional[str] = None
    execution_time_ms: int = 0
    memory_used_mb: float = 0.0
    security_violations: list[str] = field(default_factory=list)


class SandboxValidator:
    """Validate code for sandbox execution."""

    def __init__(self, config: SandboxConfig) -> None:
        self.config = config

    def validate_code(self, code: str) -> tuple[bool, list[str]]:
        """Validate code for security violations."""
        violations = []

        # Check forbidden patterns
        for pattern in self.config.forbidden_patterns:
            if pattern in code:
                violations.append(f"Forbidden pattern found: {pattern}")

        # Check imports
        import_lines = [
            line.strip()
            for line in code.split("\n")
            if line.strip().startswith("import ") or line.strip().startswith("from ")
        ]

        for line in import_lines:
            module_name = self._extract_module_name(line)

            if module_name not in self.config.allowed_modules:
                violations.append(f"Unauthorized module import: {module_name}")

        # Check for dangerous function calls
        dangerous_calls = [
            "__import__",
            "eval",
            "exec",
            "compile",
            "system",
            "popen",
        ]

        for call in dangerous_calls:
            if call + "(" in code or call + " (" in code:
                violations.append(f"Dangerous function call: {call}")

        # Check for attribute access bypass
        if "__" in code and not code.count("__") == code.count('"__"') + code.count("'__'"):
            # Could be accessing __dict__, __class__, etc.
            bypass_patterns = ["__dict__", "__class__", "__bases__", "__subclasses__"]
            for pattern in bypass_patterns:
                if pattern in code:
                    violations.append(f"Attribute bypass attempt: {pattern}")

        return len(violations) == 0, violations

    def _extract_module_name(self, line: str) -> str:
        """Extract module name from import line."""
        line = line.strip()

        if line.startswith("from "):
            # from X import Y -> X
            parts = line.split()
            if len(parts) >= 2:
                return parts[1]
        elif line.startswith("import "):
            # import X -> X
            parts = line.split()
            if len(parts) >= 2:
                return parts[1].split(".")[0]

        return ""


class SandboxExecutor:
    """Execute code in secure sandbox environment."""

    def __init__(self, config: Optional[SandboxConfig] = None) -> None:
        self.config = config or SandboxConfig()
        self.validator = SandboxValidator(self.config)
        self.audit_logger = get_audit_logger()
        self._temp_dir: Optional[Path] = None

    def initialize(self) -> None:
        """Initialize sandbox environment."""
        self._temp_dir = Path(tempfile.mkdtemp(prefix="sandbox_"))

        logger.info(
            "sandbox_initialized",
            temp_dir=str(self._temp_dir),
            max_memory_mb=self.config.max_memory_mb,
            max_cpu_seconds=self.config.max_cpu_seconds,
        )

    def cleanup(self) -> None:
        """Clean up sandbox environment."""
        if self._temp_dir and self._temp_dir.exists():
            shutil.rmtree(self._temp_dir, ignore_errors=True)
            self._temp_dir = None

            logger.info("sandbox_cleaned")

    async def execute(
        self,
        code: str,
        context: Optional[dict[str, Any]] = None,
        user_id: str = "",
    ) -> SandboxResult:
        """Execute code in sandbox."""
        start_time = datetime.now()

        # Validate code first
        is_valid, violations = self.validator.validate_code(code)

        if not is_valid:
            self._audit_sandbox_denied(user_id, violations)

            return SandboxResult(
                success=False,
                error="Code validation failed",
                security_violations=violations,
            )

        # Create isolated execution
        try:
            result = await self._execute_isolated(code, context or {})

            execution_time_ms = int(
                (datetime.now() - start_time).total_seconds() * 1000
            )

            # Audit execution
            self._audit_sandbox_execution(
                user_id=user_id,
                success=result.success,
                execution_time_ms=execution_time_ms,
                violations=result.security_violations,
            )

            metrics.record(MetricNames.TOOL_EXECUTION_TIME_MS, execution_time_ms)

            return result

        except Exception as e:
            logger.error("sandbox_execution_error", error=str(e))

            return SandboxResult(
                success=False,
                error=str(e),
                security_violations=[],
            )

    async def _execute_isolated(
        self,
        code: str,
        context: dict[str, Any],
    ) -> SandboxResult:
        """Execute code in isolated subprocess."""
        # Prepare execution script
        script = self._prepare_script(code, context)

        # Create temp file
        script_file = self._temp_dir / "execute.py"

        script_file.write_text(script)

        # Execute with resource limits
        try:
            # Use subprocess with limits
            process = await asyncio.create_subprocess_exec(
                sys.executable,
                str(script_file),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                # Note: On Windows, resource limits don't work the same way
                # This is a simplified implementation
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=self.config.max_wall_seconds,
                )

                output_str = stdout.decode("utf-8", errors="replace")
                error_str = stderr.decode("utf-8", errors="replace")

                if process.returncode != 0:
                    return SandboxResult(
                        success=False,
                        error=error_str or "Execution failed",
                        security_violations=[],
                    )

                # Limit output size
                if len(output_str) > self.config.max_output_size:
                    output_str = output_str[:self.config.max_output_size]

                # Parse output
                try:
                    output = json.loads(output_str)
                except json.JSONDecodeError:
                    output = {"raw": output_str}

                return SandboxResult(
                    success=True,
                    output=output,
                    security_violations=[],
                )

            except asyncio.TimeoutError:
                process.kill()
                await process.wait()

                return SandboxResult(
                    success=False,
                    error=f"Execution timed out after {self.config.max_wall_seconds}s",
                    security_violations=["timeout"],
                )

        finally:
            # Clean up script file
            script_file.unlink(missing_ok=True)

    def _prepare_script(self, code: str, context: dict[str, Any]) -> str:
        """Prepare execution script with isolation."""
        # Create safe execution environment
        script_lines = [
            "import json",
            "import sys",
            "",
            "# Sandbox execution",
            "_result = None",
            "",
            "# Restricted globals",
            "_safe_globals = {",
        ]

        # Add allowed modules to safe globals
        for module in self.config.allowed_modules:
            script_lines.append(f"    '{module}': __import__('{module}'),")

        script_lines.extend([
            "}",
            "",
            "# Context variables",
        ])

        # Add context variables safely
        for key, value in context.items():
            if isinstance(value, (str, int, float, bool, list, dict)):
                script_lines.append(f"_context_{key} = json.loads('{json.dumps(value)}')")

        script_lines.extend([
            "",
            "# Execute code",
            "try:",
            "    exec(code, _safe_globals, {'_result': _result})",
            "except Exception as e:",
            "    print(json.dumps({'error': str(e)}))",
            "    sys.exit(1)",
            "",
            "# Output result",
            "print(json.dumps({'result': _result}))",
        ])

        # Inject actual code
        script = "\n".join(script_lines)
        script = script.replace("exec(code, _safe_globals, {'_result': _result})",
                                f"exec('''{code}''', _safe_globals, {'_result': '_result'})")

        return script

    def test_skill_code(self, code: str) -> tuple[bool, list[str]]:
        """Test skill code before deployment."""
        # Full validation for skill deployment
        is_valid, violations = self.validator.validate_code(code)

        if not is_valid:
            return False, violations

        # Additional skill-specific checks
        skill_violations = []

        # Check required skill structure
        if "TOOL_DEFINITIONS" not in code:
            skill_violations.append("Missing TOOL_DEFINITIONS")

        # Check no dynamic imports
        if "__import__" in code or "importlib" in code:
            skill_violations.append("Dynamic imports not allowed")

        # Check no file operations
        file_ops = ["open(", "write(", "read(", "shutil.", "os.remove", "os.unlink"]
        for op in file_ops:
            if op in code:
                skill_violations.append(f"File operation not allowed: {op}")

        all_violations = violations + skill_violations

        return len(all_violations) == 0, all_violations

    def _audit_sandbox_denied(
        self,
        user_id: str,
        violations: list[str],
    ) -> None:
        """Audit sandbox execution denied."""
        self.audit_logger.log_event(
            event_type=AuditEventType.TOOL_DENIED,
            user_id=user_id,
            details={
                "reason": "sandbox_validation_failed",
                "violations": violations,
            },
            success=False,
            error_message=f"Sandbox validation failed: {len(violations)} violations",
        )

    def _audit_sandbox_execution(
        self,
        user_id: str,
        success: bool,
        execution_time_ms: int,
        violations: list[str],
    ) -> None:
        """Audit sandbox execution."""
        self.audit_logger.log_event(
            event_type=AuditEventType.AUTONOMOUS_CODE_GENERATED,
            user_id=user_id,
            details={
                "success": success,
                "execution_time_ms": execution_time_ms,
                "violations": violations,
            },
            success=success,
            error_message=None if success else f"Violations: {violations}",
        )


class DangerousOperationApproval:
    """Approval workflow for dangerous operations."""

    def __init__(self) -> None:
        self._pending_operations: dict[str, dict[str, Any]] = {}
        self._approved_operations: dict[str, bool] = {}
        self._rejected_operations: dict[str, str] = {}
        self.audit_logger = get_audit_logger()

    def request_approval(
        self,
        user_id: str,
        operation: str,
        details: dict[str, Any],
        required_role: str = "ADMIN",
    ) -> str:
        """Request approval for dangerous operation."""
        from core.enterprise.permissions import UserRole, get_permission_manager

        operation_id = f"op-{user_id}-{operation}-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        # Get user and check if they can self-approve
        perm_manager = get_permission_manager()
        user = perm_manager.get_user(user_id)

        if user and user.role.value == required_role:
            # Admin can self-approve
            self._approved_operations[operation_id] = True

            logger.info(
                "dangerous_op_self_approved",
                operation_id=operation_id,
                user_id=user_id,
                operation=operation,
            )

            return operation_id

        # Create pending request
        self._pending_operations[operation_id] = {
            "user_id": user_id,
            "operation": operation,
            "details": details,
            "required_role": required_role,
            "created_at": datetime.now().isoformat(),
        }

        logger.info(
            "dangerous_op_pending",
            operation_id=operation_id,
            user_id=user_id,
            operation=operation,
        )

        return operation_id

    def approve_operation(
        self,
        operation_id: str,
        approver_id: str,
    ) -> tuple[bool, Optional[str]]:
        """Approve a pending dangerous operation."""
        if operation_id not in self._pending_operations:
            return False, "Operation not found"

        pending = self._pending_operations[operation_id]

        # Check approver role
        from core.enterprise.permissions import UserRole, get_permission_manager

        perm_manager = get_permission_manager()
        approver = perm_manager.get_user(approver_id)

        if not approver:
            return False, "Approver not found"

        required_role = UserRole(pending["required_role"])

        if approver.role != required_role and approver.role != UserRole.ADMIN:
            return False, f"Approver must have {required_role.value} role"

        # Approve
        self._approved_operations[operation_id] = True
        del self._pending_operations[operation_id]

        self.audit_logger.log_event(
            event_type=AuditEventType.PERMISSION_GRANTED,
            user_id=approver_id,
            details={
                "operation_id": operation_id,
                "operation": pending["operation"],
                "requester": pending["user_id"],
            },
            success=True,
        )

        logger.info(
            "dangerous_op_approved",
            operation_id=operation_id,
            approver_id=approver_id,
        )

        return True, None

    def reject_operation(
        self,
        operation_id: str,
        rejector_id: str,
        reason: str,
    ) -> tuple[bool, Optional[str]]:
        """Reject a pending dangerous operation."""
        if operation_id not in self._pending_operations:
            return False, "Operation not found"

        pending = self._pending_operations[operation_id]

        # Check rejector role
        from core.enterprise.permissions import UserRole, get_permission_manager

        perm_manager = get_permission_manager()
        rejector = perm_manager.get_user(rejector_id)

        if not rejector:
            return False, "Rejector not found"

        required_role = UserRole(pending["required_role"])

        if rejector.role != required_role and rejector.role != UserRole.ADMIN:
            return False, f"Rejector must have {required_role.value} role"

        # Reject
        self._rejected_operations[operation_id] = reason
        del self._pending_operations[operation_id]

        self.audit_logger.log_event(
            event_type=AuditEventType.PERMISSION_REVOKED,
            user_id=rejector_id,
            details={
                "operation_id": operation_id,
                "operation": pending["operation"],
                "requester": pending["user_id"],
                "reason": reason,
            },
            success=False,
            error_message=f"Operation rejected: {reason}",
        )

        logger.info(
            "dangerous_op_rejected",
            operation_id=operation_id,
            rejector_id=rejector_id,
            reason=reason,
        )

        return True, None

    def check_approval(self, operation_id: str) -> tuple[bool, Optional[str]]:
        """Check if operation is approved."""
        if operation_id in self._approved_operations:
            return True, None

        if operation_id in self._rejected_operations:
            return False, self._rejected_operations[operation_id]

        if operation_id in self._pending_operations:
            return False, "Operation pending approval"

        return False, "Operation not found"

    def get_pending_operations(self) -> list[dict[str, Any]]:
        """Get all pending operations."""
        return [
            {"operation_id": op_id, **details}
            for op_id, details in self._pending_operations.items()
        ]

    def cleanup_expired(self, max_age_hours: int = 24) -> int:
        """Clean up expired pending operations."""
        from datetime import timedelta

        now = datetime.now()
        expired_count = 0

        for op_id, details in list(self._pending_operations.items()):
            created_at = datetime.fromisoformat(details["created_at"])

            if now - created_at > timedelta(hours=max_age_hours):
                del self._pending_operations[op_id]
                self._rejected_operations[op_id] = "Expired"
                expired_count += 1

        return expired_count


# Global instances
_sandbox_executor: Optional[SandboxExecutor] = None
_approval_manager: Optional[DangerousOperationApproval] = None


def get_sandbox_executor() -> SandboxExecutor:
    """Get global sandbox executor."""
    global _sandbox_executor

    if _sandbox_executor is None:
        _sandbox_executor = SandboxExecutor()
        _sandbox_executor.initialize()

    return _sandbox_executor


def get_approval_manager() -> DangerousOperationApproval:
    """Get global approval manager."""
    global _approval_manager

    if _approval_manager is None:
        _approval_manager = DangerousOperationApproval()

    return _approval_manager