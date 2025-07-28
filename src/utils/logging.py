"""
Comprehensive logging utility for Housing Price Prediction MLOps Pipeline
"""

import os
import sys
import json
import logging
import logging.config
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import uuid
import time
import psutil
from functools import wraps

class StructuredLogger:
    """
    Structured logger with JSON formatting and context management
    """
    
    def __init__(self, name: str, config_path: Optional[str] = None):
        self.name = name
        self.logger = logging.getLogger(name)
        self.request_id = None
        self.context = {}
        
        # Load logging configuration
        if config_path and Path(config_path).exists():
            logging.config.fileConfig(config_path)
        else:
            self._setup_default_logging()
    
    def _setup_default_logging(self):
        """Setup default logging configuration"""
        # Create logs directory
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)
        
        # Configure logger
        self.logger.setLevel(logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        
        # File handler with JSON formatting
        file_handler = logging.FileHandler(logs_dir / "app.log")
        file_handler.setLevel(logging.INFO)
        
        # Add handlers
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)
    
    def set_request_id(self, request_id: str = None):
        """Set request ID for tracking"""
        self.request_id = request_id or str(uuid.uuid4())
        return self.request_id
    
    def set_context(self, **kwargs):
        """Set logging context"""
        self.context.update(kwargs)
    
    def clear_context(self):
        """Clear logging context"""
        self.context.clear()
        self.request_id = None
    
    def _format_message(self, message: str, extra: Dict[str, Any] = None) -> str:
        """Format message with context and metadata"""
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "logger": self.name,
            "message": message,
            "request_id": self.request_id,
            **self.context
        }
        
        if extra:
            log_data.update(extra)
        
        # Remove None values
        log_data = {k: v for k, v in log_data.items() if v is not None}
        
        return json.dumps(log_data)
    
    def info(self, message: str, **kwargs):
        """Log info message"""
        formatted_message = self._format_message(message, kwargs)
        self.logger.info(formatted_message)
    
    def warning(self, message: str, **kwargs):
        """Log warning message"""
        formatted_message = self._format_message(message, kwargs)
        self.logger.warning(formatted_message)
    
    def error(self, message: str, **kwargs):
        """Log error message"""
        formatted_message = self._format_message(message, kwargs)
        self.logger.error(formatted_message)
    
    def debug(self, message: str, **kwargs):
        """Log debug message"""
        formatted_message = self._format_message(message, kwargs)
        self.logger.debug(formatted_message)
    
    def critical(self, message: str, **kwargs):
        """Log critical message"""
        formatted_message = self._format_message(message, kwargs)
        self.logger.critical(formatted_message)

class PerformanceLogger:
    """
    Performance monitoring and logging
    """
    
    def __init__(self, logger: StructuredLogger):
        self.logger = logger
    
    def log_system_metrics(self):
        """Log current system metrics"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            self.logger.info(
                "System metrics collected",
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                memory_available_gb=round(memory.available / (1024**3), 2),
                disk_percent=disk.percent,
                disk_free_gb=round(disk.free / (1024**3), 2)
            )
        except Exception as e:
            self.logger.error(f"Failed to collect system metrics: {e}")
    
    def time_function(self, func_name: str = None):
        """Decorator to time function execution"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                function_name = func_name or func.__name__
                
                try:
                    result = func(*args, **kwargs)
                    execution_time = time.time() - start_time
                    
                    self.logger.info(
                        f"Function {function_name} completed successfully",
                        function=function_name,
                        execution_time_seconds=round(execution_time, 4),
                        status="success"
                    )
                    
                    return result
                    
                except Exception as e:
                    execution_time = time.time() - start_time
                    
                    self.logger.error(
                        f"Function {function_name} failed",
                        function=function_name,
                        execution_time_seconds=round(execution_time, 4),
                        status="error",
                        error=str(e)
                    )
                    
                    raise
            
            return wrapper
        return decorator

class PredictionLogger:
    """
    Specialized logger for ML predictions
    """
    
    def __init__(self, logger: StructuredLogger):
        self.logger = logger
    
    def log_prediction_request(self, input_features: Dict[str, Any], request_id: str = None):
        """Log incoming prediction request"""
        self.logger.set_request_id(request_id)
        self.logger.info(
            "Prediction request received",
            input_features=input_features,
            feature_count=len(input_features)
        )
    
    def log_prediction_response(self, prediction: float, model_version: str, 
                              processing_time: float, confidence: float = None):
        """Log prediction response"""
        self.logger.info(
            "Prediction completed",
            prediction=prediction,
            model_version=model_version,
            processing_time_ms=round(processing_time * 1000, 2),
            confidence=confidence
        )
    
    def log_batch_prediction(self, batch_size: int, total_time: float, 
                           avg_time_per_prediction: float):
        """Log batch prediction metrics"""
        self.logger.info(
            "Batch prediction completed",
            batch_size=batch_size,
            total_time_seconds=round(total_time, 4),
            avg_time_per_prediction_ms=round(avg_time_per_prediction * 1000, 2),
            throughput_predictions_per_second=round(batch_size / total_time, 2)
        )
    
    def log_model_load(self, model_name: str, model_version: str, load_time: float):
        """Log model loading"""
        self.logger.info(
            "Model loaded successfully",
            model_name=model_name,
            model_version=model_version,
            load_time_seconds=round(load_time, 4)
        )
    
    def log_model_error(self, error: str, model_name: str = None, model_version: str = None):
        """Log model-related errors"""
        self.logger.error(
            "Model error occurred",
            error=error,
            model_name=model_name,
            model_version=model_version
        )

