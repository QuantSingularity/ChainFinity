#!/bin/bash
# ChainFinity EKS Node User Data Script
# Financial Grade Security Configuration

set -euo pipefail

# Logging function
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a /var/log/chainfinity-bootstrap.log
}

log "Starting ChainFinity EKS node bootstrap process..."

# Update system packages
log "Updating system packages..."
yum update -y

# Install additional security tools
log "Installing security tools..."
yum install -y \
    awscli \
    jq \
    htop \
    iotop \
    tcpdump \
    strace \
    lsof \
    nc \
    telnet \
    wget \
    curl \
    git \
    unzip \
    amazon-cloudwatch-agent \
    amazon-ssm-agent

# Configure CloudWatch agent
log "Configuring CloudWatch agent..."
cat > /opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json << 'EOF'
{
    "agent": {
        "metrics_collection_interval": 60,
        "run_as_user": "cwagent"
    },
    "logs": {
        "logs_collected": {
            "files": {
                "collect_list": [
                    {
                        "file_path": "/var/log/messages",
                        "log_group_name": "/aws/eks/chainfinity/system",
                        "log_stream_name": "{instance_id}/messages",
                        "retention_in_days": 2555
                    },
                    {
                        "file_path": "/var/log/secure",
                        "log_group_name": "/aws/eks/chainfinity/security",
                        "log_stream_name": "{instance_id}/secure",
                        "retention_in_days": 2555
                    },
                    {
                        "file_path": "/var/log/audit/audit.log",
                        "log_group_name": "/aws/eks/chainfinity/audit",
                        "log_stream_name": "{instance_id}/audit",
                        "retention_in_days": 2555
                    },
                    {
                        "file_path": "/var/log/chainfinity-bootstrap.log",
                        "log_group_name": "/aws/eks/chainfinity/bootstrap",
                        "log_stream_name": "{instance_id}/bootstrap",
                        "retention_in_days": 365
                    }
                ]
            }
        }
    },
    "metrics": {
        "namespace": "ChainFinity/EKS",
        "metrics_collected": {
            "cpu": {
                "measurement": [
                    "cpu_usage_idle",
                    "cpu_usage_iowait",
                    "cpu_usage_user",
                    "cpu_usage_system"
                ],
                "metrics_collection_interval": 60,
                "totalcpu": false
            },
            "disk": {
                "measurement": [
                    "used_percent"
                ],
                "metrics_collection_interval": 60,
                "resources": [
                    "*"
                ]
            },
            "diskio": {
                "measurement": [
                    "io_time",
                    "read_bytes",
                    "write_bytes",
                    "reads",
                    "writes"
                ],
                "metrics_collection_interval": 60,
                "resources": [
                    "*"
                ]
            },
            "mem": {
                "measurement": [
                    "mem_used_percent"
                ],
                "metrics_collection_interval": 60
            },
            "netstat": {
                "measurement": [
                    "tcp_established",
                    "tcp_time_wait"
                ],
                "metrics_collection_interval": 60
            },
            "swap": {
                "measurement": [
                    "swap_used_percent"
                ],
                "metrics_collection_interval": 60
            }
        }
    }
}
EOF

# Start CloudWatch agent
log "Starting CloudWatch agent..."
systemctl enable amazon-cloudwatch-agent
systemctl start amazon-cloudwatch-agent

# Configure audit logging
log "Configuring audit logging..."
cat >> /etc/audit/rules.d/chainfinity.rules << 'EOF'
# ChainFinity Audit Rules for Financial Compliance

# Monitor file access
-w /etc/passwd -p wa -k identity
-w /etc/group -p wa -k identity
-w /etc/shadow -p wa -k identity
-w /etc/sudoers -p wa -k identity

# Monitor network configuration
-w /etc/hosts -p wa -k network
-w /etc/resolv.conf -p wa -k network

# Monitor system calls
-a always,exit -F arch=b64 -S adjtimex -S settimeofday -k time-change
-a always,exit -F arch=b32 -S adjtimex -S settimeofday -S stime -k time-change
-a always,exit -F arch=b64 -S clock_settime -k time-change
-a always,exit -F arch=b32 -S clock_settime -k time-change

