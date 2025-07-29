"""
Tests for the Housing Price Prediction API
"""

import asyncio
import json
import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent / "src"))

from api.main import app
from api.models import HousingFeatures, PredictionResponse

# Create test client
client = TestClient(app)

# Test data
VALID_HOUSING_DATA = {
    "MedInc": 8.3252,
    "HouseAge": 41.0,
    "AveRooms": 6.984127,
    "AveBedrms": 1.023810,
    "Population": 322.0,
    "AveOccup": 2.555556,
    "Latitude": 37.88,
    "Longitude": -122.23,
}

INVALID_HOUSING_DATA = {
    "MedInc": -1.0,  # Invalid: negative income
    "HouseAge": 41.0,
    "AveRooms": 6.984127,
    "AveBedrms": 1.023810,
    "Population": 322.0,
    "AveOccup": 2.555556,
    "Latitude": 37.88,
    "Longitude": -122.23,
}


class TestRootEndpoint:
    """Test the root endpoint"""

    def test_root_endpoint(self):
        """Test root endpoint returns correct information"""
        response = client.get("/")
        assert response.status_code == 200

        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "docs" in data
        assert "health" in data
        assert data["docs"] == "/docs"
        assert data["health"] == "/health"


class TestHealthEndpoint:
    """Test the health check endpoint"""

    def test_health_endpoint_structure(self):
        """Test health endpoint returns correct structure"""
        response = client.get("/health")
        assert response.status_code == 200

        data = response.json()
        required_fields = ["status", "model_loaded", "timestamp", "uptime_seconds"]

        for field in required_fields:
            assert field in data

        assert isinstance(data["model_loaded"], bool)
        assert isinstance(data["uptime_seconds"], (int, float))
        assert data["status"] in ["healthy", "unhealthy", "degraded"]

    def test_health_endpoint_with_model_loaded(self):
        """Test health endpoint when model is loaded"""
        with patch("api.main.model", Mock()):
            with patch("api.main.model_version", "test_version"):
                response = client.get("/health")
                assert response.status_code == 200

                data = response.json()
                assert data["status"] == "healthy"
                assert data["model_loaded"] is True
                assert data["model_version"] == "test_version"

    def test_health_endpoint_without_model(self):
        """Test health endpoint when model is not loaded"""
        with patch("api.main.model", None):
            response = client.get("/health")
            assert response.status_code == 200

            data = response.json()
            assert data["status"] == "unhealthy"
            assert data["model_loaded"] is False


class TestPredictionEndpoint:
    """Test the prediction endpoint"""

    @patch("api.main.model")
    def test_predict_success(self, mock_model):
        """Test successful prediction"""
        # Mock model prediction
        mock_model.predict.return_value = [4.526]

        response = client.post("/predict", json=VALID_HOUSING_DATA)
        assert response.status_code == 200

        data = response.json()
        required_fields = [
            "prediction",
            "prediction_id",
            "model_version",
            "timestamp",
            "input_features",
        ]

        for field in required_fields:
            assert field in data

        assert isinstance(data["prediction"], (int, float))
        assert isinstance(data["prediction_id"], str)
        assert data["input_features"] == VALID_HOUSING_DATA

    def test_predict_invalid_input(self):
        """Test prediction with invalid input"""
        response = client.post("/predict", json=INVALID_HOUSING_DATA)
        assert response.status_code == 422  # Validation error

    def test_predict_missing_fields(self):
        """Test prediction with missing required fields"""
        incomplete_data = {
            "MedInc": 8.3252,
            "HouseAge": 41.0,
            # Missing other required fields
        }

        response = client.post("/predict", json=incomplete_data)
        assert response.status_code == 422

    def test_predict_model_not_loaded(self):
        """Test prediction when model is not loaded"""
        with patch("api.main.model", None):
            response = client.post("/predict", json=VALID_HOUSING_DATA)
            assert response.status_code == 503

            data = response.json()
            assert "Model not loaded" in data["detail"]

    @patch("api.main.model")
    def test_predict_model_error(self, mock_model):
        """Test prediction when model raises an error"""
        mock_model.predict.side_effect = Exception("Model error")

        response = client.post("/predict", json=VALID_HOUSING_DATA)
        assert response.status_code == 500

        data = response.json()
        assert "Prediction failed" in data["detail"]


class TestBatchPredictionEndpoint:
    """Test the batch prediction endpoint"""

    @patch("api.main.model")
    def test_batch_predict_success(self, mock_model):
        """Test successful batch prediction"""
        # Mock model prediction
        mock_model.predict.return_value = [4.526, 3.875]

        batch_data = {"instances": [VALID_HOUSING_DATA, VALID_HOUSING_DATA]}

        response = client.post("/predict/batch", json=batch_data)
        assert response.status_code == 200

        data = response.json()
        required_fields = [
            "predictions",
            "batch_id",
            "total_instances",
            "processing_time_seconds",
        ]

        for field in required_fields:
            assert field in data

        assert len(data["predictions"]) == 2
        assert data["total_instances"] == 2
        assert isinstance(data["processing_time_seconds"], (int, float))

    def test_batch_predict_empty_list(self):
        """Test batch prediction with empty instances list"""
        batch_data = {"instances": []}

        response = client.post("/predict/batch", json=batch_data)
        assert response.status_code == 422

    def test_batch_predict_too_many_instances(self):
        """Test batch prediction with too many instances"""
        batch_data = {"instances": [VALID_HOUSING_DATA] * 101}  # Exceeds limit of 100

        response = client.post("/predict/batch", json=batch_data)
        assert response.status_code == 422

    def test_batch_predict_model_not_loaded(self):
        """Test batch prediction when model is not loaded"""
        with patch("api.main.model", None):
            batch_data = {"instances": [VALID_HOUSING_DATA]}

            response = client.post("/predict/batch", json=batch_data)
            assert response.status_code == 503


