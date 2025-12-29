# Input Variables

variable "aws_region" {
  description = "AWS region to deploy resources"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "prod"
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
  default     = "researchbuddy"
}

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for public subnets"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24"]
}

variable "private_subnet_cidrs" {
  description = "CIDR blocks for private subnets"
  type        = list(string)
  default     = ["10.0.3.0/24", "10.0.4.0/24"]
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.medium"
}

variable "min_instances" {
  description = "Minimum number of EC2 instances in Auto Scaling Group"
  type        = number
  default     = 2
}

variable "max_instances" {
  description = "Maximum number of EC2 instances in Auto Scaling Group"
  type        = number
  default     = 4
}

variable "desired_instances" {
  description = "Desired number of EC2 instances in Auto Scaling Group"
  type        = number
  default     = 2
}

variable "admin_ip" {
  description = "Admin IP address for SSH access (CIDR format)"
  type        = string
  default     = "0.0.0.0/0" # Change this to your IP for security
}

variable "openai_api_key" {
  description = "OpenAI API Key"
  type        = string
  sensitive   = true
}

variable "tavily_api_key" {
  description = "Tavily API Key"
  type        = string
  sensitive   = true
  default     = ""
}

variable "semantic_scholar_api_key" {
  description = "Semantic Scholar API Key"
  type        = string
  sensitive   = true
  default     = ""
}

variable "key_pair_name" {
  description = "Name of existing EC2 key pair for SSH access"
  type        = string
  default     = "" # Leave empty to create a new key pair
}
