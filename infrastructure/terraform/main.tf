# ChainFinity Infrastructure - Financial Grade Security
# Terraform Configuration with Comprehensive Security Controls

terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.20"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.10"
    }
    tls = {
      source  = "hashicorp/tls"
      version = "~> 4.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.5"
    }
  }

  # Enhanced backend configuration with encryption
  #   backend "s3" {
  #     bucket         = "chainfinity-terraform-state"
  #     key            = "infrastructure/terraform.tfstate"
  #     region         = "us-west-2"
  #     encrypt        = true
  #     kms_key_id     = "arn:aws:kms:us-west-2:123456789012:key/12345678-1234-1234-1234-123456789012"
  #     dynamodb_table = "chainfinity-terraform-locks"
  # 
  #     # Additional security settings
  #     versioning                = true
  #     server_side_encryption_configuration {
  #       rule {
  #         apply_server_side_encryption_by_default {
  #           kms_master_key_id = "arn:aws:kms:us-west-2:123456789012:key/12345678-1234-1234-1234-123456789012"
  #           sse_algorithm     = "aws:kms"
  #         }
  #       }
  #     }
  #   }
}

# Local variables for consistent tagging and configuration
locals {
  common_tags = {
    Project            = "ChainFinity"
    Environment        = var.environment
    Owner              = "DevOps Team"
    CostCenter         = "Engineering"
    Compliance         = "SOC2-PCI-DSS"
    DataClassification = "Confidential"
    BackupRequired     = "true"
    MonitoringRequired = "true"
    SecurityLevel      = "High"
    CreatedBy          = "Terraform"
    CreatedDate        = "managed-by-terraform"
  }

  # Network configuration
  vpc_cidr = "10.0.0.0/16"
  azs      = slice(data.aws_availability_zones.available.names, 0, 3)

  # Security configuration
  allowed_cidr_blocks = var.allowed_cidr_blocks

  # Compliance settings
  backup_retention_days = 3653 # 7 years for financial compliance
  log_retention_days    = 2555 # 7 years for financial compliance
}

# Data sources
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}
data "aws_availability_zones" "available" {
  state = "available"
}

# KMS Key for encryption at rest
resource "aws_kms_key" "chainfinity" {
  description             = "ChainFinity encryption key for financial data"
  deletion_window_in_days = 30
  enable_key_rotation     = true

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "Enable IAM User Permissions"
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"
        }
        Action   = "kms:*"
        Resource = "*"
      },
      {
        Sid    = "Allow CloudWatch Logs"
        Effect = "Allow"
        Principal = {
          Service = "logs.${data.aws_region.current.name}.amazonaws.com"
        }
        Action = [
          "kms:Encrypt",
          "kms:Decrypt",
          "kms:ReEncrypt*",
          "kms:GenerateDataKey*",
          "kms:DescribeKey"
        ]
        Resource = "*"
      }
    ]
  })

  tags = merge(local.common_tags, {
    Name = "chainfinity-encryption-key"
    Type = "KMS"
  })
}

resource "aws_kms_alias" "chainfinity" {
  name          = "alias/chainfinity-encryption"
  target_key_id = aws_kms_key.chainfinity.key_id
}

# VPC with enhanced security configuration
resource "aws_vpc" "main" {
  cidr_block           = local.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  # Enhanced security features
  assign_generated_ipv6_cidr_block = false
  instance_tenancy                 = "default"

  tags = merge(local.common_tags, {
    Name = "chainfinity-vpc"
    Type = "VPC"
  })
}

# VPC Flow Logs for security monitoring
resource "aws_flow_log" "vpc_flow_log" {
  iam_role_arn    = aws_iam_role.flow_log.arn
  log_destination = aws_cloudwatch_log_group.vpc_flow_log.arn
  traffic_type    = "ALL"
  vpc_id          = aws_vpc.main.id

  tags = merge(local.common_tags, {
    Name = "chainfinity-vpc-flow-logs"
    Type = "FlowLog"
  })
}

# CloudWatch Log Group for VPC Flow Logs
resource "aws_cloudwatch_log_group" "vpc_flow_log" {
  name              = "/aws/vpc/chainfinity-flow-logs"
  retention_in_days = local.log_retention_days
  kms_key_id        = aws_kms_key.chainfinity.arn

  tags = merge(local.common_tags, {
    Name = "chainfinity-vpc-flow-logs"
    Type = "LogGroup"
  })
}

# IAM role for VPC Flow Logs
resource "aws_iam_role" "flow_log" {
  name = "chainfinity-flow-log-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "vpc-flow-logs.amazonaws.com"
        }
      }
    ]
  })

  tags = local.common_tags
}

