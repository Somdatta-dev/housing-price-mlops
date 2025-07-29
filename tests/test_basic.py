"""
Basic tests to ensure the CI pipeline works.
"""

import numpy as np
import pandas as pd
import pytest


def test_basic_functionality():
    """Test basic Python functionality."""
    assert 1 + 1 == 2
    assert "hello" == "hello"
    assert [1, 2, 3] == [1, 2, 3]


def test_pandas_functionality():
    """Test pandas functionality."""
    df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
    assert len(df) == 3
    assert list(df.columns) == ["a", "b"]
    assert df["a"].sum() == 6


def test_numpy_functionality():
    """Test numpy functionality."""
    arr = np.array([1, 2, 3, 4, 5])
    assert arr.mean() == 3.0
    assert arr.sum() == 15
    assert len(arr) == 5


def test_sample_data_structure(sample_housing_data):
    """Test the sample housing data fixture."""
    assert isinstance(sample_housing_data, pd.DataFrame)
    assert len(sample_housing_data) == 100

    expected_columns = [
        "MedInc",
        "HouseAge",
        "AveRooms",
        "AveBedrms",
        "Population",
        "AveOccup",
        "Latitude",
        "Longitude",
        "MedHouseVal",
    ]
    assert list(sample_housing_data.columns) == expected_columns


def test_sample_prediction_input(sample_prediction_input):
    """Test the sample prediction input fixture."""
    assert isinstance(sample_prediction_input, dict)
    assert "MedInc" in sample_prediction_input
    assert "Latitude" in sample_prediction_input
    assert "Longitude" in sample_prediction_input

    # Test value ranges
    assert 0 < sample_prediction_input["MedInc"] < 20
    assert 32 < sample_prediction_input["Latitude"] < 42
    assert -125 < sample_prediction_input["Longitude"] < -114


def test_mock_model(mock_model):
    """Test the mock model fixture."""
    # Test single prediction
    X_single = np.array([[1, 2, 3, 4, 5, 6, 7, 8]])
    prediction = mock_model.predict(X_single)
    assert isinstance(prediction, (int, float, np.ndarray))

    # Test multiple predictions
    X_multiple = np.random.rand(10, 8)
    predictions = mock_model.predict(X_multiple)
    assert len(predictions) == 10

    # Test score method
    y_dummy = np.random.rand(10)
    score = mock_model.score(X_multiple, y_dummy)
    assert 0 <= score <= 1


@pytest.mark.parametrize(
    "input_value,expected",
    [
        (1, 2),
        (2, 4),
        (3, 6),
        (0, 0),
        (-1, -2),
    ],
)
def test_parametrized_function(input_value, expected):
    """Test parametrized functionality."""

    def double(x):
        return x * 2

    assert double(input_value) == expected


def test_data_validation():
    """Test data validation logic."""
    # Test valid data
    valid_data = {
        "MedInc": 5.0,
        "HouseAge": 25.0,
        "AveRooms": 6.0,
        "AveBedrms": 1.2,
        "Population": 1000.0,
        "AveOccup": 3.0,
        "Latitude": 37.0,
        "Longitude": -122.0,
    }

    # All values should be numeric
    for key, value in valid_data.items():
        assert isinstance(value, (int, float))

    # Test ranges
    assert 0 < valid_data["MedInc"] < 20
    assert 0 < valid_data["HouseAge"] < 100
    assert 32 < valid_data["Latitude"] < 42
    assert -125 < valid_data["Longitude"] < -114


def test_error_handling():
    """Test error handling."""
    with pytest.raises(ValueError):
        raise ValueError("Test error")

    with pytest.raises(TypeError):
        raise TypeError("Test type error")


def test_environment_setup():
    """Test that the environment is set up correctly."""
    import os
    import sys

    # Test Python version
    assert sys.version_info >= (3, 8)

    # Test that we can import required packages
    try:
        import numpy
        import pandas
        import sklearn

        assert True
    except ImportError:
        pytest.fail("Required packages not installed")


class TestDataProcessing:
    """Test class for data processing functionality."""

    def test_data_loading(self, sample_housing_data):
        """Test data loading functionality."""
        df = sample_housing_data
        assert not df.empty
        assert df.shape[0] > 0
        assert df.shape[1] == 9

    def test_data_cleaning(self, sample_housing_data):
        """Test data cleaning functionality."""
        df = sample_housing_data.copy()

        # Add some NaN values
        df.loc[0, "MedInc"] = np.nan
        df.loc[1, "HouseAge"] = np.nan

        # Test that we can detect NaN values
        assert df.isnull().sum().sum() == 2

        # Test cleaning (drop NaN)
        df_clean = df.dropna()
        assert df_clean.isnull().sum().sum() == 0
        assert len(df_clean) == len(df) - 2

    def test_feature_validation(self, sample_housing_data):
        """Test feature validation."""
        df = sample_housing_data

        # Test that all features are numeric
        numeric_columns = [
            "MedInc",
            "HouseAge",
            "AveRooms",
            "AveBedrms",
            "Population",
            "AveOccup",
            "Latitude",
            "Longitude",
        ]

        for col in numeric_columns:
            assert pd.api.types.is_numeric_dtype(df[col])

        # Test value ranges
        assert df["Latitude"].min() >= 32.0
        assert df["Latitude"].max() <= 42.0
        assert df["Longitude"].min() >= -125.0
        assert df["Longitude"].max() <= -114.0
