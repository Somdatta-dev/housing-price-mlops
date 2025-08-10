"""
FastAPI application for Housing Price Prediction
"""

import asyncio
import logging
import os
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import mlflow
import mlflow.sklearn
import numpy as np
import pandas as pd
import uvicorn
import yaml
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import BaseModel, Field, validator

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from utils.dashboard import run_dashboard

# Import monitoring and logging utilities
from utils.logging import get_logger, log_api_request, db_logger
from utils.monitoring import alert_manager, health_checker, metrics_collector
from utils.prometheus_metrics import (
    get_prometheus_content_type,
    get_prometheus_metrics,
    record_prediction_metrics,
    record_request_metrics,
    update_health_status,
)

# Set up structured logging
logger = get_logger(__name__)


def load_config():
    """Load configuration from config.yaml"""
    config_path = Path(__file__).parent.parent.parent / "configs" / "config.yaml"
    with open(config_path, "r") as file:
        config = yaml.safe_load(file)
    return config


# Load configuration
config = load_config()

# Initialize FastAPI app
app = FastAPI(
    title=config["api"]["title"],
    description=config["api"]["description"],
    version=config["api"]["version"],
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config["api"]["cors"]["allow_origins"],
    allow_methods=config["api"]["cors"]["allow_methods"],
    allow_headers=config["api"]["cors"]["allow_headers"],
)


# Add monitoring middleware
@app.middleware("http")
async def monitoring_middleware(request: Request, call_next):
    """Middleware to collect metrics and log requests"""
    start_time = time.time()

    # Process request
    response = await call_next(request)

    # Calculate duration
    duration = time.time() - start_time

    # Extract request info
    method = request.method
    endpoint = str(request.url.path)
    status_code = response.status_code

    # Log API request
    log_api_request(method=method, endpoint=endpoint)

    # Record metrics
    metrics_collector.record_api_request(method, endpoint, status_code, duration)
    record_request_metrics(method, endpoint, status_code, duration)

    return response


# Global variables for model and scaler
model = None
model_version = None
model_name = config["mlflow"]["model_registry"]["registered_model_name"]


class HousingFeatures(BaseModel):
    """Input schema for housing price prediction"""

    MedInc: float = Field(
        ..., description="Median income in block group", ge=0.0, le=20.0, example=8.3252
    )
    HouseAge: float = Field(
        ...,
        description="Median house age in block group",
        ge=0.0,
        le=100.0,
        example=41.0,
    )
    AveRooms: float = Field(
        ...,
        description="Average number of rooms per household",
        ge=1.0,
        le=50.0,
        example=6.984127,
    )
    AveBedrms: float = Field(
        ...,
        description="Average number of bedrooms per household",
        ge=0.0,
        le=10.0,
        example=1.023810,
    )
    Population: float = Field(
        ..., description="Block group population", ge=1.0, le=50000.0, example=322.0
    )
    AveOccup: float = Field(
        ...,
        description="Average number of household members",
        ge=1.0,
        le=20.0,
        example=2.555556,
    )
    Latitude: float = Field(
        ..., description="Block group latitude", ge=32.0, le=42.0, example=37.88
    )
    Longitude: float = Field(
        ..., description="Block group longitude", ge=-125.0, le=-114.0, example=-122.23
    )

    @validator("*", pre=True)
    def validate_numeric(cls, v):
        """Ensure all values are numeric"""
        if v is None:
            raise ValueError("Value cannot be None")
        try:
            return float(v)
        except (ValueError, TypeError):
            raise ValueError("Value must be numeric")


class PredictionResponse(BaseModel):
    """Response schema for housing price prediction"""

    prediction: float = Field(
        ..., description="Predicted house value in hundreds of thousands of dollars"
    )
    prediction_id: str = Field(..., description="Unique identifier for this prediction")
    model_version: str = Field(..., description="Version of the model used")
    timestamp: str = Field(..., description="Timestamp of prediction")
    confidence_interval: Optional[Dict[str, float]] = Field(
        None, description="Confidence interval (if available)"
    )
    input_features: Dict[str, float] = Field(
        ..., description="Input features used for prediction"
    )