# Monitor privileged commands
-a always,exit -F path=/usr/bin/sudo -F perm=x -F auid>=1000 -F auid!=4294967295 -k privileged
-a always,exit -F path=/usr/bin/su -F perm=x -F auid>=1000 -F auid!=4294967295 -k privileged

# Monitor file deletions
-a always,exit -F arch=b64 -S unlink -S unlinkat -S rename -S renameat -F auid>=1000 -F auid!=4294967295 -k delete
-a always,exit -F arch=b32 -S unlink -S unlinkat -S rename -S renameat -F auid>=1000 -F auid!=4294967295 -k delete
EOF

# Restart auditd
systemctl restart auditd

# Configure sysctl for security
log "Configuring kernel security parameters..."
cat >> /etc/sysctl.d/99-chainfinity-security.conf << 'EOF'
# ChainFinity Security Configuration

# Network security
net.ipv4.ip_forward = 1
net.ipv4.conf.all.send_redirects = 0
net.ipv4.conf.default.send_redirects = 0
net.ipv4.conf.all.accept_redirects = 0
net.ipv4.conf.default.accept_redirects = 0
net.ipv4.conf.all.accept_source_route = 0
net.ipv4.conf.default.accept_source_route = 0
net.ipv4.conf.all.log_martians = 1
net.ipv4.conf.default.log_martians = 1
net.ipv4.icmp_echo_ignore_broadcasts = 1
net.ipv4.icmp_ignore_bogus_error_responses = 1
net.ipv4.tcp_syncookies = 1

# Memory protection
kernel.dmesg_restrict = 1
kernel.kptr_restrict = 2
kernel.yama.ptrace_scope = 1

# File system security
fs.suid_dumpable = 0
fs.protected_hardlinks = 1
fs.protected_symlinks = 1
EOF

sysctl -p /etc/sysctl.d/99-chainfinity-security.conf

# Configure fail2ban for intrusion prevention
log "Installing and configuring fail2ban..."
amazon-linux-extras install epel -y
yum install -y fail2ban

cat > /etc/fail2ban/jail.local << 'EOF'
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 3
backend = systemd

[sshd]
enabled = true
port = ssh
logpath = /var/log/secure
maxretry = 3
bantime = 3600
EOF

systemctl enable fail2ban
systemctl start fail2ban

# Configure Docker daemon for security
log "Configuring Docker daemon..."
mkdir -p /etc/docker
cat > /etc/docker/daemon.json << 'EOF'
{
    "log-driver": "awslogs",
    "log-opts": {
        "awslogs-group": "/aws/eks/chainfinity/docker",
        "awslogs-region": "us-west-2",
        "awslogs-stream-prefix": "docker"
    },
    "storage-driver": "overlay2",
    "storage-opts": [
        "overlay2.override_kernel_check=true"
    ],
    "exec-opts": ["native.cgroupdriver=systemd"],
    "live-restore": true,
    "userland-proxy": false,
    "no-new-privileges": true,
    "seccomp-profile": "/etc/docker/seccomp.json",
    "disable-legacy-registry": true
}
EOF

# Download Docker seccomp profile
curl -o /etc/docker/seccomp.json https://raw.githubusercontent.com/moby/moby/master/profiles/seccomp/default.json

# Configure kubelet with security settings
log "Configuring kubelet..."
mkdir -p /etc/kubernetes/kubelet

# Set up EKS bootstrap
log "Bootstrapping EKS node..."

