# Docker Deployment Guide - Housing Price Prediction MLOps

This comprehensive guide covers all aspects of Docker deployment for the Housing Price Prediction MLOps pipeline, including local deployment, Docker Hub publishing, and production strategies.

## 📋 Table of Contents

- [Prerequisites](#prerequisites)
- [Local Docker Deployment](#local-docker-deployment)
- [Docker Hub Publishing](#docker-hub-publishing)
- [Automated Docker Hub Deployment](#automated-docker-hub-deployment)
- [Manual Docker Hub Deployment](#manual-docker-hub-deployment)
- [Production Deployment Strategies](#production-deployment-strategies)
- [Docker Compose Configurations](#docker-compose-configurations)
- [Troubleshooting](#troubleshooting)
- [Best Practices](#best-practices)

## 🔧 Prerequisites

### System Requirements
- **Docker**: Version 20.10+ (latest recommended)
- **Docker Compose**: Version 2.0+ (latest recommended)
- **System Resources**: 
  - 4GB+ RAM (8GB recommended for full monitoring stack)
  - 10GB+ free disk space
  - Multi-core CPU (for optimal performance)

### Docker Hub Account
- Create account at [hub.docker.com](https://hub.docker.com)
- Verify email address
- Optional: Create access token for enhanced security

### Installation Verification
```bash
# Check Docker installation
docker --version
# Expected: Docker version 20.10.x or higher

# Check Docker Compose
docker-compose --version
# Expected: Docker Compose version 2.x.x or higher

# Verify Docker is running
docker info
# Should show system information without errors

# Test Docker functionality
docker run hello-world
# Should download and run successfully
```

## 🏠 Local Docker Deployment

### Building the Docker Image

#### Basic Build
```bash
# Navigate to project directory
cd housing-price-mlops

# Build with default tag
docker build -t housing-price-api .

# Build with specific tag
docker build -t housing-price-api:v1.0.0 .

# Build with custom name
docker build -t my-housing-api:latest .
```

#### Advanced Build Options
```bash
# Build with build arguments
docker build \
  --build-arg PYTHON_VERSION=3.9 \
  --build-arg APP_ENV=production \
  -t housing-price-api:production .

# Build without cache (clean build)
docker build --no-cache -t housing-price-api:latest .

# Build for specific platform
docker build --platform linux/amd64 -t housing-price-api:amd64 .
docker build --platform linux/arm64 -t housing-price-api:arm64 .

# Multi-platform build
docker buildx build --platform linux/amd64,linux/arm64 -t housing-price-api:multi .
```

### Running the Container

#### Basic Container Operations
```bash
# Run in detached mode with port mapping
docker run -d -p 8000:8000 --name housing-api housing-price-api:latest

# Run with custom name and restart policy
docker run -d \
  -p 8000:8000 \
  --name my-housing-service \
  --restart unless-stopped \
  housing-price-api:latest

# Run with environment variables
docker run -d \
  -p 8000:8000 \
  -e LOG_LEVEL=DEBUG \
  -e API_HOST=0.0.0.0 \
  -e MLFLOW_TRACKING_URI=http://host.docker.internal:5000 \
  --name housing-api \
  housing-price-api:latest

# Run with volume mounts for persistence
docker run -d \
  -p 8000:8000 \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/mlruns:/app/mlruns \
  -v $(pwd)/data:/app/data \
  --name housing-api \
  housing-price-api:latest
```

#### Container Management
```bash
# List running containers
docker ps

# List all containers (including stopped)
docker ps -a

# View container logs
docker logs housing-api

# Follow logs in real-time
docker logs -f housing-api

# View last 100 log lines
docker logs --tail 100 housing-api

# Execute commands inside running container
docker exec -it housing-api /bin/bash

# Copy files to/from container
docker cp local-file.txt housing-api:/app/
docker cp housing-api:/app/logs/app.log ./local-logs/

# Stop container gracefully
docker stop housing-api

# Force stop container
docker kill housing-api

# Start stopped container
docker start housing-api

# Restart container
docker restart housing-api

# Remove container
docker rm housing-api

# Remove container forcefully
docker rm -f housing-api
```

### Testing the Dockerized API

#### Health Checks
```bash
# Basic health check
curl http://localhost:8000/health

# Detailed health check
curl http://localhost:8000/health/detailed | jq '.'

# API information
curl http://localhost:8000/ | jq '.'
```

#### API Testing
```bash
# Test single prediction
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "MedInc": 8.3252,
    "HouseAge": 41.0,
    "AveRooms": 6.984127,
    "AveBedrms": 1.023810,
    "Population": 322.0,
    "AveOccup": 2.555556,
    "Latitude": 37.88,
    "Longitude": -122.23
  }' | jq '.'

# Test batch prediction
curl -X POST http://localhost:8000/predict/batch \
  -H "Content-Type: application/json" \
  -d '{
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
      }
    ]
  }' | jq '.'

# Test model information
curl http://localhost:8000/model/info | jq '.'

# Test Prometheus metrics
curl http://localhost:8000/metrics
```

## 🐳 Docker Hub Publishing

### Overview

Docker Hub is the world's largest repository of container images. Publishing your image to Docker Hub allows:
- **Global Access**: Anyone can pull and run your image
- **Version Control**: Tag-based versioning system
- **Automated Builds**: Integration with GitHub for automatic builds
- **Team Collaboration**: Share images with team members
- **Production Deployment**: Deploy to cloud platforms directly from Docker Hub

## 🤖 Automated Docker Hub Deployment

### Using the Automated Script

We've created a PowerShell script that handles the entire Docker Hub deployment process automatically.

#### Script Features
- ✅ **Validation**: Checks if local image exists
- ✅ **Tagging**: Properly tags image for Docker Hub
- ✅ **Authentication**: Handles Docker Hub login
- ✅ **Publishing**: Pushes image to Docker Hub
- ✅ **Verification**: Confirms successful deployment
- ✅ **Instructions**: Provides usage commands

#### Using the Script

1. **Make sure your image is built**:
   ```bash
   docker build -t housing-price-api:latest .
   ```

2. **Run the automated script**:
   ```powershell
   # Replace 'yourusername' with your actual Docker Hub username
   .\push-to-dockerhub.ps1 yourusername
   ```

3. **Follow the prompts**:
   - Enter Docker Hub credentials when prompted
   - Wait for the upload to complete
   - Note the provided Docker Hub URL

#### Script Output Example
```
🐳 Starting Docker Hub push process...
📋 Checking if local image exists...
✅ Local image found: housing-price-api:latest
🏷️  Tagging image for Docker Hub...
✅ Successfully tagged as: yourusername/housing-price-api:latest
🔐 Checking Docker Hub login...
Please login to Docker Hub when prompted:
Login Succeeded
🚀 Pushing image to Docker Hub...
This may take a few minutes depending on your internet connection...
🎉 Successfully pushed to Docker Hub!
Your image is now available at: https://hub.docker.com/r/yourusername/housing-price-api

To pull and run your image from anywhere:
docker pull yourusername/housing-price-api:latest
docker run -p 8000:8000 yourusername/housing-price-api:latest

📊 Image details:
REPOSITORY                        TAG       IMAGE ID       CREATED         SIZE
yourusername/housing-price-api   latest    25a0516b2137   10 minutes ago  2.89GB
```

#### Script Customization

You can modify the script for additional features:

```powershell
# Add version tagging
param(
    [Parameter(Mandatory=$true)]
    [string]$DockerHubUsername,
    [string]$Version = "latest"
)

# Tag with version
docker tag housing-price-api:latest "$DockerHubUsername/housing-price-api:$Version"
docker push "$DockerHubUsername/housing-price-api:$Version"
```

## 🔧 Manual Docker Hub Deployment

### Step-by-Step Manual Process

#### Step 1: Docker Hub Authentication

```bash
# Login to Docker Hub
docker login

# Enter your credentials when prompted:
# Username: yourusername
# Password: your-password-or-token

# Verify login
docker info | grep Username
```

#### Step 2: Image Tagging

```bash
# Tag your local image for Docker Hub
# Format: docker tag local-image:tag username/repository:tag

# Basic tagging
docker tag housing-price-api:latest yourusername/housing-price-api:latest

# Multiple tags for the same image
docker tag housing-price-api:latest yourusername/housing-price-api:v1.0.0
docker tag housing-price-api:latest yourusername/housing-price-api:stable
docker tag housing-price-api:latest yourusername/housing-price-api:production

# Verify tags
docker images yourusername/housing-price-api
```

#### Step 3: Publishing to Docker Hub

```bash
# Push specific tag
docker push yourusername/housing-price-api:latest

# Push specific version
docker push yourusername/housing-price-api:v1.0.0

# Push all tags for the repository
docker push yourusername/housing-price-api --all-tags
```

#### Step 4: Verification

```bash
# Verify the push was successful
docker search yourusername/housing-price-api

# Or visit Docker Hub directly
# https://hub.docker.com/r/yourusername/housing-price-api
```

### Advanced Manual Deployment

#### Multi-Architecture Builds

```bash
# Create and use buildx builder
docker buildx create --name multiarch-builder --use

# Build for multiple architectures
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t yourusername/housing-price-api:multiarch \
  --push .

# Verify multi-arch image
docker buildx imagetools inspect yourusername/housing-price-api:multiarch
```

#### Semantic Versioning

```bash
# Build with semantic version
VERSION="1.2.3"
docker build -t housing-price-api:$VERSION .

# Tag for Docker Hub with semantic versioning
docker tag housing-price-api:$VERSION yourusername/housing-price-api:$VERSION
docker tag housing-price-api:$VERSION yourusername/housing-price-api:1.2
docker tag housing-price-api:$VERSION yourusername/housing-price-api:1
docker tag housing-price-api:$VERSION yourusername/housing-price-api:latest

# Push all versions
docker push yourusername/housing-price-api:$VERSION
docker push yourusername/housing-price-api:1.2
docker push yourusername/housing-price-api:1
docker push yourusername/housing-price-api:latest
```

#### Private Repository Setup

```bash
# Create private repository on Docker Hub first
# Then push as normal
docker tag housing-price-api:latest yourusername/private-housing-api:latest
docker push yourusername/private-housing-api:latest

# Pull from private repository (requires authentication)
docker login
docker pull yourusername/private-housing-api:latest
```

## 🚀 Production Deployment Strategies

### Cloud Platform Deployment

#### AWS ECS (Elastic Container Service)

```bash
# Create ECS task definition
aws ecs register-task-definition \
  --family housing-price-api \
  --network-mode awsvpc \
  --requires-compatibilities FARGATE \
  --cpu 1024 \
  --memory 2048 \
  --container-definitions '[
    {
      "name": "housing-api",
      "image": "yourusername/housing-price-api:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "essential": true,
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/housing-price-api",
          "awslogs-region": "us-west-2",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]'

# Create ECS service
aws ecs create-service \
  --cluster your-cluster \
  --service-name housing-price-api \
  --task-definition housing-price-api:1 \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration 'awsvpcConfiguration={subnets=[subnet-12345],securityGroups=[sg-12345],assignPublicIp=ENABLED}'
```

#### Google Cloud Run

```bash
# Deploy to Cloud Run
gcloud run deploy housing-price-api \
  --image yourusername/housing-price-api:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8000 \
  --memory 2Gi \
  --cpu 1 \
  --max-instances 10
```

#### Azure Container Instances

```bash
# Deploy to Azure Container Instances
az container create \
  --resource-group myResourceGroup \
  --name housing-price-api \
  --image yourusername/housing-price-api:latest \
  --dns-name-label housing-api-unique \
  --ports 8000 \
  --memory 2 \
  --cpu 1
```

### Kubernetes Deployment

#### Basic Kubernetes Manifests

Create `k8s/deployment.yaml`:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: housing-price-api
  labels:
    app: housing-price-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: housing-price-api
  template:
    metadata:
      labels:
        app: housing-price-api
    spec:
      containers:
      - name: housing-api
        image: yourusername/housing-price-api:latest
        ports:
        - containerPort: 8000
        env:
        - name: LOG_LEVEL
          value: "INFO"
        - name: API_HOST
          value: "0.0.0.0"
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: housing-price-api-service
spec:
  selector:
    app: housing-price-api
  ports:
    - protocol: TCP
      port: 80
      targetPort: 8000
  type: LoadBalancer
```

Deploy to Kubernetes:
```bash
# Apply the deployment
kubectl apply -f k8s/deployment.yaml

# Check deployment status
kubectl get deployments
kubectl get pods
kubectl get services

# Get external IP
kubectl get service housing-price-api-service
```

## 🐙 Docker Compose Configurations

### Development Environment

Create `docker-compose.dev.yml`:
```yaml
version: '3.8'

services:
  housing-api:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - LOG_LEVEL=DEBUG
      - API_HOST=0.0.0.0
      - MLFLOW_TRACKING_URI=http://mlflow:5000
    volumes:
      - ./src:/app/src
      - ./logs:/app/logs
      - ./mlruns:/app/mlruns
    depends_on:
      - mlflow
    restart: unless-stopped

  mlflow:
    image: python:3.9-slim
    ports:
      - "5000:5000"
    volumes:
      - ./mlruns:/app/mlruns
    working_dir: /app
    command: >
      bash -c "
        pip install mlflow==2.5.0 &&
        mlflow server 
        --host 0.0.0.0 
        --port 5000 
        --backend-store-uri file:///app/mlruns
      "
    restart: unless-stopped

networks:
  default:
    name: housing-dev-network
```

### Production Environment

Create `docker-compose.prod.yml`:
```yaml
version: '3.8'

services:
  housing-api:
    image: yourusername/housing-price-api:latest
    ports:
      - "8000:8000"
    environment:
      - LOG_LEVEL=INFO
      - API_HOST=0.0.0.0
      - API_PORT=8000
      - MLFLOW_TRACKING_URI=http://mlflow:5000
    volumes:
      - housing_logs:/app/logs
      - housing_mlruns:/app/mlruns
    depends_on:
      - mlflow
      - prometheus
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  mlflow:
    image: python:3.9-slim
    ports:
      - "5000:5000"
    volumes:
      - housing_mlruns:/app/mlruns
    working_dir: /app
    command: >
      bash -c "
        pip install mlflow==2.5.0 &&
        mlflow server 
        --host 0.0.0.0 
        --port 5000 
        --backend-store-uri file:///app/mlruns
      "
    restart: unless-stopped

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana-dashboard.json:/var/lib/grafana/dashboards/housing-dashboard.json
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
    depends_on:
      - housing-api
    restart: unless-stopped

volumes:
  housing_logs:
  housing_mlruns:
  prometheus_data:
  grafana_data:

networks:
  default:
    name: housing-prod-network
```

### Usage Commands

```bash
# Development environment
docker-compose -f docker-compose.dev.yml up -d
docker-compose -f docker-compose.dev.yml logs -f

# Production environment
docker-compose -f docker-compose.prod.yml up -d
docker-compose -f docker-compose.prod.yml ps
docker-compose -f docker-compose.prod.yml down

# Scale services
docker-compose -f docker-compose.prod.yml up -d --scale housing-api=3
```

## 🔧 Troubleshooting

### Common Issues and Solutions

#### Issue: Docker Build Fails

**Symptoms:**
```
ERROR [6/9] COPY . .
failed to compute cache key: failed to walk /var/lib/docker/tmp/buildkit-mount123456: lstat /var/lib/docker/tmp/buildkit-mount123456/node_modules: permission denied
```

**Solutions:**
```bash
# Solution 1: Clean Docker cache
docker system prune -f
docker builder prune -f

# Solution 2: Check .dockerignore file
echo "node_modules" >> .dockerignore
echo "__pycache__" >> .dockerignore
echo "*.pyc" >> .dockerignore

# Solution 3: Build without cache
docker build --no-cache -t housing-price-api .

# Solution 4: Fix file permissions
sudo chown -R $USER:$USER .
```

#### Issue: Container Exits Immediately

**Symptoms:**
```bash
docker ps -a
# Shows container with status "Exited (1) 2 seconds ago"
```

**Solutions:**
```bash
# Check container logs
docker logs housing-api

# Common fixes:
# 1. Check if port is already in use
lsof -i :8000
sudo kill -9 $(lsof -t -i:8000)

# 2. Run with interactive mode for debugging
docker run -it housing-price-api:latest /bin/bash

# 3. Check environment variables
docker run -e LOG_LEVEL=DEBUG housing-price-api:latest

# 4. Verify Python dependencies
docker run housing-price-api:latest pip list
```

#### Issue: Cannot Connect to API

**Symptoms:**
```bash
curl http://localhost:8000/health
# curl: (7) Failed to connect to localhost port 8000: Connection refused
```

**Solutions:**
```bash
# Check if container is running
docker ps

# Check port mapping
docker port housing-api

# Check container logs
docker logs housing-api

# Test from inside container
docker exec -it housing-api curl http://localhost:8000/health

# Check firewall settings (Linux)
sudo ufw status
sudo ufw allow 8000

# Check Docker network
docker network ls
docker network inspect bridge
```

#### Issue: Docker Hub Push Fails

**Symptoms:**
```
denied: requested access to the resource is denied
```

**Solutions:**
```bash
# Solution 1: Re-authenticate
docker logout
docker login

# Solution 2: Check repository name
docker tag housing-price-api:latest yourusername/housing-price-api:latest
# Make sure 'yourusername' matches your Docker Hub username

# Solution 3: Create repository on Docker Hub first
# Visit https://hub.docker.com and create repository manually

# Solution 4: Check image size (Docker Hub has limits)
docker images housing-price-api:latest
# If > 10GB, optimize your Dockerfile
```

#### Issue: Out of Disk Space

**Symptoms:**
```
no space left on device
```

**Solutions:**
```bash
# Check Docker disk usage
docker system df

# Clean up unused resources
docker system prune -f

# Remove unused images
docker image prune -f

# Remove unused volumes
docker volume prune -f

# Remove unused networks
docker network prune -f

# Complete cleanup (WARNING: removes everything)
docker system prune -a -f --volumes
```

#### Issue: Container Performance Issues

**Symptoms:**
- Slow API responses
- High memory usage
- CPU throttling

**Solutions:**
```bash
# Monitor container resources
docker stats housing-api

# Increase container resources
docker run -d \
  -p 8000:8000 \
  --memory=4g \
  --cpus=2 \
  --name housing-api \
  housing-price-api:latest

# Check for memory leaks
docker exec housing-api ps aux
docker exec housing-api free -h

# Optimize Dockerfile
# Use multi-stage builds
# Minimize layer count
# Use .dockerignore effectively
```

### Debugging Tools and Commands

```bash
# Container inspection
docker inspect housing-api

# Execute shell in running container
docker exec -it housing-api /bin/bash

# Copy files from container
docker cp housing-api:/app/logs/app.log ./debug-logs/

# Monitor real-time logs
docker logs -f --tail 100 housing-api

# Check container processes
docker exec housing-api ps aux

# Check container network
docker exec housing-api netstat -tlnp

# Test connectivity from container
docker exec housing-api curl -v http://localhost:8000/health

# Check environment variables
docker exec housing-api env

# Monitor resource usage
docker stats --no-stream housing-api
```

## 🏆 Best Practices

### Docker Image Optimization

#### Multi-Stage Builds
```dockerfile
# Build stage
FROM python:3.9-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.9-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY . .
ENV PATH=/root/.local/bin:$PATH
CMD ["python", "-m", "uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### Minimize Image Size
```dockerfile
# Use specific base image versions
FROM python:3.9.18-slim-bullseye

# Combine RUN commands to reduce layers
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir -r requirements.txt

# Use .dockerignore effectively
# .dockerignore content:
__pycache__/
*.pyc
*.pyo
*.pyd
.git/
.pytest_cache/
.coverage
htmlcov/
.tox/
.cache/
nosetests.xml
coverage.xml
*.cover
*.log
.DS_Store
```

### Security Best Practices

#### Non-Root User
```dockerfile
# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser
RUN chown -R appuser:appuser /app
USER appuser
```

#### Secrets Management
```bash
# Use Docker secrets (Docker Swarm)
echo "my-secret-password" | docker secret create db_password -

# Use environment variables for non-sensitive config
docker run -e LOG_LEVEL=INFO housing-price-api:latest

# Use external secret management
# - AWS Secrets Manager
# - Azure Key Vault
# - HashiCorp Vault
```

#### Security Scanning
```bash
# Scan for vulnerabilities
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  aquasec/trivy image housing-price-api:latest

# Use Docker Scout (if available)
docker scout cves housing-price-api:latest

# Regular base image updates
docker pull python:3.9-slim
docker build --no-cache -t housing-price-api:latest .
```

### Production Deployment Best Practices

#### Health Checks
```dockerfile
# Add health check to Dockerfile
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1
```

#### Resource Limits
```bash
# Set resource limits
docker run -d \
  --memory=2g \
  --memory-swap=2g \
  --cpus=1.5 \
  --restart=unless-stopped \
  -p 8000:8000 \
  housing-price-api:latest
```

#### Logging Configuration
```bash
# Configure log driver
docker run -d \
  --log-driver=json-file \
  --log-opt max-size=10m \
  --log-opt max-file=3 \
  -p 8000:8000 \
  housing-price-api:latest
```

#### Backup and Recovery
```bash
# Backup volumes
docker run --rm \
  -v housing_data:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/housing_data_backup.tar.gz -C /data .

# Restore volumes
docker run --rm \
  -v housing_data:/data \
  -v $(pwd):/backup \
  alpine tar xzf /backup/housing_data_backup.tar.gz -C /data
```

### Monitoring and Observability

#### Container Metrics
```bash
# Export container metrics
docker run -d \
  --name cadvisor \
  -p 8080:8080 \
  -v /:/rootfs:ro \
  -v /var/run:/var/run:ro \
  -v /sys:/sys:ro \
  -v /var/lib/docker/:/var/lib/docker:ro \
  gcr.io/cadvisor/cadvisor:latest
```

#### Log Aggregation
```yaml
# docker-compose.yml with centralized logging
version: '3.8'
services:
  housing-api:
    image: yourusername/housing-price-api:latest
    logging:
      driver: "fluentd"
      options:
        fluentd-address: localhost:24224
        tag: housing.api
```

---

## 📞 Support and Resources

### Getting Help
- **GitHub Issues**: [Create an issue](https://github.com/yourusername/housing-price-mlops/issues)
- **Docker Documentation**: [docs.docker.com](https://docs.docker.com)
- **Docker Hub**: [hub.docker.com](https://hub.docker.com)

### Additional Resources
- **Docker Best Practices**: [Docker Official Guide](https://docs.docker.com/develop/dev-best-practices/)
- **Container Security**: [NIST Container Security Guide](https://csrc.nist.gov/publications/detail/sp/800-190/final)
- **Kubernetes Deployment**: [Kubernetes Documentation](https://kubernetes.io/docs/)

---

**Last Updated**: July 29, 2025  
**Version**: 1.0.0  
**Maintainer**: MLOps Engineering Team