resource "aws_iam_role_policy" "flow_log" {
  name = "chainfinity-flow-log-policy"
  role = aws_iam_role.flow_log.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "logs:DescribeLogGroups",
          "logs:DescribeLogStreams"
        ]
        Effect   = "Allow"
        Resource = "*"
      }
    ]
  })
}

# Private Subnets for enhanced security
resource "aws_subnet" "private" {
  count = length(local.azs)

  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.${count.index + 1}.0/24"
  availability_zone = local.azs[count.index]

  # Security: Do not assign public IPs
  map_public_ip_on_launch = false

  tags = merge(local.common_tags, {
    Name                                        = "chainfinity-private-${local.azs[count.index]}"
    Type                                        = "PrivateSubnet"
    "kubernetes.io/role/internal-elb"           = "1"
    "kubernetes.io/cluster/chainfinity-cluster" = "owned"
  })
}

# Public Subnets (minimal, for load balancers only)
resource "aws_subnet" "public" {
  count = length(local.azs)

  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.${count.index + 10}.0/24"
  availability_zone = local.azs[count.index]

  map_public_ip_on_launch = true

  tags = merge(local.common_tags, {
    Name                                        = "chainfinity-public-${local.azs[count.index]}"
    Type                                        = "PublicSubnet"
    "kubernetes.io/role/elb"                    = "1"
    "kubernetes.io/cluster/chainfinity-cluster" = "owned"
  })
}

# Database Subnets (isolated)
resource "aws_subnet" "database" {
  count = length(local.azs)

  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.${count.index + 20}.0/24"
  availability_zone = local.azs[count.index]

  # Security: No public IPs for database subnets
  map_public_ip_on_launch = false

  tags = merge(local.common_tags, {
    Name = "chainfinity-database-${local.azs[count.index]}"
    Type = "DatabaseSubnet"
  })
}

# Internet Gateway
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = merge(local.common_tags, {
    Name = "chainfinity-igw"
    Type = "InternetGateway"
  })
}

# Elastic IPs for NAT Gateways
resource "aws_eip" "nat" {
  count = length(local.azs)

  domain = "vpc"

  depends_on = [aws_internet_gateway.main]

  tags = merge(local.common_tags, {
    Name = "chainfinity-nat-eip-${local.azs[count.index]}"
    Type = "ElasticIP"
  })
}

# NAT Gateways for private subnet internet access
resource "aws_nat_gateway" "main" {
  count = length(local.azs)

  allocation_id = aws_eip.nat[count.index].id
  subnet_id     = aws_subnet.public[count.index].id

  depends_on = [aws_internet_gateway.main]

  tags = merge(local.common_tags, {
    Name = "chainfinity-nat-${local.azs[count.index]}"
    Type = "NATGateway"
  })
}

# Route Tables
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = merge(local.common_tags, {
    Name = "chainfinity-public-rt"
    Type = "RouteTable"
  })
}

resource "aws_route_table" "private" {
  count = length(local.azs)

  vpc_id = aws_vpc.main.id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.main[count.index].id
  }

  tags = merge(local.common_tags, {
    Name = "chainfinity-private-rt-${local.azs[count.index]}"
    Type = "RouteTable"
  })
}

resource "aws_route_table" "database" {
  vpc_id = aws_vpc.main.id

  # No internet access for database subnets
  tags = merge(local.common_tags, {
    Name = "chainfinity-database-rt"
    Type = "RouteTable"
  })
}

# Route Table Associations
resource "aws_route_table_association" "public" {
  count = length(aws_subnet.public)

  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table_association" "private" {
  count = length(aws_subnet.private)

  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private[count.index].id
}

resource "aws_route_table_association" "database" {
  count = length(aws_subnet.database)

  subnet_id      = aws_subnet.database[count.index].id
  route_table_id = aws_route_table.database.id
}

# Network ACLs for additional security layer
resource "aws_network_acl" "private" {
  vpc_id     = aws_vpc.main.id
  subnet_ids = aws_subnet.private[*].id

  # Allow inbound HTTPS from VPC
  ingress {
    protocol   = "tcp"
    rule_no    = 100
    action     = "allow"
    cidr_block = local.vpc_cidr
    from_port  = 443
    to_port    = 443
  }

  # Allow inbound HTTP from VPC (for health checks)
  ingress {
    protocol   = "tcp"
    rule_no    = 110
    action     = "allow"
    cidr_block = local.vpc_cidr
    from_port  = 80
    to_port    = 80
  }

  # Allow inbound ephemeral ports
  ingress {
    protocol   = "tcp"
    rule_no    = 120
    action     = "allow"
    cidr_block = "0.0.0.0/0"
    from_port  = 1024
    to_port    = 65535
  }

  # Allow outbound HTTPS
  egress {
    protocol   = "tcp"
    rule_no    = 100
    action     = "allow"
    cidr_block = "0.0.0.0/0"
    from_port  = 443
    to_port    = 443
  }

  # Allow outbound HTTP
  egress {
    protocol   = "tcp"
    rule_no    = 110
    action     = "allow"
    cidr_block = "0.0.0.0/0"
    from_port  = 80
    to_port    = 80
  }

  # Allow outbound ephemeral ports
  egress {
    protocol   = "tcp"
    rule_no    = 120
    action     = "allow"
    cidr_block = "0.0.0.0/0"
    from_port  = 1024
    to_port    = 65535
  }

  tags = merge(local.common_tags, {
    Name = "chainfinity-private-nacl"
    Type = "NetworkACL"
  })
}

