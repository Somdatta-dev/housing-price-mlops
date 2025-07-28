# Housing Price Prediction MLOps Pipeline

A complete MLOps pipeline for housing price prediction using machine learning best practices, including experiment tracking, containerization, CI/CD, and monitoring.

## 🏠 Project Overview

This project demonstrates a production-ready machine learning pipeline for predicting housing prices using the California Housing dataset. The implementation follows MLOps best practices with comprehensive tracking, deployment, and monitoring capabilities.

## 🎯 Features

- **Data Versioning**: DVC integration for dataset management
- **Experiment Tracking**: MLflow for model versioning and metrics
- **Model Development**: Multiple ML algorithms with hyperparameter tuning
- **REST API**: FastAPI-based prediction service with comprehensive endpoints
- **Containerization**: Docker deployment with multi-stage builds
- **CI/CD Pipeline**: GitHub Actions for automated testing and deployment
- **Monitoring & Logging**: Structured logging, Prometheus metrics, Grafana dashboards
- **Input Validation**: Pydantic schemas for robust data validation
- **Alerting System**: Real-time monitoring with automated alerts
- **Web Dashboard**: Interactive monitoring dashboard with real-time metrics

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Data Source   │───▶│  Data Pipeline  │───▶│   ML Models     │
│  (Housing Data) │    │   (DVC + EDA)   │    │ (MLflow Track)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                        │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Monitoring    │◀───│   REST API      │◀───│  Model Registry │
│ (Logs + Metrics)│    │  (FastAPI)      │    │   (MLflow)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                       ┌─────────────────┐
                       │ Docker Container│
                       │   (Production)  │
                       └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Docker
- Git
- MLflow

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/housing-price-mlops.git
   cd housing-price-mlops
   ```

2. **Set up virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize DVC**
   ```bash
   dvc init
   dvc remote add -d storage gdrive://your-drive-folder-id
   ```

5. **Pull data**
   ```bash
   dvc pull
   ```

### Running the Application

1. **Start MLflow tracking server**
   ```bash
   mlflow server --host 0.0.0.0 --port 5000
   ```

2. **Train models**
   ```bash
   python src/train_model.py
   ```

3. **Start the API**
   ```bash
   uvicorn src.api.main:app --host 0.0.0.0 --port 8000
   ```

4. **Access the application**
   - API Documentation: http://localhost:8000/docs
   - MLflow UI: http://localhost:5000
   - Monitoring Dashboard: http://localhost:3000
   - Prometheus Metrics: http://localhost:8000/metrics

### Docker Deployment

1. **Build the image**
   ```bash
   docker build -t housing-price-api .
   ```

2. **Run the container**
   ```bash
   docker run -p 8000:8000 housing-price-api
   ```

### Complete Monitoring Stack

1. **Start the full monitoring stack**
   ```bash
   python scripts/setup_monitoring.py
   ```

2. **Or use Docker Compose**
   ```bash
   docker-compose -f monitoring/docker-compose.monitoring.yml up -d
   ```

3. **Access monitoring services**
   - Housing API: http://localhost:8000
   - Monitoring Dashboard: http://localhost:3000
   - Grafana: http://localhost:3001 (admin/admin)
   - Prometheus: http://localhost:9090
   - Alertmanager: http://localhost:9093

## 📊 API Usage

### Prediction Endpoint

**POST** `/predict`

```json
{
  "longitude": -122.23,
  "latitude": 37.88,
  "housing_median_age": 41.0,
  "total_rooms": 880.0,
  "total_bedrooms": 129.0,
  "population": 322.0,
  "households": 126.0,
  "median_income": 8.3252
}
```

**Response:**
```json
{
  "prediction": 452600.0,
  "model_version": "1",
  "prediction_id": "uuid-string",
  "timestamp": "2025-07-28T11:50:00Z"
}
```

### Health Check

**GET** `/health`

```json
{
  "status": "healthy",
  "model_loaded": true,
  "version": "1.0.0"
}
```

## 🧪 Model Performance

| Model | RMSE | MAE | R² Score |
|-------|------|-----|----------|
| Linear Regression | 69,000 | 50,000 | 0.64 |
| Random Forest | 49,000 | 35,000 | 0.81 |
| Decision Tree | 55,000 | 40,000 | 0.75 |

*Best Model: Random Forest (registered in MLflow)*

## 📁 Project Structure

```
housing-price-mlops/
├── .github/
│   └── workflows/
│       ├── ci.yml
│       ├── cd.yml
│       └── model-retrain.yml
├── data/
│   ├── raw/
│   ├── processed/
│   ├── external/
│   ├── interim/
│   └── .gitkeep
├── src/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   └── models.py
│   ├── data/
│   │   ├── __init__.py
│   │   └── load_data.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── train_model.py
│   └── utils/
│       ├── __init__.py
│       ├── logging.py
│       ├── monitoring.py
│       ├── prometheus_metrics.py
│       └── dashboard.py
├── tests/
│   ├── test_api.py
│   ├── test_models.py
│   └── test_data.py
├── monitoring/
│   ├── grafana-dashboard.json
│   ├── prometheus.yml
│   ├── alert_rules.yml
│   ├── alertmanager.yml
│   └── docker-compose.monitoring.yml
├── scripts/
│   └── setup_monitoring.py
├── configs/
│   ├── config.yaml
│   └── logging.conf
├── logs/
├── models/
├── .dvcignore
├── .gitignore
├── .dockerignore
├── dvc.yaml
├── params.yaml
├── requirements.txt
├── setup.py
├── Dockerfile
├── Dockerfile.monitoring
├── docker-compose.yml
└── README.md
```

## 🔧 Configuration

### Environment Variables

```bash
# MLflow Configuration
MLFLOW_TRACKING_URI=http://localhost:5000
MLFLOW_EXPERIMENT_NAME=housing-price-prediction

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=INFO

