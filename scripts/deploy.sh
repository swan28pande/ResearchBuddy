#!/bin/bash
# Deployment script for ResearchBuddy

set -e

echo "🚀 Starting ResearchBuddy deployment..."

# Check if AWS CLI is configured
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ AWS CLI is not configured. Please run 'aws configure' first."
    exit 1
fi

# Check if Terraform is installed
if ! command -v terraform &> /dev/null; then
    echo "❌ Terraform is not installed. Please install Terraform first."
    exit 1
fi

# Navigate to terraform directory
cd "$(dirname "$0")/../terraform"

# Initialize Terraform
echo "📦 Initializing Terraform..."
terraform init

# Validate configuration
echo "✅ Validating Terraform configuration..."
terraform validate

# Plan deployment
echo "📋 Planning deployment..."
terraform plan -out=tfplan

# Ask for confirmation
read -p "Do you want to apply this plan? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "❌ Deployment cancelled."
    exit 0
fi

# Apply configuration
echo "🔨 Applying Terraform configuration..."
terraform apply tfplan

# Get outputs
echo ""
echo "✅ Deployment complete!"
echo ""
echo "📊 Infrastructure Details:"
echo "=========================="
terraform output

echo ""
echo "🌐 Access your application:"
echo "Backend API: $(terraform output -raw alb_url)"
echo "Frontend: $(terraform output -raw frontend_url)"
echo ""
echo "📝 Next steps:"
echo "1. Wait 2-3 minutes for instances to initialize"
echo "2. Test the backend: curl $(terraform output -raw alb_url)/hello"
echo "3. Deploy frontend: cd ../frontend && npm run build && aws s3 sync dist/ s3://$(terraform output -raw frontend_bucket_name)/"
echo ""
