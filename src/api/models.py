"""
Pydantic models for API request/response schemas
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator
import uuid

class HousingFeatures(BaseModel):
    """Input schema for housing price prediction with comprehensive validation"""
    
    MedInc: float = Field(
        ..., 
        description="Median income in block group (in tens of thousands of dollars)",
        ge=0.0,
        le=20.0,
        example=8.3252
    )
    HouseAge: float = Field(
        ..., 
        description="Median house age in block group (years)",
        ge=0.0,
        le=100.0,
        example=41.0
    )
    AveRooms: float = Field(
        ..., 
        description="Average number of rooms per household",
        ge=1.0,
        le=50.0,
        example=6.984127
    )
    AveBedrms: float = Field(
        ..., 
        description="Average number of bedrooms per household",
        ge=0.0,
        le=10.0,
        example=1.023810
    )
    Population: float = Field(
        ..., 
        description="Block group population",
        ge=1.0,
        le=50000.0,
        example=322.0
    )
    AveOccup: float = Field(
        ..., 
        description="Average number of household members",
        ge=1.0,
        le=20.0,
        example=2.555556
    )
    Latitude: float = Field(
        ..., 
        description="Block group latitude (degrees)",
        ge=32.0,
        le=42.0,
        example=37.88
    )
    Longitude: float = Field(
        ..., 
        description="Block group longitude (degrees)",
        ge=-125.0,
        le=-114.0,
        example=-122.23
    )
    
    @validator('*', pre=True)
    def validate_numeric(cls, v):
        """Ensure all values are numeric and not None"""
        if v is None:
            raise ValueError("Value cannot be None")
        try:
            return float(v)
        except (ValueError, TypeError):
            raise ValueError("Value must be numeric")
    
    @validator('AveRooms')
    def validate_rooms_reasonable(cls, v, values):
        """Validate that average rooms is reasonable"""
        if 'AveBedrms' in values and values['AveBedrms'] is not None:
            if v < values['AveBedrms']:
                raise ValueError("Average rooms cannot be less than average bedrooms")
        return v
    
    @validator('AveOccup')
    def validate_occupancy_reasonable(cls, v, values):
        """Validate that occupancy is reasonable"""
        if 'Population' in values and 'AveRooms' in values:
            if values['Population'] is not None and values['AveRooms'] is not None:
                # Basic sanity check
                if v > values['Population']:
                    raise ValueError("Average occupancy cannot exceed total population")
        return v

    class Config:
        schema_extra = {
            "example": {
                "MedInc": 8.3252,
                "HouseAge": 41.0,
                "AveRooms": 6.984127,
                "AveBedrms": 1.023810,
                "Population": 322.0,
                "AveOccup": 2.555556,
                "Latitude": 37.88,
                "Longitude": -122.23
            }
        }

class PredictionResponse(BaseModel):
    """Response schema for housing price prediction"""
    
    prediction: float = Field(
        ..., 
        description="Predicted house value in hundreds of thousands of dollars"
    )
    prediction_id: str = Field(
        ..., 
        description="Unique identifier for this prediction"
    )
    model_version: str = Field(
        ..., 
        description="Version of the model used for prediction"
    )
    timestamp: str = Field(
        ..., 
        description="ISO timestamp when prediction was made"
    )
    confidence_score: Optional[float] = Field(
        None, 
        description="Model confidence score (0-1) if available",
        ge=0.0,
        le=1.0
    )
    input_features: Dict[str, float] = Field(
        ..., 
        description="Input features used for prediction"
    )
    processing_time_ms: Optional[float] = Field(
        None,
        description="Time taken to process prediction in milliseconds"
    )

    class Config:
        schema_extra = {
            "example": {
                "prediction": 4.526,
                "prediction_id": "550e8400-e29b-41d4-a716-446655440000",
                "model_version": "1",
                "timestamp": "2025-07-28T12:00:00Z",
                "confidence_score": 0.85,
                "input_features": {
                    "MedInc": 8.3252,
                    "HouseAge": 41.0,
                    "AveRooms": 6.984127,
                    "AveBedrms": 1.023810,
                    "Population": 322.0,
                    "AveOccup": 2.555556,
                    "Latitude": 37.88,
                    "Longitude": -122.23
                },
                "processing_time_ms": 15.2
            }
        }

class BatchPredictionRequest(BaseModel):
    """Request schema for batch predictions"""
    
    instances: List[HousingFeatures] = Field(
        ..., 
        description="List of housing features for batch prediction",
        min_items=1,
        max_items=100
    )
    batch_name: Optional[str] = Field(
        None,
        description="Optional name for the batch",
        max_length=100
    )
    
    @validator('instances')
    def validate_batch_size(cls, v):
        """Validate batch size constraints"""
        if len(v) == 0:
            raise ValueError("At least one instance is required")
        if len(v) > 100:
            raise ValueError("Maximum batch size is 100 instances")
        return v

    class Config:
        schema_extra = {
            "example": {
                "instances": [
                    {
                        "MedInc": 8.3252,
                        "HouseAge": 41.0,
                        "AveRooms": 6.984127,
                        "AveBedrms": 1.023810,
                        "Population": 322.0,
                        "AveOccup": 2.555556,
                        "Latitude": 37.88,
                        "Longitude": -122.23
                    },
                    {
                        "MedInc": 7.2574,
                        "HouseAge": 21.0,
                        "AveRooms": 6.238137,
                        "AveBedrms": 0.971880,
                        "Population": 2401.0,
                        "AveOccup": 2.109842,
                        "Latitude": 37.86,
                        "Longitude": -122.22
                    }
                ],
                "batch_name": "test_batch_1"
            }
        }

class BatchPredictionResponse(BaseModel):
    """Response schema for batch predictions"""
    
    predictions: List[PredictionResponse] = Field(
        ..., 
        description="List of individual predictions"
    )
    batch_id: str = Field(
        ..., 
        description="Unique identifier for this batch"
    )
    batch_name: Optional[str] = Field(
        None,
        description="Name of the batch if provided"
    )
    total_instances: int = Field(
        ..., 
        description="Total number of instances processed"
    )
    successful_predictions: int = Field(
        ...,
        description="Number of successful predictions"
    )
    failed_predictions: int = Field(
        ...,
        description="Number of failed predictions"
    )
    processing_time_seconds: float = Field(
        ..., 
        description="Total processing time in seconds"
    )
    timestamp: str = Field(
        ...,
        description="ISO timestamp when batch was processed"
    )

class HealthResponse(BaseModel):
    """Response schema for health check"""
    
    status: str = Field(
        ..., 
        description="Service status (healthy/unhealthy/degraded)"
    )
    model_loaded: bool = Field(
        ..., 
        description="Whether the ML model is loaded and ready"
    )
    model_version: Optional[str] = Field(
        None, 
        description="Version of the loaded model"
    )
    model_name: Optional[str] = Field(
        None,
        description="Name of the loaded model"
    )
    timestamp: str = Field(
        ..., 
        description="ISO timestamp of health check"
    )
    uptime_seconds: float = Field(
        ..., 
        description="Service uptime in seconds"
    )
    memory_usage_mb: Optional[float] = Field(
        None,
        description="Current memory usage in MB"
    )
    cpu_usage_percent: Optional[float] = Field(
        None,
        description="Current CPU usage percentage"
    )

    class Config:
        schema_extra = {
            "example": {
                "status": "healthy",
                "model_loaded": True,
                "model_version": "1",
                "model_name": "HousingPriceModel",
                "timestamp": "2025-07-28T12:00:00Z",
                "uptime_seconds": 3600.5,
                "memory_usage_mb": 256.7,
                "cpu_usage_percent": 15.3
            }
        }

class ModelInfo(BaseModel):
    """Response schema for model information"""
    
    model_name: str = Field(..., description="Name of the model")
    model_version: str = Field(..., description="Version of the model")
    model_type: str = Field(..., description="Type/algorithm of the model")
    loaded_at: str = Field(..., description="ISO timestamp when model was loaded")
    model_size_mb: Optional[float] = Field(None, description="Model size in MB")
    feature_names: List[str] = Field(..., description="List of feature names")
    feature_importances: Optional[Dict[str, float]] = Field(
        None, 
        description="Feature importances (for tree-based models)"
    )
    hyperparameters: Optional[Dict[str, Any]] = Field(
        None,
        description="Model hyperparameters"
    )
    training_metrics: Optional[Dict[str, float]] = Field(
        None,
        description="Training performance metrics"
    )

    class Config:
        schema_extra = {
            "example": {
                "model_name": "HousingPriceModel",
                "model_version": "1",
                "model_type": "RandomForestRegressor",
                "loaded_at": "2025-07-28T12:00:00Z",
                "model_size_mb": 15.7,
                "feature_names": [
                    "MedInc", "HouseAge", "AveRooms", "AveBedrms", 
                    "Population", "AveOccup", "Latitude", "Longitude"
                ],
                "feature_importances": {
                    "MedInc": 0.52,
                    "Latitude": 0.11,
                    "Longitude": 0.10,
                    "HouseAge": 0.09,
                    "AveRooms": 0.08,
                    "Population": 0.04,
                    "AveOccup": 0.03,
                    "AveBedrms": 0.03
                },
                "hyperparameters": {
                    "n_estimators": 100,
                    "max_depth": 20,
                    "min_samples_split": 5,
                    "min_samples_leaf": 2
                },
                "training_metrics": {
                    "val_rmse": 0.53,
                    "val_r2": 0.800,
                    "test_rmse": 0.51,
                    "test_r2": 0.799
                }
            }
        }

class ErrorResponse(BaseModel):
    """Standard error response schema"""
    
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    timestamp: str = Field(..., description="ISO timestamp when error occurred")
    request_id: Optional[str] = Field(None, description="Request identifier for tracking")

    class Config:
        schema_extra = {
            "example": {
                "error": "ValidationError",
                "message": "Invalid input data",
                "details": {
                    "field": "MedInc",
                    "constraint": "must be between 0.0 and 20.0"
                },
                "timestamp": "2025-07-28T12:00:00Z",
                "request_id": "550e8400-e29b-41d4-a716-446655440000"
            }
        }

class ModelReloadResponse(BaseModel):
    """Response schema for model reload operation"""
    
    success: bool = Field(..., description="Whether reload was successful")
    message: str = Field(..., description="Reload status message")
    previous_version: Optional[str] = Field(None, description="Previous model version")
    new_version: Optional[str] = Field(None, description="New model version")
    timestamp: str = Field(..., description="ISO timestamp of reload operation")

    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "Model reloaded successfully",
                "previous_version": "1",
                "new_version": "2",
                "timestamp": "2025-07-28T12:00:00Z"
            }
        }

# Utility functions for creating responses
def create_prediction_response(
    prediction: float,
    model_version: str,
    input_features: Dict[str, float],
    processing_time_ms: Optional[float] = None,
    confidence_score: Optional[float] = None
) -> PredictionResponse:
    """Create a standardized prediction response"""
    return PredictionResponse(
        prediction=prediction,
        prediction_id=str(uuid.uuid4()),
        model_version=model_version,
        timestamp=datetime.utcnow().isoformat() + "Z",
        confidence_score=confidence_score,
        input_features=input_features,
        processing_time_ms=processing_time_ms
    )

def create_error_response(
    error_type: str,
    message: str,
    details: Optional[Dict[str, Any]] = None,
    request_id: Optional[str] = None
) -> ErrorResponse:
    """Create a standardized error response"""
    return ErrorResponse(
        error=error_type,
        message=message,
        details=details,
        timestamp=datetime.utcnow().isoformat() + "Z",
        request_id=request_id or str(uuid.uuid4())
    )