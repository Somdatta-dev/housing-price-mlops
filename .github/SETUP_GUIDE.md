# GitHub Actions CI/CD Setup Guide

This guide will help you configure your GitHub repository to make the CI/CD pipelines work properly.

## 🔧 Required GitHub Secrets

You need to set up the following secrets in your GitHub repository:

### Go to: Repository → Settings → Secrets and variables → Actions

#### 1. Docker Hub Secrets (Required)
```
DOCKER_USERNAME = your-dockerhub-username
DOCKER_PASSWORD = your-dockerhub-password-or-token
```

#### 2. Optional Security Scanning
```
SNYK_TOKEN = your-snyk-token (optional, for vulnerability scanning)
```

## 🛡️ Environment Protection Rules

Set up environment protection for production deployments:

### Go to: Repository → Settings → Environments

#### 1. Create "staging" Environment
- No protection rules needed
- Used for staging deployments

#### 2. Create "production" Environment
- ✅ Required reviewers: Add yourself or team members
- ✅ Wait timer: 5 minutes (optional)
- ✅ Deployment branches: Only main branch

## 📁 Required Files and Directories

The workflows expect certain files and directories to exist. Run these commands in your repository:

```bash
# Create necessary directories
mkdir -p data/raw data/processed data/external data/interim
mkdir -p logs mlruns models
mkdir -p tests/unit tests/integration tests/e2e
mkdir -p monitoring configs scripts

# Create .gitkeep files to ensure directories are tracked
touch data/raw/.gitkeep
touch data/processed/.gitkeep
touch data/external/.gitkeep
touch data/interim/.gitkeep
touch logs/.gitkeep
touch mlruns/.gitkeep
touch models/.gitkeep
```

## 🔍 Workflow Triggers

### Continuous Integration (ci.yml)
- **Triggers**: Push to main/develop, Pull requests to main
- **Jobs**: Code quality, testing, Docker build, integration tests

### Continuous Deployment (cd.yml)
- **Triggers**: Push to main, tags starting with 'v', successful CI completion
- **Jobs**: Build & push Docker image, deploy to staging/production

### Model Retraining (model-retrain.yml)
- **Triggers**: Weekly schedule (Sundays 2 AM UTC), manual dispatch
- **Jobs**: Data validation, model training, validation, deployment

## 🚀 How to Test Your Setup

### 1. Test CI Pipeline
```bash
# Make a small change and push to trigger CI
echo "# Test change" >> README.md
git add README.md
git commit -m "test: trigger CI pipeline"
git push origin main
```

### 2. Test Manual Model Retraining
- Go to Actions tab in GitHub
- Select "Model Retraining Pipeline"
- Click "Run workflow"
- Choose your options and run

### 3. Test Docker Hub Integration
- The CD pipeline will automatically push to Docker Hub when CI passes
- Check your Docker Hub repository for the new image

## 🔧 Customization Options

### Update Docker Hub Username
In `.github/workflows/cd.yml`, the image name is constructed as:
```yaml
${{ env.REGISTRY }}/${{ secrets.DOCKER_USERNAME }}/${{ env.IMAGE_NAME }}
```

This will create: `docker.io/yourusername/housing-price-api`

### Modify Deployment Targets
Currently, the workflows simulate deployments. To deploy to real environments:

1. **AWS ECS/Fargate**: Add AWS credentials and deployment scripts
2. **Google Cloud Run**: Add GCP service account and gcloud commands
3. **Azure Container Instances**: Add Azure credentials and az commands
4. **Kubernetes**: Add kubeconfig and kubectl commands

### Environment Variables
You can add environment-specific variables in GitHub:
- Repository → Settings → Secrets and variables → Actions
- Use "Variables" tab for non-sensitive configuration

## 📊 Monitoring Your Pipelines

### GitHub Actions Dashboard
- Go to Actions tab to see all workflow runs
- Click on individual runs to see detailed logs
- Use the workflow visualization to understand the pipeline flow

### Artifacts and Reports
The workflows generate several artifacts:
- **Security reports**: Bandit and Safety scan results
- **Test coverage**: HTML coverage reports
- **Docker SBOM**: Software Bill of Materials
- **Deployment reports**: Detailed deployment summaries

## 🚨 Troubleshooting Common Issues

### 1. Docker Hub Authentication Failed
```
Error: denied: requested access to the resource is denied
```
**Solution**: Check your DOCKER_USERNAME and DOCKER_PASSWORD secrets

### 2. Environment Protection Rules
```
Error: Environment protection rules not satisfied
```
**Solution**: Set up environment protection rules or remove environment requirements

### 3. Missing Dependencies
```
Error: ModuleNotFoundError: No module named 'xyz'
```
**Solution**: Ensure all dependencies are in requirements.txt

### 4. Test Failures
```
Error: Tests failed
```
**Solution**: Run tests locally first: `pytest tests/ -v`

## 🎯 Next Steps After Setup

1. **Monitor First Runs**: Watch the initial pipeline runs carefully
2. **Fix Any Issues**: Address any failures in the workflows
3. **Customize Deployments**: Add real deployment targets
4. **Set Up Notifications**: Add Slack/email notifications
5. **Add More Tests**: Expand your test coverage
6. **Security Scanning**: Set up additional security tools

## 📞 Getting Help

If you encounter issues:
1. Check the GitHub Actions logs for detailed error messages
2. Verify all secrets are set correctly
3. Ensure all required files exist
4. Test individual components locally first

---

**Remember**: The first few runs might fail as you fine-tune the configuration. This is normal!