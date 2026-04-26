#!/bin/bash
set -e

echo "=========================================="
echo "  Deploying Internal Utility Service"
echo "=========================================="

IMAGE="gbadedata/internal-utility-service"
BLUE_CONTAINER="flask_app_blue"
GREEN_CONTAINER="flask_app_green"
ACTIVE_CONTAINER="flask_app"

echo "[1/5] Pulling latest image..."
docker pull ${IMAGE}:latest

echo "[2/5] Stopping old container (if exists)..."
docker stop ${ACTIVE_CONTAINER} 2>/dev/null || true
docker rm ${ACTIVE_CONTAINER} 2>/dev/null || true

echo "[3/5] Starting new container..."
docker run -d \
  --name ${ACTIVE_CONTAINER} \
  --restart unless-stopped \
  -e SECRET_KEY="${SECRET_KEY}" \
  -e AWS_DEFAULT_REGION="eu-west-2" \
  --expose 5000 \
  ${IMAGE}:latest

echo "[4/5] Waiting for health check..."
sleep 10

STATUS=$(docker inspect --format='{{.State.Health.Status}}' ${ACTIVE_CONTAINER} 2>/dev/null || echo "unknown")
echo "Container health: ${STATUS}"

echo "[5/5] Reloading Nginx..."
docker exec nginx_proxy nginx -s reload 2>/dev/null || true

echo "=========================================="
echo "  Deployment complete!"
echo "=========================================="
docker ps | grep -E "flask_app|nginx"