resource "aws_network_acl" "database" {
  vpc_id     = aws_vpc.main.id
  subnet_ids = aws_subnet.database[*].id

  # Allow inbound PostgreSQL from private subnets only
  ingress {
    protocol   = "tcp"
    rule_no    = 100
    action     = "allow"
    cidr_block = "10.0.0.0/22" # Private subnets range
    from_port  = 5432
    to_port    = 5432
  }

  # Allow inbound ephemeral ports for responses
  ingress {
    protocol   = "tcp"
    rule_no    = 110
    action     = "allow"
    cidr_block = "10.0.0.0/22"
    from_port  = 1024
    to_port    = 65535
  }

  # Allow outbound ephemeral ports
  egress {
    protocol   = "tcp"
    rule_no    = 100
    action     = "allow"
    cidr_block = "10.0.0.0/22"
    from_port  = 1024
    to_port    = 65535
  }

  tags = merge(local.common_tags, {
    Name = "chainfinity-database-nacl"
    Type = "NetworkACL"
  })
}

# Security Groups with strict rules
resource "aws_security_group" "rds" {
  name_prefix = "chainfinity-rds-"
  vpc_id      = aws_vpc.main.id
  description = "Security group for RDS database"

  # Inbound PostgreSQL from EKS nodes only
  ingress {
    description     = "PostgreSQL from EKS nodes"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.eks_nodes_fixed.id]
  }

  # No outbound rules (database doesn't need internet)

  tags = merge(local.common_tags, {
    Name = "chainfinity-rds-sg"
    Type = "SecurityGroup"
  })

  lifecycle {
    create_before_destroy = true
  }
}


# DB Subnet Group for RDS
resource "aws_db_subnet_group" "main" {
  name       = "chainfinity-db-subnet-group"
  subnet_ids = aws_subnet.database[*].id

  tags = merge(local.common_tags, {
    Name = "chainfinity-db-subnet-group"
    Type = "DBSubnetGroup"
  })
}

# RDS Parameter Group for enhanced security
resource "aws_db_parameter_group" "postgresql" {
  family = "postgres15"
  name   = "chainfinity-postgres-params"

  # Security parameters
  parameter {
    name  = "log_statement"
    value = "all"
  }

  parameter {
    name  = "log_min_duration_statement"
    value = "1000" # Log queries taking more than 1 second
  }

  parameter {
    name  = "log_connections"
    value = "1"
  }

  parameter {
    name  = "log_disconnections"
    value = "1"
  }

  parameter {
    name  = "log_checkpoints"
    value = "1"
  }

  parameter {
    name  = "log_lock_waits"
    value = "1"
  }

  parameter {
    name  = "ssl"
    value = "1"
  }

  parameter {
    name  = "ssl_ciphers"
    value = "HIGH:MEDIUM:+3DES:!aNULL"
  }

  tags = merge(local.common_tags, {
    Name = "chainfinity-postgres-params"
    Type = "DBParameterGroup"
  })
}

# RDS Option Group
resource "aws_db_option_group" "postgresql" {
  name                     = "chainfinity-postgres-options"
  option_group_description = "ChainFinity PostgreSQL options"
  engine_name              = "postgres"
  major_engine_version     = "15"

  tags = merge(local.common_tags, {
    Name = "chainfinity-postgres-options"
    Type = "DBOptionGroup"
  })
}

