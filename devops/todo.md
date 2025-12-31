# Deployment Checklist

> Step-by-step guide to deploy Palatte. Check off each item as you complete it.

---

## Phase 1: GCP Project Setup (One-time)

These steps only need to be done once, when first setting up the infrastructure.

### Manual Steps (GCP Console)

- [ ] **Create GCP Account** (if you don't have one)
  - Go to [console.cloud.google.com](https://console.cloud.google.com)
  - Sign in with Google account

- [ ] **Create New Project**
  - Click project dropdown → "New Project"
  - Project name: `meal-planner`
  - Note your Project ID (might differ from name)

- [ ] **Enable Billing**
  - Go to Billing in GCP Console
  - Link a payment method
  - Assign billing to `meal-planner` project
  - (Required even for free tier usage)

### Automated Steps (Script)

- [ ] **Install gcloud CLI** (if not installed)
  ```bash
  # macOS
  brew install google-cloud-sdk

  # Or download from: https://cloud.google.com/sdk/docs/install
  ```

- [ ] **Authenticate gcloud**
  ```bash
  gcloud auth login
  ```

- [ ] **Run Setup Script**
  ```bash
  cd devops/cloud
  ./01-setup-project.sh
  ```
  This creates:
  - Artifact Registry repository
  - Service accounts (deployer + runtime)
  - IAM permissions
  - Key file for GitHub Actions

- [ ] **Secure the Key File**
  - File created: `devops/cloud/deployer-github-actions-key.json`
  - This file is in `.gitignore` (never commit it!)
  - Store a backup somewhere secure (password manager, encrypted drive)

---

## Phase 2: GitHub Setup

- [ ] **Add GitHub Secret**
  1. Go to your repo on GitHub
  2. Settings → Secrets and variables → Actions
  3. Click "New repository secret"
  4. Name: `GCP_SA_KEY`
  5. Value: Copy/paste entire contents of `deployer-github-actions-key.json`
  6. Click "Add secret"

- [ ] **Verify Workflow File Exists**
  - Check that `.github/workflows/deploy.yml` exists
  - This was created during initial setup

---

## Phase 3: First Deploy (Manual Test)

Before relying on CI/CD, verify the setup works with a manual deploy.

- [ ] **Run Manual Deploy**
  ```bash
  cd devops/cloud
  ./02-manual-deploy.sh v0.1.0
  ```

- [ ] **Verify App is Running**
  - Script outputs a URL like `https://palatte-xxxxx-as.a.run.app`
  - Open in browser
  - Confirm the app loads correctly

- [ ] **Check Cloud Console**
  - Go to [Cloud Run Console](https://console.cloud.google.com/run)
  - Verify `palatte` service is listed
  - Check logs for any errors

---

## Phase 4: Custom Domain Setup

- [ ] **Run Domain Script**
  ```bash
  cd devops/cloud
  ./03-setup-domain.sh palatte.dudleyong.com
  ```

- [ ] **Add DNS Record at Registrar**
  - Log into your domain registrar (e.g., Namecheap, GoDaddy, Cloudflare)
  - Add CNAME record:
    - **Host/Name:** `palatte`
    - **Type:** `CNAME`
    - **Value/Target:** `ghs.googlehosted.com`
    - **TTL:** 300 (or default)

- [ ] **Wait for Propagation**
  - DNS changes can take up to 24 hours
  - Usually much faster (minutes to a few hours)
  - Check status:
    ```bash
    gcloud run domain-mappings describe \
      --domain=palatte.dudleyong.com \
      --region=asia-southeast1
    ```

- [ ] **Verify Custom Domain**
  - Visit `https://palatte.dudleyong.com`
  - SSL certificate is auto-provisioned (may take a few minutes)
  - Confirm app loads correctly

---

## Phase 5: CI/CD Test

- [ ] **Create a GitHub Release**
  1. Go to your repo → Releases
  2. Click "Create a new release"
  3. Tag: `v0.1.0` (or next version)
  4. Title: `v0.1.0`
  5. Description: "Initial release"
  6. Click "Publish release"

- [ ] **Watch GitHub Actions**
  - Go to Actions tab in your repo
  - Find the running workflow
  - Watch it complete (should take ~2-3 minutes)

- [ ] **Verify Deployment**
  - Visit your app URL
  - Check that changes are live

---

## Ongoing Deployments

For future releases, just:

1. Create a GitHub Release with a new version tag (e.g., `v1.0.1`)
2. GitHub Actions automatically deploys

No manual steps required!

---

## Troubleshooting

### "Permission denied" running scripts
```bash
chmod +x devops/cloud/*.sh
```

### gcloud not authenticated
```bash
gcloud auth login
gcloud config set project meal-planner
```

### Docker build fails
- Make sure Docker Desktop is running
- Check `devops/docker/Dockerfile.dash-app` for errors

### Deployment fails in GitHub Actions
- Check the Actions tab for error logs
- Verify `GCP_SA_KEY` secret is set correctly
- Ensure the key hasn't expired

### Domain not working
- DNS propagation can take up to 24 hours
- Verify CNAME record is correct at registrar
- Check domain mapping status:
  ```bash
  gcloud run domain-mappings list --region=asia-southeast1
  ```

---

## Cleanup (If Needed)

To tear everything down:

```bash
# Delete Cloud Run service
gcloud run services delete palatte --region=asia-southeast1

# Delete Artifact Registry repo (and all images)
gcloud artifacts repositories delete palatte-repo --location=asia-southeast1

# Delete service accounts
gcloud iam service-accounts delete deployer-github-actions@meal-planner.iam.gserviceaccount.com
gcloud iam service-accounts delete runtime-palatte@meal-planner.iam.gserviceaccount.com

# Delete domain mapping
gcloud run domain-mappings delete --domain=palatte.dudleyong.com --region=asia-southeast1
```
