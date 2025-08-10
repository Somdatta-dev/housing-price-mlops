"""
Model training module with MLflow experiment tracking
"""

import json
import logging
import os
import subprocess
import sys
import threading
import time
from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import mlflow
import mlflow.sklearn
import numpy as np
import pandas as pd
import requests
import seaborn as sns
import yaml
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Lasso, LinearRegression, Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GridSearchCV, cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeRegressor

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_config():
    """Load configuration from config.yaml"""
    config_path = Path(__file__).parent.parent.parent / "configs" / "config.yaml"
    with open(config_path, "r") as file:
        config = yaml.safe_load(file)
    return config


def load_data():
    """
    Load training, validation, and test datasets

    Returns:
        tuple: (X_train, X_val, X_test, y_train, y_val, y_test)
    """
    config = load_config()
    processed_path = Path(config["data"]["processed_data_path"])

    # Load datasets
    train_data = pd.read_csv(processed_path / "train.csv")
    val_data = pd.read_csv(processed_path / "validation.csv")
    test_data = pd.read_csv(processed_path / "test.csv")

    # Separate features and targets
    feature_columns = [col for col in train_data.columns if col != "median_house_value"]

    X_train = train_data[feature_columns]
    y_train = train_data["median_house_value"]

    X_val = val_data[feature_columns]
    y_val = val_data["median_house_value"]

    X_test = test_data[feature_columns]
    y_test = test_data["median_house_value"]

    logger.info(f"Training data shape: {X_train.shape}")
    logger.info(f"Validation data shape: {X_val.shape}")
    logger.info(f"Test data shape: {X_test.shape}")

    return X_train, X_val, X_test, y_train, y_val, y_test


def start_mlflow_server():
    """Start MLflow server in background"""

    def run_server():
        try:
            # Change to project root directory
            os.chdir(Path(__file__).parent.parent.parent)

            # Start MLflow server
            subprocess.run(
                [
                    "mlflow",
                    "server",
                    "--host",
                    "0.0.0.0",
                    "--port",
                    "5000",
                    "--backend-store-uri",
                    "sqlite:///mlflow.db",
                ],
                check=True,
            )
        except Exception as e:
            logger.error(f"Failed to start MLflow server: {e}")

    # Start server in background thread
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    # Wait for server to start
    logger.info("Starting MLflow server...")
    for i in range(30):  # Wait up to 30 seconds
        try:
            response = requests.get("http://localhost:5000/health")
            if response.status_code == 200:
                logger.info("MLflow server started successfully!")
                return True
        except:
            pass
        time.sleep(1)

    logger.warning("MLflow server may not have started properly")
    return False


def setup_mlflow():
    """Setup MLflow tracking"""
    config = load_config()

    # Try to connect to existing server, if not start one
    try:
        response = requests.get("http://localhost:5000/health", timeout=2)
        if response.status_code == 200:
            logger.info("MLflow server already running")
        else:
            start_mlflow_server()
    except:
        logger.info("MLflow server not running, starting...")
        start_mlflow_server()

    # Set tracking URI
    mlflow.set_tracking_uri("http://localhost:5000")

    # Set or create experiment
    experiment_name = config["mlflow"]["experiment_name"]
    try:
        experiment = mlflow.get_experiment_by_name(experiment_name)
        if experiment is None:
            experiment_id = mlflow.create_experiment(experiment_name)
            logger.info(
                f"Created new experiment: {experiment_name} with ID: {experiment_id}"
            )
        else:
            experiment_id = experiment.experiment_id
            logger.info(
                f"Using existing experiment: {experiment_name} with ID: {experiment_id}"
            )
    except Exception as e:
        logger.warning(f"Could not set up MLflow experiment: {e}")
        # Fallback to local file tracking
        logger.info("Falling back to local file tracking")
        mlflow.set_tracking_uri("file:./mlruns")
        experiment_id = "0"  # Default experiment

    mlflow.set_experiment(experiment_name)
    return experiment_id


