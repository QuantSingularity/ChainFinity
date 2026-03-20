# ChainFinity Infrastructure - Financial Grade Security

This directory contains the comprehensive infrastructure configuration for the ChainFinity project, enhanced with financial-grade security controls, compliance frameworks, and robust operational capabilities.

## 🏗️ Architecture Overview

The ChainFinity infrastructure implements a multi-layered security architecture designed to meet stringent financial industry standards including SOC 2, PCI DSS, GDPR, SOX, and ISO 27001 compliance requirements.

### Key Security Features

- **Zero-Trust Network Architecture**: Comprehensive network segmentation with strict access controls
- **End-to-End Encryption**: Data encryption at rest and in transit using AES-256 and TLS 1.3
- **Multi-Factor Authentication**: Integrated with HashiCorp Vault for secrets management
- **Comprehensive Audit Logging**: 7-year retention for financial compliance
- **Automated Security Scanning**: Continuous vulnerability assessment and remediation
- **Role-Based Access Control (RBAC)**: Principle of least privilege enforcement
- **Disaster Recovery**: Multi-region backup and recovery capabilities

## 📁 Directory Structure

```
infrastructure/
├── README.md                          # This file
├── docker-compose.prod.yml            # Production Docker Compose configuration
├── ansible/                           # Configuration management
│   ├── inventory.ini                  # Inventory configuration
│   ├── playbook.yml                   # Main playbook
│   └── templates/
│       └── nginx.conf.j2              # Nginx configuration template
├── jenkins/                           # CI/CD pipeline configuration
│   └── Jenkinsfile                    # Security pipeline
├── k8s/                               # Legacy Kubernetes configurations
│   └── risk-engine-deployment.yaml    # Risk engine deployment
├── kubernetes/                        # Kubernetes configurations
│   ├── deployment.yaml                # Comprehensive application deployment
│   ├── backup/
│   │   └── cronjob.yaml               # Backup automation
│   ├── logging/
│   │   └── elasticsearch.yaml         # Log aggregation
│   └── monitoring/
│       └── prometheus-config.yaml     # Comprehensive monitoring
├── terraform/                         # Infrastructure as Code
│   ├── main.tf                        # infrastructure configuration
│   ├── variables.tf                   # Comprehensive variable definitions
│   ├── outputs.tf                     # Infrastructure outputs
│   ├── terraform.tfvars               # Production configuration
│   └── templates/
│       └── user_data.sh.tpl           # Secure node initialization
├── security/                          # Security configurations
│   ├── vault/                         # HashiCorp Vault configuration
│   │   ├── vault-config.hcl           # Vault server configuration
│   │   ├── init-vault.sh              # Vault initialization script
│   │   └── policies/                  # Vault access policies
│   │       ├── admin-policy.hcl       # Administrator access
│   │       ├── developer-policy.hcl   # Developer access
│   │       ├── application-policy.hcl # Application access
│   │       └── readonly-policy.hcl    # Read-only access
│   ├── policies/                      # Security policies
│   │   ├── rbac-policies.yaml         # Kubernetes RBAC
│   │   └── network-policies.yaml      # Network security policies
│   ├── certificates/                  # Certificate management
│   │   └── cert-manager-config.yaml   # TLS certificate automation
│   └── compliance/                    # Compliance frameworks
│       └── compliance-framework.yaml  # SOC2, PCI-DSS, GDPR configuration
├── networking/                        # Network configurations
└── monitoring/                        # Monitoring
    └── security/                      # Security monitoring
```

## 🚀 Quick Start

### Prerequisites

1. **AWS Account** with appropriate permissions
2. **Terraform** v1.0.0 or later
3. **Ansible** v2.9 or later
4. **kubectl** configured with EKS cluster access
5. **Jenkins** server with necessary plugins
6. **Docker** and Docker Compose
7. **HashiCorp Vault** (optional, can be deployed via Terraform)

### 1. Infrastructure Deployment

#### Step 1: Configure Terraform Variables

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your specific configuration
```

**Important Security Configuration:**

- Update `allowed_cidr_blocks` with your organization's IP ranges
- Configure `alert_email_addresses` for security notifications
- Set strong passwords and use AWS Secrets Manager for sensitive data
- Review compliance framework settings

#### Step 2: Deploy Infrastructure

```bash
# Initialize Terraform
terraform init

# Review the deployment plan
terraform plan

