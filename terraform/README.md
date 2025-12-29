# AWS Deployment with Terraform

This directory contains Terraform configuration for deploying ResearchBuddy to AWS.

## Architecture

- **VPC**: Multi-AZ setup with public and private subnets
- **ALB**: Application Load Balancer for traffic distribution
- **EC2**: Auto Scaling Group (2-4 instances)
- **S3**: Frontend hosting and logs
- **CloudWatch**: Monitoring and logging
- **IAM**: Roles and policies for EC2 instances

## Prerequisites

1. **AWS Account** with appropriate permissions
2. **AWS CLI** configured (`aws configure`)
3. **Terraform** >= 1.0 installed
4. **API Keys**: OpenAI, Tavily (optional), Semantic Scholar (optional)

## Quick Start

### 1. Configure Variables

```bash
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars` and set your values:
- `admin_ip`: Your IP address for SSH access
- API keys (or set via environment variables)

### 2. Deploy Infrastructure

```bash
# Initialize Terraform
terraform init

# Preview changes
terraform plan

# Apply configuration
terraform apply
```

Or use the deployment script:
```bash
../scripts/deploy.sh
```

### 3. Access Your Application

After deployment completes (2-3 minutes):

```bash
# Get URLs
terraform output

# Test backend
curl $(terraform output -raw alb_url)/hello

# Deploy frontend
cd ../frontend
npm run build
aws s3 sync dist/ s3://$(cd ../terraform && terraform output -raw frontend_bucket_name)/
```

## Configuration Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `aws_region` | AWS region | `us-east-1` |
| `environment` | Environment name | `prod` |
| `instance_type` | EC2 instance type | `t3.medium` |
| `min_instances` | Min instances in ASG | `2` |
| `max_instances` | Max instances in ASG | `4` |
| `admin_ip` | IP for SSH access | `0.0.0.0/0` |

## GitHub Actions CI/CD

The repository includes automated deployment via GitHub Actions.

### Required Secrets

Set these in GitHub repository settings → Secrets:

- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `OPENAI_API_KEY`
- `TAVILY_API_KEY` (optional)
- `SEMANTIC_SCHOLAR_API_KEY` (optional)

### Workflow

1. Push to `main` branch
2. Tests run automatically
3. Terraform applies infrastructure changes
4. Frontend deploys to S3
5. Health checks verify deployment

## Monitoring

### CloudWatch Dashboard

View metrics at: AWS Console → CloudWatch → Dashboards → `researchbuddy-dashboard`

### Logs

```bash
# View application logs
aws logs tail /aws/ec2/researchbuddy --follow
```

### Health Checks

```bash
# Manual health check
../scripts/health-check.sh $(terraform output -raw alb_dns_name)
```

## Scaling

Auto Scaling triggers:
- **Scale Up**: CPU > 70% for 4 minutes
- **Scale Down**: CPU < 20% for 4 minutes

Manual scaling:
```bash
aws autoscaling set-desired-capacity \
  --auto-scaling-group-name $(terraform output -raw asg_name) \
  --desired-capacity 3
```

## Cost Optimization

### Estimated Monthly Costs
- EC2 (2x t3.medium): ~$60
- ALB: ~$20
- NAT Gateway: ~$32
- S3 + CloudWatch: ~$10
- **Total: ~$122/month**

### Reduce Costs
```bash
# Use smaller instances
terraform apply -var="instance_type=t3.small"

# Reduce minimum instances
terraform apply -var="min_instances=1"
```

## Troubleshooting

### Instances not healthy

```bash
# Check instance status
aws ec2 describe-instance-status

# View user data logs
aws ec2 get-console-output --instance-id <instance-id>

# SSH into instance
ssh -i your-key.pem ubuntu@<instance-ip>
sudo journalctl -u researchbuddy-backend -f
```

### Deployment fails

```bash
# Check Terraform state
terraform show

# Destroy and recreate
terraform destroy
terraform apply
```

## Cleanup

To destroy all resources:

```bash
terraform destroy
```

**Warning**: This will delete all infrastructure including data!

## Security Best Practices

1. **Restrict SSH access**: Set `admin_ip` to your specific IP
2. **Use HTTPS**: Configure ACM certificate for ALB
3. **Secrets management**: Use AWS Secrets Manager for API keys
4. **Enable VPC Flow Logs**: For network monitoring
5. **Regular updates**: Keep AMIs and dependencies updated

## Advanced Configuration

### Enable HTTPS

1. Request ACM certificate
2. Uncomment HTTPS listener in `alb.tf`
3. Update security group rules
4. Apply changes

### Add RDS Database

1. Create `rds.tf` with database configuration
2. Update security groups
3. Update application connection string

### Multi-Region Deployment

1. Duplicate terraform directory
2. Change `aws_region` variable
3. Set up Route53 for DNS routing

## Support

For issues or questions:
- Check CloudWatch logs
- Review Terraform plan output
- Consult AWS documentation
