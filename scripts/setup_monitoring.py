#!/usr/bin/env python3
"""
Setup script for Housing Price Prediction MLOps Monitoring Stack
"""

import os
import sys
import subprocess
import time
import requests
from pathlib import Path

def run_command(command, description):
    """Run a shell command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e.stderr}")
        return None

def check_service_health(url, service_name, timeout=30):
    """Check if a service is healthy"""
    print(f"🔍 Checking {service_name} health at {url}...")
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"✅ {service_name} is healthy")
                return True
        except requests.exceptions.RequestException:
            pass
        
        time.sleep(2)
    
    print(f"❌ {service_name} health check failed after {timeout}s")
    return False

def setup_monitoring_stack():
    """Set up the complete monitoring stack"""
    print("🚀 Setting up Housing Price Prediction MLOps Monitoring Stack")
    print("=" * 60)
    
    # Check if Docker is installed
    if not run_command("docker --version", "Checking Docker installation"):
        print("❌ Docker is not installed. Please install Docker first.")
        return False
    
    if not run_command("docker-compose --version", "Checking Docker Compose installation"):
        print("❌ Docker Compose is not installed. Please install Docker Compose first.")
        return False
    
    # Create monitoring directory if it doesn't exist
    monitoring_dir = Path("monitoring")
    monitoring_dir.mkdir(exist_ok=True)
    
    # Stop any existing containers
    run_command("docker-compose -f monitoring/docker-compose.monitoring.yml down", 
                "Stopping existing monitoring containers")
    
    # Build and start the monitoring stack
    if not run_command("docker-compose -f monitoring/docker-compose.monitoring.yml up -d --build", 
                       "Starting monitoring stack"):
        return False
    
    print("\n🔄 Waiting for services to start...")
    time.sleep(10)
    
    # Check service health
    services = [
        ("http://localhost:8000/health", "Housing API"),
        ("http://localhost:5000", "MLflow"),
        ("http://localhost:9090", "Prometheus"),
        ("http://localhost:3001", "Grafana"),
        ("http://localhost:3000", "Monitoring Dashboard"),
        ("http://localhost:9093", "Alertmanager")
    ]
    
    all_healthy = True
    for url, service in services:
        if not check_service_health(url, service):
            all_healthy = False
    
    if all_healthy:
        print("\n🎉 Monitoring stack setup completed successfully!")
        print_service_urls()
    else:
        print("\n⚠️  Some services may not be fully ready. Check logs with:")
        print("docker-compose -f monitoring/docker-compose.monitoring.yml logs")
    
    return all_healthy

def print_service_urls():
    """Print URLs for all services"""
    print("\n📊 Service URLs:")
    print("-" * 40)
    print("🏠 Housing API:           http://localhost:8000")
    print("📈 API Documentation:     http://localhost:8000/docs")
    print("🔬 MLflow:               http://localhost:5000")
    print("📊 Prometheus:           http://localhost:9090")
    print("📈 Grafana:              http://localhost:3001 (admin/admin)")
    print("🖥️  Monitoring Dashboard: http://localhost:3000")
    print("🚨 Alertmanager:         http://localhost:9093")
    print("📊 Prometheus Metrics:   http://localhost:8000/metrics")
    
    print("\n🔧 Useful Commands:")
    print("-" * 40)
    print("View logs:     docker-compose -f monitoring/docker-compose.monitoring.yml logs")
    print("Stop stack:    docker-compose -f monitoring/docker-compose.monitoring.yml down")
    print("Restart:       docker-compose -f monitoring/docker-compose.monitoring.yml restart")
    print("Scale API:     docker-compose -f monitoring/docker-compose.monitoring.yml up -d --scale housing-api=3")

def setup_grafana_datasource():
    """Configure Grafana datasource"""
    print("🔄 Configuring Grafana datasource...")
    
    # Wait for Grafana to be ready
    if not check_service_health("http://localhost:3001", "Grafana", 60):
        return False
    
    # Configure Prometheus datasource
    datasource_config = {
        "name": "Prometheus",
        "type": "prometheus",
        "url": "http://prometheus:9090",
        "access": "proxy",
        "isDefault": True
    }
    
    try:
        response = requests.post(
            "http://localhost:3001/api/datasources",
            json=datasource_config,
            auth=("admin", "admin"),
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code in [200, 409]:  # 409 = already exists
            print("✅ Grafana datasource configured")
            return True
        else:
            print(f"❌ Failed to configure Grafana datasource: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to configure Grafana datasource: {e}")
        return False

def test_monitoring_endpoints():
    """Test monitoring endpoints"""
    print("\n🧪 Testing monitoring endpoints...")
    
    endpoints = [
        ("http://localhost:8000/health", "Health Check"),
        ("http://localhost:8000/metrics", "Prometheus Metrics"),
        ("http://localhost:8000/monitoring/metrics/summary", "Metrics Summary"),
        ("http://localhost:8000/health/detailed", "Detailed Health"),
        ("http://localhost:3000/api/metrics/summary", "Dashboard Metrics")
    ]
    
    for url, name in endpoints:
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                print(f"✅ {name}: OK")
            else:
                print(f"❌ {name}: HTTP {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"❌ {name}: {e}")

def main():
    """Main setup function"""
    try:
        # Change to project root directory
        script_dir = Path(__file__).parent
        project_root = script_dir.parent
        os.chdir(project_root)
        
        # Setup monitoring stack
        if setup_monitoring_stack():
            # Configure Grafana
            time.sleep(5)  # Give Grafana more time to start
            setup_grafana_datasource()
            
            # Test endpoints
            test_monitoring_endpoints()
            
            print("\n🎯 Next Steps:")
            print("1. Visit http://localhost:3000 for the monitoring dashboard")
            print("2. Visit http://localhost:3001 for Grafana (admin/admin)")
            print("3. Visit http://localhost:8000/docs for API documentation")
            print("4. Test the API with some predictions to see metrics")
            
        else:
            print("\n❌ Setup failed. Check the logs for more details.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️  Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()