# Deploy infrastructure (this will take 15-30 minutes)
terraform apply
```

#### Step 3: Configure kubectl

```bash
# Configure kubectl to connect to the EKS cluster
aws eks update-kubeconfig --region us-west-2 --name chainfinity-cluster
```

### 2. Security Setup

#### Step 1: Initialize HashiCorp Vault

```bash
cd security/vault
chmod +x init-vault.sh
./init-vault.sh
```

**⚠️ Security Notice:** Securely store the Vault unseal keys and root token. These are critical for disaster recovery.

#### Step 2: Deploy Security Policies

```bash
# Apply RBAC policies
kubectl apply -f security/policies/rbac-policies.yaml

# Apply network security policies
kubectl apply -f security/policies/network-policies.yaml

# Deploy certificate management
kubectl apply -f security/certificates/cert-manager-config.yaml
```

### 3. Application Deployment

#### Step 1: Deploy Kubernetes Applications

```bash
# Deploy the ChainFinity application
kubectl apply -f kubernetes/deployment.yaml

# Verify deployment
kubectl get pods -n chainfinity
kubectl get services -n chainfinity
```

#### Step 2: Configure Monitoring

```bash
# Deploy Prometheus monitoring
kubectl apply -f kubernetes/monitoring/prometheus-config.yaml

# Verify monitoring stack
kubectl get pods -n chainfinity-monitoring
```

### 4. Configuration Management with Ansible

```bash
cd ansible

# Update inventory with your server details
vim inventory.ini

# Run the configuration playbook
ansible-playbook -i inventory.ini playbook.yml
```

## 🔒 Security Features

### Encryption

- **Data at Rest**: AES-256 encryption for all storage (EBS, S3, RDS)
- **Data in Transit**: TLS 1.3 for all communications
- **Key Management**: AWS KMS with automatic key rotation
- **Secrets Management**: HashiCorp Vault with dynamic secrets

### Access Control

- **Multi-Factor Authentication**: Required for all user access
- **Role-Based Access Control**: Kubernetes RBAC with principle of least privilege
- **Service Accounts**: Dedicated service accounts with minimal permissions
- **API Authentication**: JWT tokens with short expiration times

### Network Security

- **VPC Isolation**: Private subnets for all application components
- **Network Segmentation**: Separate subnets for different tiers
- **Security Groups**: Restrictive firewall rules
- **Network Policies**: Kubernetes network policies for pod-to-pod communication
- **WAF Protection**: AWS WAF with OWASP Top 10 protection

### Monitoring and Auditing

- **Comprehensive Logging**: All actions logged with 7-year retention
- **Real-time Monitoring**: Prometheus and Grafana dashboards
- **Security Scanning**: Automated vulnerability assessments
- **Compliance Monitoring**: Continuous compliance checking
- **Incident Response**: Automated alerting and response procedures

## 📊 Compliance Frameworks

### SOC 2 Type II

- **Security**: Multi-layered security controls
- **Availability**: 99.9% uptime SLA with redundancy
- **Processing Integrity**: Data validation and error handling
- **Confidentiality**: Encryption and access controls
- **Privacy**: GDPR-compliant data handling

### PCI DSS Level 1

- **Network Security**: Segmented networks with firewalls
- **Data Protection**: Encryption of cardholder data
- **Access Control**: Strong authentication and authorization
- **Monitoring**: Comprehensive logging and monitoring
- **Security Testing**: Regular vulnerability assessments

### GDPR Compliance

- **Data Minimization**: Collect only necessary data
- **Consent Management**: Explicit consent mechanisms
- **Right to Erasure**: Data deletion capabilities
- **Data Portability**: Export functionality
- **Privacy by Design**: Built-in privacy controls

## 🚨 Troubleshooting

### Common Issues

#### 1. Terraform Apply Fails

```bash
# Check AWS credentials
aws sts get-caller-identity

# Verify resource limits
aws service-quotas list-service-quotas --service-code ec2

# Check for existing resources
terraform state list
```

#### 2. Kubernetes Pods Not Starting

```bash
# Check pod status
kubectl describe pod <pod-name> -n chainfinity

# Check logs
kubectl logs <pod-name> -n chainfinity

# Check resource usage
kubectl top pods -n chainfinity
```

#### 3. Vault Initialization Issues

```bash
# Check Vault status
vault status

# Check Vault logs
kubectl logs -l app=vault -n chainfinity-security

# Verify network connectivity
kubectl exec -it <vault-pod> -n chainfinity-security -- vault status
```

#### 4. Certificate Issues

```bash
# Check certificate status
kubectl get certificates -n chainfinity

# Check cert-manager logs
kubectl logs -l app=cert-manager -n cert-manager

