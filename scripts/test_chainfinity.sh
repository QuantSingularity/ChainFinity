#!/bin/bash
# ChainFinity Testing Automation Script
# This script automates the testing process for all components of the ChainFinity platform

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
PROJECT_DIR="$(pwd)"
# LOG_FILE gets a real value once LOG_DIR is known; default keeps early
# log() calls (e.g. during argument parsing) from tripping `set -u`.
LOG_FILE="/dev/null"
LOG_DIR="$PROJECT_DIR/logs"
REPORT_DIR="$PROJECT_DIR/test-reports"
TEST_TIMEOUT=300 # 5 minutes per test suite
PARALLEL_TESTS=true
COVERAGE_THRESHOLD=80
TEST_COMPONENT="all"

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

  echo "[${timestamp}] [${level}] ${message}" >> "$LOG_FILE"
}

# Function to check if a command exists
command_exists() {
  command -v "$1" >/dev/null 2>&1
}

# Apply --timeout (TEST_TIMEOUT seconds) to a test command. `timeout` is not available on
# every platform (for example stock macOS); without it the command simply runs unbounded.
run_with_timeout() {
  if command_exists timeout; then
    timeout "$TEST_TIMEOUT" "$@"
  else
    "$@"
  fi
}

# --- Testing Functions ---