# RDS Database with enhanced security
resource "aws_db_instance" "chainfinity_db" {
  identifier = "chainfinity-db"

  # Engine configuration
  engine         = "postgres"
  engine_version = "15.4"
  instance_class = var.db_instance_class

  # Storage configuration with encryption
  allocated_storage     = var.db_allocated_storage
  max_allocated_storage = var.db_max_allocated_storage
  storage_type          = "gp3"
  storage_encrypted     = true
  kms_key_id            = aws_kms_key.chainfinity.arn

  # Database configuration
  db_name  = var.db_name
  username = var.db_username
  password = var.db_password
  port     = 5432

  # Network configuration
  vpc_security_group_ids = [aws_security_group.rds.id]
  db_subnet_group_name   = aws_db_subnet_group.main.name
  publicly_accessible    = false

  # Parameter and option groups
  parameter_group_name = aws_db_parameter_group.postgresql.name
  option_group_name    = aws_db_option_group.postgresql.name

  # Backup configuration for compliance
  backup_retention_period = min(var.backup_retention_days, 35) # RDS max is 35 days; use AWS Backup for longer retention
  backup_window           = "03:00-04:00"         # UTC
  maintenance_window      = "sun:04:00-sun:05:00" # UTC

  # Security features
  copy_tags_to_snapshot     = true
  deletion_protection       = true
  skip_final_snapshot       = false
  final_snapshot_identifier = "chainfinity-db-final-snapshot-${formatdate("YYYY-MM-DD-hhmm", timestamp())}"
  delete_automated_backups  = false

  # Monitoring and logging
  monitoring_interval = 60
  monitoring_role_arn = aws_iam_role.rds_monitoring.arn

  enabled_cloudwatch_logs_exports = [
    "postgresql"
  ]

  # Performance insights
  performance_insights_enabled          = true
  performance_insights_kms_key_id       = aws_kms_key.chainfinity.arn
  performance_insights_retention_period = 731 # 2 years

  # Multi-AZ for high availability
  multi_az = var.environment == "production" ? true : false

  tags = merge(local.common_tags, {
    Name = "chainfinity-database"
    Type = "RDSInstance"
  })

  depends_on = [
    aws_cloudwatch_log_group.rds
  ]
}

# CloudWatch Log Group for RDS
resource "aws_cloudwatch_log_group" "rds" {
  name              = "/aws/rds/instance/chainfinity-db/postgresql"
  retention_in_days = local.log_retention_days
  kms_key_id        = aws_kms_key.chainfinity.arn

  tags = merge(local.common_tags, {
    Name = "chainfinity-rds-logs"
    Type = "LogGroup"
  })
}

# IAM role for RDS monitoring
resource "aws_iam_role" "rds_monitoring" {
  name = "chainfinity-rds-monitoring-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "monitoring.rds.amazonaws.com"
        }
      }
    ]
  })

  tags = local.common_tags
}

resource "aws_iam_role_policy_attachment" "rds_monitoring" {
  role       = aws_iam_role.rds_monitoring.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonRDSEnhancedMonitoringRole"
}

# EKS Cluster IAM Role
resource "aws_iam_role" "eks_cluster" {
  name = "chainfinity-eks-cluster-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "eks.amazonaws.com"
        }
      }
    ]
  })

  tags = local.common_tags
}

# EKS Cluster IAM Role Policy Attachments
resource "aws_iam_role_policy_attachment" "eks_cluster_policy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSClusterPolicy"
  role       = aws_iam_role.eks_cluster.name
}

resource "aws_iam_role_policy_attachment" "eks_vpc_resource_controller" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSVPCResourceController"
  role       = aws_iam_role.eks_cluster.name
}

# EKS Node Group IAM Role
resource "aws_iam_role" "eks_nodes" {
  name = "chainfinity-eks-nodes-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })

  tags = local.common_tags
}

# EKS Node Group IAM Role Policy Attachments
resource "aws_iam_role_policy_attachment" "eks_worker_node_policy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy"
  role       = aws_iam_role.eks_nodes.name
}

resource "aws_iam_role_policy_attachment" "eks_cni_policy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy"
  role       = aws_iam_role.eks_nodes.name
}

resource "aws_iam_role_policy_attachment" "eks_container_registry_readonly" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
  role       = aws_iam_role.eks_nodes.name
}

# Additional IAM policy for enhanced security
resource "aws_iam_role_policy" "eks_nodes_additional" {
  name = "chainfinity-eks-nodes-additional-policy"
  role = aws_iam_role.eks_nodes.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue",
          "secretsmanager:DescribeSecret"
        ]
        Resource = [
          "arn:aws:secretsmanager:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:secret:chainfinity/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "kms:Decrypt",
          "kms:DescribeKey"
        ]
        Resource = [
          aws_kms_key.chainfinity.arn
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "ssm:GetParameter",
          "ssm:GetParameters",
          "ssm:GetParametersByPath"
        ]
        Resource = [
          "arn:aws:ssm:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:parameter/chainfinity/*"
        ]
      }
    ]
  })
}

