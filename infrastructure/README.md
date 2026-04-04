# ChainFinity Infrastructure

Financial-grade, production-ready infrastructure for the ChainFinity platform.
Covers Terraform (AWS), Kubernetes, Ansible, Vault, CI/CD, Docker, and Security.

---

## Quick Start

### Local Development (Docker Compose)

```bash
cp .env.example .env
# Edit .env and fill in all required secrets

docker compose up -d
```

Services available:
| Service | URL |
|-------------|----------------------------|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8080 |
| Prometheus | http://localhost:9090 |
| Grafana | http://localhost:3001 |
| Alertmanager| http://localhost:9093 |

---

## Directory Structure

```
infrastructure/
├── docker/                     # Docker build artifacts
│   ├── Dockerfile.frontend     # Multi-stage React/nginx build
│   ├── Dockerfile.backend      # Multi-stage Python build
│   ├── nginx-frontend.conf     # Nginx config for frontend container
│   ├── grafana/                # Grafana provisioning (datasources, dashboards)
│   ├── alertmanager/           # Alertmanager config
│   └── postgres/               # PostgreSQL init scripts
├── docker-compose.yml          # Full local dev stack
├── .env.example                # Environment variable template
│
├── terraform/                  # AWS infrastructure (EKS, RDS, VPC, etc.)
│   ├── main.tf                 # Core resources
│   ├── sg_fix.tf               # Security groups (circular-dep-free)
│   ├── variables.tf            # Input variables with validations
│   ├── outputs.tf              # Output values
│   ├── terraform.tfvars        # Production values (do NOT commit secrets)
│   ├── backend.example.tf      # S3 backend config (rename and fill in)
│   └── templates/
│       └── user_data.sh.tpl    # EKS node bootstrap script
│
├── kubernetes/                 # K8s manifests
│   ├── deployment.yaml         # Namespace, Deployments, Services, Ingress, HPA, PDB
│   ├── secret.example.yaml     # All required secrets (fill in, use Sealed Secrets in prod)
│   ├── backup/
│   │   └── cronjob.yaml        # PostgreSQL backup CronJob
│   ├── logging/
│   │   └── elasticsearch.yaml  # Elasticsearch StatefulSet (3-node cluster)
│   └── monitoring/
│       ├── prometheus-config.yaml  # Prometheus ConfigMap + Deployment
│       ├── grafana.yaml            # Grafana Deployment
│       └── alertmanager.yaml       # Alertmanager StatefulSet (2-node HA)
│
├── ansible/                    # Server configuration
│   ├── playbook.yml            # Main playbook
│   ├── inventory.ini           # Inventory (do not commit real IPs)
│   └── templates/
│       └── nginx.conf.j2       # Nginx reverse proxy (HTTP→HTTPS, rate-limiting)
│
├── security/
│   ├── certificates/
│   │   └── cert-manager-config.yaml  # ClusterIssuers, Certificates
│   ├── compliance/
│   │   └── compliance-framework.yaml # SOC2/PCI-DSS/GDPR controls
│   ├── policies/
│   │   ├── network-policies.yaml     # Zero-trust NetworkPolicies
│   │   └── rbac-policies.yaml        # RBAC Roles, Bindings, ServiceAccounts
│   └── vault/
│       ├── vault-config.hcl          # Vault server config (raft HA, KMS auto-unseal)
│       ├── init-vault.sh             # Vault initialisation script
│       └── policies/                 # Vault HCL policies
│
└── ci-cd/
    └── ci-cd.yml               # GitHub Actions pipeline
```

---

## Terraform Deployment

### Prerequisites

- Terraform >= 1.0
- AWS CLI configured (`aws sts get-caller-identity`)
- S3 bucket + DynamoDB table for state (see `backend.example.tf`)

### Steps

```bash
cd terraform

# 1. Configure backend
cp backend.example.tf backend.tf
# Edit backend.tf with your S3 bucket and DynamoDB table

# 2. Set secrets via environment (never in tfvars)
export TF_VAR_db_password="$(openssl rand -base64 24)"

# 3. Initialise
terraform init

# 4. Plan
terraform plan -var-file=terraform.tfvars

# 5. Apply
terraform apply -var-file=terraform.tfvars
```

---

## Kubernetes Deployment

```bash
# 1. Get kubeconfig
aws eks update-kubeconfig --region us-west-2 --name chainfinity-cluster

# 2. Create secrets (use Sealed Secrets or Vault in production)
# Fill in kubernetes/secret.example.yaml → save as secret.yaml
kubectl apply -f kubernetes/secret.yaml   # Never commit this file

# 3. Apply manifests
kubectl apply -f kubernetes/deployment.yaml
kubectl apply -f kubernetes/backup/cronjob.yaml
kubectl apply -f kubernetes/logging/elasticsearch.yaml
kubectl apply -f kubernetes/monitoring/prometheus-config.yaml
kubectl apply -f kubernetes/monitoring/grafana.yaml
kubectl apply -f kubernetes/monitoring/alertmanager.yaml

# 4. Verify rollout
kubectl rollout status deployment/chainfinity-frontend -n chainfinity
kubectl rollout status deployment/chainfinity-backend  -n chainfinity
```

---

## Vault Initialisation

```bash
export VAULT_ADDR=https://vault.chainfinity.internal:8200
export VAULT_POLICIES_DIR=/opt/vault/policies

bash security/vault/init-vault.sh
```

**Important:** Move unseal keys and root token off the server immediately after init.

---

## Security Notes

- All secrets must be injected via environment variables or Vault — never hardcoded.
- `terraform.tfvars` must never contain real passwords. Use `TF_VAR_*` env vars.
- `kubernetes/secret.example.yaml` is a template only — generated `secret.yaml` must not be committed.
- Network policies default-deny all traffic; only explicitly allowed paths are open.
- All pods run as non-root with `readOnlyRootFilesystem` where possible.
- EKS nodes use IMDSv2 (required, hop limit 2).
- RDS is not publicly accessible; only reachable from EKS node security group.

---

## Compliance

| Framework | Status | Notes                                      |
| --------- | ------ | ------------------------------------------ |
| SOC 2 II  | Ready  | Audit logging, encryption, access controls |
| PCI DSS   | Ready  | Network isolation, key management, logging |
| GDPR      | Ready  | Data retention policies, DPO contact       |
| SOX 404   | Ready  | ITGC controls, audit trail                 |
| ISO 27001 | Ready  | ISMS controls implemented                  |
