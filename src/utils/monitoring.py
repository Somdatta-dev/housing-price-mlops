"""
Monitoring and metrics collection system for Housing Price Prediction MLOps Pipeline
"""

import asyncio
import json
import sqlite3
import threading
import time
from collections import defaultdict, deque
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import psutil


@dataclass
class MetricPoint:
    """Data class for metric points"""

    timestamp: str
    name: str
    value: float
    tags: Dict[str, str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class MetricsCollector:
    """
    Collects and stores various metrics
    """

    def __init__(self, db_path: str = "data/metrics.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()

        # In-memory storage for real-time metrics
        self.metrics_buffer = deque(maxlen=1000)
        self.counters = defaultdict(int)
        self.gauges = defaultdict(float)
        self.histograms = defaultdict(list)

        # Thread-safe lock
        self.lock = threading.Lock()

    def _init_database(self):
        """Initialize metrics database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Metrics table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    name TEXT NOT NULL,
                    value REAL NOT NULL,
                    tags TEXT,
                    type TEXT DEFAULT 'gauge'
                )
            """
            )

            # System metrics table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS system_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    cpu_percent REAL,
                    memory_percent REAL,
                    memory_used_gb REAL,
                    disk_percent REAL,
                    disk_used_gb REAL,
                    network_bytes_sent INTEGER,
                    network_bytes_recv INTEGER
                )
            """
            )

            # API metrics table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS api_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    endpoint TEXT NOT NULL,
                    method TEXT NOT NULL,
                    status_code INTEGER NOT NULL,
                    response_time_ms REAL NOT NULL,
                    request_size_bytes INTEGER,
                    response_size_bytes INTEGER
                )
            """
            )

            # Model metrics table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS model_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    model_name TEXT NOT NULL,
                    model_version TEXT NOT NULL,
                    prediction_time_ms REAL NOT NULL,
                    prediction_value REAL,
                    confidence_score REAL,
                    input_features TEXT
                )
            """
            )

            conn.commit()

    def record_counter(self, name: str, value: int = 1, tags: Dict[str, str] = None):
        """Record a counter metric"""
        with self.lock:
            key = f"{name}:{json.dumps(tags or {}, sort_keys=True)}"
            self.counters[key] += value

            metric = MetricPoint(
                timestamp=datetime.utcnow().isoformat() + "Z",
                name=name,
                value=self.counters[key],
                tags=tags,
            )
            self.metrics_buffer.append(metric)
            self._store_metric(metric, "counter")

    def record_gauge(self, name: str, value: float, tags: Dict[str, str] = None):
        """Record a gauge metric"""
        with self.lock:
            key = f"{name}:{json.dumps(tags or {}, sort_keys=True)}"
            self.gauges[key] = value

            metric = MetricPoint(
                timestamp=datetime.utcnow().isoformat() + "Z",
                name=name,
                value=value,
                tags=tags,
            )
            self.metrics_buffer.append(metric)
            self._store_metric(metric, "gauge")

    def record_histogram(self, name: str, value: float, tags: Dict[str, str] = None):
        """Record a histogram metric"""
        with self.lock:
            key = f"{name}:{json.dumps(tags or {}, sort_keys=True)}"
            self.histograms[key].append(value)

            # Keep only last 100 values
            if len(self.histograms[key]) > 100:
                self.histograms[key] = self.histograms[key][-100:]

            metric = MetricPoint(
                timestamp=datetime.utcnow().isoformat() + "Z",
                name=name,
                value=value,
                tags=tags,
            )
            self.metrics_buffer.append(metric)
            self._store_metric(metric, "histogram")

    def _store_metric(self, metric: MetricPoint, metric_type: str):
        """Store metric in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO metrics (timestamp, name, value, tags, type)
                    VALUES (?, ?, ?, ?, ?)
                """,
                    (
                        metric.timestamp,
                        metric.name,
                        metric.value,
                        json.dumps(metric.tags) if metric.tags else None,
                        metric_type,
                    ),
                )
                conn.commit()
        except Exception as e:
            print(f"Failed to store metric: {e}")

    def record_system_metrics(self):
        """Record current system metrics"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")
            network = psutil.net_io_counters()

            timestamp = datetime.utcnow().isoformat() + "Z"

            # Record individual metrics
            self.record_gauge("system.cpu.percent", cpu_percent)
            self.record_gauge("system.memory.percent", memory.percent)
            self.record_gauge("system.memory.used_gb", memory.used / (1024**3))
            self.record_gauge("system.disk.percent", disk.percent)
            self.record_gauge("system.disk.used_gb", disk.used / (1024**3))

            # Store in system_metrics table
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO system_metrics 
                    (timestamp, cpu_percent, memory_percent, memory_used_gb, 
                     disk_percent, disk_used_gb, network_bytes_sent, network_bytes_recv)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        timestamp,
                        cpu_percent,
                        memory.percent,
                        memory.used / (1024**3),
                        disk.percent,
                        disk.used / (1024**3),
                        network.bytes_sent,
                        network.bytes_recv,
                    ),
                )
                conn.commit()

        except Exception as e:
            print(f"Failed to record system metrics: {e}")

    def record_api_request(
        self,
        endpoint: str,
        method: str,
        status_code: int,
        response_time_ms: float,
        request_size: int = None,
        response_size: int = None,
    ):
        """Record API request metrics"""
        timestamp = datetime.utcnow().isoformat() + "Z"

        # Record individual metrics
        self.record_counter(
            "api.requests.total",
            tags={"endpoint": endpoint, "method": method, "status": str(status_code)},
        )

        self.record_histogram(
            "api.response_time_ms",
            response_time_ms,
            tags={"endpoint": endpoint, "method": method},
        )

        # Store in api_metrics table
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO api_metrics 
                    (timestamp, endpoint, method, status_code, response_time_ms,
                     request_size_bytes, response_size_bytes)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        timestamp,
                        endpoint,
                        method,
                        status_code,
                        response_time_ms,
                        request_size,
                        response_size,
                    ),
                )
                conn.commit()
        except Exception as e:
            print(f"Failed to record API metrics: {e}")

    def record_model_prediction(
        self,
        model_name: str,
        model_version: str,
        prediction_time_ms: float,
        prediction_value: float,
        confidence_score: float = None,
        input_features: Dict[str, Any] = None,
    ):
        """Record model prediction metrics"""
        timestamp = datetime.utcnow().isoformat() + "Z"

        # Record individual metrics
        self.record_counter(
            "model.predictions.total",
            tags={"model_name": model_name, "model_version": model_version},
        )

        self.record_histogram(
            "model.prediction_time_ms",
            prediction_time_ms,
            tags={"model_name": model_name, "model_version": model_version},
        )

        self.record_histogram(
            "model.prediction_value",
            prediction_value,
            tags={"model_name": model_name, "model_version": model_version},
        )

        if confidence_score is not None:
            self.record_histogram(
                "model.confidence_score",
                confidence_score,
                tags={"model_name": model_name, "model_version": model_version},
            )

        # Store in model_metrics table
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO model_metrics 
                    (timestamp, model_name, model_version, prediction_time_ms,
                     prediction_value, confidence_score, input_features)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        timestamp,
                        model_name,
                        model_version,
                        prediction_time_ms,
                        prediction_value,
                        confidence_score,
                        json.dumps(input_features) if input_features else None,
                    ),
                )
                conn.commit()
        except Exception as e:
            print(f"Failed to record model metrics: {e}")

    def get_metrics_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get metrics summary for the last N hours"""
        cutoff_time = (datetime.utcnow() - timedelta(hours=hours)).isoformat() + "Z"

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # API metrics
                cursor.execute(
                    """
                    SELECT COUNT(*), AVG(response_time_ms), 
                           COUNT(CASE WHEN status_code >= 400 THEN 1 END) as errors
                    FROM api_metrics 
                    WHERE timestamp > ?
                """,
                    (cutoff_time,),
                )
                api_stats = cursor.fetchone()

                # Model metrics
                cursor.execute(
                    """
                    SELECT COUNT(*), AVG(prediction_time_ms), AVG(prediction_value)
                    FROM model_metrics 
                    WHERE timestamp > ?
                """,
                    (cutoff_time,),
                )
                model_stats = cursor.fetchone()

                # System metrics (latest)
                cursor.execute(
                    """
                    SELECT cpu_percent, memory_percent, disk_percent
                    FROM system_metrics 
                    ORDER BY timestamp DESC 
                    LIMIT 1
                """
                )
                system_stats = cursor.fetchone()

                return {
                    "time_period_hours": hours,
                    "api": {
                        "total_requests": api_stats[0] or 0,
                        "avg_response_time_ms": round(api_stats[1] or 0, 2),
                        "error_count": api_stats[2] or 0,
                        "error_rate": round(
                            (api_stats[2] or 0) / max(api_stats[0] or 1, 1) * 100, 2
                        ),
                    },
                    "model": {
                        "total_predictions": model_stats[0] or 0,
                        "avg_prediction_time_ms": round(model_stats[1] or 0, 2),
                        "avg_prediction_value": round(model_stats[2] or 0, 2),
                    },
                    "system": {
                        "cpu_percent": system_stats[0] if system_stats else 0,
                        "memory_percent": system_stats[1] if system_stats else 0,
                        "disk_percent": system_stats[2] if system_stats else 0,
                    },
                }
        except Exception as e:
            print(f"Failed to get metrics summary: {e}")
            return {}


class AlertManager:
    """
    Manages alerts based on metrics thresholds
    """

    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics_collector = metrics_collector
        self.alert_rules = []
        self.active_alerts = {}

    def add_alert_rule(
        self,
        name: str,
        metric_name: str,
        threshold: float,
        comparison: str = "greater",
        duration_minutes: int = 5,
    ):
        """Add an alert rule"""
        rule = {
            "name": name,
            "metric_name": metric_name,
            "threshold": threshold,
            "comparison": comparison,  # greater, less, equal
            "duration_minutes": duration_minutes,
            "last_triggered": None,
        }
        self.alert_rules.append(rule)

    def check_alerts(self):
        """Check all alert rules"""
        current_time = datetime.utcnow()

        for rule in self.alert_rules:
            # Get recent metric values
            cutoff_time = (
                current_time - timedelta(minutes=rule["duration_minutes"])
            ).isoformat() + "Z"

            try:
                with sqlite3.connect(self.metrics_collector.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        """
                        SELECT AVG(value) FROM metrics 
                        WHERE name = ? AND timestamp > ?
                    """,
                        (rule["metric_name"], cutoff_time),
                    )

                    result = cursor.fetchone()
                    if result and result[0] is not None:
                        avg_value = result[0]

                        # Check threshold
                        triggered = False
                        if (
                            rule["comparison"] == "greater"
                            and avg_value > rule["threshold"]
                        ):
                            triggered = True
                        elif (
                            rule["comparison"] == "less"
                            and avg_value < rule["threshold"]
                        ):
                            triggered = True
                        elif (
                            rule["comparison"] == "equal"
                            and abs(avg_value - rule["threshold"]) < 0.001
                        ):
                            triggered = True

                        if triggered:
                            self._trigger_alert(rule, avg_value)
                        else:
                            self._resolve_alert(rule["name"])

            except Exception as e:
                print(f"Failed to check alert rule {rule['name']}: {e}")

    def _trigger_alert(self, rule: Dict[str, Any], current_value: float):
        """Trigger an alert"""
        alert_key = rule["name"]

        if alert_key not in self.active_alerts:
            alert = {
                "name": rule["name"],
                "metric_name": rule["metric_name"],
                "threshold": rule["threshold"],
                "current_value": current_value,
                "triggered_at": datetime.utcnow().isoformat() + "Z",
                "status": "active",
            }

            self.active_alerts[alert_key] = alert
            self._send_alert_notification(alert)

    def _resolve_alert(self, alert_name: str):
        """Resolve an alert"""
        if alert_name in self.active_alerts:
            self.active_alerts[alert_name]["status"] = "resolved"
            self.active_alerts[alert_name]["resolved_at"] = (
                datetime.utcnow().isoformat() + "Z"
            )
            del self.active_alerts[alert_name]

    def _send_alert_notification(self, alert: Dict[str, Any]):
        """Send alert notification (placeholder for actual notification system)"""
        print(f"🚨 ALERT: {alert['name']}")
        print(f"   Metric: {alert['metric_name']}")
        print(f"   Threshold: {alert['threshold']}")
        print(f"   Current Value: {alert['current_value']}")
        print(f"   Triggered At: {alert['triggered_at']}")


class HealthChecker:
    """
    Health check system
    """

    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics_collector = metrics_collector
        self.health_checks = []

    def add_health_check(self, name: str, check_function, interval_seconds: int = 60):
        """Add a health check"""
        health_check = {
            "name": name,
            "check_function": check_function,
            "interval_seconds": interval_seconds,
            "last_run": None,
            "last_status": None,
            "last_error": None,
        }
        self.health_checks.append(health_check)

    def run_health_checks(self) -> Dict[str, Any]:
        """Run all health checks"""
        results = {}
        overall_status = "healthy"

        for check in self.health_checks:
            try:
                status = check["check_function"]()
                check["last_run"] = datetime.utcnow().isoformat() + "Z"
                check["last_status"] = status
                check["last_error"] = None

                results[check["name"]] = {
                    "status": status,
                    "last_run": check["last_run"],
                }

                if status != "healthy":
                    overall_status = "unhealthy"

            except Exception as e:
                check["last_run"] = datetime.utcnow().isoformat() + "Z"
                check["last_status"] = "error"
                check["last_error"] = str(e)

                results[check["name"]] = {
                    "status": "error",
                    "error": str(e),
                    "last_run": check["last_run"],
                }

                overall_status = "unhealthy"

        # Record overall health metric
        health_score = 1.0 if overall_status == "healthy" else 0.0
        self.metrics_collector.record_gauge("system.health_score", health_score)

        return {
            "overall_status": overall_status,
            "checks": results,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }


# Global instances
metrics_collector = MetricsCollector()
alert_manager = AlertManager(metrics_collector)
health_checker = HealthChecker(metrics_collector)


# Setup default alert rules
def setup_default_alerts():
    """Setup default alert rules"""
    alert_manager.add_alert_rule(
        name="High CPU Usage",
        metric_name="system.cpu.percent",
        threshold=80.0,
        comparison="greater",
        duration_minutes=5,
    )

    alert_manager.add_alert_rule(
        name="High Memory Usage",
        metric_name="system.memory.percent",
        threshold=85.0,
        comparison="greater",
        duration_minutes=5,
    )

    alert_manager.add_alert_rule(
        name="High API Response Time",
        metric_name="api.response_time_ms",
        threshold=1000.0,
        comparison="greater",
        duration_minutes=3,
    )

    alert_manager.add_alert_rule(
        name="High Model Prediction Time",
        metric_name="model.prediction_time_ms",
        threshold=500.0,
        comparison="greater",
        duration_minutes=3,
    )


# Setup default health checks
def setup_default_health_checks():
    """Setup default health checks"""

    def check_disk_space():
        disk = psutil.disk_usage("/")
        if disk.percent > 90:
            return "unhealthy"
        elif disk.percent > 80:
            return "warning"
        return "healthy"

    def check_memory():
        memory = psutil.virtual_memory()
        if memory.percent > 90:
            return "unhealthy"
        elif memory.percent > 80:
            return "warning"
        return "healthy"

    def check_database():
        try:
            with sqlite3.connect(metrics_collector.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                return "healthy"
        except:
            return "unhealthy"

    health_checker.add_health_check("disk_space", check_disk_space, 300)  # 5 minutes
    health_checker.add_health_check("memory", check_memory, 60)  # 1 minute
    health_checker.add_health_check("database", check_database, 120)  # 2 minutes


# Initialize monitoring system
def initialize_monitoring():
    """Initialize the monitoring system"""
    setup_default_alerts()
    setup_default_health_checks()
    print("Monitoring system initialized")


# Background monitoring task
class MonitoringService:
    """Background service for continuous monitoring"""

    def __init__(self):
        self.running = False
        self.thread = None

    def start(self):
        """Start the monitoring service"""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(
                target=self._run_monitoring_loop, daemon=True
            )
            self.thread.start()
            print("Monitoring service started")

    def stop(self):
        """Stop the monitoring service"""
        self.running = False
        if self.thread:
            self.thread.join()
        print("Monitoring service stopped")

    def _run_monitoring_loop(self):
        """Main monitoring loop"""
        while self.running:
            try:
                # Collect system metrics every minute
                metrics_collector.record_system_metrics()

                # Check alerts every 30 seconds
                alert_manager.check_alerts()

                # Run health checks every 2 minutes
                health_checker.run_health_checks()

                time.sleep(30)  # Sleep for 30 seconds

            except Exception as e:
                print(f"Error in monitoring loop: {e}")
                time.sleep(60)  # Sleep longer on error


# Global monitoring service
monitoring_service = MonitoringService()