# EKS Cluster with enhanced security
resource "aws_eks_cluster" "chainfinity" {
  name     = "chainfinity-cluster"
  role_arn = aws_iam_role.eks_cluster.arn
  version  = var.kubernetes_version

  vpc_config {
    subnet_ids              = aws_subnet.private[*].id
    endpoint_private_access = true
    endpoint_public_access  = var.eks_endpoint_public_access
    public_access_cidrs     = var.eks_endpoint_public_access ? local.allowed_cidr_blocks : []
    security_group_ids      = [aws_security_group.eks_cluster_fixed.id]
  }

  # Enhanced logging
  enabled_cluster_log_types = [
    "api",
    "audit",
    "authenticator",
    "controllerManager",
    "scheduler"
  ]

  # Encryption configuration
  encryption_config {
    provider {
      key_arn = aws_kms_key.chainfinity.arn
    }
    resources = ["secrets"]
  }

  tags = merge(local.common_tags, {
    Name = "chainfinity-cluster"
    Type = "EKSCluster"
  })

  depends_on = [
    aws_iam_role_policy_attachment.eks_cluster_policy,
    aws_iam_role_policy_attachment.eks_vpc_resource_controller,
    aws_cloudwatch_log_group.eks_cluster
  ]
}

# CloudWatch Log Group for EKS
resource "aws_cloudwatch_log_group" "eks_cluster" {
  name              = "/aws/eks/chainfinity-cluster/cluster"
  retention_in_days = local.log_retention_days
  kms_key_id        = aws_kms_key.chainfinity.arn

  tags = merge(local.common_tags, {
    Name = "chainfinity-eks-cluster-logs"
    Type = "LogGroup"
  })
}

# Launch template for EKS nodes with enhanced security
resource "aws_launch_template" "eks_nodes" {
  name_prefix   = "chainfinity-eks-nodes-"
  image_id      = data.aws_ssm_parameter.eks_ami_release_version.value
  instance_type = var.node_instance_type

  vpc_security_group_ids = [aws_security_group.eks_nodes_fixed.id]

  # Enhanced security configuration
  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required"
    http_put_response_hop_limit = 2
    instance_metadata_tags      = "enabled"
  }

  monitoring {
    enabled = true
  }

  block_device_mappings {
    device_name = "/dev/xvda"
    ebs {
      volume_size           = var.node_disk_size
      volume_type           = "gp3"
      encrypted             = true
      kms_key_id            = aws_kms_key.chainfinity.arn
      delete_on_termination = true
    }
  }

  user_data = base64encode(templatefile("${path.module}/templates/user_data.sh.tpl", {
    cluster_name        = aws_eks_cluster.chainfinity.name
    cluster_endpoint    = aws_eks_cluster.chainfinity.endpoint
    cluster_ca          = aws_eks_cluster.chainfinity.certificate_authority[0].data
    bootstrap_arguments = "--container-runtime containerd"
  }))

  tag_specifications {
    resource_type = "instance"
    tags = merge(local.common_tags, {
      Name = "chainfinity-eks-node"
      Type = "EKSNode"
    })
  }

  tags = merge(local.common_tags, {
    Name = "chainfinity-eks-nodes-template"
    Type = "LaunchTemplate"
  })
}

# Data source for EKS optimized AMI
data "aws_ssm_parameter" "eks_ami_release_version" {
  name = "/aws/service/eks/optimized-ami/${aws_eks_cluster.chainfinity.version}/amazon-linux-2/recommended/image_id"
}

# EKS Node Group
resource "aws_eks_node_group" "chainfinity" {
  cluster_name    = aws_eks_cluster.chainfinity.name
  node_group_name = "chainfinity-nodes"
  node_role_arn   = aws_iam_role.eks_nodes.arn
  subnet_ids      = aws_subnet.private[*].id

  # Instance configuration — type/AMI/disk controlled by launch_template
  capacity_type = var.node_capacity_type

  # Scaling configuration
  scaling_config {
    desired_size = var.node_desired_size
    max_size     = var.node_max_size
    min_size     = var.node_min_size
  }

  # Update configuration
  update_config {
    max_unavailable_percentage = 25
  }

  # Launch template
  launch_template {
    id      = aws_launch_template.eks_nodes.id
    version = aws_launch_template.eks_nodes.latest_version
  }

  tags = merge(local.common_tags, {
    Name = "chainfinity-node-group"
    Type = "EKSNodeGroup"
  })

  depends_on = [
    aws_iam_role_policy_attachment.eks_worker_node_policy,
    aws_iam_role_policy_attachment.eks_cni_policy,
    aws_iam_role_policy_attachment.eks_container_registry_readonly,
  ]
}

# Application Load Balancer
resource "aws_lb" "main" {
  name               = "chainfinity-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb_fixed.id]
  subnets            = aws_subnet.public[*].id

  # Security features
  enable_deletion_protection = var.environment == "production" ? true : false
  drop_invalid_header_fields = true

  # Logging
  access_logs {
    bucket  = aws_s3_bucket.alb_logs.bucket
    prefix  = "alb-logs"
    enabled = true
  }

  tags = merge(local.common_tags, {
    Name = "chainfinity-alb"
    Type = "ApplicationLoadBalancer"
  })
}

