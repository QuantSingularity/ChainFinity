# ChainFinity Infrastructure Variables
# Financial Grade Security Configuration Variables

# Environment Configuration
variable "environment" {
  description = "Environment name (dev, staging, production)"
  type        = string
  default     = "production"

  validation {
    condition     = contains(["dev", "staging", "production"], var.environment)
    error_message = "Environment must be one of: dev, staging, production."
  }
}

variable "region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-west-2"
}

# Network Configuration
variable "allowed_cidr_blocks" {
  description = "CIDR blocks allowed to access the infrastructure"
  type        = list(string)
  default     = ["10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"]

  validation {
    condition     = length(var.allowed_cidr_blocks) > 0
    error_message = "At least one CIDR block must be specified."
  }
}

# Domain Configuration
variable "domain_name" {
  description = "Domain name for the application"
  type        = string
  default     = "chainfinity.com"
}

variable "manage_dns" {
  description = "Whether to manage DNS with Route53"
  type        = bool
  default     = true
}

# Database Configuration
variable "db_name" {
  description = "Name of the database"
  type        = string
  default     = "chainfinity"

  validation {
    condition     = can(regex("^[a-zA-Z][a-zA-Z0-9_]*$", var.db_name))
    error_message = "Database name must start with a letter and contain only alphanumeric characters and underscores."
  }
}

variable "db_username" {
  description = "Database master username"
  type        = string
  default     = "chainfinity_admin"
  sensitive   = true

  validation {
    condition     = length(var.db_username) >= 8 && length(var.db_username) <= 63
    error_message = "Database username must be between 8 and 63 characters."
  }
}

variable "db_password" {
  description = "Database master password"
  type        = string
  sensitive   = true

  validation {
    condition     = length(var.db_password) >= 12
    error_message = "Database password must be at least 12 characters long."
  }
}

variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.r6g.large"

  validation {
    condition = contains([
      "db.t3.micro", "db.t3.small", "db.t3.medium", "db.t3.large",
      "db.r6g.large", "db.r6g.xlarge", "db.r6g.2xlarge", "db.r6g.4xlarge"
    ], var.db_instance_class)
    error_message = "Invalid database instance class."
  }
}

variable "db_allocated_storage" {
  description = "Initial allocated storage for RDS instance (GB)"
  type        = number
  default     = 100

  validation {
    condition     = var.db_allocated_storage >= 20 && var.db_allocated_storage <= 65536
    error_message = "Database allocated storage must be between 20 and 65536 GB."
  }
}

variable "db_max_allocated_storage" {
  description = "Maximum allocated storage for RDS instance (GB)"
  type        = number
  default     = 1000

  validation {
    condition     = var.db_max_allocated_storage >= 100
    error_message = "Database max allocated storage must be at least 100 GB."
  }
}

# EKS Configuration
variable "kubernetes_version" {
  description = "Kubernetes version for EKS cluster"
  type        = string
  default     = "1.28"

  validation {
    condition = contains([
      "1.26", "1.27", "1.28", "1.29"
    ], var.kubernetes_version)
    error_message = "Kubernetes version must be a supported EKS version."
  }
}

variable "eks_endpoint_public_access" {
  description = "Enable public access to EKS API endpoint"
  type        = bool
  default     = false
}

# Node Group Configuration
variable "node_instance_type" {
  description = "EC2 instance type for EKS nodes"
  type        = string
  default     = "m6i.large"
}

variable "node_instance_types" {
  description = "List of EC2 instance types for EKS nodes"
  type        = list(string)
  default     = ["m6i.large", "m6i.xlarge", "c6i.large", "c6i.xlarge"]
}

variable "node_capacity_type" {
  description = "Capacity type for EKS nodes (ON_DEMAND or SPOT)"
  type        = string
  default     = "ON_DEMAND"

  validation {
    condition     = contains(["ON_DEMAND", "SPOT"], var.node_capacity_type)
    error_message = "Node capacity type must be either ON_DEMAND or SPOT."
  }
}

variable "node_desired_size" {
  description = "Desired number of EKS nodes"
  type        = number
  default     = 3

  validation {
    condition     = var.node_desired_size >= 1 && var.node_desired_size <= 100
    error_message = "Node desired size must be between 1 and 100."
  }
}

variable "node_min_size" {
  description = "Minimum number of EKS nodes"
  type        = number
  default     = 1

  validation {
    condition     = var.node_min_size >= 1
    error_message = "Node minimum size must be at least 1."
  }
}

variable "node_max_size" {
  description = "Maximum number of EKS nodes"
  type        = number
  default     = 10

  validation {
    condition     = var.node_max_size >= 1 && var.node_max_size <= 100
    error_message = "Node maximum size must be between 1 and 100."
  }
}

variable "node_disk_size" {
  description = "Disk size for EKS nodes (GB)"
  type        = number
  default     = 50

  validation {
    condition     = var.node_disk_size >= 20 && var.node_disk_size <= 1000
    error_message = "Node disk size must be between 20 and 1000 GB."
  }
}

# Security Configuration
variable "enable_waf" {
  description = "Enable AWS WAF for additional security"
  type        = bool
  default     = true
}

variable "enable_shield" {
  description = "Enable AWS Shield Advanced for DDoS protection"
  type        = bool
  default     = false
}

variable "enable_guardduty" {
  description = "Enable AWS GuardDuty for threat detection"
  type        = bool
  default     = true
}

variable "enable_config" {
  description = "Enable AWS Config for compliance monitoring"
  type        = bool
  default     = true
}

variable "enable_cloudtrail" {
  description = "Enable AWS CloudTrail for audit logging"
  type        = bool
  default     = true
}

