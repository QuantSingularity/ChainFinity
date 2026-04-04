# ChainFinity Infrastructure Outputs
# Financial Grade Security Infrastructure Outputs

# VPC and Networking Outputs
output "vpc_id" {
  description = "ID of the VPC"
  value       = aws_vpc.main.id
}

output "vpc_cidr_block" {
  description = "CIDR block of the VPC"
  value       = aws_vpc.main.cidr_block
}

output "private_subnet_ids" {
  description = "IDs of the private subnets"
  value       = aws_subnet.private[*].id
}

output "public_subnet_ids" {
  description = "IDs of the public subnets"
  value       = aws_subnet.public[*].id
}

output "database_subnet_ids" {
  description = "IDs of the database subnets"
  value       = aws_subnet.database[*].id
}

output "nat_gateway_ids" {
  description = "IDs of the NAT gateways"
  value       = aws_nat_gateway.main[*].id
}

output "internet_gateway_id" {
  description = "ID of the Internet Gateway"
  value       = aws_internet_gateway.main.id
}

# Security Group Outputs
output "alb_security_group_id" {
  description = "ID of the ALB security group"
  value       = aws_security_group.alb_fixed.id
}

output "eks_cluster_security_group_id" {
  description = "ID of the EKS cluster security group"
  value       = aws_security_group.eks_cluster_fixed.id
}

output "eks_nodes_security_group_id" {
  description = "ID of the EKS nodes security group"
  value       = aws_security_group.eks_nodes_fixed.id
}

output "rds_security_group_id" {
  description = "ID of the RDS security group"
  value       = aws_security_group.rds.id
}

# EKS Cluster Outputs
output "cluster_id" {
  description = "Name/ID of the EKS cluster"
  value       = aws_eks_cluster.chainfinity.id
}

output "cluster_arn" {
  description = "ARN of the EKS cluster"
  value       = aws_eks_cluster.chainfinity.arn
}

output "cluster_endpoint" {
  description = "Endpoint for EKS control plane"
  value       = aws_eks_cluster.chainfinity.endpoint
}

output "cluster_version" {
  description = "Kubernetes version of the EKS cluster"
  value       = aws_eks_cluster.chainfinity.version
}

output "cluster_platform_version" {
  description = "Platform version for the EKS cluster"
  value       = aws_eks_cluster.chainfinity.platform_version
}

output "cluster_certificate_authority_data" {
  description = "Base64 encoded certificate data required to communicate with the cluster"
  value       = aws_eks_cluster.chainfinity.certificate_authority[0].data
}

output "cluster_oidc_issuer_url" {
  description = "The URL on the EKS cluster OIDC Issuer"
  value       = aws_eks_cluster.chainfinity.identity[0].oidc[0].issuer
}

output "cluster_security_group_id" {
  description = "Security group ID attached to the EKS cluster"
  value       = aws_eks_cluster.chainfinity.vpc_config[0].cluster_security_group_id
}

# EKS Node Group Outputs
output "node_group_arn" {
  description = "ARN of the EKS node group"
  value       = aws_eks_node_group.chainfinity.arn
}

output "node_group_status" {
  description = "Status of the EKS node group"
  value       = aws_eks_node_group.chainfinity.status
}

output "node_group_capacity_type" {
  description = "Type of capacity associated with the EKS Node Group"
  value       = aws_eks_node_group.chainfinity.capacity_type
}

output "node_group_instance_types" {
  description = "Set of instance types associated with the EKS Node Group"
  value       = aws_eks_node_group.chainfinity.instance_types
}

# Database Outputs
output "db_instance_id" {
  description = "RDS instance ID"
  value       = aws_db_instance.chainfinity_db.id
}

output "db_instance_arn" {
  description = "RDS instance ARN"
  value       = aws_db_instance.chainfinity_db.arn
}

output "db_instance_endpoint" {
  description = "RDS instance endpoint"
  value       = aws_db_instance.chainfinity_db.endpoint
  sensitive   = true
}

output "db_instance_hosted_zone_id" {
  description = "RDS instance hosted zone ID"
  value       = aws_db_instance.chainfinity_db.hosted_zone_id
}

output "db_instance_port" {
  description = "RDS instance port"
  value       = aws_db_instance.chainfinity_db.port
}

output "db_instance_name" {
  description = "RDS instance database name"
  value       = aws_db_instance.chainfinity_db.db_name
}