class DatabaseLogger:
    """
    Database logging for predictions and metrics
    """
    
    def __init__(self, db_path: str = "data/predictions.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database"""
        import sqlite3
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create predictions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS predictions (
                    id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    model_version TEXT NOT NULL,
                    input_features TEXT NOT NULL,
                    prediction REAL NOT NULL,
                    confidence REAL,
                    processing_time_ms REAL NOT NULL,
                    request_source TEXT
                )
            """)
            
            # Create metrics table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    metric_name TEXT NOT NULL,
                    metric_value REAL NOT NULL,
                    tags TEXT
                )
            """)
            
            # Create system_logs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS system_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    level TEXT NOT NULL,
                    logger TEXT NOT NULL,
                    message TEXT NOT NULL,
                    request_id TEXT,
                    extra_data TEXT
                )
            """)
            
            conn.commit()
    
    def log_prediction(self, prediction_id: str, model_version: str, 
                      input_features: Dict[str, Any], prediction: float,
                      processing_time_ms: float, confidence: float = None,
                      request_source: str = None):
        """Log prediction to database"""
        import sqlite3
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO predictions 
                    (id, timestamp, model_version, input_features, prediction, 
                     confidence, processing_time_ms, request_source)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    prediction_id,
                    datetime.utcnow().isoformat() + "Z",
                    model_version,
                    json.dumps(input_features),
                    prediction,
                    confidence,
                    processing_time_ms,
                    request_source
                ))
                conn.commit()
        except Exception as e:
            print(f"Failed to log prediction to database: {e}")
    
    def log_metric(self, metric_name: str, metric_value: float, tags: Dict[str, Any] = None):
        """Log metric to database"""
        import sqlite3
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO metrics (timestamp, metric_name, metric_value, tags)
                    VALUES (?, ?, ?, ?)
                """, (
                    datetime.utcnow().isoformat() + "Z",
                    metric_name,
                    metric_value,
                    json.dumps(tags) if tags else None
                ))
                conn.commit()
        except Exception as e:
            print(f"Failed to log metric to database: {e}")
    
    def get_prediction_stats(self, hours: int = 24) -> Dict[str, Any]:
        """Get prediction statistics for the last N hours"""
        import sqlite3
        from datetime import timedelta
        
        cutoff_time = (datetime.utcnow() - timedelta(hours=hours)).isoformat() + "Z"
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Total predictions
                cursor.execute("""
                    SELECT COUNT(*) FROM predictions 
                    WHERE timestamp > ?
                """, (cutoff_time,))
                total_predictions = cursor.fetchone()[0]
                
                # Average processing time
                cursor.execute("""
                    SELECT AVG(processing_time_ms) FROM predictions 
                    WHERE timestamp > ?
                """, (cutoff_time,))
                avg_processing_time = cursor.fetchone()[0] or 0
                
                # Predictions by model version
                cursor.execute("""
                    SELECT model_version, COUNT(*) FROM predictions 
                    WHERE timestamp > ?
                    GROUP BY model_version
                """, (cutoff_time,))
                by_model_version = dict(cursor.fetchall())
                
                return {
                    "total_predictions": total_predictions,
                    "avg_processing_time_ms": round(avg_processing_time, 2),
                    "predictions_by_model_version": by_model_version,
                    "time_period_hours": hours
                }
        except Exception as e:
            print(f"Failed to get prediction stats: {e}")
            return {}

# Global logger instances
app_logger = StructuredLogger("app")
api_logger = StructuredLogger("api")
model_logger = StructuredLogger("model")
data_logger = StructuredLogger("data")

# Performance logger
performance_logger = PerformanceLogger(app_logger)

# Prediction logger
prediction_logger = PredictionLogger(api_logger)

# Database logger
db_logger = DatabaseLogger()

def get_logger(name: str) -> StructuredLogger:
    """Get a logger instance by name"""
    return StructuredLogger(name)

def setup_logging(config_path: str = None):
    """Setup logging configuration"""
    global app_logger, api_logger, model_logger, data_logger
    
    config_file = config_path or "configs/logging.conf"
    
    app_logger = StructuredLogger("app", config_file)
    api_logger = StructuredLogger("api", config_file)
    model_logger = StructuredLogger("model", config_file)
    data_logger = StructuredLogger("data", config_file)
    
    app_logger.info("Logging system initialized")

# Context manager for request tracking
class RequestContext:
    """Context manager for tracking requests"""
    
    def __init__(self, logger: StructuredLogger, request_id: str = None, **context):
        self.logger = logger
        self.request_id = request_id
        self.context = context
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        self.logger.set_request_id(self.request_id)
        self.logger.set_context(**self.context)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        execution_time = time.time() - self.start_time
        
        if exc_type is None:
            self.logger.info(
                "Request completed successfully",
                execution_time_seconds=round(execution_time, 4)
            )
        else:
            self.logger.error(
                "Request failed",
                execution_time_seconds=round(execution_time, 4),
                error_type=exc_type.__name__,
                error_message=str(exc_val)
            )
        
        self.logger.clear_context()

# Example usage functions
def log_api_request(endpoint: str, method: str, request_id: str = None):
    """Log API request"""
    with RequestContext(api_logger, request_id, endpoint=endpoint, method=method):
        api_logger.info(f"API request to {endpoint}")

def log_model_training(model_name: str, parameters: Dict[str, Any]):
    """Log model training"""
    model_logger.info(
        "Model training started",
        model_name=model_name,
        parameters=parameters
    )

def log_data_processing(dataset_name: str, records_count: int):
    """Log data processing"""
    data_logger.info(
        "Data processing completed",
        dataset_name=dataset_name,
        records_processed=records_count
    )