variable "enable_security_hub" {
  description = "Enable AWS Security Hub for security posture management"
  type        = bool
  default     = true
}

# Monitoring and Alerting
variable "alert_email_addresses" {
  description = "Email addresses for alerts and notifications"
  type        = list(string)
  default     = ["admin@chainfinity.com", "security@chainfinity.com"]

  validation {
    condition = alltrue([
      for email in var.alert_email_addresses : can(regex("^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$", email))
    ])
    error_message = "All email addresses must be valid."
  }
}

variable "enable_detailed_monitoring" {
  description = "Enable detailed CloudWatch monitoring"
  type        = bool
  default     = true
}

variable "log_retention_days" {
  description = "CloudWatch log retention period in days (CloudWatch only accepts specific values)"
  type        = number
  default     = 2557 # 7 years for financial compliance

  validation {
    condition = contains([
      0, 1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1096, 1827, 2192, 2557, 2922, 3288, 3653
    ], var.log_retention_days)
    error_message = "Log retention days must be a retention period CloudWatch Logs supports (for example 365, 731, 2192, 2557 or 3653)."
  }
}

# Backup Configuration
variable "backup_retention_days" {
  description = "Backup retention period in days"
  type        = number
  default     = 2555 # 7 years for financial compliance

  validation {
    condition     = var.backup_retention_days >= 7 && var.backup_retention_days <= 3653
    error_message = "Backup retention must be between 7 and 3653 days."
  }
}

variable "enable_point_in_time_recovery" {
  description = "Enable point-in-time recovery for RDS"
  type        = bool
  default     = true
}

variable "backup_window" {
  description = "Preferred backup window for RDS"
  type        = string
  default     = "03:00-04:00"

  validation {
    condition     = can(regex("^([0-1][0-9]|2[0-3]):[0-5][0-9]-([0-1][0-9]|2[0-3]):[0-5][0-9]$", var.backup_window))
    error_message = "Backup window must be in format HH:MM-HH:MM."
  }
}

variable "maintenance_window" {
  description = "Preferred maintenance window for RDS"
  type        = string
  default     = "sun:04:00-sun:05:00"

  validation {
    condition     = can(regex("^(mon|tue|wed|thu|fri|sat|sun):[0-2][0-9]:[0-5][0-9]-(mon|tue|wed|thu|fri|sat|sun):[0-2][0-9]:[0-5][0-9]$", var.maintenance_window))
    error_message = "Maintenance window must be in format ddd:HH:MM-ddd:HH:MM."
  }
}

# Compliance Configuration
variable "compliance_frameworks" {
  description = "List of compliance frameworks to implement"
  type        = list(string)
  default     = ["SOC2", "PCI-DSS", "GDPR", "SOX", "ISO27001"]

  validation {
    condition = alltrue([
      for framework in var.compliance_frameworks : contains(["SOC2", "PCI-DSS", "GDPR", "SOX", "ISO27001", "HIPAA", "FedRAMP"], framework)
    ])
    error_message = "Invalid compliance framework specified."
  }
}

variable "data_classification_level" {
  description = "Data classification level for the application"
  type        = string
  default     = "confidential"

  validation {
    condition     = contains(["public", "internal", "confidential", "restricted"], var.data_classification_level)
    error_message = "Data classification level must be one of: public, internal, confidential, restricted."
  }
}

variable "enable_encryption_at_rest" {
  description = "Enable encryption at rest for all storage"
  type        = bool
  default     = true
}

variable "enable_encryption_in_transit" {
  description = "Enable encryption in transit for all communications"
  type        = bool
  default     = true
}

# Cost Management
variable "enable_cost_anomaly_detection" {
  description = "Enable AWS Cost Anomaly Detection"
  type        = bool
  default     = true
}

variable "cost_budget_limit" {
  description = "Monthly cost budget limit in USD"
  type        = number
  default     = 5000

  validation {
    condition     = var.cost_budget_limit > 0
    error_message = "Cost budget limit must be greater than 0."
  }
}

# Disaster Recovery
variable "enable_multi_region" {
  description = "Enable multi-region deployment for disaster recovery"
  type        = bool
  default     = false
}

variable "dr_region" {
  description = "Disaster recovery region"
  type        = string
  default     = "us-east-1"
}

variable "rto_hours" {
  description = "Recovery Time Objective in hours"
  type        = number
  default     = 4

  validation {
    condition     = var.rto_hours >= 1 && var.rto_hours <= 72
    error_message = "RTO must be between 1 and 72 hours."
  }
}

variable "rpo_hours" {
  description = "Recovery Point Objective in hours"
  type        = number
  default     = 1

  validation {
    condition     = var.rpo_hours >= 0.25 && var.rpo_hours <= 24
    error_message = "RPO must be between 0.25 and 24 hours."
  }
}

# Development Configuration
variable "enable_development_tools" {
  description = "Enable development and debugging tools"
  type        = bool
  default     = false
}

variable "enable_bastion_host" {
  description = "Enable bastion host for secure access"
  type        = bool
  default     = false
}

# Feature Flags
variable "feature_flags" {
  description = "Feature flags for enabling/disabling specific features"
  type = object({
    enable_api_gateway        = optional(bool, false)
    enable_elasticsearch      = optional(bool, true)
    enable_redis_cluster      = optional(bool, true)
    enable_message_queue      = optional(bool, true)
    enable_cdn                = optional(bool, true)
    enable_container_insights = optional(bool, true)
  })
  default = {}
}

# Tags
variable "additional_tags" {
  description = "Additional tags to apply to all resources"
  type        = map(string)
  default     = {}
}