output "db_instance_username" {
  description = "RDS instance master username"
  value       = aws_db_instance.chainfinity_db.username
  sensitive   = true
}

output "db_subnet_group_id" {
  description = "RDS subnet group ID"
  value       = aws_db_subnet_group.main.id
}

output "db_parameter_group_id" {
  description = "RDS parameter group ID"
  value       = aws_db_parameter_group.postgresql.id
}

# Load Balancer Outputs
output "alb_id" {
  description = "ID of the Application Load Balancer"
  value       = aws_lb.main.id
}

output "alb_arn" {
  description = "ARN of the Application Load Balancer"
  value       = aws_lb.main.arn
}

output "alb_dns_name" {
  description = "DNS name of the Application Load Balancer"
  value       = aws_lb.main.dns_name
}

output "alb_zone_id" {
  description = "Zone ID of the Application Load Balancer"
  value       = aws_lb.main.zone_id
}

output "alb_target_group_arn" {
  description = "ARN of the ALB target group"
  value       = aws_lb_target_group.app.arn
}

# Certificate Outputs
output "acm_certificate_arn" {
  description = "ARN of the ACM certificate"
  value       = aws_acm_certificate.main.arn
}

output "acm_certificate_domain_name" {
  description = "Domain name of the ACM certificate"
  value       = aws_acm_certificate.main.domain_name
}

output "acm_certificate_status" {
  description = "Status of the ACM certificate"
  value       = aws_acm_certificate_validation.main.certificate_arn
}

# Route53 Outputs
output "route53_zone_id" {
  description = "Route53 zone ID"
  value       = var.manage_dns ? aws_route53_zone.main[0].zone_id : null
}

output "route53_zone_name_servers" {
  description = "Route53 zone name servers"
  value       = var.manage_dns ? aws_route53_zone.main[0].name_servers : null
}

output "application_url" {
  description = "URL of the application"
  value       = "https://${var.domain_name}"
}

# Security Outputs
output "kms_key_id" {
  description = "ID of the KMS key"
  value       = aws_kms_key.chainfinity.key_id
}

output "kms_key_arn" {
  description = "ARN of the KMS key"
  value       = aws_kms_key.chainfinity.arn
}

output "kms_alias_arn" {
  description = "ARN of the KMS key alias"
  value       = aws_kms_alias.chainfinity.arn
}

output "waf_web_acl_id" {
  description = "ID of the WAF Web ACL"
  value       = var.enable_waf ? aws_wafv2_web_acl.main[0].id : null
}

output "waf_web_acl_arn" {
  description = "ARN of the WAF Web ACL"
  value       = var.enable_waf ? aws_wafv2_web_acl.main[0].arn : null
}

# Secrets Manager Outputs
output "db_credentials_secret_arn" {
  description = "ARN of the database credentials secret"
  value       = aws_secretsmanager_secret.db_credentials.arn
  sensitive   = true
}

output "app_secrets_secret_arn" {
  description = "ARN of the application secrets"
  value       = aws_secretsmanager_secret.app_secrets.arn
  sensitive   = true
}

# S3 Bucket Outputs
output "alb_logs_bucket_id" {
  description = "ID of the ALB logs S3 bucket"
  value       = aws_s3_bucket.alb_logs.id
}

output "alb_logs_bucket_arn" {
  description = "ARN of the ALB logs S3 bucket"
  value       = aws_s3_bucket.alb_logs.arn
}

output "backups_bucket_id" {
  description = "ID of the backups S3 bucket"
  value       = aws_s3_bucket.backups.id
}

output "backups_bucket_arn" {
  description = "ARN of the backups S3 bucket"
  value       = aws_s3_bucket.backups.arn
}

# CloudWatch Outputs
output "cloudwatch_log_group_vpc_flow_logs" {
  description = "Name of the VPC Flow Logs CloudWatch log group"
  value       = aws_cloudwatch_log_group.vpc_flow_log.name
}

output "cloudwatch_log_group_eks_cluster" {
  description = "Name of the EKS cluster CloudWatch log group"
  value       = aws_cloudwatch_log_group.eks_cluster.name
}

output "cloudwatch_log_group_rds" {
  description = "Name of the RDS CloudWatch log group"
  value       = aws_cloudwatch_log_group.rds.name
}

