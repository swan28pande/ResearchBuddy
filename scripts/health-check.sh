#!/bin/bash
# Health check script for ResearchBuddy

set -e

if [ -z "$1" ]; then
    echo "Usage: $0 <alb-dns-name>"
    exit 1
fi

ALB_DNS=$1
MAX_RETRIES=20
RETRY_COUNT=0
SLEEP_TIME=15

echo "🏥 Running health check for: $ALB_DNS"
echo "=================================="

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    echo "Attempt $((RETRY_COUNT + 1))/$MAX_RETRIES..."
    
    if curl -f -s "http://$ALB_DNS/hello" > /dev/null 2>&1; then
        echo "✅ Health check passed!"
        echo ""
        echo "Testing /hello endpoint:"
        curl "http://$ALB_DNS/hello"
        echo ""
        echo ""
        echo "✅ Backend is healthy and responding!"
        exit 0
    fi
    
    echo "⏳ Service not ready yet, waiting ${SLEEP_TIME}s..."
    RETRY_COUNT=$((RETRY_COUNT + 1))
    sleep $SLEEP_TIME
done

echo "❌ Health check failed after $MAX_RETRIES attempts"
echo "Please check:"
echo "1. EC2 instances are running"
echo "2. Security groups allow traffic"
echo "3. Application logs in CloudWatch"
exit 1
