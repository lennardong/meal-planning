#!/bin/bash
# ==============================================================================
# GCP Project Setup Script
# ==============================================================================
# One-time setup for deploying Palatte to GCP Cloud Run.
#
# Prerequisites:
#   - gcloud CLI installed and authenticated
#   - Billing enabled on GCP project
#
# What this script does:
#   1. Enables required GCP APIs
#   2. Creates Artifact Registry repository for Docker images
#   3. Creates service accounts (deployer + runtime)
#   4. Grants IAM permissions
#   5. Exports deployer key for GitHub Actions
#
# Usage:
#   ./01-setup-project.sh
#
# After running:
#   - Add contents of deployer-github-actions-key.json to GitHub Secrets as GCP_SA_KEY
# ==============================================================================

set -euo pipefail

# Load shared configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/config.env"

echo "=============================================="
echo "GCP Project Setup for ${SERVICE_NAME}"
echo "=============================================="
echo "Project:  ${PROJECT_ID}"
echo "Region:   ${REGION}"
echo "=============================================="

# ------------------------------------------------------------------------------
# Set active project
# ------------------------------------------------------------------------------
echo ""
echo "[1/6] Setting active GCP project..."
gcloud config set project "${PROJECT_ID}"

# ------------------------------------------------------------------------------
# Enable required APIs
# ------------------------------------------------------------------------------
echo ""
echo "[2/6] Enabling required APIs..."
gcloud services enable \
    run.googleapis.com \
    artifactregistry.googleapis.com \
    iam.googleapis.com

# ------------------------------------------------------------------------------
# Create Artifact Registry repository
# ------------------------------------------------------------------------------
echo ""
echo "[3/6] Creating Artifact Registry repository..."
if gcloud artifacts repositories describe "${REPO_NAME}" \
    --location="${REGION}" &>/dev/null; then
    echo "Repository '${REPO_NAME}' already exists, skipping."
else
    gcloud artifacts repositories create "${REPO_NAME}" \
        --repository-format=docker \
        --location="${REGION}" \
        --description="Docker images for ${SERVICE_NAME}"
    echo "Repository '${REPO_NAME}' created."
fi

# ------------------------------------------------------------------------------
# Create Deployer Service Account (for GitHub Actions)
# ------------------------------------------------------------------------------
echo ""
echo "[4/6] Creating deployer service account..."
if gcloud iam service-accounts describe "${SA_DEPLOYER_EMAIL}" &>/dev/null; then
    echo "Service account '${SA_DEPLOYER}' already exists, skipping creation."
else
    gcloud iam service-accounts create "${SA_DEPLOYER}" \
        --display-name="GitHub Actions Deployer" \
        --description="Used by GitHub Actions to deploy to Cloud Run"
    echo "Service account '${SA_DEPLOYER}' created."
fi

# Grant deployer permissions
echo "Granting deployer permissions..."

# Can deploy to Cloud Run
gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
    --member="serviceAccount:${SA_DEPLOYER_EMAIL}" \
    --role="roles/run.admin" \
    --condition=None \
    --quiet

# Can push images to Artifact Registry
gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
    --member="serviceAccount:${SA_DEPLOYER_EMAIL}" \
    --role="roles/artifactregistry.writer" \
    --condition=None \
    --quiet

# Can act as service accounts (needed to deploy with runtime SA)
gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
    --member="serviceAccount:${SA_DEPLOYER_EMAIL}" \
    --role="roles/iam.serviceAccountUser" \
    --condition=None \
    --quiet

echo "Deployer permissions granted."

# ------------------------------------------------------------------------------
# Create Runtime Service Account (for Cloud Run service)
# ------------------------------------------------------------------------------
echo ""
echo "[5/6] Creating runtime service account..."
if gcloud iam service-accounts describe "${SA_RUNTIME_EMAIL}" &>/dev/null; then
    echo "Service account '${SA_RUNTIME}' already exists, skipping creation."
else
    gcloud iam service-accounts create "${SA_RUNTIME}" \
        --display-name="Palatte Runtime" \
        --description="Minimal permissions for running the Palatte service"
    echo "Service account '${SA_RUNTIME}' created."
fi

# Runtime account needs minimal permissions
# For this app: no additional permissions needed (no GCP services accessed at runtime)
echo "Runtime service account has minimal permissions (none needed for this app)."

# ------------------------------------------------------------------------------
# Export Deployer Key for GitHub Actions
# ------------------------------------------------------------------------------
echo ""
echo "[6/6] Exporting deployer key for GitHub Actions..."
KEY_FILE="${SCRIPT_DIR}/deployer-github-actions-key.json"
if [[ -f "${KEY_FILE}" ]]; then
    echo "Key file already exists at: ${KEY_FILE}"
    echo "Delete it manually if you need to regenerate."
else
    gcloud iam service-accounts keys create "${KEY_FILE}" \
        --iam-account="${SA_DEPLOYER_EMAIL}"
    echo "Key exported to: ${KEY_FILE}"
fi

# ------------------------------------------------------------------------------
# Summary
# ------------------------------------------------------------------------------
echo ""
echo "=============================================="
echo "Setup Complete!"
echo "=============================================="
echo ""
echo "Next steps:"
echo "  1. Add the contents of '${KEY_FILE}' to GitHub Secrets"
echo "     - Go to: repo Settings > Secrets > Actions"
echo "     - Create secret: GCP_SA_KEY"
echo "     - Paste the JSON contents"
echo ""
echo "  2. Run 02-manual-deploy.sh to test the setup"
echo ""
echo "IMPORTANT: Keep deployer-github-actions-key.json secure!"
echo "           Add it to .gitignore if not already."
echo "=============================================="