# S3 bucket for ALB logs
resource "aws_s3_bucket" "alb_logs" {
  bucket        = "chainfinity-alb-logs-${random_string.bucket_suffix.result}"
  force_destroy = var.environment != "production"

  tags = merge(local.common_tags, {
    Name = "chainfinity-alb-logs"
    Type = "S3Bucket"
  })
}

resource "aws_s3_bucket_versioning" "alb_logs" {
  bucket = aws_s3_bucket.alb_logs.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "alb_logs" {
  bucket = aws_s3_bucket.alb_logs.id

  server_side_encryption_configuration {
    rule {
      apply_server_side_encryption_by_default {
        kms_master_key_id = aws_kms_key.chainfinity.arn
        sse_algorithm     = "aws:kms"
      }
    }
  }
}

resource "aws_s3_bucket_public_access_block" "alb_logs" {
  bucket = aws_s3_bucket.alb_logs.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_lifecycle_configuration" "alb_logs" {
  bucket = aws_s3_bucket.alb_logs.id

  rule {
    id     = "log_retention"
    status = "Enabled"

    expiration {
      days = local.log_retention_days
    }

    noncurrent_version_expiration {
      noncurrent_days = 30
    }
  }
}

# Random string for unique bucket naming
resource "random_string" "bucket_suffix" {
  length  = 8
  special = false
  upper   = false
}

# ALB Target Group
resource "aws_lb_target_group" "app" {
  name     = "chainfinity-app-tg"
  port     = 80
  protocol = "HTTP"
  vpc_id   = aws_vpc.main.id

  target_type = "ip"

  health_check {
    enabled             = true
    healthy_threshold   = 2
    unhealthy_threshold = 2
    timeout             = 5
    interval            = 30
    path                = "/health"
    matcher             = "200"
    port                = "traffic-port"
    protocol            = "HTTP"
  }

  tags = merge(local.common_tags, {
    Name = "chainfinity-app-tg"
    Type = "TargetGroup"
  })
}

# ALB Listener (HTTPS)
resource "aws_lb_listener" "https" {
  load_balancer_arn = aws_lb.main.arn
  port              = "443"
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS13-1-2-2021-06"
  certificate_arn   = aws_acm_certificate_validation.main.certificate_arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.app.arn
  }

  tags = local.common_tags
}

# ALB Listener (HTTP - redirect to HTTPS)
resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.main.arn
  port              = "80"
  protocol          = "HTTP"

  default_action {
    type = "redirect"

    redirect {
      port        = "443"
      protocol    = "HTTPS"
      status_code = "HTTP_301"
    }
  }

  tags = local.common_tags
}


# ACM Certificate for HTTPS
resource "aws_acm_certificate" "main" {
  domain_name       = var.domain_name
  validation_method = "DNS"

  subject_alternative_names = [
    "*.${var.domain_name}",
    "api.${var.domain_name}",
    "app.${var.domain_name}"
  ]

  lifecycle {
    create_before_destroy = true
  }

  tags = merge(local.common_tags, {
    Name = "chainfinity-certificate"
    Type = "ACMCertificate"
  })
}

# Route53 Zone (if managing DNS)
resource "aws_route53_zone" "main" {
  count = var.manage_dns ? 1 : 0
  name  = var.domain_name

  tags = merge(local.common_tags, {
    Name = "chainfinity-zone"
    Type = "Route53Zone"
  })
}

# Route53 records for certificate validation
resource "aws_route53_record" "cert_validation" {
  for_each = var.manage_dns ? {
    for dvo in aws_acm_certificate.main.domain_validation_options : dvo.domain_name => {
      name   = dvo.resource_record_name
      record = dvo.resource_record_value
      type   = dvo.resource_record_type
    }
  } : {}

  allow_overwrite = true
  name            = each.value.name
  records         = [each.value.record]
  ttl             = 60
  type            = each.value.type
  zone_id         = aws_route53_zone.main[0].zone_id
}

# ACM Certificate validation
resource "aws_acm_certificate_validation" "main" {
  certificate_arn         = aws_acm_certificate.main.arn
  validation_record_fqdns = var.manage_dns ? [for record in aws_route53_record.cert_validation : record.fqdn] : []

  timeouts {
    create = "5m"
  }
}

# Route53 record for ALB
resource "aws_route53_record" "main" {
  count   = var.manage_dns ? 1 : 0
  zone_id = aws_route53_zone.main[0].zone_id
  name    = var.domain_name
  type    = "A"

  alias {
    name                   = aws_lb.main.dns_name
    zone_id                = aws_lb.main.zone_id
    evaluate_target_health = true
  }
}

