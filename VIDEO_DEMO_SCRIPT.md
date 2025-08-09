# 5-Minute Video Demo Script - Housing Price Prediction MLOps Pipeline

## 🎬 **DEMO STRUCTURE (5 minutes total)**

### **INTRODUCTION (30 seconds)**
"Hello, I'm demonstrating my complete MLOps pipeline for California Housing Price Prediction. This project implements enterprise-grade MLOps practices including data versioning, experiment tracking, API deployment, CI/CD, and monitoring."

---

## **SEGMENT 1: PROJECT OVERVIEW & STRUCTURE (45 seconds)**

### **What to Show:**
1. **GitHub Repository**: Open your GitHub repo page
   - Show clean repository structure
   - Highlight key directories: `src/`, `configs/`, `monitoring/`, `.github/workflows/`
   - Point out comprehensive documentation

2. **Local Project Structure**: Open VS Code/terminal
   ```bash
   tree -L 2  # Or use file explorer
   ```
   - **Mention**: "Well-organized MLOps project with separation of concerns"
   - **Show**: `src/` (data, models, api, utils), `configs/`, `monitoring/`, `tests/`

### **Script**: 
"The project follows MLOps best practices with clear separation between data processing, model training, API service, and monitoring components. Everything is version controlled and documented."

---

## **SEGMENT 2: DATA PIPELINE & DVC (60 seconds)**

### **Commands to Run:**
```bash
# Initialize DVC if needed (first time)
# dvc init --no-scm

# Show DVC pipeline (if dvc.lock exists)
dvc dag 2>/dev/null || echo "Pipeline will be visible after first run"

# Run data loading stage
dvc repro load_data

# Check generated data
ls data/raw/
ls data/processed/
head -5 data/processed/train.csv
```

### **What to Show:**
- DVC pipeline visualization
- Data loading process in action
- Generated train/validation/test splits
- Dataset info file

### **Script**: 
"I've fixed the DVC configuration - the lock file is now properly tracked for reproducibility. The data pipeline uses DVC for versioning and automatically downloads California Housing data, performs train/validation/test splits, and tracks all data artifacts."

---

## **SEGMENT 3: MODEL TRAINING & MLFLOW (75 seconds)**

### **Commands to Run:**
```bash
# Train models
dvc repro train_models

# Start MLflow UI (in background)
mlflow ui --port 5000 &

# Open browser to http://localhost:5000
```

### **What to Show:**
1. **Model Training Process**: Terminal output showing multiple algorithms
2. **MLflow UI**: 
   - Navigate to experiments
   - Show different runs with metrics (RMSE, MAE, R²)
   - Compare model performance
   - Show model artifacts and parameters
   - Demonstrate Model Registry with best model

### **Script**: 
"The training pipeline automatically runs 4 different algorithms - Linear Regression, Ridge, Random Forest, and Decision Tree. MLflow tracks all experiments, parameters, metrics, and artifacts. The best model is automatically registered in the Model Registry."

---

## **SEGMENT 4: MODEL EVALUATION (30 seconds)**

### **Commands to Run:**
```bash
# Run evaluation stage
dvc repro evaluate_models

# Show generated plots
ls plots/
# Open one visualization
```

### **What to Show:**
- Evaluation process running
- Generated plots: residuals, feature importance, prediction distribution
- Evaluation metrics in JSON format

### **Script**: 
"The evaluation stage generates comprehensive metrics and visualizations including residual analysis, feature importance, and prediction distribution plots."

---

## **SEGMENT 5: API DEMONSTRATION (75 seconds)**

### **Commands to Run:**
```bash
# Build and run Docker container
docker build -t housing-api .
docker run -d -p 8000:8000 housing-api

# Test API endpoints
curl http://localhost:8000/health
curl http://localhost:8000/

# Make prediction
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d @examples/sample_request.json

# Open browser to http://localhost:8000/docs
```

### **What to Show:**
1. **Docker Build**: Container being built successfully
2. **API Health Check**: JSON response showing healthy status
3. **Interactive API Documentation**: FastAPI Swagger UI
4. **Live Prediction**: Make a real prediction request
5. **Batch Prediction**: Show batch endpoint capability
6. **Model Info**: Display model metadata endpoint