# Verify DNS configuration
nslookup chainfinity.com
```

### Emergency Procedures

#### Security Incident Response

1. **Immediate Actions**:
   - Isolate affected systems
   - Preserve evidence
   - Notify security team

2. **Assessment**:
   - Determine scope and impact
   - Classify incident severity
   - Activate incident response team

3. **Containment**:
   - Block malicious traffic
   - Revoke compromised credentials
   - Apply emergency patches

#### Disaster Recovery

1. **Database Recovery**:

   ```bash
   # Restore from backup
   aws rds restore-db-instance-from-db-snapshot \
     --db-instance-identifier chainfinity-db-restored \
     --db-snapshot-identifier chainfinity-db-snapshot-YYYY-MM-DD
   ```

2. **Application Recovery**:

   ````bash
   # Deploy to DR region
   terraform apply -var="region=us-east-1"

   # Update DNS to point to DR region
   aws route53 change-resource-record-sets \
     --hosted-zone-id Z123456789 \
     --change-batch file://dns-failover.json
   ```s
   ````

## 🔧 Validation & Deployment Commands

### Prerequisites Installation

```bash
# Install Terraform
wget https://releases.hashicorp.com/terraform/1.6.6/terraform_1.6.6_linux_amd64.zip
unzip terraform_1.6.6_linux_amd64.zip
sudo mv terraform /usr/local/bin/

# Install kubectl
curl -LO "https://dl.k8s.io/release/v1.28.0/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

# Install yamllint
pip install yamllint

# Install ansible-lint
pip install ansible-lint

# Install helm (optional)
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
```

### Terraform Validation

```bash
cd infrastructure/terraform

# 1. Format check (should show no changes)
terraform fmt -recursive -check

# 2. Initialize with local backend for testing
terraform init -backend=false

# 3. Validate configuration
terraform validate

# 4. Plan with example variables (local dev)
terraform plan -var-file=terraform.tfvars.example -out=plan.out

# For production deployment with actual values:
# terraform init -backend-config="bucket=YOUR_BUCKET"
# export TF_VAR_db_password="YOUR_ACTUAL_PASSWORD"
# terraform plan -var-file=terraform.tfvars
```

### Kubernetes Validation

```bash
cd infrastructure/kubernetes

# 1. YAML lint check
yamllint deployment.yaml
yamllint backup/cronjob.yaml
yamllint logging/elasticsearch.yaml
yamllint monitoring/prometheus-config.yaml

# 2. Kubernetes dry-run validation
kubectl apply --dry-run=client -f deployment.yaml
kubectl apply --dry-run=client -f backup/cronjob.yaml
kubectl apply --dry-run=client -f logging/elasticsearch.yaml
kubectl apply --dry-run=client -f monitoring/prometheus-config.yaml

# 3. Apply to cluster (with caution)
kubectl apply -f deployment.yaml
kubectl apply -f backup/cronjob.yaml
```

### Ansible Validation

```bash
cd infrastructure/ansible

# 1. Syntax check
ansible-playbook playbook.yml --syntax-check

# 2. Lint check
ansible-lint playbook.yml

# 3. Dry run
ansible-playbook -i inventory.example.ini playbook.yml --check

# 4. Actual run (with caution)
# ansible-playbook -i inventory.ini playbook.yml
```

### CI/CD Pipeline Validation

```bash
cd infrastructure/ci-cd

# 1. Validate YAML syntax
yamllint ci-cd.yml

# 2. If using GitHub Actions locally (with act):
# act -n  # Dry run
# act push  # Test push event
```

## 🔐 Secret Management

**IMPORTANT**: Never commit secrets to version control!

### Using Terraform with Secrets

```bash
# Option 1: Environment variables
export TF_VAR_db_password="your-password"
export AWS_ACCESS_KEY_ID="your-key"
export AWS_SECRET_ACCESS_KEY="your-secret"

# Option 2: terraform.tfvars (add to .gitignore)
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with actual values

# Option 3: AWS Secrets Manager (recommended for production)
# Secrets are automatically retrieved by Terraform
```

### Using Kubernetes Secrets

```bash
# Option 1: kubectl create secret
kubectl create secret generic chainfinity-secrets \
  --from-literal=DB_PASSWORD='your-password' \
  --from-literal=JWT_SECRET='your-jwt-secret' \
  -n chainfinity

# Option 2: From file
cp kubernetes/secret.example.yaml kubernetes/secret.yaml
# Edit secret.yaml with actual values (add to .gitignore)
kubectl apply -f kubernetes/secret.yaml

# Option 3: External Secrets Operator (recommended for production)
# Configure External Secrets to pull from AWS Secrets Manager or Vault
```

### Using Ansible Vault

```bash
# Create encrypted vault file
ansible-vault create ansible/vault.yml

# Add secrets to vault:
# db_password: your_actual_password
# api_key: your_actual_api_key

# Run playbook with vault
ansible-playbook -i inventory.ini playbook.yml --ask-vault-pass
```