# Get instance metadata
INSTANCE_ID=$(curl -s http://169.254.169.254/latest/meta-data/instance-id)
REGION=$(curl -s http://169.254.169.254/latest/meta-data/placement/region)

# Configure kubelet extra args for security
KUBELET_EXTRA_ARGS="--node-labels=chainfinity.com/instance-id=$INSTANCE_ID"
KUBELET_EXTRA_ARGS="$KUBELET_EXTRA_ARGS --protect-kernel-defaults=true"
KUBELET_EXTRA_ARGS="$KUBELET_EXTRA_ARGS --read-only-port=0"
KUBELET_EXTRA_ARGS="$KUBELET_EXTRA_ARGS --anonymous-auth=false"
KUBELET_EXTRA_ARGS="$KUBELET_EXTRA_ARGS --authorization-mode=Webhook"
KUBELET_EXTRA_ARGS="$KUBELET_EXTRA_ARGS --client-ca-file=/etc/kubernetes/pki/ca.crt"
KUBELET_EXTRA_ARGS="$KUBELET_EXTRA_ARGS --event-qps=0"
KUBELET_EXTRA_ARGS="$KUBELET_EXTRA_ARGS --rotate-certificates=true"
KUBELET_EXTRA_ARGS="$KUBELET_EXTRA_ARGS --rotate-server-certificates=true"
KUBELET_EXTRA_ARGS="$KUBELET_EXTRA_ARGS --tls-cipher-suites=TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256,TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384"

# Bootstrap the node
/etc/eks/bootstrap.sh ${cluster_name} \
    --apiserver-endpoint ${cluster_endpoint} \
    --b64-cluster-ca ${cluster_ca} \
    --kubelet-extra-args "$KUBELET_EXTRA_ARGS" \
    ${bootstrap_arguments} \
    --use-max-pods false

# Install additional monitoring tools
log "Installing additional monitoring tools..."

# Install node_exporter for Prometheus monitoring
useradd --no-create-home --shell /bin/false node_exporter
wget https://github.com/prometheus/node_exporter/releases/download/v1.6.1/node_exporter-1.6.1.linux-amd64.tar.gz
tar xvf node_exporter-1.6.1.linux-amd64.tar.gz
cp node_exporter-1.6.1.linux-amd64/node_exporter /usr/local/bin/
chown node_exporter:node_exporter /usr/local/bin/node_exporter
rm -rf node_exporter-1.6.1.linux-amd64*

# Create systemd service for node_exporter
cat > /etc/systemd/system/node_exporter.service << 'EOF'
[Unit]
Description=Node Exporter
Wants=network-online.target
After=network-online.target

[Service]
User=node_exporter
Group=node_exporter
Type=simple
ExecStart=/usr/local/bin/node_exporter \
    --collector.systemd \
    --collector.processes \
    --collector.interrupts \
    --collector.tcpstat \
    --collector.meminfo_numa \
    --no-collector.arp \
    --no-collector.bcache \
    --no-collector.bonding \
    --no-collector.conntrack \
    --no-collector.edac \
    --no-collector.entropy \
    --no-collector.filefd \
    --no-collector.hwmon \
    --no-collector.infiniband \
    --no-collector.ipvs \
    --no-collector.mdadm \
    --no-collector.netclass \
    --no-collector.netstat \
    --no-collector.nfs \
    --no-collector.nfsd \
    --no-collector.pressure \
    --no-collector.rapl \
    --no-collector.schedstat \
    --no-collector.sockstat \
    --no-collector.softnet \
    --no-collector.stat \
    --no-collector.textfile \
    --no-collector.thermal_zone \
    --no-collector.time \
    --no-collector.timex \
    --no-collector.udp_queues \
    --no-collector.uname \
    --no-collector.vmstat \
    --no-collector.xfs \
    --no-collector.zfs

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable node_exporter
systemctl start node_exporter

# Configure log rotation
log "Configuring log rotation..."
cat > /etc/logrotate.d/chainfinity << 'EOF'
/var/log/chainfinity-*.log {
    daily
    missingok
    rotate 2555
    compress
    delaycompress
    notifempty
    create 644 root root
    postrotate
        /bin/systemctl reload rsyslog > /dev/null 2>&1 || true
    endscript
}
EOF

# Set up automatic security updates
log "Configuring automatic security updates..."
yum install -y yum-cron
sed -i 's/update_cmd = default/update_cmd = security/' /etc/yum/yum-cron.conf
sed -i 's/apply_updates = no/apply_updates = yes/' /etc/yum/yum-cron.conf
systemctl enable yum-cron
systemctl start yum-cron

# Configure SSH hardening
log "Hardening SSH configuration..."
cp /etc/ssh/sshd_config /etc/ssh/sshd_config.backup
cat >> /etc/ssh/sshd_config << 'EOF'

# ChainFinity SSH Security Configuration
Protocol 2
PermitRootLogin no
PasswordAuthentication no
PermitEmptyPasswords no
ChallengeResponseAuthentication no
UsePAM yes
X11Forwarding no
PrintMotd no
ClientAliveInterval 300
ClientAliveCountMax 2
MaxAuthTries 3
MaxSessions 2
LoginGraceTime 60
AllowUsers ec2-user
EOF

systemctl restart sshd

# Install and configure AIDE (Advanced Intrusion Detection Environment)
log "Installing and configuring AIDE..."
yum install -y aide
aide --init
mv /var/lib/aide/aide.db.new.gz /var/lib/aide/aide.db.gz

# Create AIDE check script
cat > /usr/local/bin/aide-check.sh << 'EOF'
#!/bin/bash
# AIDE integrity check script

AIDE_LOG="/var/log/aide.log"
AIDE_REPORT="/tmp/aide-report.txt"

# Run AIDE check
aide --check > "$AIDE_REPORT" 2>&1
AIDE_EXIT_CODE=$?

# Log results
echo "[$(date)] AIDE check completed with exit code: $AIDE_EXIT_CODE" >> "$AIDE_LOG"

# If changes detected, send alert
if [ $AIDE_EXIT_CODE -ne 0 ]; then
    echo "[$(date)] AIDE detected file system changes" >> "$AIDE_LOG"
    cat "$AIDE_REPORT" >> "$AIDE_LOG"

    # Send to CloudWatch Logs
    aws logs put-log-events \
        --log-group-name "/aws/eks/chainfinity/security" \
        --log-stream-name "$(curl -s http://169.254.169.254/latest/meta-data/instance-id)/aide" \
        --log-events timestamp=$(date +%s000),message="AIDE detected file system changes: $(cat $AIDE_REPORT | head -20)" \
        --region us-west-2 || true
fi

# Clean up
rm -f "$AIDE_REPORT"
EOF

chmod +x /usr/local/bin/aide-check.sh

# Schedule AIDE checks
echo "0 2 * * * root /usr/local/bin/aide-check.sh" >> /etc/crontab

# Final security configurations
log "Applying final security configurations..."

# Disable unused services
systemctl disable postfix || true
systemctl stop postfix || true

# Set file permissions
chmod 600 /etc/ssh/sshd_config
chmod 644 /etc/passwd
chmod 644 /etc/group
chmod 600 /etc/shadow
chmod 600 /etc/gshadow

# Create compliance report
log "Creating compliance report..."
cat > /var/log/chainfinity-compliance-report.json << EOF
{
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "instance_id": "$INSTANCE_ID",
    "region": "$REGION",
    "compliance_checks": {
        "audit_logging_enabled": true,
        "fail2ban_installed": true,
        "ssh_hardened": true,
        "automatic_updates_enabled": true,
        "aide_installed": true,
        "cloudwatch_agent_installed": true,
        "node_exporter_installed": true,
        "docker_security_configured": true,
        "kernel_security_parameters_set": true,
        "log_rotation_configured": true
    },
    "security_tools": {
        "fail2ban": "$(fail2ban-client version 2>/dev/null || echo 'not available')",
        "aide": "$(aide --version 2>/dev/null | head -1 || echo 'not available')",
        "cloudwatch_agent": "$(amazon-cloudwatch-agent-ctl -m ec2 -c file:/opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json -a query | jq -r '.status' 2>/dev/null || echo 'not available')"
    }
}
EOF

# Send compliance report to CloudWatch
aws logs put-log-events \
    --log-group-name "/aws/eks/chainfinity/compliance" \
    --log-stream-name "$INSTANCE_ID/bootstrap" \
    --log-events timestamp=$(date +%s000),message="$(cat /var/log/chainfinity-compliance-report.json)" \
    --region us-west-2 || true

log "ChainFinity EKS node bootstrap completed successfully!"
log "Compliance report generated at: /var/log/chainfinity-compliance-report.json"

# Signal completion
/opt/aws/bin/cfn-signal -e $? --stack ${AWS::StackName} --resource AutoScalingGroup --region ${AWS::Region} || true