def evaluate_model(model, X_val, y_val, X_test=None, y_test=None):
    """
    Evaluate model performance

    Args:
        model: Trained model
        X_val: Validation features
        y_val: Validation targets
        X_test: Test features (optional)
        y_test: Test targets (optional)

    Returns:
        dict: Evaluation metrics
    """
    # Validation predictions
    y_val_pred = model.predict(X_val)

    # Calculate validation metrics
    val_rmse = np.sqrt(mean_squared_error(y_val, y_val_pred))
    val_mae = mean_absolute_error(y_val, y_val_pred)
    val_r2 = r2_score(y_val, y_val_pred)

    metrics = {"val_rmse": val_rmse, "val_mae": val_mae, "val_r2": val_r2}

    # Test predictions if test data provided
    if X_test is not None and y_test is not None:
        y_test_pred = model.predict(X_test)
        test_rmse = np.sqrt(mean_squared_error(y_test, y_test_pred))
        test_mae = mean_absolute_error(y_test, y_test_pred)
        test_r2 = r2_score(y_test, y_test_pred)

        metrics.update(
            {"test_rmse": test_rmse, "test_mae": test_mae, "test_r2": test_r2}
        )

    return metrics


def create_feature_importance_plot(model, feature_names, model_name):
    """Create feature importance plot for tree-based models"""
    if hasattr(model, "feature_importances_"):
        # Get feature importances
        importances = model.feature_importances_
        indices = np.argsort(importances)[::-1]

        # Create plot
        plt.figure(figsize=(10, 6))
        plt.title(f"Feature Importance - {model_name}")
        plt.bar(range(len(importances)), importances[indices])
        plt.xticks(
            range(len(importances)), [feature_names[i] for i in indices], rotation=45
        )
        plt.tight_layout()

        # Save plot
        plot_path = f"feature_importance_{model_name.lower().replace(' ', '_')}.png"
        plt.savefig(plot_path)
        plt.close()

        return plot_path
    return None


def train_linear_regression(X_train, y_train, X_val, y_val, X_test, y_test):
    """Train Linear Regression model with hyperparameter tuning"""
    logger.info("Training Linear Regression model...")

    with mlflow.start_run(run_name="Linear_Regression"):
        # Define parameter grid
        param_grid = {"regressor__fit_intercept": [True, False]}

        # Create pipeline with scaling
        pipeline = Pipeline(
            [("scaler", StandardScaler()), ("regressor", LinearRegression())]
        )

        # Grid search
        grid_search = GridSearchCV(
            pipeline, param_grid, cv=5, scoring="neg_mean_squared_error", n_jobs=-1
        )

        # Fit model
        grid_search.fit(X_train, y_train)
        best_model = grid_search.best_estimator_

        # Log parameters
        mlflow.log_params(grid_search.best_params_)
        mlflow.log_param("model_type", "Linear Regression")

        # Evaluate model
        metrics = evaluate_model(best_model, X_val, y_val, X_test, y_test)
        mlflow.log_metrics(metrics)

        # Log model
        mlflow.sklearn.log_model(best_model, "model")

        logger.info(
            f"Linear Regression - Val RMSE: {metrics['val_rmse']:.2f}, Val R²: {metrics['val_r2']:.3f}"
        )

        return best_model, metrics


def train_ridge_regression(X_train, y_train, X_val, y_val, X_test, y_test):
    """Train Ridge Regression model with hyperparameter tuning"""
    logger.info("Training Ridge Regression model...")

    with mlflow.start_run(run_name="Ridge_Regression"):
        # Define parameter grid
        param_grid = {"regressor__alpha": [0.1, 1.0, 10.0, 100.0, 1000.0]}

        # Create pipeline with scaling
        pipeline = Pipeline([("scaler", StandardScaler()), ("regressor", Ridge())])

        # Grid search
        grid_search = GridSearchCV(
            pipeline, param_grid, cv=5, scoring="neg_mean_squared_error", n_jobs=-1
        )

        # Fit model
        grid_search.fit(X_train, y_train)
        best_model = grid_search.best_estimator_

        # Log parameters
        mlflow.log_params(grid_search.best_params_)
        mlflow.log_param("model_type", "Ridge Regression")

        # Evaluate model
        metrics = evaluate_model(best_model, X_val, y_val, X_test, y_test)
        mlflow.log_metrics(metrics)

        # Log model
        mlflow.sklearn.log_model(best_model, "model")

        logger.info(
            f"Ridge Regression - Val RMSE: {metrics['val_rmse']:.2f}, Val R²: {metrics['val_r2']:.3f}"
        )

        return best_model, metrics


