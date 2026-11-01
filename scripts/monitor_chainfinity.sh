#!/bin/bash
# ChainFinity Monitoring Script
# This script provides comprehensive monitoring for the ChainFinity platform

# --- Configuration ---
# Exit immediately if a command exits with a non-zero status, treat unset variables as an error, and fail if any command in a pipeline fails
set -euo pipefail

# Color definitions
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default Configuration
CONFIG_FILE="monitor_config.json"
LOG_DIR="./logs"
ALERT_THRESHOLD=80
CHECK_INTERVAL=300 # 5 minutes
REPORT_INTERVAL=86400 # 24 hours
SLACK_WEBHOOK=""
EMAIL_RECIPIENT=""

# --- Utility Functions ---

# Function to log messages
log() {
  local level="$1"
  local message="$2"
  local timestamp
  timestamp=$(date +"%Y-%m-%d %H:%M:%S")

  case $level in
    "INFO")
      echo -e "${BLUE}[${timestamp}] [${level}] ${message}${NC}"
      ;;
    "WARNING")
      echo -e "${YELLOW}[${timestamp}] [${level}] ${message}${NC}"
      ;;
    "ERROR")
      echo -e "${RED}[${timestamp}] [${level}] ${message}${NC}"
      ;;
    "SUCCESS")
      echo -e "${GREEN}[${timestamp}] [${level}] ${message}${NC}"
      ;;
  esac

  # Append to log file, ensure LOG_FILE is set
  if [ -n "${LOG_FILE:-}" ]; then
    echo "[${timestamp}] [${level}] ${message}" >> "$LOG_FILE"
  fi
}

# Function to check if a command exists
command_exists() {
  command -v "$1" >/dev/null 2>&1
}

# Function to send alerts
send_alert() {
  local subject="$1"
  local message="$2"
  local severity="$3" # critical, warning, info

  log "WARNING" "Alert: $subject - $message"

  # Send to Slack if configured
  if [ -n "$SLACK_WEBHOOK" ]; then
    local color
    case $severity in
      "critical") color="#FF0000" ;; # Red
      "warning") color="#FFA500" ;; # Orange
      "info") color="#0000FF" ;; # Blue
      *) color="#808080" ;; # Gray
    esac

    # Use curl with a timeout and silent mode
    curl -s --max-time 5 -X POST -H 'Content-type: application/json' \
      --data "{\"attachments\":[{\"color\":\"$color\",\"title\":\"$subject\",\"text\":\"$message\"}]}" \
      "$SLACK_WEBHOOK" || log "ERROR" "Failed to send Slack alert."
  fi

  # Send email if configured
  if [ -n "$EMAIL_RECIPIENT" ]; then
    # Use mail command if available
    if command_exists mail; then
      echo "$message" | mail -s "ChainFinity Monitor: $subject" "$EMAIL_RECIPIENT" || log "ERROR" "Failed to send email alert."
    else
      log "WARNING" "Mail command not found. Cannot send email alerts."
    fi
  fi
}

# --- Monitoring Checks ---

# Function to check system resources
check_system_resources() {
  log "INFO" "Checking system resources..."

  # Check CPU usage (using 'top' is unreliable for a single snapshot, using 'mpstat' or 'iostat' is better, but 'top' is common)
  # Using awk to get the idle percentage and calculating usage
  local cpu_idle
  cpu_idle=$(top -bn1 | grep "Cpu(s)" | awk '{print $8}' | cut -d ',' -f 1)
  local cpu_usage
  cpu_usage=$(echo "100 - $cpu_idle" | bc)

  if (( $(echo "$cpu_usage > $ALERT_THRESHOLD" | bc -l) )); then
    send_alert "High CPU Usage" "CPU usage is at ${cpu_usage}%" "warning"
  fi

  # Check memory usage
  local mem_total
  mem_total=$(free -m | awk '/Mem:/ {print $2}')
  local mem_used
  mem_used=$(free -m | awk '/Mem:/ {print $3}')
  # Avoid division by zero
  if [ "$mem_total" -gt 0 ]; then
    local mem_usage
    mem_usage=$(echo "scale=2; $mem_used * 100 / $mem_total" | bc)

    if (( $(echo "$mem_usage > $ALERT_THRESHOLD" | bc -l) )); then
      send_alert "High Memory Usage" "Memory usage is at ${mem_usage}%" "warning"
    fi
  fi

  # Check disk usage
  local disk_usage
  disk_usage=$(df -h / | awk 'NR==2 {print $5}' | tr -d '%')
  if [ -n "$disk_usage" ] && [ "$disk_usage" -gt "$ALERT_THRESHOLD" ]; then
    send_alert "High Disk Usage" "Disk usage is at ${disk_usage}%" "warning"
  fi

  log "SUCCESS" "System resource check completed"
}