# Secrets Manager for database credentials
resource "aws_secretsmanager_secret" "db_credentials" {
  name                    = "chainfinity/database/credentials"
  description             = "Database credentials for ChainFinity"
  kms_key_id              = aws_kms_key.chainfinity.arn
  recovery_window_in_days = 30

  tags = merge(local.common_tags, {
    Name = "chainfinity-db-credentials"
    Type = "Secret"
  })
}

resource "aws_secretsmanager_secret_version" "db_credentials" {
  secret_id = aws_secretsmanager_secret.db_credentials.id
  secret_string = jsonencode({
    username = var.db_username
    password = var.db_password
    engine   = "postgres"
    host     = aws_db_instance.chainfinity_db.endpoint
    port     = aws_db_instance.chainfinity_db.port
    dbname   = aws_db_instance.chainfinity_db.db_name
  })
}

# Secrets Manager for application secrets
resource "aws_secretsmanager_secret" "app_secrets" {
  name                    = "chainfinity/application/secrets"
  description             = "Application secrets for ChainFinity"
  kms_key_id              = aws_kms_key.chainfinity.arn
  recovery_window_in_days = 30

  tags = merge(local.common_tags, {
    Name = "chainfinity-app-secrets"
    Type = "Secret"
  })
}

resource "aws_secretsmanager_secret_version" "app_secrets" {
  secret_id = aws_secretsmanager_secret.app_secrets.id
  secret_string = jsonencode({
    jwt_secret     = random_password.jwt_secret.result
    api_key        = random_password.api_key.result
    encryption_key = random_password.encryption_key.result
  })
}

# Random passwords for application secrets
resource "random_password" "jwt_secret" {
  length  = 64
  special = true
}

resource "random_password" "api_key" {
  length  = 32
  special = false
}

resource "random_password" "encryption_key" {
  length  = 32
  special = false
}

# CloudWatch Log Groups for application logs
resource "aws_cloudwatch_log_group" "application" {
  name              = "/aws/eks/chainfinity/application"
  retention_in_days = local.log_retention_days
  kms_key_id        = aws_kms_key.chainfinity.arn

  tags = merge(local.common_tags, {
    Name = "chainfinity-application-logs"
    Type = "LogGroup"
  })
}

# CloudWatch Dashboard
resource "aws_cloudwatch_dashboard" "main" {
  dashboard_name = "ChainFinity-Infrastructure"

  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6

        properties = {
          metrics = [
            ["AWS/EKS", "cluster_failed_request_count", "ClusterName", aws_eks_cluster.chainfinity.name],
            ["AWS/EKS", "cluster_request_total", "ClusterName", aws_eks_cluster.chainfinity.name]
          ]
          view    = "timeSeries"
          stacked = false
          region  = data.aws_region.current.name
          title   = "EKS Cluster Metrics"
          period  = 300
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 6
        width  = 12
        height = 6

        properties = {
          metrics = [
            ["AWS/RDS", "CPUUtilization", "DBInstanceIdentifier", aws_db_instance.chainfinity_db.id],
            ["AWS/RDS", "DatabaseConnections", "DBInstanceIdentifier", aws_db_instance.chainfinity_db.id],
            ["AWS/RDS", "FreeableMemory", "DBInstanceIdentifier", aws_db_instance.chainfinity_db.id]
          ]
          view    = "timeSeries"
          stacked = false
          region  = data.aws_region.current.name
          title   = "RDS Database Metrics"
          period  = 300
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 12
        width  = 12
        height = 6

        properties = {
          metrics = [
            ["AWS/ApplicationELB", "RequestCount", "LoadBalancer", aws_lb.main.arn_suffix],
            ["AWS/ApplicationELB", "TargetResponseTime", "LoadBalancer", aws_lb.main.arn_suffix],
            ["AWS/ApplicationELB", "HTTPCode_Target_2XX_Count", "LoadBalancer", aws_lb.main.arn_suffix],
            ["AWS/ApplicationELB", "HTTPCode_Target_4XX_Count", "LoadBalancer", aws_lb.main.arn_suffix],
            ["AWS/ApplicationELB", "HTTPCode_Target_5XX_Count", "LoadBalancer", aws_lb.main.arn_suffix]
          ]
          view    = "timeSeries"
          stacked = false
          region  = data.aws_region.current.name
          title   = "Application Load Balancer Metrics"
          period  = 300
        }
      }
    ]
  })

  tags = local.common_tags
}