def train_random_forest(X_train, y_train, X_val, y_val, X_test, y_test):
    """Train Random Forest model with hyperparameter tuning"""
    logger.info("Training Random Forest model...")

    with mlflow.start_run(run_name="Random_Forest"):
        # Define parameter grid
        param_grid = {
            "n_estimators": [50, 100, 200],
            "max_depth": [10, 20, 30, None],
            "min_samples_split": [2, 5, 10],
            "min_samples_leaf": [1, 2, 4],
        }

        # Create model
        rf = RandomForestRegressor(random_state=42, n_jobs=-1)

        # Grid search
        grid_search = GridSearchCV(
            rf,
            param_grid,
            cv=3,  # Reduced CV for faster training
            scoring="neg_mean_squared_error",
            n_jobs=-1,
        )

        # Fit model
        grid_search.fit(X_train, y_train)
        best_model = grid_search.best_estimator_

        # Log parameters
        mlflow.log_params(grid_search.best_params_)
        mlflow.log_param("model_type", "Random Forest")

        # Evaluate model
        metrics = evaluate_model(best_model, X_val, y_val, X_test, y_test)
        mlflow.log_metrics(metrics)

        # Create and log feature importance plot
        feature_names = X_train.columns.tolist()
        plot_path = create_feature_importance_plot(
            best_model, feature_names, "Random Forest"
        )
        if plot_path:
            mlflow.log_artifact(plot_path)
            os.remove(plot_path)  # Clean up

        # Log model
        mlflow.sklearn.log_model(best_model, "model")

        logger.info(
            f"Random Forest - Val RMSE: {metrics['val_rmse']:.2f}, Val R²: {metrics['val_r2']:.3f}"
        )

        return best_model, metrics


def train_decision_tree(X_train, y_train, X_val, y_val, X_test, y_test):
    """Train Decision Tree model with hyperparameter tuning"""
    logger.info("Training Decision Tree model...")

    with mlflow.start_run(run_name="Decision_Tree"):
        # Define parameter grid
        param_grid = {
            "max_depth": [5, 10, 15, 20, None],
            "min_samples_split": [2, 5, 10, 20],
            "min_samples_leaf": [1, 2, 5, 10],
        }

        # Create model
        dt = DecisionTreeRegressor(random_state=42)

        # Grid search
        grid_search = GridSearchCV(
            dt, param_grid, cv=5, scoring="neg_mean_squared_error", n_jobs=-1
        )

        # Fit model
        grid_search.fit(X_train, y_train)
        best_model = grid_search.best_estimator_

        # Log parameters
        mlflow.log_params(grid_search.best_params_)
        mlflow.log_param("model_type", "Decision Tree")

        # Evaluate model
        metrics = evaluate_model(best_model, X_val, y_val, X_test, y_test)
        mlflow.log_metrics(metrics)

        # Create and log feature importance plot
        feature_names = X_train.columns.tolist()
        plot_path = create_feature_importance_plot(
            best_model, feature_names, "Decision Tree"
        )
        if plot_path:
            mlflow.log_artifact(plot_path)
            os.remove(plot_path)  # Clean up

        # Log model
        mlflow.sklearn.log_model(best_model, "model")

        logger.info(
            f"Decision Tree - Val RMSE: {metrics['val_rmse']:.2f}, Val R²: {metrics['val_r2']:.3f}"
        )

        return best_model, metrics


