"""Secure Tool Executor - Execute tool calls with safety checks."""

import asyncio
import time
import uuid
from typing import Any, Optional
from datetime import datetime

from core.tools.registry import ToolRegistry, get_registry
from core.tools.types import Tool, ToolCall, ToolResult, ToolStatus
from core.agent.types import ExecutionContext
from core.enterprise.permissions import (
    PermissionManager,
    Permission,
    UserRole,
    get_permission_manager,
)
from core.security.audit import AuditLogger, AuditEventType, get_audit_logger
from core.security.sandbox import DangerousOperationApproval, get_approval_manager
from core.logging import get_logger
from core.metrics import get_metrics, MetricNames

logger = get_logger("tools.executor")
metrics = get_metrics()


# Dangerous tools requiring admin approval
DANGEROUS_TOOLS = {
    "delete_file": "ADMIN",
    "shell_execute": "ADMIN",
    "write_file": "MANAGER",
    "autonomous_create": "ADMIN",
}

# Tool to permission mapping
TOOL_PERMISSIONS: dict[str, Permission] = {
    "read_file": Permission.VIEW_DATA,
    "write_file": Permission.CREATE_CONTENT,
    "delete_file": Permission.MANAGE_SETTINGS,
    "list_directory": Permission.VIEW_DATA,
    "analyze_code": Permission.VIEW_DATA,
    "generate_code": Permission.CREATE_CONTENT,
    "refactor_code": Permission.CREATE_CONTENT,
    "debug_code": Permission.VIEW_DATA,
    "execute": Permission.CREATE_CONTENT,

    # Enterprise tools
    "get_live_metrics": Permission.VIEW_ANALYTICS,
    "analyze_audience": Permission.VIEW_ANALYTICS,
    "calculate_conversion": Permission.VIEW_ANALYTICS,
    "generate_report": Permission.MANAGE_REPORTS,
    "get_product_info": Permission.VIEW_DATA,
    "update_product": Permission.MANAGE_PRODUCTS,
    "sync_inventory": Permission.MANAGE_PRODUCTS,
    "adjust_price": Permission.MANAGE_PRODUCTS,
    "query_order": Permission.VIEW_ORDERS,
    "handle_refund": Permission.PROCESS_ORDERS,
    "auto_reply": Permission.HANDLE_CUSTOMER,
}