# CloudWatch Alarms for critical metrics
resource "aws_cloudwatch_metric_alarm" "high_cpu" {
  alarm_name          = "chainfinity-rds-high-cpu"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/RDS"
  period              = "300"
  statistic           = "Average"
  threshold           = "80"
  alarm_description   = "This metric monitors RDS CPU utilization"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    DBInstanceIdentifier = aws_db_instance.chainfinity_db.id
  }

  tags = local.common_tags
}

resource "aws_cloudwatch_metric_alarm" "database_connections" {
  alarm_name          = "chainfinity-rds-high-connections"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "DatabaseConnections"
  namespace           = "AWS/RDS"
  period              = "300"
  statistic           = "Average"
  threshold           = "80"
  alarm_description   = "This metric monitors RDS connection count"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    DBInstanceIdentifier = aws_db_instance.chainfinity_db.id
  }

  tags = local.common_tags
}

resource "aws_cloudwatch_metric_alarm" "alb_response_time" {
  alarm_name          = "chainfinity-alb-high-response-time"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "TargetResponseTime"
  namespace           = "AWS/ApplicationELB"
  period              = "300"
  statistic           = "Average"
  threshold           = "1"
  alarm_description   = "This metric monitors ALB response time"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    LoadBalancer = aws_lb.main.arn_suffix
  }

  tags = local.common_tags
}

# SNS Topic for alerts
resource "aws_sns_topic" "alerts" {
  name              = "chainfinity-alerts"
  kms_master_key_id = aws_kms_key.chainfinity.arn

  tags = merge(local.common_tags, {
    Name = "chainfinity-alerts"
    Type = "SNSTopic"
  })
}

resource "aws_sns_topic_subscription" "email_alerts" {
  count     = length(var.alert_email_addresses)
  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email_addresses[count.index]
}

# WAF Web ACL for additional security
resource "aws_wafv2_web_acl" "main" {
  count = var.enable_waf ? 1 : 0
  name  = "chainfinity-web-acl"
  scope = "REGIONAL"

  default_action {
    allow {}
  }

  # Rate limiting rule
  rule {
    name     = "RateLimitRule"
    priority = 1

    override_action {
      none {}
    }

    statement {
      rate_based_statement {
        limit              = 2000
        aggregate_key_type = "IP"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "RateLimitRule"
      sampled_requests_enabled   = true
    }

    action {
      block {}
    }
  }

  # AWS Managed Rules
  rule {
    name     = "AWSManagedRulesCommonRuleSet"
    priority = 2

    override_action {
      none {}
    }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesCommonRuleSet"
        vendor_name = "AWS"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "CommonRuleSetMetric"
      sampled_requests_enabled   = true
    }
  }

  # Known bad inputs rule
  rule {
    name     = "AWSManagedRulesKnownBadInputsRuleSet"
    priority = 3

    override_action {
      none {}
    }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesKnownBadInputsRuleSet"
        vendor_name = "AWS"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "KnownBadInputsRuleSetMetric"
      sampled_requests_enabled   = true
    }
  }

  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = "ChainFinityWebACL"
    sampled_requests_enabled   = true
  }

  tags = merge(local.common_tags, {
    Name = "chainfinity-web-acl"
    Type = "WAFv2WebACL"
  })
}

# Associate WAF with ALB
resource "aws_wafv2_web_acl_association" "main" {
  count        = var.enable_waf ? 1 : 0
  resource_arn = aws_lb.main.arn
  web_acl_arn  = aws_wafv2_web_acl.main[0].arn
}

# S3 bucket for backups
resource "aws_s3_bucket" "backups" {
  bucket        = "chainfinity-backups-${random_string.bucket_suffix.result}"
  force_destroy = var.environment != "production"

  tags = merge(local.common_tags, {
    Name = "chainfinity-backups"
    Type = "S3Bucket"
  })
}

resource "aws_s3_bucket_versioning" "backups" {
  bucket = aws_s3_bucket.backups.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "backups" {
  bucket = aws_s3_bucket.backups.id

  server_side_encryption_configuration {
    rule {
      apply_server_side_encryption_by_default {
        kms_master_key_id = aws_kms_key.chainfinity.arn
        sse_algorithm     = "aws:kms"
      }
    }
  }
}

resource "aws_s3_bucket_public_access_block" "backups" {
  bucket = aws_s3_bucket.backups.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_lifecycle_configuration" "backups" {
  bucket = aws_s3_bucket.backups.id

  rule {
    id     = "backup_lifecycle"
    status = "Enabled"

    transition {
      days          = 30
      storage_class = "STANDARD_IA"
    }

    transition {
      days          = 90
      storage_class = "GLACIER"
    }

    transition {
      days          = 365
      storage_class = "DEEP_ARCHIVE"
    }

    expiration {
      days = local.backup_retention_days
    }

    noncurrent_version_expiration {
      noncurrent_days = 30
    }
  }
}

