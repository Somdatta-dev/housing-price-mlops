#!/usr/bin/env python3
"""
Validation script to check if the CI/CD setup is ready.
Run this before pushing to GitHub to ensure everything works.
"""

import os
import sys
import subprocess
from pathlib import Path
import importlib.util


def check_file_exists(file_path, description):
    """Check if a file exists."""
    if Path(file_path).exists():
        print(f"✅ {description}: {file_path}")
        return True
    else:
        print(f"❌ {description}: {file_path} (MISSING)")
        return False


def check_directory_exists(dir_path, description):
    """Check if a directory exists."""
    if Path(dir_path).exists() and Path(dir_path).is_dir():
        print(f"✅ {description}: {dir_path}")
        return True
    else:
        print(f"❌ {description}: {dir_path} (MISSING)")
        return False


def check_python_import(module_name):
    """Check if a Python module can be imported."""
    try:
        importlib.import_module(module_name)
        print(f"✅ Python module: {module_name}")
        return True
    except ImportError:
        print(f"❌ Python module: {module_name} (CANNOT IMPORT)")
        return False


def run_command(command, description):
    """Run a shell command and check if it succeeds."""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description}")
            return True
        else:
            print(f"❌ {description}: {result.stderr.strip()}")
            return False
    except Exception as e:
        print(f"❌ {description}: {str(e)}")
        return False


def main():
    """Main validation function."""
    print("🔍 Validating CI/CD Setup for Housing Price Prediction MLOps")
    print("=" * 60)
    
    all_checks_passed = True
    
    # Check GitHub Actions workflows
    print("\n📋 GitHub Actions Workflows:")
    workflow_checks = [
        check_file_exists(".github/workflows/ci.yml", "CI Workflow"),
        check_file_exists(".github/workflows/cd.yml", "CD Workflow"),
        check_file_exists(".github/workflows/model-retrain.yml", "Model Retraining Workflow"),
    ]
    all_checks_passed &= all(workflow_checks)
    
    # Check required directories
    print("\n📁 Required Directories:")
    directory_checks = [
        check_directory_exists("data/raw", "Raw Data Directory"),
        check_directory_exists("data/processed", "Processed Data Directory"),
        check_directory_exists("logs", "Logs Directory"),
        check_directory_exists("mlruns", "MLflow Runs Directory"),
        check_directory_exists("models", "Models Directory"),
        check_directory_exists("tests", "Tests Directory"),
        check_directory_exists("tests/unit", "Unit Tests Directory"),
        check_directory_exists("tests/integration", "Integration Tests Directory"),
        check_directory_exists("tests/e2e", "E2E Tests Directory"),
    ]
    all_checks_passed &= all(directory_checks)
    
    # Check required files
    print("\n📄 Required Files:")
    file_checks = [
        check_file_exists("requirements.txt", "Requirements File"),
        check_file_exists("Dockerfile", "Dockerfile"),
        check_file_exists("tests/__init__.py", "Tests Init File"),
        check_file_exists("tests/conftest.py", "Pytest Configuration"),
        check_file_exists("tests/test_basic.py", "Basic Tests"),
        check_file_exists("tests/test_api_basic.py", "API Tests"),
        check_file_exists(".github/SETUP_GUIDE.md", "Setup Guide"),
        check_file_exists("setup_github_secrets.md", "Secrets Setup Guide"),
    ]
    all_checks_passed &= all(file_checks)
    
    # Check Python dependencies
    print("\n🐍 Python Dependencies:")
    dependency_checks = [
        check_python_import("pandas"),
        check_python_import("numpy"),
        check_python_import("sklearn"),
        check_python_import("fastapi"),
        check_python_import("uvicorn"),
        check_python_import("pytest"),
        check_python_import("mlflow"),
    ]
    all_checks_passed &= all(dependency_checks)
    
    # Check Docker
    print("\n🐳 Docker:")
    docker_checks = [
        run_command("docker --version", "Docker Installation"),
        run_command("docker info", "Docker Service Running"),
    ]
    all_checks_passed &= all(docker_checks)
    
    # Check Git
    print("\n📝 Git:")
    git_checks = [
        run_command("git --version", "Git Installation"),
        run_command("git status", "Git Repository"),
    ]
    all_checks_passed &= all(git_checks)
    
    # Run basic tests
    print("\n🧪 Basic Tests:")
    test_checks = [
        run_command("python -m pytest tests/test_basic.py -v", "Basic Tests"),
        run_command("python -m pytest tests/test_api_basic.py -v", "API Tests"),
    ]
    all_checks_passed &= all(test_checks)
    
    # Check Docker build
    print("\n🏗️ Docker Build Test:")
    docker_build_check = run_command("docker build -t housing-price-api:test .", "Docker Build")
    all_checks_passed &= docker_build_check
    
    # Summary
    print("\n" + "=" * 60)
    if all_checks_passed:
        print("🎉 ALL CHECKS PASSED! Your setup is ready for CI/CD.")
        print("\n📋 Next Steps:")
        print("1. Set up GitHub secrets (see setup_github_secrets.md)")
        print("2. Push your code to GitHub")
        print("3. Check GitHub Actions for workflow execution")
        print("4. Verify Docker image is pushed to Docker Hub")
        return 0
    else:
        print("❌ SOME CHECKS FAILED! Please fix the issues above.")
        print("\n🔧 Common Solutions:")
        print("- Install missing dependencies: pip install -r requirements.txt")
        print("- Create missing directories: mkdir -p data/raw data/processed logs mlruns models")
        print("- Install Docker if not available")
        print("- Check file paths and permissions")
        return 1


if __name__ == "__main__":
    sys.exit(main())