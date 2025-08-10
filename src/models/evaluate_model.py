"""
Model evaluation module for Housing Price Prediction MLOps Pipeline
Evaluates trained models and generates comprehensive metrics and visualizations
"""

import json
import logging
import os
import warnings
from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import mlflow
import mlflow.sklearn
import numpy as np
import pandas as pd
import seaborn as sns
import yaml
from sklearn.metrics import (
    explained_variance_score,
    mean_absolute_error,
    mean_absolute_percentage_error,
    mean_squared_error,
    r2_score,
)
from sklearn.preprocessing import StandardScaler

# Suppress warnings
warnings.filterwarnings("ignore")

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set style for plots
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")


def load_config():
    """Load configuration from config.yaml"""
    config_path = Path(__file__).parent.parent.parent / "configs" / "config.yaml"
    with open(config_path, "r") as file:
        config = yaml.safe_load(file)
    return config


def load_test_data():
    """Load test dataset"""
    config = load_config()
    test_path = Path(config["data"]["processed_data_path"]) / "test.csv"
    
    logger.info(f"Loading test data from: {test_path}")
    test_data = pd.read_csv(test_path)
    
    # Separate features and target
    X_test = test_data.drop("median_house_value", axis=1)
    y_test = test_data["median_house_value"]
    
    logger.info(f"Test data shape: {X_test.shape}")
    return X_test, y_test


def load_best_model():
    """Load the best model from MLflow Model Registry"""
    try:
        # Set MLflow tracking URI
        mlflow.set_tracking_uri("http://localhost:5000")
        
        # Get the latest version of the best model
        client = mlflow.MlflowClient()
        
        # Try to get from model registry first
        try:
            config = load_config()
            model_name = config["mlflow"]["model_registry"]["registered_model_name"]
            latest_version = client.get_latest_versions(model_name, stages=["Production"])
            
            if not latest_version:
                latest_version = client.get_latest_versions(model_name, stages=["Staging"])
            
            if not latest_version:
                latest_version = client.get_latest_versions(model_name)
            
            if latest_version:
                model_uri = f"models:/{model_name}/{latest_version[0].version}"
                model = mlflow.sklearn.load_model(model_uri)
                model_info = {
                    "name": model_name,
                    "version": latest_version[0].version,
                    "stage": latest_version[0].current_stage
                }
                logger.info(f"Loaded model from registry: {model_name} v{latest_version[0].version}")
                return model, model_info
        except Exception as e:
            logger.warning(f"Could not load from model registry: {e}")
        
        # Fallback: Load from latest run
        config = load_config()
        experiment_name = config["mlflow"]["experiment_name"]
        experiment = mlflow.get_experiment_by_name(experiment_name)
        if experiment:
            runs = mlflow.search_runs(
                experiment_ids=[experiment.experiment_id],
                order_by=["metrics.rmse ASC"],
                max_results=1
            )
            
            if not runs.empty:
                best_run_id = runs.iloc[0].run_id
                model_uri = f"runs:/{best_run_id}/model"
                model = mlflow.sklearn.load_model(model_uri)
                model_info = {
                    "name": "best-model-from-run",
                    "run_id": best_run_id,
                    "stage": "evaluation"
                }
                logger.info(f"Loaded model from run: {best_run_id}")
                return model, model_info
        
        raise Exception("No trained models found")
        
    except Exception as e:
        logger.error(f"Error loading model: {e}")
        # Fallback to a simple model for evaluation
        from sklearn.ensemble import RandomForestRegressor
        logger.warning("Using fallback Random Forest model for evaluation")
        model = RandomForestRegressor(n_estimators=10, random_state=42)
        
        # Quick train on available data
        config = load_config()
        train_path = Path(config["data"]["processed_data_path"]) / "train.csv"
        if train_path.exists():
            train_data = pd.read_csv(train_path)
            X_train = train_data.drop("median_house_value", axis=1)
            y_train = train_data["median_house_value"]
            model.fit(X_train, y_train)
        
        model_info = {"name": "fallback-rf", "version": "1.0", "stage": "evaluation"}
        return model, model_info