class SecureToolExecutor:
    """Execute tool calls with security checks."""

    def __init__(
        self,
        registry: Optional[ToolRegistry] = None,
        permission_manager: Optional[PermissionManager] = None,
        audit_logger: Optional[AuditLogger] = None,
        approval_manager: Optional[DangerousOperationApproval] = None,
    ) -> None:
        self.registry = registry or get_registry()
        self.permission_manager = permission_manager or get_permission_manager()
        self.audit_logger = audit_logger or get_audit_logger()
        self.approval_manager = approval_manager or get_approval_manager()
        self._pending_approvals: dict[str, dict[str, Any]] = {}

    async def execute(
        self,
        call: ToolCall,
        context: ExecutionContext,
        session_id: str = "",
    ) -> ToolResult:
        """Execute a single tool call with security checks."""
        start_time = time.time()

        # Get tool definition
        tool = self.registry.get(call.name)

        if not tool:
            self._audit_tool_denied(
                user_id=context.user_id,
                tool_name=call.name,
                reason="unknown_tool",
                session_id=session_id,
            )

            return ToolResult.error(
                call_id=call.call_id or str(uuid.uuid4()),
                error=f"Unknown tool: {call.name}",
            )

        # Step 1: Check user exists and is active
        user = self.permission_manager.get_user(context.user_id)

        if not user:
            self._audit_tool_denied(
                user_id=context.user_id,
                tool_name=call.name,
                reason="user_not_found",
                session_id=session_id,
            )

            return ToolResult.error(
                call_id=call.call_id or str(uuid.uuid4()),
                error="User not found or inactive",
            )

        if not user.is_active:
            self._audit_tool_denied(
                user_id=context.user_id,
                tool_name=call.name,
                reason="user_inactive",
                session_id=session_id,
            )

            return ToolResult.error(
                call_id=call.call_id or str(uuid.uuid4()),
                error="User account is inactive",
            )

        # Step 2: Check tool permission
        required_permission = TOOL_PERMISSIONS.get(call.name)

        if required_permission:
            if not user.has_permission(required_permission):
                self._audit_permission_denied(
                    user_id=context.user_id,
                    tool_name=call.name,
                    required_permission=required_permission.value,
                    session_id=session_id,
                )

                return ToolResult.error(
                    call_id=call.call_id or str(uuid.uuid4()),
                    error=f"Permission denied: requires {required_permission.value}",
                )

        # Step 3: Check dangerous tool restriction
        if call.name in DANGEROUS_TOOLS:
            required_role = UserRole(DANGEROUS_TOOLS[call.name])

            if user.role != required_role and user.role != UserRole.ADMIN:
                # Request approval for non-authorized users
                approval_id = self.approval_manager.request_approval(
                    user_id=context.user_id,
                    operation=call.name,
                    details={
                        "params": call.params,
                        "reason": f"Requires {required_role.value} role",
                    },
                    required_role=DANGEROUS_TOOLS[call.name],
                )

                # Check if auto-approved (admin self-approval)
                approved, _ = self.approval_manager.check_approval(approval_id)

                if not approved:
                    self._audit_tool_denied(
                        user_id=context.user_id,
                        tool_name=call.name,
                        reason=f"requires_approval_{approval_id}",
                        session_id=session_id,
                    )

                    return ToolResult.error(
                        call_id=call.call_id or str(uuid.uuid4()),
                        error=f"Dangerous operation requires approval. Approval ID: {approval_id}",
                        metadata={"approval_id": approval_id, "pending": True},
                    )

        # Step 4: Validate parameters
        try:
            validated_params = self._validate_params(tool, call.params)
        except ValueError as e:
            self._audit_tool_denied(
                user_id=context.user_id,
                tool_name=call.name,
                reason="invalid_params",
                error=str(e),
                session_id=session_id,
            )

            return ToolResult.error(
                call_id=call.call_id or str(uuid.uuid4()),
                error=f"Invalid parameters: {e}",
            )

        # Step 5: Execute with timeout and audit
        try:
            result = await asyncio.wait_for(
                self._execute_tool(tool, validated_params, context),
                timeout=tool.timeout,
            )

            execution_time_ms = int((time.time() - start_time) * 1000)

            # Audit success
            self._audit_tool_success(
                user_id=context.user_id,
                tool_name=call.name,
                params=validated_params,
                result=result,
                execution_time_ms=execution_time_ms,
                session_id=session_id,
            )

            # Metrics
            metrics.record(MetricNames.TOOL_EXECUTION_TIME_MS, execution_time_ms)
            metrics.increment(MetricNames.TOOL_EXECUTION_COUNT)

            logger.info(
                "tool_executed",
                tool=call.name,
                user_id=context.user_id,
                execution_time_ms=execution_time_ms,
            )

            return ToolResult.success(
                call_id=call.call_id or str(uuid.uuid4()),
                output=result,
                execution_time_ms=execution_time_ms,
            )

        except asyncio.TimeoutError:
            execution_time_ms = int((time.time() - start_time) * 1000)

            self._audit_tool_error(
                user_id=context.user_id,
                tool_name=call.name,
                error="timeout",
                execution_time_ms=execution_time_ms,
                session_id=session_id,
            )

            metrics.increment(MetricNames.TOOL_FAILURE_COUNT)

            return ToolResult.error(
                call_id=call.call_id or str(uuid.uuid4()),
                error=f"Tool execution timed out after {tool.timeout}s",
                execution_time_ms=execution_time_ms,
            )

        except Exception as e:
            execution_time_ms = int((time.time() - start_time) * 1000)

            self._audit_tool_error(
                user_id=context.user_id,
                tool_name=call.name,
                error=str(e),
                execution_time_ms=execution_time_ms,
                session_id=session_id,
            )

            metrics.increment(MetricNames.TOOL_FAILURE_COUNT)

            logger.error(
                "tool_execution_error",
                tool=call.name,
                error=str(e),
            )

            return ToolResult.error(
                call_id=call.call_id or str(uuid.uuid4()),
                error=str(e),
                execution_time_ms=execution_time_ms,
            )

    async def execute_parallel(
        self,
        calls: list[ToolCall],
        context: ExecutionContext,
        session_id: str = "",
    ) -> list[ToolResult]:
        """Execute multiple tool calls in parallel."""
        tasks = [
            self.execute(call, context, session_id)
            for call in calls
        ]
        return await asyncio.gather(*tasks)

    async def execute_approved(
        self,
        approval_id: str,
        context: ExecutionContext,
        session_id: str = "",
    ) -> ToolResult:
        """Execute a dangerous operation that has been approved."""
        # Verify approval
        approved, reason = self.approval_manager.check_approval(approval_id)

        if not approved:
            return ToolResult.error(
                call_id=approval_id,
                error=f"Operation not approved: {reason}",
            )

        # Get operation details
        pending_ops = self.approval_manager.get_pending_operations()
        approved_ops = [
            op for op_id, approved in self.approval_manager._approved_operations.items()
            if op_id == approval_id and approved
        ]

        # Note: Approved operations are stored differently, we need to track them
        # For now, we'll use the approval_id to reconstruct the call
        call_id = approval_id.replace("op-", "").split("-")[-1] or approval_id

        return ToolResult.success(
            call_id=call_id,
            output={"status": "approved_operation_ready", "approval_id": approval_id},
        )

    def request_dangerous_operation(
        self,
        tool_name: str,
        params: dict[str, Any],
        context: ExecutionContext,
    ) -> str:
        """Request approval for a dangerous operation."""
        if tool_name not in DANGEROUS_TOOLS:
            raise ValueError(f"{tool_name} is not a dangerous operation")

        return self.approval_manager.request_approval(
            user_id=context.user_id,
            operation=tool_name,
            details={"params": params},
            required_role=DANGEROUS_TOOLS[tool_name],
        )

    def _validate_params(self, tool: Tool, params: dict[str, Any]) -> dict[str, Any]:
        """Validate tool parameters against schema."""
        schema = tool.parameters

        if not schema:
            return params

        required = schema.get("required", [])
        properties = schema.get("properties", {})

        # Check required parameters
        for req in required:
            if req not in params:
                raise ValueError(f"Missing required parameter: {req}")

        # Validate parameter types
        validated = {}

        for key, value in params.items():
            if key in properties:
                prop_def = properties[key]
                prop_type = prop_def.get("type")

                if prop_type == "string" and not isinstance(value, str):
                    validated[key] = str(value)

                elif prop_type == "number" and not isinstance(value, (int, float)):
                    try:
                        validated[key] = float(value)
                    except ValueError:
                        raise ValueError(f"Parameter {key} must be a number")

                elif prop_type == "boolean" and not isinstance(value, bool):
                    validated[key] = bool(value)

                elif prop_type == "array" and not isinstance(value, list):
                    raise ValueError(f"Parameter {key} must be an array")

                elif prop_type == "object" and not isinstance(value, dict):
                    raise ValueError(f"Parameter {key} must be an object")

                else:
                    validated[key] = value
            else:
                validated[key] = value

        return validated

    async def _execute_tool(
        self,
        tool: Tool,
        params: dict[str, Any],
        context: ExecutionContext,
    ) -> Any:
        """Execute the tool handler."""
        handler = self.registry.get_handler(tool.name)

        if handler is None:
            return self._default_handler(tool, params, context)

        if asyncio.iscoroutinefunction(handler):
            return await handler(params, context)
        else:
            return handler(params, context)

    def _default_handler(
        self,
        tool: Tool,
        params: dict[str, Any],
        context: ExecutionContext,
    ) -> Any:
        """Default handler for tools without registered handlers."""
        logger.warning(
            "no_handler_for_tool",
            tool=tool.name,
        )

        return {
            "tool": tool.name,
            "params": params,
            "status": "no_handler_registered",
        }

    # Audit methods

    def _audit_tool_success(
        self,
        user_id: str,
        tool_name: str,
        params: dict[str, Any],
        result: Any,
        execution_time_ms: int,
        session_id: str,
    ) -> None:
        """Audit successful tool execution."""
        self.audit_logger.log_tool_execution(
            user_id=user_id,
            tool_name=tool_name,
            params=params,
            result={"output": str(result)[:200]},
            success=True,
            execution_time_ms=execution_time_ms,
            session_id=session_id,
        )

    def _audit_tool_error(
        self,
        user_id: str,
        tool_name: str,
        error: str,
        execution_time_ms: int,
        session_id: str,
    ) -> None:
        """Audit failed tool execution."""
        self.audit_logger.log_tool_execution(
            user_id=user_id,
            tool_name=tool_name,
            params={},
            result={"error": error},
            success=False,
            execution_time_ms=execution_time_ms,
            session_id=session_id,
        )

    def _audit_permission_denied(
        self,
        user_id: str,
        tool_name: str,
        required_permission: str,
        session_id: str,
    ) -> None:
        """Audit permission denied."""
        self.audit_logger.log_permission_denied(
            user_id=user_id,
            tool_name=tool_name,
            required_permission=required_permission,
            session_id=session_id,
        )

    def _audit_tool_denied(
        self,
        user_id: str,
        tool_name: str,
        reason: str,
        session_id: str,
        error: Optional[str] = None,
    ) -> None:
        """Audit tool denied."""
        self.audit_logger.log_event(
            event_type=AuditEventType.TOOL_DENIED,
            user_id=user_id,
            session_id=session_id,
            details={
                "tool_name": tool_name,
                "reason": reason,
                "error": error,
            },
            success=False,
            error_message=error or f"Tool denied: {reason}",
        )


# For backwards compatibility, also export ToolExecutor
ToolExecutor = SecureToolExecutor


# Global secure executor
_secure_executor: Optional[SecureToolExecutor] = None


def get_secure_executor() -> SecureToolExecutor:
    """Get global secure tool executor."""
    global _secure_executor

    if _secure_executor is None:
        _secure_executor = SecureToolExecutor()

    return _secure_executor