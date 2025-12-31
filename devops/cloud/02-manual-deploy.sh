#!/bin/bash
# ==============================================================================
# Manual Deploy Script
# ==============================================================================
# Manually build and deploy Palatte to Cloud Run.
# Useful for testing before CI/CD is wired up, or for hotfixes.
#
# Prerequisites:
#   - 01-setup-project.sh has been run
#   - gcloud CLI authenticated with deployer permissions
#   - Docker running locally
#
# Usage:
#   ./02-manual-deploy.sh [version]
#
# Examples:
#   ./02-manual-deploy.sh           # Uses 'manual-<timestamp>' as version
#   ./02-manual-deploy.sh v1.0.0    # Uses specified version
# ==============================================================================

set -euo pipefail

# Load shared configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
source "${SCRIPT_DIR}/config.env"

# Version tag (default to timestamp if not provided)
VERSION="${1:-manual-$(date +%Y%m%d-%H%M%S)}"

echo "=============================================="
echo "Manual Deploy: ${SERVICE_NAME}"
echo "=============================================="
echo "Project:  ${PROJECT_ID}"
echo "Region:   ${REGION}"
echo "Version:  ${VERSION}"
echo "=============================================="

# ------------------------------------------------------------------------------
# Configure Docker for Artifact Registry
# ------------------------------------------------------------------------------
echo ""
echo "[1/4] Configuring Docker authentication..."
gcloud auth configure-docker "${REGION}-docker.pkg.dev" --quiet

# ------------------------------------------------------------------------------
# Build Docker image
# ------------------------------------------------------------------------------
echo ""
echo "[2/4] Building Docker image..."
cd "${REPO_ROOT}"

# Force linux/amd64 platform for Cloud Run (important if building on ARM Mac)
docker build \
    --platform=linux/amd64 \
    -f "${DOCKERFILE_PATH}" \
    -t "${IMAGE_NAME}:${VERSION}" \
    -t "${IMAGE_NAME}:latest" \
    .

echo "Image built: ${IMAGE_NAME}:${VERSION}"

# ------------------------------------------------------------------------------
# Push to Artifact Registry
# ------------------------------------------------------------------------------
echo ""
echo "[3/4] Pushing to Artifact Registry..."
docker push "${IMAGE_NAME}:${VERSION}"
docker push "${IMAGE_NAME}:latest"

echo "Image pushed successfully."

# ------------------------------------------------------------------------------
# Deploy to Cloud Run
# ------------------------------------------------------------------------------
echo ""
echo "[4/4] Deploying to Cloud Run..."
gcloud run deploy "${SERVICE_NAME}" \
    --image="${IMAGE_NAME}:${VERSION}" \
    --region="${REGION}" \
    --platform=managed \
    --port="${CONTAINER_PORT}" \
    --allow-unauthenticated \
    --service-account="${SA_RUNTIME_EMAIL}" \
    --max-instances="${MAX_INSTANCES}" \
    --quiet

# Get service URL
SERVICE_URL=$(gcloud run services describe "${SERVICE_NAME}" \
    --region="${REGION}" \
    --format='value(status.url)')

# ------------------------------------------------------------------------------
# Summary
# ------------------------------------------------------------------------------
echo ""
echo "=============================================="
echo "Deploy Complete!"
echo "=============================================="
echo ""
echo "Service URL: ${SERVICE_URL}"
echo "Version:     ${VERSION}"
echo ""
echo "Your app is now live at the URL above."
echo "=============================================="
