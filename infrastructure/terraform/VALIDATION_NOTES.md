# ChainFinity Terraform Validation Notes

## Fixes Applied

### Security Groups (sg_fix.tf)

The original `main.tf` had circular dependencies between `alb`, `eks_cluster`, and `eks_nodes`
security groups (each inline egress/ingress block referenced the other). This was broken out
into `sg_fix.tf` using `aws_security_group_rule` resources. The original broken SG blocks have
been removed from `main.tf` entirely.

### EKS Node Group

- Removed `instance_types`, `ami_type`, and `disk_size` from `aws_eks_node_group` — all three
  are invalid when a `launch_template` is specified (AWS API error).
- `instance_type` is now set only in the launch template.

### S3 Bucket Encryption

`aws_s3_bucket_encryption` is not a valid Terraform AWS provider resource. Renamed to
`aws_s3_bucket_server_side_encryption_configuration` for both `alb_logs` and `backups` buckets.

### RDS Backup Retention

`backup_retention_period` was set to `local.backup_retention_days` (3653). AWS RDS maximum is
35 days. Changed to `min(var.backup_retention_days, 35)`. For longer compliance retention,
use AWS Backup plans with snapshot copy to S3.

### WAF Resources

`aws_wafv2_web_acl` and `aws_wafv2_web_acl_association` were always created, ignoring
`var.enable_waf`. Added `count = var.enable_waf ? 1 : 0`. Updated outputs accordingly.

### User Data Template

Removed the `local_file` resource anti-pattern (wrote rendered template to disk, breaking
CI/CD pipelines). Launch template now calls `templatefile()` directly on `user_data.sh.tpl`.
Fixed `bootstrap_arguments` variable which was passed but not used in the template.

### Tags

`timestamp()` in `common_tags.CreatedDate` caused perpetual diffs on every `terraform plan`.
Replaced with the static string `"managed-by-terraform"`.

### ALB TLS Policy

Updated from deprecated `ELBSecurityPolicy-TLS-1-2-2017-01` to
`ELBSecurityPolicy-TLS13-1-2-2021-06` (supports TLS 1.2 and 1.3).

### db_password Validation

Added a `validation` block to `var.db_password` rejecting short values and common placeholder
strings (`CHANGE_ME`, `password`, `admin`, `default`).

### Outputs

WAF outputs updated to be conditional (`var.enable_waf ? ... : null`) with `[0]` index.

## Pre-Apply Checklist

1. Set required variables:

   ```
   export TF_VAR_db_password="$(openssl rand -base64 24)"
   ```

2. Configure S3 backend in `backend.example.tf` → rename to `backend.tf`

3. Ensure AWS credentials are configured:

   ```
   aws sts get-caller-identity
   ```

4. Run validation:

   ```
   terraform init
   terraform fmt -recursive -check
   terraform validate
   terraform plan -var-file=terraform.tfvars
   ```

5. For production, review and apply:
   ```
   terraform apply -var-file=terraform.tfvars
   ```
