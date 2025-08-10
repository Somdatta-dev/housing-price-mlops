# Docker Quick Reference - Housing Price Prediction MLOps

A quick reference guide for common Docker operations with the Housing Price Prediction MLOps pipeline.

## 🚀 Quick Start Commands

### Build and Run Locally
```bash
# Build the image
docker build -t housing-price-api:latest .

# Run the container
docker run -d -p 8000:8000 --name housing-api housing-price-api:latest

# Test the API
curl http://localhost:8000/health
```

### Automated Docker Hub Deployment
```powershell
# Windows PowerShell (Recommended)
.\push-to-dockerhub.ps1 yourusername
```

### Manual Docker Hub Deployment
```bash
# Login, tag, and push
docker login
docker tag housing-price-api:latest yourusername/housing-price-api:latest
docker push yourusername/housing-price-api:latest
```

## 🏗️ Build Commands

| Command | Description |
|---------|-------------|
| `docker build -t housing-price-api:latest .` | Basic build |
| `docker build --no-cache -t housing-price-api:latest .` | Clean build (no cache) |
| `docker build -t housing-price-api:v1.0.0 .` | Build with version tag |
| `docker buildx build --platform linux/amd64,linux/arm64 -t housing-price-api:multi .` | Multi-platform build |

## 🏃 Run Commands

| Command | Description |
|---------|-------------|
| `docker run -d -p 8000:8000 --name housing-api housing-price-api:latest` | Basic run |
| `docker run -d -p 8000:8000 -e LOG_LEVEL=DEBUG --name housing-api housing-price-api:latest` | Run with environment variables |
| `docker run -d -p 8000:8000 -v $(pwd)/logs:/app/logs --name housing-api housing-price-api:latest` | Run with volume mount |
| `docker run -d -p 8000:8000 --memory=2g --cpus=1.5 --name housing-api housing-price-api:latest` | Run with resource limits |

## 🔧 Management Commands

| Command | Description |
|---------|-------------|
| `docker ps` | List running containers |
| `docker ps -a` | List all containers |
| `docker logs housing-api` | View container logs |
| `docker logs -f housing-api` | Follow logs in real-time |
| `docker exec -it housing-api /bin/bash` | Execute shell in container |
| `docker stop housing-api` | Stop container |
| `docker start housing-api` | Start stopped container |
| `docker restart housing-api` | Restart container |
| `docker rm housing-api` | Remove container |
| `docker rm -f housing-api` | Force remove container |

## 🐙 Docker Hub Commands

| Command | Description |
|---------|-------------|
| `docker login` | Login to Docker Hub |
| `docker logout` | Logout from Docker Hub |
| `docker tag housing-price-api:latest yourusername/housing-price-api:latest` | Tag for Docker Hub |
| `docker push yourusername/housing-price-api:latest` | Push to Docker Hub |
| `docker pull yourusername/housing-price-api:latest` | Pull from Docker Hub |
| `docker search yourusername/housing-price-api` | Search Docker Hub |

## 🧪 Testing Commands

| Command | Description |
|---------|-------------|
| `curl http://localhost:8000/health` | Health check |
| `curl http://localhost:8000/health/detailed` | Detailed health check |
| `curl http://localhost:8000/` | API info |
| `curl -X POST http://localhost:8000/predict -H "Content-Type: application/json" -d @test-data.json` | Test prediction |
| `curl http://localhost:8000/metrics` | Prometheus metrics |

## 📊 Monitoring Commands

| Command | Description |
|---------|-------------|
| `docker stats housing-api` | Monitor resource usage |
| `docker inspect housing-api` | Inspect container details |
| `docker port housing-api` | Show port mappings |
| `docker top housing-api` | Show running processes |
| `docker diff housing-api` | Show filesystem changes |

## 🧹 Cleanup Commands

| Command | Description |
|---------|-------------|
| `docker system prune -f` | Remove unused resources |
| `docker image prune -f` | Remove unused images |
| `docker volume prune -f` | Remove unused volumes |
| `docker network prune -f` | Remove unused networks |
| `docker system df` | Show Docker disk usage |
| `docker images` | List all images |
| `docker rmi housing-price-api:latest` | Remove specific image |

## 🐳 Docker Compose Commands

| Command | Description |
|---------|-------------|
| `docker-compose up -d` | Start services in background |
| `docker-compose down` | Stop and remove services |
| `docker-compose ps` | List running services |
| `docker-compose logs -f` | Follow all service logs |
| `docker-compose logs housing-api` | View specific service logs |
| `docker-compose restart housing-api` | Restart specific service |
| `docker-compose exec housing-api /bin/bash` | Execute shell in service |

## 🔍 Debugging Commands

| Command | Description |
|---------|-------------|
| `docker logs --tail 100 housing-api` | View last 100 log lines |
| `docker exec housing-api ps aux` | Show processes in container |
| `docker exec housing-api netstat -tlnp` | Show network connections |
| `docker exec housing-api curl http://localhost:8000/health` | Test from inside container |
| `docker cp housing-api:/app/logs/app.log ./debug.log` | Copy file from container |
| `docker run -it housing-price-api:latest /bin/bash` | Run container interactively |

## 🚨 Troubleshooting Quick Fixes

### Container Won't Start
```bash
# Check logs
docker logs housing-api

# Run interactively
docker run -it housing-price-api:latest /bin/bash

# Check port conflicts
lsof -i :8000
```

### API Not Responding
```bash
# Check if container is running
docker ps

# Check port mapping
docker port housing-api

# Test from inside container
docker exec housing-api curl http://localhost:8000/health
```

### Docker Hub Push Fails
```bash
# Re-authenticate
docker logout && docker login

# Check image name
docker images | grep housing-price-api

# Verify tag format
docker tag housing-price-api:latest yourusername/housing-price-api:latest
```

### Out of Disk Space
```bash
# Quick cleanup
docker system prune -f

# Aggressive cleanup (removes everything)
docker system prune -a -f --volumes
```

## 📋 Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `API_HOST` | `0.0.0.0` | API host binding |
| `API_PORT` | `8000` | API port |
| `MLFLOW_TRACKING_URI` | `http://localhost:5000` | MLflow server URL |

## 🔗 Useful URLs

| Service | URL | Description |
|---------|-----|-------------|
| **API Documentation** | http://localhost:8000/docs | Swagger UI |
| **API Health** | http://localhost:8000/health | Health check |
| **Prometheus Metrics** | http://localhost:8000/metrics | Metrics endpoint |
| **MLflow UI** | http://localhost:5000 | Experiment tracking |

## 📝 Example API Test

```bash
# Test prediction endpoint
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
  }'
```

## 🎯 Production Deployment

```bash
# Production-ready deployment
docker run -d \
  --name housing-api-prod \
  --restart unless-stopped \
  -p 8000:8000 \
  -e LOG_LEVEL=INFO \
  -e API_HOST=0.0.0.0 \
  -v /var/log/housing-api:/app/logs \
  --memory=2g \
  --cpus=1.5 \
  yourusername/housing-price-api:latest
```

## 📚 Additional Resources

- **Complete Guide**: [DOCKER_DEPLOYMENT_GUIDE.md](DOCKER_DEPLOYMENT_GUIDE.md)
- **Main Documentation**: [README.md](README.md)
- **Docker Documentation**: https://docs.docker.com
- **Docker Hub**: https://hub.docker.com

---

**Quick Tip**: Use `docker --help` or `docker <command> --help` for detailed command information.

**Last Updated**: July 29, 2025