# Function to check Docker containers
check_docker_containers() {
  log "INFO" "Checking Docker containers..."

  if ! command_exists docker; then
    log "WARNING" "Docker is not installed. Skipping container check."
    return
  fi

  # Get all running containers
  local containers
  containers=$(docker ps --format "{{.Names}}")

  for container in $containers; do
    local status
    status=$(docker inspect --format='{{.State.Status}}' "$container")
    local health
    health=$(docker inspect --format='{{if .State.Health}}{{.State.Health.Status}}{{else}}N/A{{end}}' "$container")

    if [ "$status" != "running" ]; then
      send_alert "Container Not Running" "Container $container is $status" "critical"
    elif [ "$health" == "unhealthy" ]; then
      send_alert "Unhealthy Container" "Container $container is unhealthy" "critical"
    fi

    # Check container resource usage (docker stats is interactive, better to use a single shot command)
    # Using 'docker stats --no-stream' is the correct approach for a script
    local stats
    stats=$(docker stats --no-stream --format "{{.CPUPerc}}\t{{.MemPerc}}" "$container" 2>/dev/null)
    if [ -n "$stats" ]; then
      local cpu_perc
      cpu_perc=$(echo "$stats" | awk '{print $1}' | tr -d '%')
      local mem_perc
      mem_perc=$(echo "$stats" | awk '{print $2}' | tr -d '%')

      if (( $(echo "$cpu_perc > $ALERT_THRESHOLD" | bc -l) )); then
        send_alert "High Container CPU Usage" "Container $container CPU usage is at ${cpu_perc}%" "warning"
      fi

      if (( $(echo "$mem_perc > $ALERT_THRESHOLD" | bc -l) )); then
        send_alert "High Container Memory Usage" "Container $container memory usage is at ${mem_perc}%" "warning"
      fi
    fi
  done

  log "SUCCESS" "Docker container check completed"
}

# Function to check database health
check_database_health() {
  log "INFO" "Checking database health..."

  # Check PostgreSQL (assuming connection details are in .env or hardcoded for monitoring)
  # This check is highly dependent on the environment. We'll use a generic check.
  if command_exists psql; then
    # Attempt a simple connection check
    if ! psql -h localhost -U postgres -c "SELECT 1" > /dev/null 2>&1; then
      send_alert "Database Connection Failed" "Cannot connect to PostgreSQL database" "critical"
    else
      log "INFO" "PostgreSQL connection successful."
    fi
  fi

  # Check Redis
  if command_exists redis-cli; then
    if ! redis-cli ping > /dev/null 2>&1; then
      send_alert "Redis Connection Failed" "Cannot connect to Redis" "critical"
    else
      log "INFO" "Redis connection successful."
    fi
  fi

  log "SUCCESS" "Database health check completed"
}