# Function to run blockchain tests
run_blockchain_tests() {
  log "INFO" "Running blockchain tests..."

  local blockchain_dir="$PROJECT_DIR/code/blockchain"
  if [ ! -d "$blockchain_dir" ]; then
    log "ERROR" "Blockchain directory not found: $blockchain_dir"
    return 1
  fi

  (
    cd "$blockchain_dir"
    log "INFO" "Installing blockchain dependencies..."
    npm install --silent

    # Run tests with coverage
    log "INFO" "Running Hardhat tests with coverage..."
    if ! run_with_timeout npm run test:coverage; then
      log "ERROR" "Blockchain tests failed"
      return 1
    fi

    # Check coverage threshold
    if command_exists jq; then
      local coverage_file="coverage/coverage-summary.json"
      if [ -f "$coverage_file" ]; then
        local line_coverage
        line_coverage=$(jq -r '.total.lines.pct' "$coverage_file")
        if [ "$(echo "$line_coverage < $COVERAGE_THRESHOLD" | bc -l)" = "1" ]; then
          log "WARNING" "Blockchain test coverage ($line_coverage%) is below threshold ($COVERAGE_THRESHOLD%)"
        else
          log "SUCCESS" "Blockchain test coverage: $line_coverage%"
        fi
      fi
    fi

    # Copy reports
    mkdir -p "$REPORT_DIR/blockchain"
    cp -r coverage/* "$REPORT_DIR/blockchain/"
  ) || return 1

  log "SUCCESS" "Blockchain tests completed"
  return 0
}

# Function to run backend tests
run_backend_tests() {
  log "INFO" "Running backend tests..."

  local backend_dir="$PROJECT_DIR/code/backend"
  if [ ! -d "$backend_dir" ]; then
    log "ERROR" "Backend directory not found: $backend_dir"
    return 1
  fi

  (
    cd "$backend_dir"
    # Activate virtual environment if it exists
    if [ -d "$PROJECT_DIR/venv" ]; then
      source "$PROJECT_DIR/venv/bin/activate"
    fi

    # Install project dependencies
    log "INFO" "Installing backend dependencies..."
    if [ -f "requirements.txt" ]; then
      pip install -r requirements.txt --quiet
    fi

    # Install testing dependencies
    pip install pytest pytest-cov --quiet

    # Run tests with coverage
    log "INFO" "Running pytest with coverage..."
    if ! run_with_timeout python -m pytest --cov=. --cov-report=xml --cov-report=html; then
      log "ERROR" "Backend tests failed"
      return 1
    fi

    # Check coverage threshold
    if command_exists coverage; then
      local coverage_report
      coverage_report=$(coverage report | grep TOTAL | awk '{print $NF}' | tr -d '%')
      if [ "$(echo "$coverage_report < $COVERAGE_THRESHOLD" | bc -l)" = "1" ]; then
        log "WARNING" "Backend test coverage ($coverage_report%) is below threshold ($COVERAGE_THRESHOLD%)"
      else
        log "SUCCESS" "Backend test coverage: $coverage_report%"
      fi
    fi

    # Copy reports
    mkdir -p "$REPORT_DIR/backend"
    cp -r htmlcov/* "$REPORT_DIR/backend/"
    cp coverage.xml "$REPORT_DIR/backend/"
  ) || return 1

  log "SUCCESS" "Backend tests completed"
  return 0
}

# Function to run frontend tests
run_frontend_tests() {
  log "INFO" "Running frontend tests..."

  local frontend_dir="$PROJECT_DIR/web-frontend"
  if [ ! -d "$frontend_dir" ]; then
    log "ERROR" "Frontend directory not found: $frontend_dir"
    return 1
  fi

  (
    cd "$frontend_dir"
    log "INFO" "Installing frontend dependencies..."
    npm install --silent

    # Run tests with coverage
    log "INFO" "Running Jest tests with coverage..."
    if ! run_with_timeout npm test -- --coverage --watchAll=false; then
      log "ERROR" "Frontend tests failed"
      return 1
    fi

    # Check coverage threshold
    if [ -f "coverage/coverage-summary.json" ] && command_exists jq; then
      local line_coverage
      line_coverage=$(jq -r '.total.lines.pct' coverage/coverage-summary.json)
      if [ "$(echo "$line_coverage < $COVERAGE_THRESHOLD" | bc -l)" = "1" ]; then
        log "WARNING" "Frontend test coverage ($line_coverage%) is below threshold ($COVERAGE_THRESHOLD%)"
      else
        log "SUCCESS" "Frontend test coverage: $line_coverage%"
      fi
    fi

    # Copy reports
    mkdir -p "$REPORT_DIR/frontend"
    cp -r coverage/* "$REPORT_DIR/frontend/"
  ) || return 1

  log "SUCCESS" "Frontend tests completed"
  return 0
}

# Function to run mobile frontend tests
run_mobile_frontend_tests() {
  log "INFO" "Running mobile frontend tests..."

  local mobile_dir="$PROJECT_DIR/mobile-frontend"
  if [ ! -d "$mobile_dir" ]; then
    log "WARNING" "Mobile frontend directory not found: $mobile_dir. Skipping tests."
    return 0
  fi

  (
    cd "$mobile_dir"
    log "INFO" "Installing mobile frontend dependencies..."
    npm install --silent

    # Run tests with coverage
    log "INFO" "Running Jest tests with coverage..."
    if ! run_with_timeout npm test -- --coverage --watchAll=false; then
      log "ERROR" "Mobile frontend tests failed"
      return 1
    fi

    # Check coverage threshold
    if [ -f "coverage/coverage-summary.json" ] && command_exists jq; then
      local line_coverage
      line_coverage=$(jq -r '.total.lines.pct' coverage/coverage-summary.json)
      if [ "$(echo "$line_coverage < $COVERAGE_THRESHOLD" | bc -l)" = "1" ]; then
        log "WARNING" "Mobile frontend test coverage ($line_coverage%) is below threshold ($COVERAGE_THRESHOLD%)"
      else
        log "SUCCESS" "Mobile frontend test coverage: $line_coverage%"
      fi
    fi

    # Copy reports
    mkdir -p "$REPORT_DIR/mobile-frontend"
    cp -r coverage/* "$REPORT_DIR/mobile-frontend/"
  ) || return 1

  log "SUCCESS" "Mobile frontend tests completed"
  return 0
}

# Function to run integration tests
run_integration_tests() {
  log "INFO" "Running integration tests..."

  local integration_dir="$PROJECT_DIR/code/integration-tests"
  if [ ! -d "$integration_dir" ]; then
    log "WARNING" "Integration tests directory not found: $integration_dir. Skipping tests."
    return 0
  fi

  (
    cd "$integration_dir"
    log "INFO" "Installing integration test dependencies..."
    npm install --silent

    # Run integration tests
    log "INFO" "Running integration tests..."
    if ! run_with_timeout npm test; then
      log "ERROR" "Integration tests failed"
      return 1
    fi

    # Copy reports if they exist
    if [ -d "coverage" ]; then
      mkdir -p "$REPORT_DIR/integration"
      cp -r coverage/* "$REPORT_DIR/integration/"
    fi
  ) || return 1

  log "SUCCESS" "Integration tests completed"
  return 0
}

# Function to generate combined test report
generate_test_report() {
  log "INFO" "Generating combined test report..."

  local report_file="$REPORT_DIR/test-report.html"
  local temp_report
  temp_report=$(mktemp)

  # Use a temporary file for the report content to avoid issues with EOF
  cat > "$temp_report" << EOF
<!DOCTYPE html>
<html>
<head>
  <title>ChainFinity Test Report - $(date +%Y-%m-%d)</title>
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
    .progress-bar {
      height: 20px;
      background-color: #e0e0e0;
      border-radius: 10px;
      margin-bottom: 10px;
    }
    .progress-bar-fill {
      height: 100%;
      border-radius: 10px;
      background-color: #4CAF50;
    }
  </style>
</head>
<body>
  <h1>ChainFinity Test Report</h1>
  <p>Generated on: $(date +%Y-%m-%d\ %H:%M:%S)</p>

  <div class="section">
    <h2>Test Summary</h2>
    <table>
      <tr>
        <th>Component</th>
        <th>Status</th>
        <th>Coverage</th>
        <th>Details</th>
      </tr>
EOF

  # Helper function to add component row
  add_component_row() {
    local component_name="$1"
    local report_path="$2"
    local coverage_json="$3"
    local coverage_key="$4"
    local coverage_report_path="$5"

    local status="Not Run"
    local coverage="N/A"
    local status_class=""
    local details_link="N/A"

    if [ -f "$report_path" ]; then
      status="Success"
      status_class="success"
      details_link="<a href=\"$coverage_report_path\">View Details</a>"

      if [ -f "$coverage_json" ] && command_exists jq; then
        coverage=$(jq -r "$coverage_key" "$coverage_json" 2>/dev/null || echo "N/A")
      fi
    fi

    cat >> "$temp_report" << EOF
      <tr>
        <td>$component_name</td>
        <td class="$status_class">$status</td>
        <td>
          <div class="progress-bar">
            <div class="progress-bar-fill" style="width: ${coverage}%;"></div>
          </div>
          ${coverage}%
        </td>
        <td>$details_link</td>
      </tr>
EOF
  }

  # Add component rows
  add_component_row "Blockchain" "$REPORT_DIR/blockchain/index.html" "$REPORT_DIR/blockchain/coverage-summary.json" '.total.lines.pct' "blockchain/index.html"
  add_component_row "Backend" "$REPORT_DIR/backend/index.html" "$PROJECT_DIR/code/backend/.coverage" 'report | grep TOTAL | awk "{print \$NF}" | tr -d "%"' "backend/index.html"
  add_component_row "Frontend" "$REPORT_DIR/frontend/index.html" "$REPORT_DIR/frontend/coverage-summary.json" '.total.lines.pct' "frontend/index.html"
  add_component_row "Mobile Frontend" "$REPORT_DIR/mobile-frontend/index.html" "$REPORT_DIR/mobile-frontend/coverage-summary.json" '.total.lines.pct' "mobile-frontend/index.html"
  add_component_row "Integration" "$REPORT_DIR/integration/index.html" "$REPORT_DIR/integration/coverage-summary.json" '.total.lines.pct' "integration/index.html"

  # Close the report
  cat >> "$temp_report" << EOF
    </table>
  </div>

  <div class="section">
    <h2>Test Log (Last 50 lines)</h2>
    <pre>$(tail -n 50 "$LOG_FILE" || echo "No log entries.")</pre>
  </div>
</body>
</html>
EOF

  mv "$temp_report" "$report_file"
  log "SUCCESS" "Test report generated: $report_file"
}

# --- Main Execution ---

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --project-dir)
      PROJECT_DIR="$2"
      shift 2
      ;;
    --log-dir)
      LOG_DIR="$2"
      shift 2
      ;;
    --report-dir)
      REPORT_DIR="$2"
      shift 2
      ;;
    --timeout)
      TEST_TIMEOUT="$2"
      shift 2
      ;;
    --no-parallel)
      PARALLEL_TESTS=false
      shift
      ;;
    --coverage-threshold)
      COVERAGE_THRESHOLD="$2"
      shift 2
      ;;
    --component)
      TEST_COMPONENT="$2"
      shift 2
      ;;
    --help)
      echo "Usage: $0 [options]"
      echo "Options:"
      echo "  --project-dir DIR        Set project directory (default: current directory)"
      echo "  --log-dir DIR            Log directory (default: ./logs)"
      echo "  --report-dir DIR         Test report directory (default: ./test-reports)"
      echo "  --timeout SEC            Test timeout in seconds (default: 300)"
      echo "  --no-parallel            Disable parallel testing"
      echo "  --coverage-threshold NUM Minimum code coverage percentage (default: 80)"
      echo "  --component NAME         Test only specific component (blockchain, backend, frontend, mobile, integration, all)"
      echo "  --help                   Show this help message"
      exit 0
      ;;
    *)
      log "ERROR" "Unknown option: $1"
      exit 1
      ;;
  esac
done

# Create directories if they don't exist
mkdir -p "$LOG_DIR"
mkdir -p "$REPORT_DIR"

# Log file
LOG_FILE="$LOG_DIR/tests_$(date +%Y%m%d_%H%M%S).log"

main() {
  log "INFO" "Starting ChainFinity test automation..."
  log "INFO" "Project directory: $PROJECT_DIR"
  log "INFO" "Coverage threshold: $COVERAGE_THRESHOLD%"

  # Track overall success
  local success=true

  # Define test functions to run
  local test_functions=()
  case "${TEST_COMPONENT}" in
    "blockchain")
      test_functions=("run_blockchain_tests")
      ;;
    "backend")
      test_functions=("run_backend_tests")
      ;;
    "frontend")
      test_functions=("run_frontend_tests")
      ;;
    "mobile")
      test_functions=("run_mobile_frontend_tests")
      ;;
    "integration")
      test_functions=("run_integration_tests")
      ;;
    "all")
      test_functions=("run_blockchain_tests" "run_backend_tests" "run_frontend_tests" "run_mobile_frontend_tests" "run_integration_tests")
      ;;
    *)
      log "ERROR" "Unknown component: $TEST_COMPONENT"
      exit 1
      ;;
  esac

  # Run tests
  if [ "$PARALLEL_TESTS" = true ] && command_exists parallel; then
    log "INFO" "Running tests in parallel..."
    # Parallel execution logic is complex and often fails in shell scripts.
    # For simplicity and reliability, we will run sequentially even if parallel is requested,
    # unless the user has a robust parallel setup.
    log "WARNING" "Parallel execution is complex and may fail. Running sequentially for stability."
    PARALLEL_TESTS=false
  fi

  if [ "$PARALLEL_TESTS" = false ]; then
    for func in "${test_functions[@]}"; do
      log "INFO" "Executing test function: $func"
      if ! "$func"; then
        success=false
      fi
    done
  fi

  # Generate test report
  generate_test_report

  # Final status
  if [ "$success" = true ]; then
    log "SUCCESS" "All tests completed successfully!"
    exit 0
  else
    log "ERROR" "Some tests failed. Check the report for details."
    exit 1
  fi
}

# Run main function
main