class TestModelInfoEndpoint:
    """Test the model info endpoint"""

    @patch("api.main.model")
    @patch("api.main.model_version", "test_version")
    @patch("api.main.model_name", "TestModel")
    def test_model_info_success(self, mock_model):
        """Test successful model info retrieval"""
        # Mock model with feature importances
        mock_model.feature_importances_ = [0.1, 0.2, 0.15, 0.05, 0.1, 0.05, 0.2, 0.15]
        mock_model.__class__.__name__ = "RandomForestRegressor"

        response = client.get("/model/info")
        assert response.status_code == 200

        data = response.json()
        required_fields = ["model_name", "model_version", "model_type", "loaded_at"]

        for field in required_fields:
            assert field in data

        assert data["model_name"] == "TestModel"
        assert data["model_version"] == "test_version"
        assert data["model_type"] == "RandomForestRegressor"
        assert "feature_importances" in data

    def test_model_info_model_not_loaded(self):
        """Test model info when model is not loaded"""
        with patch("api.main.model", None):
            response = client.get("/model/info")
            assert response.status_code == 503


class TestModelReloadEndpoint:
    """Test the model reload endpoint"""

    @patch("api.main.load_model")
    async def test_model_reload_success(self, mock_load_model):
        """Test successful model reload"""
        mock_load_model.return_value = True

        with patch("api.main.model_version", "new_version"):
            response = client.post("/model/reload")
            assert response.status_code == 200

            data = response.json()
            assert "message" in data
            assert "model_version" in data
            assert "timestamp" in data
            assert "reloaded successfully" in data["message"]

    @patch("api.main.load_model")
    async def test_model_reload_failure(self, mock_load_model):
        """Test failed model reload"""
        mock_load_model.return_value = False

        response = client.post("/model/reload")
        assert response.status_code == 500


class TestInputValidation:
    """Test input validation for housing features"""

    def test_housing_features_validation(self):
        """Test HousingFeatures model validation"""
        # Test valid data
        valid_features = HousingFeatures(**VALID_HOUSING_DATA)
        assert valid_features.MedInc == 8.3252

        # Test invalid data
        with pytest.raises(ValueError):
            HousingFeatures(**INVALID_HOUSING_DATA)

    def test_latitude_longitude_bounds(self):
        """Test latitude and longitude bounds validation"""
        # Invalid latitude (too high)
        invalid_lat_data = VALID_HOUSING_DATA.copy()
        invalid_lat_data["Latitude"] = 50.0

        response = client.post("/predict", json=invalid_lat_data)
        assert response.status_code == 422

        # Invalid longitude (too low)
        invalid_lon_data = VALID_HOUSING_DATA.copy()
        invalid_lon_data["Longitude"] = -130.0

        response = client.post("/predict", json=invalid_lon_data)
        assert response.status_code == 422

    def test_numeric_validation(self):
        """Test that all fields must be numeric"""
        invalid_data = VALID_HOUSING_DATA.copy()
        invalid_data["MedInc"] = "not_a_number"

        response = client.post("/predict", json=invalid_data)
        assert response.status_code == 422


class TestErrorHandling:
    """Test error handling"""

    def test_404_endpoint(self):
        """Test non-existent endpoint returns 404"""
        response = client.get("/nonexistent")
        assert response.status_code == 404

    def test_method_not_allowed(self):
        """Test wrong HTTP method returns 405"""
        response = client.get("/predict")  # Should be POST
        assert response.status_code == 405


class TestCORS:
    """Test CORS configuration"""

    def test_cors_headers(self):
        """Test CORS headers are present"""
        response = client.options("/predict")
        # CORS headers should be present in preflight response
        assert response.status_code in [200, 405]  # Depending on FastAPI version


# Integration tests
class TestIntegration:
    """Integration tests"""

    @patch("api.main.model")
    def test_full_prediction_workflow(self, mock_model):
        """Test complete prediction workflow"""
        mock_model.predict.return_value = [4.526]

        # 1. Check health
        health_response = client.get("/health")
        assert health_response.status_code == 200

        # 2. Make prediction
        pred_response = client.post("/predict", json=VALID_HOUSING_DATA)
        assert pred_response.status_code == 200

        # 3. Get model info
        info_response = client.get("/model/info")
        assert info_response.status_code == 200

        # Verify all responses are consistent
        health_data = health_response.json()
        pred_data = pred_response.json()
        info_data = info_response.json()

        assert health_data["model_loaded"] is True
        assert isinstance(pred_data["prediction"], (int, float))
        assert "model_type" in info_data


if __name__ == "__main__":
    pytest.main([__file__])
