"""Metrics collection module."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable
from collections import defaultdict
import time


@dataclass
class MetricPoint:
    """Single metric data point."""
    name: str
    value: float
    timestamp: datetime = field(default_factory=datetime.now)
    tags: dict[str, str] = field(default_factory=dict)


@dataclass
class MetricSummary:
    """Summary statistics for a metric."""
    name: str
    count: int = 0
    total: float = 0.0
    min: float = float("inf")
    max: float = float("-inf")
    avg: float = 0.0

    def add(self, value: float) -> None:
        """Add a new value to the summary."""
        self.count += 1
        self.total += value
        self.min = min(self.min, value)
        self.max = max(self.max, value)
        self.avg = self.total / self.count


class MetricsCollector:
    """Collect and aggregate metrics."""

    def __init__(self) -> None:
        self._metrics: dict[str, list[MetricPoint]] = defaultdict(list)
        self._summaries: dict[str, MetricSummary] = {}
        self._counters: dict[str, int] = defaultdict(int)
        self._histograms: dict[str, list[float]] = defaultdict(list)

    def record(
        self,
        name: str,
        value: float,
        tags: Optional[dict[str, str]] = None,
    ) -> None:
        """Record a metric value."""
        point = MetricPoint(
            name=name,
            value=value,
            tags=tags or {},
        )
        self._metrics[name].append(point)

        # Update summary
        if name not in self._summaries:
            self._summaries[name] = MetricSummary(name=name)
        self._summaries[name].add(value)

    def increment(self, name: str, value: int = 1) -> None:
        """Increment a counter."""
        self._counters[name] += value

    def histogram(self, name: str, value: float) -> None:
        """Add to histogram."""
        self._histograms[name].append(value)

    def timing(self, name: str) -> Callable[[], None]:
        """Context manager for timing."""
        start = time.time()

        def end() -> None:
            elapsed = (time.time() - start) * 1000  # Convert to ms
            self.record(name, elapsed)

        return end

    def get_summary(self, name: str) -> Optional[MetricSummary]:
        """Get summary for a metric."""
        return self._summaries.get(name)

    def get_counter(self, name: str) -> int:
        """Get counter value."""
        return self._counters.get(name, 0)

    def get_histogram_percentile(
        self,
        name: str,
        percentile: float = 95.0,
    ) -> Optional[float]:
        """Get percentile from histogram."""
        values = self._histograms.get(name, [])
        if not values:
            return None

        sorted_values = sorted(values)
        index = int(len(sorted_values) * percentile / 100)
        return sorted_values[index]

    def get_all_metrics(self) -> dict[str, Any]:
        """Get all collected metrics."""
        return {
            "summaries": {
                name: {
                    "count": summary.count,
                    "total": summary.total,
                    "min": summary.min,
                    "max": summary.max,
                    "avg": summary.avg,
                }
                for name, summary in self._summaries.items()
            },
            "counters": dict(self._counters),
            "histograms": {
                name: {
                    "count": len(values),
                    "p50": self.get_histogram_percentile(name, 50),
                    "p95": self.get_histogram_percentile(name, 95),
                    "p99": self.get_histogram_percentile(name, 99),
                }
                for name, values in self._histograms.items()
                if values
            },
        }

    def export_prometheus(self) -> str:
        """Export metrics in Prometheus format."""
        import os

        lines = []

        # Add common labels
        pod_name = os.environ.get("POD_NAME", "unknown")
        namespace = os.environ.get("POD_NAMESPACE", "default")

        common_labels = f'pod="{pod_name}",namespace="{namespace}"'

        # Export counters
        for name, value in self._counters.items():
            metric_name = name.replace(".", "_").replace("-", "_")
            lines.append(f"# TYPE {metric_name} counter")
            lines.append(f"{metric_name}{{{common_labels}}} {value}")

        # Export summaries (as gauges for avg/min/max)
        for name, summary in self._summaries.items():
            metric_name = name.replace(".", "_").replace("-", "_")
            lines.append(f"# TYPE {metric_name}_avg gauge")
            lines.append(f"{metric_name}_avg{{{common_labels}}} {summary.avg}")
            lines.append(f"# TYPE {metric_name}_min gauge")
            lines.append(f"{metric_name}_min{{{common_labels}}} {summary.min}")
            lines.append(f"# TYPE {metric_name}_max gauge")
            lines.append(f"{metric_name}_max{{{common_labels}}} {summary.max}")
            lines.append(f"# TYPE {metric_name}_count counter")
            lines.append(f"{metric_name}_count{{{common_labels}}} {summary.count}")

        # Export histograms
        for name, values in self._histograms.items():
            if not values:
                continue

            metric_name = name.replace(".", "_").replace("-", "_")
            lines.append(f"# TYPE {metric_name} histogram")

            sorted_values = sorted(values)
            count = len(sorted_values)
            sum_value = sum(sorted_values)

            # Bucket counts
            buckets = [50, 100, 250, 500, 1000, 2500, 5000, 10000]
            bucket_counts = []

            for bucket in buckets:
                bucket_count = sum(1 for v in sorted_values if v <= bucket)
                bucket_counts.append(bucket_count)
                lines.append(
                    f"{metric_name}_bucket{{le=\"{bucket}\",{common_labels}}} {bucket_count}"
                )

            # +Inf bucket
            lines.append(
                f"{metric_name}_bucket{{le=\"+Inf\",{common_labels}}} {count}"
            )

            lines.append(f"{metric_name}_sum{{{common_labels}}} {sum_value}")
            lines.append(f"{metric_name}_count{{{common_labels}}} {count}")

        return "\n".join(lines) + "\n"

    def clear(self) -> None:
        """Clear all collected metrics."""
        self._metrics.clear()
        self._summaries.clear()
        self._counters.clear()
        self._histograms.clear()


# Global metrics collector
_metrics: Optional[MetricsCollector] = None


def get_metrics() -> MetricsCollector:
    """Get or create global metrics collector."""
    global _metrics

    if _metrics is None:
        _metrics = MetricsCollector()

    return _metrics


# Predefined metric names
class MetricNames:
    """Standard metric name constants."""

    # Model metrics
    MODEL_CALL_COUNT = "model_call_count"
    MODEL_LATENCY_MS = "model_latency_ms"
    MODEL_TOKENS_USED = "model_tokens_used"
    MODEL_FAILURE_COUNT = "model_failure_count"

    # Tool metrics
    TOOL_EXECUTION_COUNT = "tool_execution_count"
    TOOL_EXECUTION_TIME_MS = "tool_execution_time_ms"
    TOOL_FAILURE_COUNT = "tool_failure_count"

    # Memory metrics
    MEMORY_WRITE_COUNT = "memory_write_count"
    MEMORY_READ_COUNT = "memory_read_count"
    MEMORY_RETRIEVE_TIME_MS = "memory_retrieve_time_ms"

    # Skill metrics
    SKILL_USAGE_COUNT = "skill_usage_count"
    SKILL_LOAD_COUNT = "skill_load_count"
    SKILL_CREATION_COUNT = "skill_creation_count"

    # Agent metrics
    AGENT_RESPONSE_TIME_MS = "agent_response_time_ms"
    AGENT_ITERATION_COUNT = "agent_iteration_count"
    AGENT_ERROR_COUNT = "agent_error_count"

    # Evolution metrics
    EVOLUTION_EVENT_COUNT = "evolution_event_count"
    AUTONOMOUS_CREATION_COUNT = "autonomous_creation_count"