# Model Configuration
MODEL_NAME=housing-price-model
MODEL_STAGE=Production
```

## 🧪 Testing

Run the test suite:

```bash
# Unit tests
pytest tests/ -v

# Coverage report
pytest tests/ --cov=src --cov-report=html

# API tests
pytest tests/test_api.py -v
```

## 📈 Monitoring & Observability

### Comprehensive Monitoring Stack

- **Prometheus**: Metrics collection and alerting
- **Grafana**: Interactive dashboards and visualizations
- **Custom Dashboard**: Real-time monitoring web interface
- **Structured Logging**: JSON-formatted logs with context
- **Database Logging**: Persistent storage of predictions and metrics
- **Health Checks**: Multi-component system health monitoring
- **Alerting**: Automated alerts for system anomalies

### Metrics Collected

- **API Metrics**: Request count, response time, error rates, throughput
- **Model Metrics**: Prediction distribution, inference time, model accuracy
- **System Metrics**: CPU usage, memory usage, disk usage, uptime
- **Business Metrics**: Prediction trends, data quality scores, drift detection
- **Custom Metrics**: Application-specific KPIs and performance indicators

### Monitoring Endpoints

- **Prometheus Metrics**: `GET /metrics` - Prometheus-compatible metrics
- **Health Check**: `GET /health` - Basic service health
- **Detailed Health**: `GET /health/detailed` - Component-level health status
- **Metrics Summary**: `GET /monitoring/metrics/summary` - Aggregated metrics
- **Active Alerts**: `GET /monitoring/alerts` - Current system alerts
- **Dashboard**: `GET /monitoring/dashboard` - Web-based monitoring interface

### Logging Capabilities

- **Structured JSON Logging**: Machine-readable log format
- **Request/Response Logging**: Complete API interaction tracking
- **Prediction Logging**: Model inference tracking with metadata
- **Performance Logging**: Response time and resource usage tracking
- **Error Logging**: Comprehensive error tracking and debugging
- **Database Logging**: Persistent log storage with SQLite
- **Log Rotation**: Automated log management to prevent disk issues

### Alerting System

- **Real-time Monitoring**: Continuous system health assessment
- **Threshold-based Alerts**: Configurable alert conditions
- **Multi-channel Notifications**: Email, webhook, and dashboard alerts
- **Alert Escalation**: Severity-based alert routing
- **Alert History**: Complete audit trail of system events

## 🚀 CI/CD Pipeline

### GitHub Actions Workflows

1. **Continuous Integration** (`.github/workflows/ci.yml`)
   - Code quality checks (flake8, black, isort)
   - Unit tests with coverage
   - Security scanning (bandit, safety)
   - Docker image building

2. **Continuous Deployment** (`.github/workflows/cd.yml`)
   - Deploy to staging environment
   - Run integration tests
   - Deploy to production
   - Notify deployment status

## 🔒 Security

- Input validation with Pydantic schemas
- Container security scanning
- Dependency vulnerability checks
- API rate limiting
- Authentication and authorization (planned)

## 📚 Documentation

- **API Documentation**: Auto-generated with FastAPI/Swagger
- **Code Documentation**: Docstrings following Google style
- **Architecture Documentation**: System design and data flow
- **Deployment Guide**: Step-by-step deployment instructions

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- California Housing Dataset from scikit-learn
- MLflow for experiment tracking
- FastAPI for the web framework
- Docker for containerization
- GitHub Actions for CI/CD

## 📞 Support

For questions and support, please open an issue in the GitHub repository or contact [your-email@example.com].

---

**Project Status**: 🚧 In Development  
**Last Updated**: July 28, 2025  
**Version**: 1.0.0