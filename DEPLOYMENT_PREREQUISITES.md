# AWS Deployment Prerequisites

## What You Need

### 1. AWS Account
- Create account at: https://aws.amazon.com
- Credit card required (for billing)

### 2. AWS Credentials
You need to create an IAM user with programmatic access:

1. Go to AWS Console → IAM → Users → Create User
2. User name: `terraform-user`
3. Attach policies:
   - AmazonEC2FullAccess
   - AmazonVPCFullAccess
   - ElasticLoadBalancingFullAccess
   - IAMFullAccess
4. Create access key → Download credentials

You'll get:
- AWS Access Key ID (starts with AKIA...)
- AWS Secret Access Key

### 3. API Keys
- **OpenAI API Key** (required): Get from https://platform.openai.com/api-keys
- **Tavily API Key** (optional): Get from https://tavily.com
- **Semantic Scholar API Key** (optional): Get from https://www.semanticscholar.org/product/api

## Your IP Address
For SSH access security: `129.49.252.167/32`

## Estimated Costs
- Monthly: ~$112
- Hourly: ~$0.15

## Next Steps
Once you have credentials:
1. I'll configure AWS CLI
2. Create terraform.tfvars
3. Deploy infrastructure (10 minutes)
