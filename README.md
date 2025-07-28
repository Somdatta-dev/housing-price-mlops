# Housing Price Prediction MLOps Pipeline

A complete MLOps pipeline for housing price prediction using machine learning best practices, including experiment tracking, containerization, CI/CD, and monitoring.

## 🏠 Project Overview

This project demonstrates a production-ready machine learning pipeline for predicting housing prices using the California Housing dataset. The implementation follows MLOps best practices with comprehensive tracking, deployment, and monitoring capabilities.

## 🎯 Features

- **Data Versioning**: DVC integration for dataset management
- **Experiment Tracking**: MLflow for model versioning and metrics
- **Model Development**: Multiple ML algorithms with hyperparameter tuning
- **REST API**: FastAPI-based prediction service
- **Containerization**: Docker deployment with multi-stage builds
- **CI/CD Pipeline**: GitHub Actions for automated testing and deployment
- **Monitoring**: Comprehensive logging and metrics collection
- **Input Validation**: Pydantic schemas for robust data validation

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

### Docker Deployment

1. **Build the image**
   ```bash
   docker build -t housing-price-api .
   ```

2. **Run the container**
   ```bash
   docker run -p 8000:8000 housing-price-api
   ```

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
│       └── cd.yml
├── data/
│   ├── raw/
│   ├── processed/
│   └── .gitkeep
├── src/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   └── models.py
│   ├── data/
│   │   ├── __init__.py
│   │   └── preprocessing.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── train_model.py
│   └── utils/
│       ├── __init__.py
│       └── logging.py
├── tests/
│   ├── test_api.py
│   ├── test_models.py
│   └── test_preprocessing.py
├── notebooks/
│   └── exploratory_analysis.ipynb
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
├── configs/
│   ├── config.yaml
│   └── logging.conf
├── .dvcignore
├── .gitignore
├── dvc.yaml
├── params.yaml
├── requirements.txt
├── setup.py
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

## 📈 Monitoring

### Metrics Collected

- **Request Metrics**: Count, latency, error rates
- **Model Metrics**: Prediction distribution, confidence scores
- **System Metrics**: CPU, memory, disk usage
- **Business Metrics**: Prediction accuracy over time

### Logging

Structured JSON logging with the following levels:
- **INFO**: Request/response logging
- **WARNING**: Performance degradation
- **ERROR**: Prediction failures
- **DEBUG**: Detailed execution traces

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