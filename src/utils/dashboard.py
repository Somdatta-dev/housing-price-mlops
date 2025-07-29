"""
Simple web dashboard for monitoring Housing Price Prediction MLOps Pipeline
"""

import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List

import plotly.graph_objs as go
import plotly.utils
from flask import Flask, jsonify, render_template_string, request

from .monitoring import alert_manager, health_checker, metrics_collector

app = Flask(__name__)

# HTML template for the dashboard
DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Housing Price Prediction - Monitoring Dashboard</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body { 
            font-family: Arial, sans-serif; 
            margin: 0; 
            padding: 20px; 
            background-color: #f5f5f5; 
        }
        .header { 
            background-color: #2c3e50; 
            color: white; 
            padding: 20px; 
            margin: -20px -20px 20px -20px; 
            text-align: center; 
        }
        .metrics-grid { 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); 
            gap: 20px; 
            margin-bottom: 30px; 
        }
        .metric-card { 
            background: white; 
            padding: 20px; 
            border-radius: 8px; 
            box-shadow: 0 2px 4px rgba(0,0,0,0.1); 
        }
        .metric-value { 
            font-size: 2em; 
            font-weight: bold; 
            color: #3498db; 
        }
        .metric-label { 
            color: #7f8c8d; 
            margin-top: 5px; 
        }
        .status-healthy { color: #27ae60; }
        .status-warning { color: #f39c12; }
        .status-unhealthy { color: #e74c3c; }
        .chart-container { 
            background: white; 
            padding: 20px; 
            border-radius: 8px; 
            box-shadow: 0 2px 4px rgba(0,0,0,0.1); 
            margin-bottom: 20px; 
        }
        .alerts-container {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        .alert-item {
            padding: 10px;
            margin: 10px 0;
            border-left: 4px solid #e74c3c;
            background-color: #fdf2f2;
        }
        .refresh-btn {
            background-color: #3498db;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 4px;
            cursor: pointer;
            margin: 10px 0;
        }
        .refresh-btn:hover {
            background-color: #2980b9;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🏠 Housing Price Prediction - Monitoring Dashboard</h1>
        <p>Real-time monitoring and metrics for MLOps pipeline</p>
        <button class="refresh-btn" onclick="location.reload()">🔄 Refresh Dashboard</button>
    </div>

    <!-- Health Status -->
    <div class="metric-card">
        <h3>🏥 System Health</h3>
        <div id="health-status">Loading...</div>
    </div>

    <!-- Key Metrics -->
    <div class="metrics-grid">
        <div class="metric-card">
            <div class="metric-value" id="total-requests">-</div>
            <div class="metric-label">Total API Requests (24h)</div>
        </div>
        <div class="metric-card">
            <div class="metric-value" id="avg-response-time">-</div>
            <div class="metric-label">Avg Response Time (ms)</div>
        </div>
        <div class="metric-card">
            <div class="metric-value" id="total-predictions">-</div>
            <div class="metric-label">Total Predictions (24h)</div>
        </div>
        <div class="metric-card">
            <div class="metric-value" id="error-rate">-</div>
            <div class="metric-label">Error Rate (%)</div>
        </div>
        <div class="metric-card">
            <div class="metric-value" id="cpu-usage">-</div>
            <div class="metric-label">CPU Usage (%)</div>
        </div>
        <div class="metric-card">
            <div class="metric-value" id="memory-usage">-</div>
            <div class="metric-label">Memory Usage (%)</div>
        </div>
    </div>

    <!-- Active Alerts -->
    <div class="alerts-container">
        <h3>🚨 Active Alerts</h3>
        <div id="active-alerts">Loading...</div>
    </div>

    <!-- Charts -->
    <div class="chart-container">
        <h3>📊 API Response Time (Last 24 Hours)</h3>
        <div id="response-time-chart"></div>
    </div>

    <div class="chart-container">
        <h3>📈 System Metrics (Last 24 Hours)</h3>
        <div id="system-metrics-chart"></div>
    </div>

    <div class="chart-container">
        <h3>🤖 Model Predictions (Last 24 Hours)</h3>
        <div id="predictions-chart"></div>
    </div>

    <script>
        // Load dashboard data
        async function loadDashboard() {
            try {
                // Load metrics summary
                const metricsResponse = await fetch('/api/metrics/summary');
                const metrics = await metricsResponse.json();
                
                // Update metric cards
                document.getElementById('total-requests').textContent = metrics.api.total_requests;
                document.getElementById('avg-response-time').textContent = metrics.api.avg_response_time_ms;
                document.getElementById('total-predictions').textContent = metrics.model.total_predictions;
                document.getElementById('error-rate').textContent = metrics.api.error_rate + '%';
                document.getElementById('cpu-usage').textContent = metrics.system.cpu_percent + '%';
                document.getElementById('memory-usage').textContent = metrics.system.memory_percent + '%';

                // Load health status
                const healthResponse = await fetch('/api/health/detailed');
                const health = await healthResponse.json();
                
                let healthHtml = `<div class="status-${health.overall_status}">${health.overall_status.toUpperCase()}</div>`;
                for (const [check, result] of Object.entries(health.checks)) {
                    healthHtml += `<div><strong>${check}:</strong> <span class="status-${result.status}">${result.status}</span></div>`;
                }
                document.getElementById('health-status').innerHTML = healthHtml;

                // Load active alerts
                const alertsResponse = await fetch('/api/alerts');
                const alerts = await alertsResponse.json();
                
                let alertsHtml = '';
                if (alerts.length === 0) {
                    alertsHtml = '<div style="color: #27ae60;">✅ No active alerts</div>';
                } else {
                    alerts.forEach(alert => {
                        alertsHtml += `
                            <div class="alert-item">
                                <strong>${alert.name}</strong><br>
                                Metric: ${alert.metric_name}<br>
                                Threshold: ${alert.threshold}, Current: ${alert.current_value}<br>
                                Triggered: ${alert.triggered_at}
                            </div>
                        `;
                    });
                }
                document.getElementById('active-alerts').innerHTML = alertsHtml;

                // Load charts
                await loadCharts();

            } catch (error) {
                console.error('Failed to load dashboard:', error);
            }
        }

        async function loadCharts() {
            try {
                // Response time chart
                const responseTimeResponse = await fetch('/api/metrics/response-time-history');
                const responseTimeData = await responseTimeResponse.json();
                
                const responseTimeTrace = {
                    x: responseTimeData.timestamps,
                    y: responseTimeData.values,
                    type: 'scatter',
                    mode: 'lines',
                    name: 'Response Time (ms)',
                    line: { color: '#3498db' }
                };
                
                Plotly.newPlot('response-time-chart', [responseTimeTrace], {
                    title: 'API Response Time',
                    xaxis: { title: 'Time' },
                    yaxis: { title: 'Response Time (ms)' }
                });

                // System metrics chart
                const systemMetricsResponse = await fetch('/api/metrics/system-history');
                const systemMetricsData = await systemMetricsResponse.json();
                
                const cpuTrace = {
                    x: systemMetricsData.timestamps,
                    y: systemMetricsData.cpu,
                    type: 'scatter',
                    mode: 'lines',
                    name: 'CPU %',
                    line: { color: '#e74c3c' }
                };
                
                const memoryTrace = {
                    x: systemMetricsData.timestamps,
                    y: systemMetricsData.memory,
                    type: 'scatter',
                    mode: 'lines',
                    name: 'Memory %',
                    line: { color: '#f39c12' }
                };
                
                Plotly.newPlot('system-metrics-chart', [cpuTrace, memoryTrace], {
                    title: 'System Resource Usage',
                    xaxis: { title: 'Time' },
                    yaxis: { title: 'Usage (%)' }
                });

                // Predictions chart
                const predictionsResponse = await fetch('/api/metrics/predictions-history');
                const predictionsData = await predictionsResponse.json();
                
                const predictionsTrace = {
                    x: predictionsData.timestamps,
                    y: predictionsData.values,
                    type: 'scatter',
                    mode: 'markers',
                    name: 'Predictions',
                    marker: { color: '#27ae60', size: 6 }
                };
                
                Plotly.newPlot('predictions-chart', [predictionsTrace], {
                    title: 'Model Predictions Over Time',
                    xaxis: { title: 'Time' },
                    yaxis: { title: 'Predicted House Value' }
                });

            } catch (error) {
                console.error('Failed to load charts:', error);
            }
        }

        // Load dashboard on page load
        document.addEventListener('DOMContentLoaded', loadDashboard);

        // Auto-refresh every 30 seconds
        setInterval(loadDashboard, 30000);
    </script>
</body>
</html>
"""


@app.route("/")
def dashboard():
    """Main dashboard page"""
    return render_template_string(DASHBOARD_HTML)


@app.route("/api/metrics/summary")
def metrics_summary():
    """Get metrics summary"""
    summary = metrics_collector.get_metrics_summary(24)
    return jsonify(summary)


@app.route("/api/health/detailed")
def health_detailed():
    """Get detailed health status"""
    health_status = health_checker.run_health_checks()
    return jsonify(health_status)


@app.route("/api/alerts")
def active_alerts():
    """Get active alerts"""
    alerts = list(alert_manager.active_alerts.values())
    return jsonify(alerts)


@app.route("/api/metrics/response-time-history")
def response_time_history():
    """Get response time history"""
    hours = int(request.args.get("hours", 24))
    cutoff_time = (datetime.utcnow() - timedelta(hours=hours)).isoformat() + "Z"

    try:
        with sqlite3.connect(metrics_collector.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT timestamp, response_time_ms 
                FROM api_metrics 
                WHERE timestamp > ? 
                ORDER BY timestamp
            """,
                (cutoff_time,),
            )

            data = cursor.fetchall()
            timestamps = [row[0] for row in data]
            values = [row[1] for row in data]

            return jsonify({"timestamps": timestamps, "values": values})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/metrics/system-history")
def system_history():
    """Get system metrics history"""
    hours = int(request.args.get("hours", 24))
    cutoff_time = (datetime.utcnow() - timedelta(hours=hours)).isoformat() + "Z"

    try:
        with sqlite3.connect(metrics_collector.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT timestamp, cpu_percent, memory_percent 
                FROM system_metrics 
                WHERE timestamp > ? 
                ORDER BY timestamp
            """,
                (cutoff_time,),
            )

            data = cursor.fetchall()
            timestamps = [row[0] for row in data]
            cpu = [row[1] for row in data]
            memory = [row[2] for row in data]

            return jsonify({"timestamps": timestamps, "cpu": cpu, "memory": memory})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/metrics/predictions-history")
def predictions_history():
    """Get predictions history"""
    hours = int(request.args.get("hours", 24))
    cutoff_time = (datetime.utcnow() - timedelta(hours=hours)).isoformat() + "Z"

    try:
        with sqlite3.connect(metrics_collector.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT timestamp, prediction_value 
                FROM model_metrics 
                WHERE timestamp > ? 
                ORDER BY timestamp
            """,
                (cutoff_time,),
            )

            data = cursor.fetchall()
            timestamps = [row[0] for row in data]
            values = [row[1] for row in data]

            return jsonify({"timestamps": timestamps, "values": values})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/metrics/export")
def export_metrics():
    """Export metrics as JSON"""
    hours = int(request.args.get("hours", 24))
    cutoff_time = (datetime.utcnow() - timedelta(hours=hours)).isoformat() + "Z"

    try:
        with sqlite3.connect(metrics_collector.db_path) as conn:
            cursor = conn.cursor()

            # Get all metrics
            cursor.execute(
                """
                SELECT timestamp, name, value, tags, type 
                FROM metrics 
                WHERE timestamp > ? 
                ORDER BY timestamp
            """,
                (cutoff_time,),
            )

            metrics_data = []
            for row in cursor.fetchall():
                metrics_data.append(
                    {
                        "timestamp": row[0],
                        "name": row[1],
                        "value": row[2],
                        "tags": json.loads(row[3]) if row[3] else None,
                        "type": row[4],
                    }
                )

            return jsonify(
                {
                    "export_time": datetime.utcnow().isoformat() + "Z",
                    "time_period_hours": hours,
                    "metrics_count": len(metrics_data),
                    "metrics": metrics_data,
                }
            )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def run_dashboard(host="0.0.0.0", port=3000, debug=False):
    """Run the dashboard server"""
    print(f"Starting monitoring dashboard on http://{host}:{port}")
    app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    run_dashboard(debug=True)