# Function to check API endpoints
check_api_endpoints() {
  log "INFO" "Checking API endpoints..."

  # Load endpoints from config file
  if [ -f "$CONFIG_FILE" ]; then
    # Check if jq is installed
    if ! command_exists jq; then
      log "ERROR" "jq is required to parse $CONFIG_FILE. Skipping API check."
      return 1
    fi

    # Use a secure way to iterate over JSON array
    local endpoints
    endpoints=$(jq -r '.api_endpoints[] | "\(.name)\t\(.url)"' "$CONFIG_FILE")

    echo "$endpoints" | while IFS=$'\t' read -r name url; do
      if [ -z "$url" ]; then
        continue
      fi
      # Use curl with a timeout and silent mode
      local response
      response=$(curl -s --max-time 10 -o /dev/null -w "%{http_code}" "$url")

      if [ "$response" != "200" ]; then
        send_alert "API Endpoint Down" "Endpoint $name ($url) returned status code $response" "critical"
      else
        log "INFO" "API Endpoint $name ($url) is healthy (Status: $response)."
      fi
    done
  else
    log "WARNING" "Config file not found: $CONFIG_FILE. Skipping API check."
  fi

  log "SUCCESS" "API endpoint check completed"
}

# Function to check blockchain nodes
check_blockchain_nodes() {
  log "INFO" "Checking blockchain nodes..."

  if [ -f "$CONFIG_FILE" ]; then
    if ! command_exists jq; then
      log "ERROR" "jq is required to parse $CONFIG_FILE. Skipping blockchain check."
      return 1
    fi

    local nodes
    nodes=$(jq -r '.blockchain_nodes[] | "\(.name)\t\(.url)\t\(.type)"' "$CONFIG_FILE")

    echo "$nodes" | while IFS=$'\t' read -r name url type; do
      if [ -z "$url" ]; then
        continue
      fi

      case $type in
        "ethereum"|"binance")
          # Check Ethereum/BSC node using eth_blockNumber
          local response
          response=$(curl -s --max-time 10 -X POST -H "Content-Type: application/json" --data '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}' "$url")

          if ! echo "$response" | jq -e '.result' > /dev/null; then
            send_alert "Blockchain Node Down" "$type node $name ($url) is not responding correctly" "critical"
          else
            local block_number
            block_number=$(echo "$response" | jq -r '.result' | sed 's/0x//')
            local block_decimal
            block_decimal=$((16#$block_number))
            log "INFO" "$type node $name is at block $block_decimal"
          fi
          ;;

        *)
          log "WARNING" "Unknown blockchain node type: $type for node $name. Skipping check."
          ;;
      esac
    done
  else
    log "WARNING" "Config file not found: $CONFIG_FILE. Skipping blockchain check."
  fi

  log "SUCCESS" "Blockchain node check completed"
}

