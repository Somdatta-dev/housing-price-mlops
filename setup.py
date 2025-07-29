"""
Setup configuration for Housing Price Prediction MLOps Pipeline
"""

import os

from setuptools import find_packages, setup

# Read the contents of README file
this_directory = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

# Read requirements from requirements.txt
with open(os.path.join(this_directory, 'requirements.txt'), encoding='utf-8') as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name="housing-price-mlops",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A complete MLOps pipeline for housing price prediction",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/housing-price-mlops",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Data Scientists",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "pytest-mock>=3.11.1",
            "pytest-asyncio>=0.21.1",
            "black>=23.7.0",
            "flake8>=6.0.0",
            "isort>=5.12.0",
            "mypy>=1.5.1",
            "pre-commit>=3.3.3",
            "bandit>=1.7.5",
            "safety>=2.3.5",
        ],
        "docs": [
            "sphinx>=7.1.2",
            "sphinx-rtd-theme>=1.3.0",
        ],
        "monitoring": [
            "prometheus-client>=0.17.1",
            "grafana-api>=1.0.3",
        ],
        "cloud": [
            "boto3>=1.28.25",
            "google-cloud-storage>=2.10.0",
            "azure-storage-blob>=12.17.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "housing-train=models.train_model:main",
            "housing-api=api.main:main",
            "housing-predict=models.predict:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.yaml", "*.yml", "*.json", "*.conf"],
    },
    zip_safe=False,
    keywords="mlops, machine learning, housing prediction, fastapi, mlflow, docker",
    project_urls={
        "Bug Reports": "https://github.com/yourusername/housing-price-mlops/issues",
        "Source": "https://github.com/yourusername/housing-price-mlops",
        "Documentation": "https://housing-price-mlops.readthedocs.io/",
    },
)