class HealthResponse(BaseModel):
    """Response schema for health check"""

    status: str = Field(..., description="Service status")
    model_loaded: bool = Field(..., description="Whether model is loaded")
    model_version: Optional[str] = Field(None, description="Loaded model version")
    timestamp: str = Field(..., description="Health check timestamp")
    uptime_seconds: float = Field(..., description="Service uptime in seconds")


class BatchPredictionRequest(BaseModel):
    """Request schema for batch predictions"""

    instances: List[HousingFeatures] = Field(
        ..., description="List of housing features for batch prediction"
    )

    @validator("instances")
    def validate_batch_size(cls, v):
        if len(v) == 0:
            raise ValueError("At least one instance is required")
        if len(v) > 100:  # Limit batch size
            raise ValueError("Maximum batch size is 100 instances")
        return v


class BatchPredictionResponse(BaseModel):
    """Response schema for batch predictions"""

    predictions: List[PredictionResponse] = Field(
        ..., description="List of predictions"
    )
    batch_id: str = Field(..., description="Unique identifier for this batch")
    total_instances: int = Field(..., description="Total number of instances processed")
    processing_time_seconds: float = Field(..., description="Total processing time")


# Application startup time
startup_time = time.time()


async def load_model():
    """Load the latest model from MLflow Model Registry"""
    global model, model_version

    # Direct model loading from available artifacts (works even without MLflow server)
    try:
        from pathlib import Path
        
        # Find available model artifacts
        models_dir = Path("./mlruns/1/models/")
        if models_dir.exists():
            model_paths = list(models_dir.glob("m-*"))
            if model_paths:
                # Load the first available model (you could implement logic to choose the best one)
                model_path = model_paths[0]
                model_artifact_path = model_path / "artifacts"
                
                model = mlflow.sklearn.load_model(str(model_artifact_path))
                model_version = model_path.name
                
                logger.info(f"Successfully loaded model from {model_artifact_path}")
                logger.info(f"Model type: {type(model).__name__}")
                return True
        
        logger.warning("No model artifacts found in ./mlruns/1/models/")
    except Exception as direct_error:
        logger.warning(f"Direct model loading failed: {direct_error}")

    # Fallback: Try local file-based loading from experiment
    try:
        mlflow.set_tracking_uri("file:./mlruns")
        # Try to load from latest run
        experiment = mlflow.get_experiment_by_name("housing-price-prediction")
        if experiment:
            runs = mlflow.search_runs(experiment_ids=[experiment.experiment_id])
            if not runs.empty:
                latest_run = runs.iloc[0]
                model_uri = f"runs:/{latest_run.run_id}/model"
                model = mlflow.sklearn.load_model(model_uri)
                model_version = "latest"
                logger.info("Loaded model from latest MLflow run")
                return True
        else:
            logger.warning(
                "No 'housing-price-prediction' experiment found in local MLflow"
            )
    except Exception as local_error:
        logger.warning(f"Local model loading failed: {local_error}")

    # Final fallback to MLflow server (if available)
    try:
        import asyncio

        # Set MLflow tracking URI
        mlflow.set_tracking_uri("http://localhost:5000")

        # Load the latest version of the registered model
        client = mlflow.tracking.MlflowClient()

        # Get the latest versions with timeout
        latest_versions = client.get_latest_versions(
            model_name, stages=["None", "Staging", "Production"]
        )

        if not latest_versions:
            logger.error(f"No versions found for model {model_name}")
            return False

        # Use the first available version (could be enhanced to prefer Production > Staging > None)
        model_version_info = latest_versions[0]
        model_version = model_version_info.version

        # Load the model
        model_uri = f"models:/{model_name}/{model_version}"
        model = mlflow.sklearn.load_model(model_uri)

        logger.info(f"Successfully loaded model {model_name} version {model_version}")
        return True

    except Exception as e:
        logger.error(f"MLflow server model loading failed: {e}")

        return False