# Function to generate daily report
generate_report() {
  log "INFO" "Generating monitoring report..."

  local report_file

  report_file="$LOG_DIR/report_$(date +%Y%m%d).html"
  local temp_report
  temp_report=$(mktemp)

  # Memory usage for the report (computed here: it is used in several places below)
  local mem_pct mem_state mem_label
  mem_pct=$(free -m | awk '/Mem:/ {printf "%.2f", $3 * 100 / $2}')
  if (($(echo "$mem_pct > $ALERT_THRESHOLD" | bc -l))); then
    mem_state="warning"
    mem_label="HIGH"
  else
    mem_state="success"
    mem_label="OK"
  fi

  # Use a temporary file for the report content to avoid issues with EOF
  cat > "$temp_report" << EOF
<!DOCTYPE html>
<html>
<head>
  <title>ChainFinity Monitoring Report - $(date +%Y-%m-%d)</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 20px; }
    h1 { color: #333366; }
    .section { margin-bottom: 20px; }
    .success { color: green; }
    .warning { color: orange; }
    .error { color: red; }
    table { border-collapse: collapse; width: 100%; }
    th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
    th { background-color: #f2f2f2; }
    tr:nth-child(even) { background-color: #f9f9f9; }
  </style>
</head>
<body>
  <h1>ChainFinity Monitoring Report</h1>
  <p>Generated on: $(date +%Y-%m-%d\ %H:%M:%S)</p>

  <div class="section">
    <h2>System Resources</h2>
    <table>
      <tr>
        <th>Metric</th>
        <th>Value</th>
        <th>Status</th>
      </tr>
      <tr>
        <td>CPU Usage</td>
        <td>$(top -bn1 | grep "Cpu(s)" | awk '{print 100 - $8}' | cut -d ',' -f 1)%</td>
        <td class="$(if (( $(echo "$(top -bn1 | grep "Cpu(s)" | awk '{print 100 - $8}' | cut -d ',' -f 1) > $ALERT_THRESHOLD" | bc -l) )); then echo "warning"; else echo "success"; fi)">
          $(if (( $(echo "$(top -bn1 | grep "Cpu(s)" | awk '{print 100 - $8}' | cut -d ',' -f 1) > $ALERT_THRESHOLD" | bc -l) )); then echo "HIGH"; else echo "OK"; fi)
        </td>
      </tr>
      <tr>
        <td>Memory Usage</td>
        <td>${mem_pct}%</td>
        <td class="${mem_state}">
          ${mem_label}
        </td>
      </tr>
      <tr>
        <td>Disk Usage</td>
        <td>$(df -h / | awk 'NR==2 {print $5}')</td>
        <td class="$(if [ "$(df -h / | awk 'NR==2 {print $5}' | tr -d '%')" -gt "$ALERT_THRESHOLD" ]; then echo "warning"; else echo "success"; fi)">
          $(if [ "$(df -h / | awk 'NR==2 {print $5}' | tr -d '%')" -gt "$ALERT_THRESHOLD" ]; then echo "HIGH"; else echo "OK"; fi)
        </td>
      </tr>
    </table>
  </div>

  <div class="section">
    <h2>Docker Containers</h2>
    <table>
      <tr>
        <th>Container</th>
        <th>Status</th>
        <th>Health</th>
        <th>CPU Usage</th>
        <th>Memory Usage</th>
      </tr>
EOF

  # Add Docker container data
  if command_exists docker; then
    local containers
    containers=$(docker ps -a --format "{{.Names}}")

    for container in $containers; do
      local status
      status=$(docker inspect --format='{{.State.Status}}' "$container" 2>/dev/null || echo "N/A")
      local health
      health=$(docker inspect --format='{{if .State.Health}}{{.State.Health.Status}}{{else}}N/A{{end}}' "$container" 2>/dev/null || echo "N/A")
      local stats
      stats=$(docker stats --no-stream --format "{{.CPUPerc}}\t{{.MemPerc}}" "$container" 2>/dev/null || echo "N/A\tN/A")
      local cpu_usage
      cpu_usage=$(echo "$stats" | awk '{print $1}')
      local mem_usage
      mem_usage=$(echo "$stats" | awk '{print $2}')

      cat >> "$temp_report" << EOF
      <tr>
        <td>$container</td>
        <td class="$(if [ "$status" != "running" ]; then echo "error"; else echo "success"; fi)">$status</td>
        <td class="$(if [ "$health" == "unhealthy" ]; then echo "error"; elif [ "$health" == "healthy" ]; then echo "success"; else echo ""; fi)">$health</td>
        <td>$cpu_usage</td>
        <td>$mem_usage</td>
      </tr>
EOF
    done
  else
    cat >> "$temp_report" << EOF
      <tr>
        <td colspan="5">Docker not installed</td>
      </tr>
EOF
  fi

  # Close the report
  cat >> "$temp_report" << EOF
    </table>
  </div>

  <div class="section">
    <h2>Log Summary (Last 24h)</h2>
    <table>
      <tr>
        <th>Log Level</th>
        <th>Count</th>
      </tr>
      <tr>
        <td>ERROR</td>
        <td>$(grep -c "\[ERROR\]" "$LOG_FILE" || echo 0)</td>
      </tr>
      <tr>
        <td>WARNING</td>
        <td>$(grep -c "\[WARNING\]" "$LOG_FILE" || echo 0)</td>
      </tr>
      <tr>
        <td>INFO</td>
        <td>$(grep -c "\[INFO\]" "$LOG_FILE" || echo 0)</td>
      </tr>
      <tr>
        <td>SUCCESS</td>
        <td>$(grep -c "\[SUCCESS\]" "$LOG_FILE" || echo 0)</td>
      </tr>
    </table>
  </div>

  <div class="section">
    <h2>Recent Errors (Last 10)</h2>
    <pre>$(grep "\[ERROR\]" "$LOG_FILE" | tail -n 10 || echo "No recent errors.")</pre>
  </div>
</body>
</html>
EOF

  mv "$temp_report" "$report_file"
  log "SUCCESS" "Report generated: $report_file"

  # Send report if configured
  if [ -n "$EMAIL_RECIPIENT" ]; then
    if command_exists mail; then
      cat "$report_file" | mail -a "Content-Type: text/html" -s "ChainFinity Daily Monitoring Report - $(date +%Y-%m-%d)" "$EMAIL_RECIPIENT"
      log "INFO" "Report sent to $EMAIL_RECIPIENT"
    else
      log "WARNING" "Mail command not found. Cannot send email report."
    fi
  fi
}

# Function to create default config file
create_default_config() {
  if [ ! -f "$CONFIG_FILE" ]; then
    cat > "$CONFIG_FILE" << EOF
{
  "api_endpoints": [
    {
      "name": "Backend API Health Check",
      "url": "http://localhost:8080/health"
    },
    {
      "name": "Frontend Root",
      "url": "http://localhost:3000"
    }
  ],
  "blockchain_nodes": [
    {
      "name": "Ethereum Mainnet (Infura)",
      "url": "https://mainnet.infura.io/v3/YOUR_INFURA_KEY",
      "type": "ethereum"
    },
    {
      "name": "BSC Mainnet",
      "url": "https://bsc-dataseed.binance.org/",
      "type": "binance"
    }
  ]
}
EOF
    log "INFO" "Created default config file: $CONFIG_FILE"
  fi
}

# --- Main Execution ---

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --config)
      CONFIG_FILE="$2"
      shift 2
      ;;
    --log-dir)
      LOG_DIR="$2"
      shift 2
      ;;
    --alert-threshold)
      ALERT_THRESHOLD="$2"
      shift 2
      ;;
    --check-interval)
      CHECK_INTERVAL="$2"
      shift 2
      ;;
    --report-interval)
      REPORT_INTERVAL="$2"
      shift 2
      ;;
    --slack-webhook)
      SLACK_WEBHOOK="$2"
      shift 2
      ;;
    --email)
      EMAIL_RECIPIENT="$2"
      shift 2
      ;;
    --help)
      echo "Usage: $0 [options]"
      echo "Options:"
      echo "  --config FILE           Configuration file path (default: monitor_config.json)"
      echo "  --log-dir DIR           Log directory (default: ./logs)"
      echo "  --alert-threshold NUM   Alert threshold percentage (default: 80)"
      echo "  --check-interval SEC    Check interval in seconds (default: 300)"
      echo "  --report-interval SEC   Report interval in seconds (default: 86400)"
      echo "  --slack-webhook URL     Slack webhook URL for notifications"
      echo "  --email ADDRESS         Email address for notifications"
      echo "  --help                  Show this help message"
      exit 0
      ;;
    *)
      log "ERROR" "Unknown option: $1"
      exit 1
      ;;
  esac
done

# Create log directory and set log file path
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/monitor_$(date +%Y%m%d).log"

# Create default config if it doesn't exist
create_default_config

log "INFO" "Starting ChainFinity monitoring loop..."
log "INFO" "Check interval: $CHECK_INTERVAL seconds"
log "INFO" "Report interval: $REPORT_INTERVAL seconds"

last_report_time=$(date +%s)

# Main monitoring loop
while true; do
  # Run all checks
  check_system_resources
  check_docker_containers
  check_database_health
  check_api_endpoints
  check_blockchain_nodes

  # Generate report if it's time
  current_time=$(date +%s)
  if [ $((current_time - last_report_time)) -ge "$REPORT_INTERVAL" ]; then
    generate_report
    last_report_time=$current_time
  fi

  # Sleep until next check
  log "INFO" "Sleeping for $CHECK_INTERVAL seconds..."
  sleep "$CHECK_INTERVAL"
done
