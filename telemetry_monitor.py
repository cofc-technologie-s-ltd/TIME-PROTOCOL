import time
from typing import Dict, Any, List

class SystemTelemetryMonitor:
    """
    Real-time Telemetry & Institutional Alerting Engine for TIME Protocol.
    Monitors node cluster health, transaction throughput, and cryptographic security events.
    """
    def __init__(self, node_id: str):
        self.node_id = node_id
        self.metrics_log: List[Dict[str, Any]] = []
        self.security_alerts: List[Dict[str, Any]] = []

    def record_metric(self, metric_name: str, value: float, unit: str) -> Dict[str, Any]:
        """
        Records a system performance metric (e.g., TPS, latency, memory usage).
        """
        metric_entry = {
            "node_id": self.node_id,
            "metric": metric_name,
            "value": value,
            "unit": unit,
            "timestamp": time.time()
        }
        self.metrics_log.append(metric_entry)
        return metric_entry

    def trigger_security_alert(self, severity: str, event_type: str, description: str) -> Dict[str, Any]:
        """
        Triggers an instant security alert for anomaly detection or potential threat isolation.
        """
        alert = {
            "node_id": self.node_id,
            "severity": severity.upper(),  # LOW, MEDIUM, HIGH, CRITICAL
            "event": event_type,
            "description": description,
            "timestamp": time.time()
        }
        self.security_alerts.append(alert)
        return alert

    def generate_health_report(self) -> Dict[str, Any]:
        """
        Generates an executive health report summarizing system status and active alerts.
        """
        return {
            "node_id": self.node_id,
            "status": "HEALTHY" if not any(a["severity"] == "CRITICAL" for a in self.security_alerts) else "WARNING",
            "total_metrics_recorded": len(self.metrics_log),
            "total_security_alerts": len(self.security_alerts),
            "last_check_timestamp": time.time()
        }
