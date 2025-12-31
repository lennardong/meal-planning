# TODO this script is no longer used. Intead, this is done manually. Revise insructions in todo.md and then delete this script. 
#
#!/bin/bash
# ==============================================================================
# Custom Domain Setup Script
# ==============================================================================
# Maps a custom domain to the Cloud Run service.
#
# Prerequisites:
#   - Service already deployed (run 02-manual-deploy.sh first)
#   - You own the domain and can add DNS records
#
# What this script does:
#   1. Creates domain mapping in Cloud Run
#   2. Shows you the DNS records to add at your registrar
#
# Usage:
#   ./03-setup-domain.sh [domain]
#
# Examples:
#   ./03-setup-domain.sh                        # Uses default: palatte.dudleyong.com
#   ./03-setup-domain.sh myapp.example.com      # Custom domain
# ==============================================================================

set -euo pipefail

# Load shared configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/config.env"

# Domain (default or provided)
DOMAIN="${1:-palatte.dudleyong.com}"

echo "=============================================="
echo "Custom Domain Setup: ${SERVICE_NAME}"
echo "=============================================="
echo "Domain:   ${DOMAIN}"
echo "Service:  ${SERVICE_NAME}"
echo "Region:   ${REGION}"
echo "=============================================="

# ------------------------------------------------------------------------------
# Check if service exists
# ------------------------------------------------------------------------------
echo ""
echo "[1/3] Checking service exists..."
if ! gcloud run services describe "${SERVICE_NAME}" --region="${REGION}" &>/dev/null; then
    echo "ERROR: Service '${SERVICE_NAME}' not found."
    echo "Run 02-manual-deploy.sh first to deploy the service."
    exit 1
fi
echo "Service found."

# ------------------------------------------------------------------------------
# Create domain mapping
# ------------------------------------------------------------------------------
echo ""
echo "[2/3] Creating domain mapping..."

# Check if mapping already exists
if gcloud run domain-mappings describe --domain="${DOMAIN}" --region="${REGION}" &>/dev/null 2>&1; then
    echo "Domain mapping for '${DOMAIN}' already exists."
else
    gcloud run domain-mappings create \
        --service="${SERVICE_NAME}" \
        --domain="${DOMAIN}" \
        --region="${REGION}"
    echo "Domain mapping created."
fi

# ------------------------------------------------------------------------------
# Get DNS records
# ------------------------------------------------------------------------------
echo ""
echo "[3/3] Retrieving DNS configuration..."

# Note: Cloud Run domain mappings use a CNAME to ghs.googlehosted.com for subdomains
echo ""
echo "=============================================="
echo "DNS Configuration Required"
echo "=============================================="
echo ""
echo "Add the following DNS record at your domain registrar:"
echo ""
echo "  Type:   CNAME"
echo "  Host:   ${DOMAIN%%.*}"
echo "  Value:  ghs.googlehosted.com"
echo "  TTL:    300 (or default)"
echo ""
echo "=============================================="
echo ""
echo "After adding the DNS record:"
echo "  - Propagation can take up to 24 hours"
echo "  - SSL certificate will be auto-provisioned"
echo "  - Check status: gcloud run domain-mappings describe --domain=${DOMAIN} --region=${REGION}"
echo ""
echo "Your app will be available at: https://${DOMAIN}"
echo "=============================================="