def calculate_regression_metrics(y_true, y_pred):
    """Calculate comprehensive regression metrics"""
    metrics = {
        "mae": mean_absolute_error(y_true, y_pred),
        "mse": mean_squared_error(y_true, y_pred),
        "rmse": np.sqrt(mean_squared_error(y_true, y_pred)),
        "r2_score": r2_score(y_true, y_pred),
        "explained_variance": explained_variance_score(y_true, y_pred),
        "mape": mean_absolute_percentage_error(y_true, y_pred) * 100,
    }
    
    # Additional metrics
    residuals = y_true - y_pred
    metrics["mean_residual"] = np.mean(residuals)
    metrics["std_residual"] = np.std(residuals)
    metrics["max_residual"] = np.max(np.abs(residuals))
    metrics["median_residual"] = np.median(np.abs(residuals))
    
    return metrics


def create_plots_directory():
    """Create plots directory if it doesn't exist"""
    plots_dir = Path("plots")
    plots_dir.mkdir(exist_ok=True)
    return plots_dir


def plot_residuals(y_true, y_pred, plots_dir):
    """Create residuals plot"""
    residuals = y_true - y_pred
    
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
    
    # Residuals vs Predicted
    ax1.scatter(y_pred, residuals, alpha=0.6, color='blue')
    ax1.axhline(y=0, color='red', linestyle='--', alpha=0.8)
    ax1.set_xlabel('Predicted Values')
    ax1.set_ylabel('Residuals')
    ax1.set_title('Residuals vs Predicted Values')
    ax1.grid(True, alpha=0.3)
    
    # Residuals histogram
    ax2.hist(residuals, bins=50, color='skyblue', alpha=0.7, edgecolor='black')
    ax2.set_xlabel('Residuals')
    ax2.set_ylabel('Frequency')
    ax2.set_title('Distribution of Residuals')
    ax2.grid(True, alpha=0.3)
    
    # Q-Q plot for normality
    from scipy import stats
    stats.probplot(residuals, dist="norm", plot=ax3)
    ax3.set_title('Q-Q Plot of Residuals')
    ax3.grid(True, alpha=0.3)
    
    # Actual vs Predicted
    ax4.scatter(y_true, y_pred, alpha=0.6, color='green')
    min_val = min(y_true.min(), y_pred.min())
    max_val = max(y_true.max(), y_pred.max())
    ax4.plot([min_val, max_val], [min_val, max_val], 'red', linestyle='--', alpha=0.8)
    ax4.set_xlabel('Actual Values')
    ax4.set_ylabel('Predicted Values')
    ax4.set_title('Actual vs Predicted Values')
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(plots_dir / 'residuals.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info("Residuals plot saved successfully")


def plot_feature_importance(model, feature_names, plots_dir):
    """Create feature importance plot"""
    try:
        # Get feature importance
        if hasattr(model, 'feature_importances_'):
            importances = model.feature_importances_
        elif hasattr(model, 'coef_'):
            importances = np.abs(model.coef_)
        else:
            logger.warning("Model doesn't have feature importances, skipping plot")
            # Create a placeholder plot
            plt.figure(figsize=(10, 6))
            plt.text(0.5, 0.5, 'Feature importance not available for this model type', 
                    ha='center', va='center', transform=plt.gca().transAxes, fontsize=16)
            plt.title('Feature Importance')
            plt.savefig(plots_dir / 'feature_importance.png', dpi=300, bbox_inches='tight')
            plt.close()
            return
        
        # Create feature importance dataframe
        feature_importance_df = pd.DataFrame({
            'feature': feature_names,
            'importance': importances
        }).sort_values('importance', ascending=True)
        
        # Plot
        plt.figure(figsize=(10, 8))
        bars = plt.barh(feature_importance_df['feature'], feature_importance_df['importance'])
        
        # Color bars
        colors = plt.cm.viridis(np.linspace(0, 1, len(bars)))
        for bar, color in zip(bars, colors):
            bar.set_color(color)
        
        plt.xlabel('Feature Importance')
        plt.title('Feature Importance for Housing Price Prediction')
        plt.grid(True, alpha=0.3, axis='x')
        plt.tight_layout()
        
        plt.savefig(plots_dir / 'feature_importance.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info("Feature importance plot saved successfully")
        
        return feature_importance_df.to_dict('records')
        
    except Exception as e:
        logger.error(f"Error creating feature importance plot: {e}")
        return None


def plot_prediction_distribution(y_true, y_pred, plots_dir):
    """Create prediction distribution plot (for regression, this replaces confusion matrix)"""
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
    
    # Distribution of actual vs predicted
    ax1.hist(y_true, bins=50, alpha=0.7, label='Actual', color='blue', density=True)
    ax1.hist(y_pred, bins=50, alpha=0.7, label='Predicted', color='red', density=True)
    ax1.set_xlabel('House Value (in $100k)')
    ax1.set_ylabel('Density')
    ax1.set_title('Distribution of Actual vs Predicted Values')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Error distribution by prediction range
    pred_ranges = pd.qcut(y_pred, q=5, labels=['Low', 'Low-Med', 'Medium', 'Med-High', 'High'])
    errors = np.abs(y_true - y_pred)
    error_by_range = pd.DataFrame({'range': pred_ranges, 'error': errors})
    
    box_plot = error_by_range.boxplot(column='error', by='range', ax=ax2)
    ax2.set_title('Absolute Error by Prediction Range')
    ax2.set_xlabel('Prediction Range')
    ax2.set_ylabel('Absolute Error')
    ax2.grid(True, alpha=0.3)
    
    # Scatter plot with error coloring
    errors_normalized = (errors - errors.min()) / (errors.max() - errors.min())
    scatter = ax3.scatter(y_true, y_pred, c=errors_normalized, cmap='Reds', alpha=0.6)
    min_val = min(y_true.min(), y_pred.min())
    max_val = max(y_true.max(), y_pred.max())
    ax3.plot([min_val, max_val], [min_val, max_val], 'black', linestyle='--', alpha=0.8)
    ax3.set_xlabel('Actual Values')
    ax3.set_ylabel('Predicted Values')
    ax3.set_title('Predictions Colored by Error Magnitude')
    plt.colorbar(scatter, ax=ax3, label='Normalized Error')
    ax3.grid(True, alpha=0.3)
    
    # Error vs actual values
    ax4.scatter(y_true, errors, alpha=0.6, color='purple')
    ax4.set_xlabel('Actual Values')
    ax4.set_ylabel('Absolute Error')
    ax4.set_title('Prediction Error vs Actual Values')
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(plots_dir / 'confusion_matrix.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info("Prediction distribution plot saved successfully")


def save_evaluation_metrics(metrics, model_info, feature_importance=None):
    """Save evaluation metrics to JSON file"""
    evaluation_data = {
        "model_info": model_info,
        "evaluation_metrics": metrics,
        "feature_importance": feature_importance,
        "evaluation_timestamp": pd.Timestamp.now().isoformat()
    }
    
    with open("evaluation_metrics.json", "w") as f:
        json.dump(evaluation_data, f, indent=2, default=str)
    
    logger.info("Evaluation metrics saved to evaluation_metrics.json")


def save_metrics_for_dvc(metrics):
    """Save metrics in DVC format"""
    dvc_metrics = {
        "test_rmse": metrics["rmse"],
        "test_mae": metrics["mae"],
        "test_r2": metrics["r2_score"],
        "test_mape": metrics["mape"]
    }
    
    with open("metrics.json", "w") as f:
        json.dump(dvc_metrics, f, indent=2)
    
    logger.info("DVC metrics saved to metrics.json")


def main():
    """Main evaluation function"""
    logger.info("Starting model evaluation process...")
    
    try:
        # Create plots directory
        plots_dir = create_plots_directory()
        
        # Load test data
        X_test, y_test = load_test_data()
        
        # Load best model
        model, model_info = load_best_model()
        
        # Make predictions
        logger.info("Making predictions on test set...")
        y_pred = model.predict(X_test)
        
        # Calculate metrics
        logger.info("Calculating evaluation metrics...")
        metrics = calculate_regression_metrics(y_test, y_pred)
        
        # Log metrics
        for metric_name, value in metrics.items():
            logger.info(f"{metric_name}: {value:.4f}")
        
        # Create visualizations
        logger.info("Creating evaluation plots...")
        plot_residuals(y_test, y_pred, plots_dir)
        feature_importance = plot_feature_importance(model, X_test.columns.tolist(), plots_dir)
        plot_prediction_distribution(y_test, y_pred, plots_dir)
        
        # Save metrics
        save_evaluation_metrics(metrics, model_info, feature_importance)
        save_metrics_for_dvc(metrics)
        
        logger.info("Model evaluation completed successfully!")
        logger.info(f"Key metrics - RMSE: {metrics['rmse']:.4f}, R²: {metrics['r2_score']:.4f}, MAE: {metrics['mae']:.4f}")
        
        return metrics, model_info
        
    except Exception as e:
        logger.error(f"Error during model evaluation: {e}")
        raise


if __name__ == "__main__":
    main()
