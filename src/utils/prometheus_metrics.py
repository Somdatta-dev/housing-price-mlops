"""
Prometheus metrics integration for Housing Price Prediction MLOps Pipeline
Provides /metrics endpoint for Prometheus scraping
"""

import sqlite3
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict

import psutil
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Gauge,
    Histogram,
    Info,
    generate_latest,
)
from prometheus_client.core import CollectorRegistry

from .monitoring import metrics_collector


class PrometheusMetrics:
    """Prometheus metrics collector and exporter"""

    def __init__(self):
        # Create custom registry
        self.registry = CollectorRegistry()

        # API Metrics
        self.api_requests_total = Counter(
            "housing_api_requests_total",
            "Total number of API requests",
            ["method", "endpoint", "status"],
            registry=self.registry,
        )

        self.api_request_duration = Histogram(
            "housing_api_request_duration_seconds",
            "API request duration in seconds",
            ["method", "endpoint"],
            registry=self.registry,
        )

        self.api_errors_total = Counter(
            "housing_api_errors_total",
            "Total number of API errors",
            ["endpoint", "error_type"],
            registry=self.registry,
        )

        # Model Metrics
        self.model_predictions_total = Counter(
            "housing_model_predictions_total",
            "Total number of model predictions",
            ["model_name", "prediction_type"],
            registry=self.registry,
        )

        self.model_prediction_value = Histogram(
            "housing_model_prediction_value",
            "Distribution of predicted house values",
            buckets=[
                50000,
                100000,
                200000,
                300000,
                500000,
                750000,
                1000000,
                float("inf"),
            ],
            registry=self.registry,
        )

        self.model_inference_duration = Histogram(
            "housing_model_inference_duration_seconds",
            "Model inference duration in seconds",
            ["model_name"],
            registry=self.registry,
        )

        # System Metrics
        self.system_cpu_usage = Gauge(
            "housing_system_cpu_usage_percent",
            "System CPU usage percentage",
            registry=self.registry,
        )

        self.system_memory_usage = Gauge(
            "housing_system_memory_usage_percent",
            "System memory usage percentage",
            registry=self.registry,
        )

        self.system_disk_usage = Gauge(
            "housing_system_disk_usage_percent",
            "System disk usage percentage",
            registry=self.registry,
        )

        # Application Health
        self.app_health_status = Gauge(
            "housing_app_health_status",
            "Application health status (1=healthy, 0=unhealthy)",
            ["component"],
            registry=self.registry,
        )

        self.app_uptime_seconds = Gauge(
            "housing_app_uptime_seconds",
            "Application uptime in seconds",
            registry=self.registry,
        )

        # Data Quality Metrics
        self.data_quality_score = Gauge(
            "housing_data_quality_score",
            "Data quality score (0-1)",
            ["dataset"],
            registry=self.registry,
        )

        self.data_drift_score = Gauge(
            "housing_data_drift_score",
            "Data drift score (0-1)",
            ["feature"],
            registry=self.registry,
        )

        # Model Performance
        self.model_accuracy = Gauge(
            "housing_model_accuracy",
            "Model accuracy score",
            ["model_name", "metric"],
            registry=self.registry,
        )

        # Application Info
        self.app_info = Info(
            "housing_app_info", "Application information", registry=self.registry
        )

        # Initialize app info
        self.app_info.info(
            {
                "version": "1.0.0",
                "model_type": "random_forest",
                "framework": "scikit-learn",
                "api_framework": "fastapi",
                "python_version": "3.9+",
            }
        )

        # Track start time for uptime calculation
        self.start_time = time.time()

    def record_api_request(
        self, method: str, endpoint: str, status_code: int, duration: float
    ):
        """Record API request metrics"""
        status = "success" if 200 <= status_code < 400 else "error"

        self.api_requests_total.labels(
            method=method, endpoint=endpoint, status=status
        ).inc()

        self.api_request_duration.labels(method=method, endpoint=endpoint).observe(
            duration
        )

        if status == "error":
            error_type = "client_error" if 400 <= status_code < 500 else "server_error"
            self.api_errors_total.labels(endpoint=endpoint, error_type=error_type).inc()

    def record_model_prediction(
        self,
        model_name: str,
        prediction_value: float,
        inference_time: float,
        prediction_type: str = "single",
    ):
        """Record model prediction metrics"""
        self.model_predictions_total.labels(
            model_name=model_name, prediction_type=prediction_type
        ).inc()

        self.model_prediction_value.observe(prediction_value)

        self.model_inference_duration.labels(model_name=model_name).observe(
            inference_time
        )

    def update_system_metrics(self):
        """Update system resource metrics"""
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        self.system_cpu_usage.set(cpu_percent)

        # Memory usage
        memory = psutil.virtual_memory()
        self.system_memory_usage.set(memory.percent)

        # Disk usage
        disk = psutil.disk_usage("/")
        disk_percent = (disk.used / disk.total) * 100
        self.system_disk_usage.set(disk_percent)

        # Uptime
        uptime = time.time() - self.start_time
        self.app_uptime_seconds.set(uptime)

    def update_health_metrics(self, health_status: Dict[str, Any]):
        """Update application health metrics"""
        for component, status in health_status.get("checks", {}).items():
            health_value = 1 if status.get("status") == "healthy" else 0
            self.app_health_status.labels(component=component).set(health_value)

    def update_model_performance(self, model_name: str, metrics: Dict[str, float]):
        """Update model performance metrics"""
        for metric_name, value in metrics.items():
            self.model_accuracy.labels(model_name=model_name, metric=metric_name).set(
                value
            )

    def update_data_quality(self, dataset: str, quality_score: float):
        """Update data quality metrics"""
        self.data_quality_score.labels(dataset=dataset).set(quality_score)

    def update_data_drift(self, feature: str, drift_score: float):
        """Update data drift metrics"""
        self.data_drift_score.labels(feature=feature).set(drift_score)

    def get_metrics_from_db(self):
        """Load and update metrics from database"""
        try:
            # Get recent metrics from database
            cutoff_time = (datetime.utcnow() - timedelta(hours=1)).isoformat() + "Z"

            with sqlite3.connect(metrics_collector.db_path) as conn:
                cursor = conn.cursor()

                # Get API metrics
                cursor.execute(
                    """
                    SELECT endpoint, method, status_code, response_time_ms, COUNT(*) as count
                    FROM api_metrics 
                    WHERE timestamp > ? 
                    GROUP BY endpoint, method, status_code
                """,
                    (cutoff_time,),
                )

                for row in cursor.fetchall():
                    endpoint, method, status_code, avg_response_time, count = row
                    # Update counters based on database data
                    # Note: This is a simplified approach - in production you'd want
                    # to track these metrics in real-time rather than from database

                # Get model performance metrics
                cursor.execute(
                    """
                    SELECT model_name, metric_name, metric_value 
                    FROM model_performance 
                    ORDER BY timestamp DESC 
                    LIMIT 10
                """
                )

                for row in cursor.fetchall():
                    model_name, metric_name, metric_value = row
                    self.model_accuracy.labels(
                        model_name=model_name, metric=metric_name
                    ).set(metric_value)

        except Exception as e:
            print(f"Error loading metrics from database: {e}")

    def generate_metrics(self) -> str:
        """Generate Prometheus metrics in text format"""
        # Update system metrics
        self.update_system_metrics()

        # Load metrics from database
        self.get_metrics_from_db()

        # Generate metrics text
        return generate_latest(self.registry)

    def get_content_type(self) -> str:
        """Get content type for metrics endpoint"""
        return CONTENT_TYPE_LATEST


# Global instance
prometheus_metrics = PrometheusMetrics()


def get_prometheus_metrics() -> str:
    """Get Prometheus metrics as string"""
    return prometheus_metrics.generate_metrics()


def get_prometheus_content_type() -> str:
    """Get Prometheus content type"""
    return prometheus_metrics.get_content_type()


# Middleware function for FastAPI
def record_request_metrics(
    method: str, endpoint: str, status_code: int, duration: float
):
    """Record request metrics (to be called from FastAPI middleware)"""
    prometheus_metrics.record_api_request(method, endpoint, status_code, duration)


def record_prediction_metrics(
    model_name: str, prediction_value: float, inference_time: float
):
    """Record prediction metrics (to be called from prediction endpoints)"""
    prometheus_metrics.record_model_prediction(
        model_name, prediction_value, inference_time
    )


def update_health_status(health_status: Dict[str, Any]):
    """Update health status metrics"""
    prometheus_metrics.update_health_metrics(health_status)