def compare_models(results):
    """Compare model results and select the best one"""
    logger.info("\n" + "=" * 50)
    logger.info("MODEL COMPARISON RESULTS")
    logger.info("=" * 50)

    best_model = None
    best_score = float("inf")
    best_name = ""

    for name, (model, metrics) in results.items():
        val_rmse = metrics["val_rmse"]
        val_r2 = metrics["val_r2"]

        logger.info(f"{name}:")
        logger.info(f"  Validation RMSE: {val_rmse:.2f}")
        logger.info(f"  Validation R²: {val_r2:.3f}")

        if "test_rmse" in metrics:
            logger.info(f"  Test RMSE: {metrics['test_rmse']:.2f}")
            logger.info(f"  Test R²: {metrics['test_r2']:.3f}")

        logger.info("-" * 30)

        # Select best model based on validation RMSE
        if val_rmse < best_score:
            best_score = val_rmse
            best_model = model
            best_name = name

    logger.info(f"BEST MODEL: {best_name} (RMSE: {best_score:.2f})")
    logger.info("=" * 50)

    return best_model, best_name, best_score


def register_best_model(best_model, best_name, best_score):
    """Register the best model in MLflow Model Registry"""
    config = load_config()
    model_name = config["mlflow"]["model_registry"]["registered_model_name"]

    try:
        # Log the best model with a specific run
        with mlflow.start_run(run_name=f"Best_Model_{best_name}"):
            mlflow.sklearn.log_model(
                best_model, "model", registered_model_name=model_name
            )
            mlflow.log_param("model_type", best_name)
            mlflow.log_metric("best_val_rmse", best_score)

        logger.info(f"Best model registered as: {model_name}")

    except Exception as e:
        logger.error(f"Failed to register model: {e}")


def save_metrics_to_file(results, best_name, best_score):
    """Save metrics to JSON file for DVC tracking"""
    try:
        # Prepare metrics for JSON serialization
        metrics_data = {}
        
        # Add best model info
        metrics_data["best_model"] = {
            "name": best_name,
            "val_rmse": float(best_score)
        }
        
        # Add all model results
        for model_name, (model, metrics) in results.items():
            model_metrics = {}
            for key, value in metrics.items():
                # Convert numpy types to Python types for JSON serialization
                if isinstance(value, (np.integer, np.floating, np.ndarray)):
                    model_metrics[key] = float(value)
                else:
                    model_metrics[key] = value
            
            metrics_data[model_name.lower().replace(" ", "_")] = model_metrics
        
        # Save to JSON file
        with open("metrics.json", "w") as f:
            json.dump(metrics_data, f, indent=2)
        
        logger.info("Metrics saved to metrics.json")
        
    except Exception as e:
        logger.error(f"Failed to save metrics to file: {e}")


def main():
    """Main training function"""
    logger.info("Starting model training pipeline...")

    # Setup MLflow
    experiment_id = setup_mlflow()

    # Load data
    X_train, X_val, X_test, y_train, y_val, y_test = load_data()

    # Train models
    results = {}

    # Linear Regression
    try:
        model, metrics = train_linear_regression(
            X_train, y_train, X_val, y_val, X_test, y_test
        )
        results["Linear Regression"] = (model, metrics)
    except Exception as e:
        logger.error(f"Failed to train Linear Regression: {e}")

    # Ridge Regression
    try:
        model, metrics = train_ridge_regression(
            X_train, y_train, X_val, y_val, X_test, y_test
        )
        results["Ridge Regression"] = (model, metrics)
    except Exception as e:
        logger.error(f"Failed to train Ridge Regression: {e}")

    # Random Forest
    try:
        model, metrics = train_random_forest(
            X_train, y_train, X_val, y_val, X_test, y_test
        )
        results["Random Forest"] = (model, metrics)
    except Exception as e:
        logger.error(f"Failed to train Random Forest: {e}")

    # Decision Tree
    try:
        model, metrics = train_decision_tree(
            X_train, y_train, X_val, y_val, X_test, y_test
        )
        results["Decision Tree"] = (model, metrics)
    except Exception as e:
        logger.error(f"Failed to train Decision Tree: {e}")

    # Compare models and select best
    if results:
        best_model, best_name, best_score = compare_models(results)

        # Save metrics to JSON file for DVC
        save_metrics_to_file(results, best_name, best_score)

        # Register best model
        register_best_model(best_model, best_name, best_score)

        logger.info("Model training pipeline completed successfully!")
        return best_model, results
    else:
        logger.error("No models were trained successfully!")
        return None, {}


if __name__ == "__main__":
    main()
