# AWS Configuration
aws_region  = "us-east-1"
environment = "prod"

# Instance Configuration (Cost-optimized)
instance_type     = "t3.micro"   # Smaller, cheaper instance
min_instances     = 1            # Start with just 1 instance
max_instances     = 2            # Can scale to 2 if needed
desired_instances = 1            # Start with 1 instance

# Security - Your IP for SSH access
admin_ip = "129.49.252.167/32"

# API Keys - Add your keys here later
openai_api_key            = "PLACEHOLDER_ADD_YOUR_KEY_LATER"
tavily_api_key           = ""
semantic_scholar_api_key = ""

# Optional: EC2 Key Pair (for SSH access)
# key_pair_name = "my-existing-key"
