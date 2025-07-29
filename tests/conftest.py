"""
Pytest configuration and fixtures for the housing price prediction tests.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import shutil


@pytest.fixture
def sample_housing_data():
    """Create sample housing data for testing."""
    np.random.seed(42)
    n_samples = 100
    
    data = {
        'MedInc': np.random.uniform(1.0, 15.0, n_samples),
        'HouseAge': np.random.uniform(1.0, 52.0, n_samples),
        'AveRooms': np.random.uniform(3.0, 10.0, n_samples),
        'AveBedrms': np.random.uniform(0.8, 2.0, n_samples),
        'Population': np.random.uniform(100.0, 5000.0, n_samples),
        'AveOccup': np.random.uniform(1.0, 5.0, n_samples),
        'Latitude': np.random.uniform(32.0, 42.0, n_samples),
        'Longitude': np.random.uniform(-125.0, -114.0, n_samples),
        'MedHouseVal': np.random.uniform(0.5, 5.0, n_samples)
    }
    
    return pd.DataFrame(data)


@pytest.fixture
def sample_prediction_input():
    """Create sample input for prediction testing."""
    return {
        "MedInc": 8.3252,
        "HouseAge": 41.0,
        "AveRooms": 6.984127,
        "AveBedrms": 1.023810,
        "Population": 322.0,
        "AveOccup": 2.555556,
        "Latitude": 37.88,
        "Longitude": -122.23
    }


@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for test data."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_model():
    """Create a mock model for testing."""
    class MockModel:
        def predict(self, X):
            # Return dummy predictions
            if hasattr(X, 'shape'):
                return np.random.uniform(1.0, 5.0, X.shape[0])
            else:
                return np.random.uniform(1.0, 5.0, 1)[0]
        
        def score(self, X, y):
            return 0.85
    
    return MockModel()