### **Script**: 
"The API is containerized with Docker and provides RESTful endpoints for predictions. It includes comprehensive input validation, batch processing, health checks, and automatic API documentation."

---

## **SEGMENT 6: CI/CD PIPELINE (45 seconds)**

### **What to Show:**
1. **GitHub Actions**: Open your GitHub repo → Actions tab
   - Show successful CI/CD runs
   - Point out the 3 workflows: CI, CD, Model Retraining
   - Show test results and deployment logs

2. **Docker Hub**: Show your published Docker images
   - Navigate to your Docker Hub repository
   - Show different image tags and build history

### **Script**: 
"The CI/CD pipeline includes 23 jobs across 3 workflows - code quality checks, security scanning, automated testing, and deployment to Docker Hub. Every commit triggers the pipeline ensuring code quality and automated deployment."

---

## **SEGMENT 7: MONITORING & DASHBOARDS (60 seconds)**

### **Commands to Run:**
```bash
# Start monitoring stack
docker-compose -f monitoring/docker-compose.monitoring.yml up -d

# Check services
docker-compose -f monitoring/docker-compose.monitoring.yml ps

# Open monitoring interfaces
```

### **What to Show:**
1. **Prometheus Metrics**: http://localhost:9090
   - Show housing-specific metrics
   - Demonstrate metric queries

2. **Grafana Dashboard**: http://localhost:3000 (admin/admin)
   - Import or show pre-configured dashboard
   - Display API performance metrics
   - Show system resource monitoring
   - Demonstrate alerting rules

3. **API Metrics Endpoint**: http://localhost:8000/metrics
   - Show Prometheus-format metrics

### **Script**: 
"The monitoring stack includes Prometheus for metrics collection and Grafana for visualization. It tracks API performance, model behavior, system resources, and provides real-time alerting capabilities."

---

## **SEGMENT 8: TESTING & QUALITY (30 seconds)**

### **Commands to Run:**
```bash
# Run test suite
pytest tests/ -v --cov=src

# Show test coverage report
```

### **What to Show:**
- Comprehensive test results
- High test coverage percentage
- Different test types (unit, integration, API tests)

### **Script**: 
"The project includes comprehensive testing with high coverage - unit tests, integration tests, and API tests ensuring reliability and maintainability."

---

## **CONCLUSION (30 seconds)**

### **What to Show:**
- Quick recap of architecture diagram (if available)
- Key achievement highlights
- GitHub repository final view

### **Script**: 
"This MLOps pipeline demonstrates production-ready implementation with automated data processing, experiment tracking, containerized deployment, CI/CD automation, and comprehensive monitoring. It exceeds academic requirements and showcases enterprise-grade MLOps practices suitable for real-world applications."

---

## **🎯 DEMO TIPS & PREPARATION**

### **Before Recording:**
1. **Clean up terminals** - Clear history, set readable font size
2. **Close unnecessary applications** - Focus on demo content
3. **Test all commands** - Ensure everything works smoothly
4. **Prepare browser tabs** - Pre-open MLflow UI, Grafana, GitHub
5. **Have backup** - Screenshots ready if services don't start quickly

### **During Recording:**
- **Speak clearly** and explain what you're doing
- **Move cursor slowly** when highlighting code/interfaces  
- **Pause briefly** between segments for clarity
- **Show actual outputs** - don't just mention them
- **Keep energy up** - enthusiasm shows pride in your work

### **Time Management:**
- **Practice once** to ensure 5-minute timing
- **Have a backup plan** - Know what to skip if running long
- **Focus on key features** - Don't get lost in details

### **Key Messages to Emphasize:**
✅ **Production-ready** implementation  
✅ **Comprehensive** MLOps practices  
✅ **Automated** end-to-end pipeline  
✅ **Enterprise-grade** monitoring and deployment  
✅ **Exceeds** academic requirements  

---

## **ALTERNATIVE QUICK COMMANDS (If Short on Time)**

If you need to speed up any segment:

```bash
# Quick pipeline run
dvc repro

# Fast API test
curl -s http://localhost:8000/health | jq

# Quick Docker demo  
docker run --rm -p 8000:8000 housing-api &
sleep 5 && curl http://localhost:8000/
```

**Good luck with your demo! Your implementation is exceptional and will make a great impression.** 🚀