@app.on_event("startup")
async def startup_event():
    """Initialize the application"""
    logger.info("Starting Housing Price Prediction API...")

    # Initialize monitoring (metrics collector is already initialized)
    logger.info("Metrics collector initialized and ready")

    # Try to load the model (non-blocking)
    try:
        model_loaded = await load_model()
        if not model_loaded:
            logger.warning(
                "Failed to load model. API will start but predictions will fail."
            )
        else:
            logger.info("Model loaded successfully")
    except Exception as e:
        logger.error(f"Error during model loading: {e}")
        logger.warning("API will start without model. Predictions will fail.")

    logger.info("API startup completed successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown"""
    logger.info("Shutting down Housing Price Prediction API...")

    # Stop background monitoring
    metrics_collector.stop_background_collection()

    logger.info("API shutdown completed")


@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint with basic API information"""
    return {
        "message": "Housing Price Prediction API",
        "version": config["api"]["version"],
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    current_time = time.time()
    uptime = current_time - startup_time

    return HealthResponse(
        status="healthy" if model is not None else "unhealthy",
        model_loaded=model is not None,
        model_version=model_version,
        timestamp=datetime.utcnow().isoformat() + "Z",
        uptime_seconds=uptime,
    )


@app.post("/predict", response_model=PredictionResponse)
async def predict_house_price(features: HousingFeatures):
    """Predict house price for a single instance"""

    if model is None:
        raise HTTPException(
            status_code=503,
            detail="Model not loaded. Please check the health endpoint.",
        )

    try:
        # Convert input to DataFrame
        input_data = pd.DataFrame([features.dict()])

        # Make prediction
        start_time = time.time()
        prediction = model.predict(input_data)[0]
        prediction_time = time.time() - start_time

        # Generate unique prediction ID
        prediction_id = str(uuid.uuid4())

        # Log prediction to database and structured logs
        db_logger.log_prediction(
            prediction_id=prediction_id,
            model_version=model_version or "unknown",
            input_features=features.dict(),
            prediction=float(prediction),
            processing_time_ms=prediction_time * 1000,
        )

        # Record metrics
        metrics_collector.record_model_prediction(
            model_name=model_name,
            model_version=model_version or "unknown",
            prediction_time_ms=prediction_time * 1000,
            prediction_value=float(prediction),
        )
        record_prediction_metrics(model_name, float(prediction), prediction_time)

        logger.info(
            f"Prediction {prediction_id}: {prediction:.4f} (took {prediction_time:.4f}s)"
        )

        return PredictionResponse(
            prediction=float(prediction),
            prediction_id=prediction_id,
            model_version=model_version or "unknown",
            timestamp=datetime.utcnow().isoformat() + "Z",
            input_features=features.dict(),
        )

    except Exception as e:
        logger.error(f"Prediction failed: {e}")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


@app.post("/predict/batch", response_model=BatchPredictionResponse)
async def predict_batch(request: BatchPredictionRequest):
    """Predict house prices for multiple instances"""

    if model is None:
        raise HTTPException(
            status_code=503,
            detail="Model not loaded. Please check the health endpoint.",
        )

    try:
        start_time = time.time()
        batch_id = str(uuid.uuid4())
        predictions = []

        # Convert all instances to DataFrame
        input_data = pd.DataFrame([instance.dict() for instance in request.instances])

        # Make batch prediction
        batch_predictions = model.predict(input_data)

        # Create individual prediction responses and log each
        for i, (instance, prediction) in enumerate(
            zip(request.instances, batch_predictions)
        ):
            prediction_id = f"{batch_id}_{i}"

            # Log individual prediction
            db_logger.log_prediction(
                prediction_id=prediction_id,
                model_version=model_version or "unknown",
                input_features=instance.dict(),
                prediction=float(prediction),
                processing_time_ms=0,  # Individual time not tracked in batch
            )

            # Record metrics for each prediction
            record_prediction_metrics(model_name, float(prediction), 0)

            predictions.append(
                PredictionResponse(
                    prediction=float(prediction),
                    prediction_id=prediction_id,
                    model_version=model_version or "unknown",
                    timestamp=datetime.utcnow().isoformat() + "Z",
                    input_features=instance.dict(),
                )
            )

        processing_time = time.time() - start_time

        # Record batch metrics
        for prediction_resp in predictions:
            metrics_collector.record_model_prediction(
                model_name=model_name,
                model_version=model_version or "unknown",
                prediction_time_ms=0,  # Individual time not tracked in batch
                prediction_value=prediction_resp.prediction,
            )

        logger.info(
            f"Batch prediction {batch_id}: {len(predictions)} instances processed in {processing_time:.4f}s"
        )

        return BatchPredictionResponse(
            predictions=predictions,
            batch_id=batch_id,
            total_instances=len(predictions),
            processing_time_seconds=processing_time,
        )

    except Exception as e:
        logger.error(f"Batch prediction failed: {e}")
        raise HTTPException(
            status_code=500, detail=f"Batch prediction failed: {str(e)}"
        )


@app.get("/model/info")
async def get_model_info():
    """Get information about the loaded model"""

    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    try:
        # Get model metadata
        model_info = {
            "model_name": model_name,
            "model_version": model_version,
            "model_type": type(model).__name__,
            "loaded_at": datetime.utcnow().isoformat() + "Z",
        }

        # Add model-specific information if available
        if hasattr(model, "feature_importances_"):
            # For tree-based models
            feature_names = [
                "MedInc",
                "HouseAge",
                "AveRooms",
                "AveBedrms",
                "Population",
                "AveOccup",
                "Latitude",
                "Longitude",
            ]
            importances = model.feature_importances_
            # Handle both numpy arrays and lists
            if hasattr(importances, "tolist"):
                importances_list = importances.tolist()
            else:
                importances_list = list(importances)
            model_info["feature_importances"] = dict(
                zip(feature_names, importances_list)
            )

        if hasattr(model, "n_estimators"):
            model_info["n_estimators"] = model.n_estimators

        if hasattr(model, "max_depth"):
            model_info["max_depth"] = model.max_depth

        return model_info

    except Exception as e:
        logger.error(f"Failed to get model info: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get model info: {str(e)}"
        )


@app.post("/model/reload")
async def reload_model():
    """Reload the model from MLflow Model Registry"""

    try:
        success = await load_model()

        if success:
            return {
                "message": "Model reloaded successfully",
                "model_version": model_version,
                "timestamp": datetime.utcnow().isoformat() + "Z",
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to reload model")

    except Exception as e:
        logger.error(f"Model reload failed: {e}")
        raise HTTPException(status_code=500, detail=f"Model reload failed: {str(e)}")


# Monitoring and Metrics Endpoints


@app.get("/metrics")
async def prometheus_metrics():
    """Prometheus metrics endpoint"""
    metrics_data = get_prometheus_metrics()
    return PlainTextResponse(
        content=metrics_data, media_type=get_prometheus_content_type()
    )


@app.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check with component status"""
    health_status = health_checker.run_health_checks()

    # Update Prometheus health metrics
    update_health_status(health_status)

    return health_status


@app.get("/monitoring/dashboard")
async def monitoring_dashboard():
    """Redirect to monitoring dashboard"""
    return {
        "message": "Monitoring dashboard available",
        "dashboard_url": "http://localhost:3000",
        "note": "Start dashboard with: python -m src.utils.dashboard",
    }


@app.get("/monitoring/metrics/summary")
async def metrics_summary():
    """Get metrics summary"""
    summary = metrics_collector.get_metrics_summary(24)
    return summary


@app.get("/monitoring/alerts")
async def active_alerts():
    """Get active alerts"""
    alerts = list(alert_manager.active_alerts.values())
    return {"alerts": alerts, "count": len(alerts)}


@app.post("/monitoring/alerts/test")
async def test_alert():
    """Test alert system"""
    test_alert = {
        "name": "test_alert",
        "metric_name": "test_metric",
        "threshold": 100,
        "current_value": 150,
        "severity": "warning",
    }

    alert_manager.trigger_alert(**test_alert)

    return {"message": "Test alert triggered", "alert": test_alert}


# Error handlers
@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    return JSONResponse(
        status_code=400, content={"detail": f"Invalid input: {str(exc)}"}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


def main():
    """Main function to run the API"""
    uvicorn.run(
        "main:app",
        host=config["api"]["host"],
        port=config["api"]["port"],
        reload=config["api"]["reload"],
        log_level="info",
    )


if __name__ == "__main__":
    main()
