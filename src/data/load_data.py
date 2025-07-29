"""
Data loading and initial processing module for Housing Price Prediction
"""

import logging
import os
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from sklearn.datasets import fetch_california_housing
from sklearn.model_selection import train_test_split

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_config():
    """Load configuration from config.yaml"""
    config_path = Path(__file__).parent.parent.parent / "configs" / "config.yaml"
    with open(config_path, "r") as file:
        config = yaml.safe_load(file)
    return config


def download_california_housing_data():
    """
    Download California Housing dataset from sklearn

    Returns:
        tuple: (X, y) features and target
    """
    logger.info("Downloading California Housing dataset...")

    # Fetch the dataset
    housing = fetch_california_housing(as_frame=True)

    # Get features and target
    X = housing.data
    y = housing.target

    logger.info(f"Dataset loaded successfully. Shape: {X.shape}")
    logger.info(f"Features: {list(X.columns)}")
    logger.info(f"Target: {housing.target_names}")

    return X, y, housing


def create_raw_dataset():
    """
    Create and save raw dataset to data/raw/
    """
    config = load_config()

    # Load data
    X, y, housing_info = download_california_housing_data()

    # Combine features and target
    raw_data = X.copy()
    raw_data["median_house_value"] = y

    # Create data directory if it doesn't exist
    raw_data_path = Path(config["data"]["raw_data_path"])
    raw_data_path.mkdir(parents=True, exist_ok=True)

    # Save raw data
    raw_file_path = raw_data_path / "california_housing_raw.csv"
    raw_data.to_csv(raw_file_path, index=False)

    logger.info(f"Raw dataset saved to: {raw_file_path}")

    # Save dataset info
    info_file_path = raw_data_path / "dataset_info.txt"
    with open(info_file_path, "w") as f:
        f.write("California Housing Dataset Information\n")
        f.write("=====================================\n\n")
        f.write(f"Dataset shape: {raw_data.shape}\n")
        f.write(f"Features: {list(X.columns)}\n")
        f.write(f"Target: median_house_value\n\n")
        f.write("Feature Descriptions:\n")
        f.write("- MedInc: median income in block group\n")
        f.write("- HouseAge: median house age in block group\n")
        f.write("- AveRooms: average number of rooms per household\n")
        f.write("- AveBedrms: average number of bedrooms per household\n")
        f.write("- Population: block group population\n")
        f.write("- AveOccup: average number of household members\n")
        f.write("- Latitude: block group latitude\n")
        f.write("- Longitude: block group longitude\n\n")
        f.write("Target Description:\n")
        f.write("- median_house_value: median house value for California districts,\n")
        f.write("  expressed in hundreds of thousands of dollars ($100,000s)\n")

    logger.info(f"Dataset info saved to: {info_file_path}")

    return raw_data


def load_raw_data():
    """
    Load raw data from CSV file

    Returns:
        pd.DataFrame: Raw housing data
    """
    config = load_config()
    raw_file_path = Path(config["data"]["raw_data_path"]) / "california_housing_raw.csv"

    if not raw_file_path.exists():
        logger.warning("Raw data file not found. Creating it...")
        return create_raw_dataset()

    logger.info(f"Loading raw data from: {raw_file_path}")
    data = pd.read_csv(raw_file_path)

    return data


def split_data(data, test_size=0.2, validation_size=0.2, random_state=42):
    """
    Split data into train, validation, and test sets

    Args:
        data (pd.DataFrame): Input data
        test_size (float): Proportion of test set
        validation_size (float): Proportion of validation set from remaining data
        random_state (int): Random seed

    Returns:
        tuple: (X_train, X_val, X_test, y_train, y_val, y_test)
    """
    logger.info("Splitting data into train, validation, and test sets...")

    # Separate features and target
    X = data.drop("median_house_value", axis=1)
    y = data["median_house_value"]

    # First split: separate test set
    X_temp, X_test, y_temp, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=None
    )

    # Second split: separate train and validation from remaining data
    X_train, X_val, y_train, y_val = train_test_split(
        X_temp, y_temp, test_size=validation_size, random_state=random_state
    )

    logger.info(f"Train set shape: {X_train.shape}")
    logger.info(f"Validation set shape: {X_val.shape}")
    logger.info(f"Test set shape: {X_test.shape}")

    return X_train, X_val, X_test, y_train, y_val, y_test


def save_split_data(X_train, X_val, X_test, y_train, y_val, y_test):
    """
    Save split datasets to processed data directory
    """
    config = load_config()
    processed_path = Path(config["data"]["processed_data_path"])
    processed_path.mkdir(parents=True, exist_ok=True)

    # Combine features and targets for each set
    train_data = X_train.copy()
    train_data["median_house_value"] = y_train

    val_data = X_val.copy()
    val_data["median_house_value"] = y_val

    test_data = X_test.copy()
    test_data["median_house_value"] = y_test

    # Save datasets
    train_data.to_csv(processed_path / "train.csv", index=False)
    val_data.to_csv(processed_path / "validation.csv", index=False)
    test_data.to_csv(processed_path / "test.csv", index=False)

    logger.info(f"Split datasets saved to: {processed_path}")


def get_data_summary(data):
    """
    Generate data summary statistics

    Args:
        data (pd.DataFrame): Input data

    Returns:
        dict: Summary statistics
    """
    summary = {
        "shape": data.shape,
        "columns": list(data.columns),
        "dtypes": data.dtypes.to_dict(),
        "missing_values": data.isnull().sum().to_dict(),
        "summary_stats": data.describe().to_dict(),
        "memory_usage": data.memory_usage(deep=True).sum(),
    }

    return summary


def main():
    """
    Main function to load and prepare data
    """
    logger.info("Starting data loading process...")

    # Create raw dataset
    raw_data = create_raw_dataset()

    # Generate summary
    summary = get_data_summary(raw_data)
    logger.info(f"Data summary: {summary['shape']} rows and columns")

    # Split data
    X_train, X_val, X_test, y_train, y_val, y_test = split_data(raw_data)

    # Save split data
    save_split_data(X_train, X_val, X_test, y_train, y_val, y_test)

    logger.info("Data loading and splitting completed successfully!")

    return raw_data, (X_train, X_val, X_test, y_train, y_val, y_test)


if __name__ == "__main__":
    main()
