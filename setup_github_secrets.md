# GitHub Secrets Setup Guide

Follow these steps to set up the required secrets for your CI/CD pipeline:

## 🔐 Step 1: Go to GitHub Repository Settings

1. Navigate to your GitHub repository
2. Click on **Settings** tab
3. In the left sidebar, click **Secrets and variables** → **Actions**

## 🐳 Step 2: Add Docker Hub Secrets

Click **New repository secret** and add these secrets:

### DOCKER_USERNAME
- **Name**: `DOCKER_USERNAME`
- **Secret**: `docker_username` (your Docker Hub username)

### DOCKER_PASSWORD
- **Name**: `DOCKER_PASSWORD`
- **Secret**: Your Docker Hub password or access token

> **💡 Tip**: For better security, use a Docker Hub access token instead of your password:
> 1. Go to Docker Hub → Account Settings → Security
> 2. Create a new access token
> 3. Use the token as your DOCKER_PASSWORD

## 🛡️ Step 3: Set Up Environment Protection (Optional)

### Create Staging Environment
1. Go to **Settings** → **Environments**
2. Click **New environment**
3. Name: `staging`
4. Click **Configure environment**
5. No protection rules needed for staging

### Create Production Environment
1. Click **New environment**
2. Name: `production`
3. Click **Configure environment**
4. Enable **Required reviewers** and add yourself
5. Set **Wait timer** to 5 minutes (optional)
6. Under **Deployment branches**, select **Selected branches** and add `main`

## 🧪 Step 4: Test Your Setup

### Push a Test Commit
```bash
# Make a small change
echo "# CI/CD Test" >> README.md
git add README.md
git commit -m "test: trigger CI/CD pipeline"
git push origin main
```

### Check GitHub Actions
1. Go to **Actions** tab in your repository
2. You should see the workflows running:
   - ✅ **Continuous Integration** (should run immediately)
   - ✅ **Continuous Deployment** (should run after CI passes)

### Expected Results
- **CI Pipeline**: Should pass all tests and build Docker image
- **CD Pipeline**: Should build and push Docker image to Docker Hub
- **Docker Hub**: Check `https://hub.docker.com/r/somdatta25/housing-price-api` for your image

## 🔍 Step 5: Monitor and Debug

### If CI Fails
1. Click on the failed workflow in Actions tab
2. Check the logs for specific errors
3. Common issues:
   - Missing dependencies in `requirements.txt`
   - Test failures
   - Code quality issues

### If CD Fails
1. Check Docker Hub credentials are correct
2. Verify `DOCKER_USERNAME` matches your Docker Hub username exactly
3. Ensure `DOCKER_PASSWORD` is valid

### If Docker Push Fails
```
Error: denied: requested access to the resource is denied
```
- Double-check your Docker Hub credentials
- Make sure the repository name matches your username

## 🎯 Step 6: Manual Workflow Testing

### Test Model Retraining
1. Go to **Actions** tab
2. Click **Model Retraining Pipeline**
3. Click **Run workflow**
4. Choose options:
   - Force retrain: `true`
   - Data source: `latest`
   - Model types: `all`
5. Click **Run workflow**

## 📊 Step 7: View Results

### Successful Pipeline Should Show:
- ✅ All CI jobs passing (code quality, tests, Docker build)
- ✅ Docker image pushed to Docker Hub
- ✅ Staging deployment (simulated)
- ✅ Production deployment (simulated, requires approval)

### Artifacts Generated:
- Security reports (Bandit, Safety)
- Test coverage reports
- Docker SBOM (Software Bill of Materials)
- Deployment reports

## 🚨 Troubleshooting Common Issues

### Issue: "Environment protection rules not satisfied"
**Solution**: Either set up environment protection rules or remove the `environment:` lines from the workflow files.

### Issue: "Secret DOCKER_USERNAME not found"
**Solution**: Make sure you've added the secret with the exact name `DOCKER_USERNAME`.

### Issue: Tests failing
**Solution**: Run tests locally first:
```bash
pip install -r requirements.txt
pytest tests/ -v
```

### Issue: Docker build failing
**Solution**: Test Docker build locally:
```bash
docker build -t housing-price-api:test .
```

## 🎉 Success Indicators

When everything is working correctly, you should see:

1. **Green checkmarks** on all workflow runs
2. **New Docker image** at `https://hub.docker.com/r/somdatta25/housing-price-api`
3. **Artifacts** uploaded to each workflow run
4. **Deployment reports** generated

## 📞 Need Help?

If you encounter issues:
1. Check the detailed logs in GitHub Actions
2. Verify all secrets are set correctly
3. Test individual components locally
4. Make sure all required files exist in your repository

---

**Next Steps**: Once your CI/CD is working, you can customize the deployment targets to deploy to real environments like AWS, GCP, or Azure!