output "cloudwatch_log_group_application" {
  description = "Name of the application CloudWatch log group"
  value       = aws_cloudwatch_log_group.application.name
}

output "cloudwatch_dashboard_url" {
  description = "URL of the CloudWatch dashboard"
  value       = "https://${data.aws_region.current.name}.console.aws.amazon.com/cloudwatch/home?region=${data.aws_region.current.name}#dashboards:name=${aws_cloudwatch_dashboard.main.dashboard_name}"
}

# SNS Outputs
output "sns_topic_alerts_arn" {
  description = "ARN of the alerts SNS topic"
  value       = aws_sns_topic.alerts.arn
}

# IAM Role Outputs
output "eks_cluster_role_arn" {
  description = "ARN of the EKS cluster IAM role"
  value       = aws_iam_role.eks_cluster.arn
}

output "eks_nodes_role_arn" {
  description = "ARN of the EKS nodes IAM role"
  value       = aws_iam_role.eks_nodes.arn
}

output "rds_monitoring_role_arn" {
  description = "ARN of the RDS monitoring IAM role"
  value       = aws_iam_role.rds_monitoring.arn
}

output "flow_log_role_arn" {
  description = "ARN of the VPC Flow Log IAM role"
  value       = aws_iam_role.flow_log.arn
}

# Configuration Outputs for Kubernetes
output "kubectl_config" {
  description = "kubectl configuration for connecting to the EKS cluster"
  value = {
    cluster_name     = aws_eks_cluster.chainfinity.name
    cluster_endpoint = aws_eks_cluster.chainfinity.endpoint
    cluster_ca_data  = aws_eks_cluster.chainfinity.certificate_authority[0].data
    region           = data.aws_region.current.name
  }
  sensitive = true
}

# Compliance and Security Information
output "compliance_info" {
  description = "Compliance and security configuration information"
  value = {
    encryption_at_rest_enabled    = true
    encryption_in_transit_enabled = true
    vpc_flow_logs_enabled         = true
    cloudtrail_enabled            = var.enable_cloudtrail
    guardduty_enabled             = var.enable_guardduty
    config_enabled                = var.enable_config
    security_hub_enabled          = var.enable_security_hub
    waf_enabled                   = var.enable_waf
    backup_retention_days         = local.backup_retention_days
    log_retention_days            = local.log_retention_days
    compliance_frameworks         = var.compliance_frameworks
    data_classification_level     = var.data_classification_level
  }
}

# Cost Information
output "estimated_monthly_cost" {
  description = "Estimated monthly cost breakdown (approximate)"
  value = {
    eks_cluster     = "~$73/month (control plane)"
    eks_nodes       = "~$150-300/month (depending on instance types and count)"
    rds_database    = "~$200-500/month (depending on instance class)"
    alb             = "~$20-50/month"
    nat_gateways    = "~$45/month (per NAT gateway)"
    data_transfer   = "Variable based on usage"
    cloudwatch_logs = "Variable based on log volume"
    s3_storage      = "Variable based on storage usage"
    kms             = "~$1/month per key + usage"
    total_estimated = "~$500-1000/month (baseline, excluding data transfer and storage)"
  }
}

# Connection Information
output "connection_info" {
  description = "Connection information for accessing services"
  value = {
    application_url   = "https://${var.domain_name}"
    monitoring_url    = var.manage_dns ? "https://monitoring.${var.domain_name}" : "Configure DNS manually"
    database_endpoint = aws_db_instance.chainfinity_db.endpoint
    cluster_endpoint  = aws_eks_cluster.chainfinity.endpoint
    load_balancer_dns = aws_lb.main.dns_name
  }
  sensitive = true
}

# Backup and Recovery Information
output "backup_recovery_info" {
  description = "Backup and disaster recovery information"
  value = {
    rds_backup_retention_days   = aws_db_instance.chainfinity_db.backup_retention_period
    rds_backup_window           = aws_db_instance.chainfinity_db.backup_window
    rds_maintenance_window      = aws_db_instance.chainfinity_db.maintenance_window
    s3_backup_bucket            = aws_s3_bucket.backups.bucket
    point_in_time_recovery      = var.enable_point_in_time_recovery
    multi_az_enabled            = aws_db_instance.chainfinity_db.multi_az
    deletion_protection_enabled = aws_db_instance.chainfinity_db.deletion_protection
  }
}
