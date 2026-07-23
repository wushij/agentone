"""app/monitor/otel.py — OpenTelemetry / Prometheus 指标与 Trace 导出预留层"""

from typing import Any


class OtelExporter:
    """OpenTelemetry 链路导出器（预留扩展，接入 Jaeger / Prometheus / Grafana）。"""

    def __init__(self, service_name: str = "agent-one"):
        self.service_name = service_name
        self._enabled = False

    def setup_telemetry(self, endpoint: str | None = None) -> None:
        """初始化 OpenTelemetry SDK 与 Exporter。"""
        if endpoint:
            self._enabled = True

    def record_span(self, name: str, attributes: dict[str, Any] | None = None) -> None:
        """记录标准 OpenTelemetry Trace Span。"""
        pass

    def export_metrics() -> dict[str, Any]:
        """导出 Prometheus 格式指标数据。"""
        return {"status": "ok", "telemetry_enabled": False}


otel_exporter = OtelExporter()
