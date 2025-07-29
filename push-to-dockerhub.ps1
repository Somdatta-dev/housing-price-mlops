# Docker Hub Push Script for Housing Price API
# Usage: .\push-to-dockerhub.ps1 YOUR_DOCKERHUB_USERNAME

param(
    [Parameter(Mandatory=$true)]
    [string]$DockerHubUsername
)

Write-Host "🐳 Starting Docker Hub push process..." -ForegroundColor Green

# Step 1: Check if image exists
Write-Host "📋 Checking if local image exists..." -ForegroundColor Yellow
$imageExists = docker images housing-price-api:latest --format "{{.Repository}}"
if (-not $imageExists) {
    Write-Host "❌ Error: housing-price-api:latest image not found!" -ForegroundColor Red
    Write-Host "Please build the image first with: docker build -t housing-price-api:latest ." -ForegroundColor Red
    exit 1
}
Write-Host "✅ Local image found: housing-price-api:latest" -ForegroundColor Green

# Step 2: Tag the image for Docker Hub
Write-Host "🏷️  Tagging image for Docker Hub..." -ForegroundColor Yellow
$dockerHubTag = "$DockerHubUsername/housing-price-api:latest"
docker tag housing-price-api:latest $dockerHubTag

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Successfully tagged as: $dockerHubTag" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to tag image" -ForegroundColor Red
    exit 1
}

# Step 3: Login to Docker Hub (if not already logged in)
Write-Host "🔐 Checking Docker Hub login..." -ForegroundColor Yellow
Write-Host "Please login to Docker Hub when prompted:" -ForegroundColor Cyan
docker login

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Docker Hub login failed" -ForegroundColor Red
    exit 1
}

# Step 4: Push to Docker Hub
Write-Host "🚀 Pushing image to Docker Hub..." -ForegroundColor Yellow
Write-Host "This may take a few minutes depending on your internet connection..." -ForegroundColor Cyan
docker push $dockerHubTag

if ($LASTEXITCODE -eq 0) {
    Write-Host "🎉 Successfully pushed to Docker Hub!" -ForegroundColor Green
    Write-Host "Your image is now available at: https://hub.docker.com/r/$DockerHubUsername/housing-price-api" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "To pull and run your image from anywhere:" -ForegroundColor Yellow
    Write-Host "docker pull $dockerHubTag" -ForegroundColor White
    Write-Host "docker run -p 8000:8000 $dockerHubTag" -ForegroundColor White
} else {
    Write-Host "❌ Failed to push image to Docker Hub" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "📊 Image details:" -ForegroundColor Yellow
docker images $dockerHubTag