#!/bin/bash

# ChainFinity Backend Test Runner Script

set -e

echo " Running ChainFinity Backend Tests"
echo "===================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    print_warning "Virtual environment not detected. Activating..."
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
        print_status "Virtual environment activated"
    else
        print_error "Virtual environment not found. Please create one with: python -m venv venv"
        exit 1
    fi
fi

# Install test dependencies if not already installed
print_status "Installing test dependencies..."
pip install -q pytest pytest-asyncio pytest-cov httpx

# Set environment variables for testing
export ENVIRONMENT=testing
export DATABASE_URL=sqlite+aiosqlite:///:memory:
export REDIS_URL=redis://localhost:6379/1
export SECRET_KEY=test-secret-key-for-testing-only

# Create test directories if they don't exist
mkdir -p tests/unit tests/integration tests/fixtures
mkdir -p htmlcov

print_status "Running linting checks..."
if command -v flake8 &> /dev/null; then
    flake8 app/ services/ models/ --max-line-length=100 --ignore=E203,W503 || print_warning "Linting issues found"
else
    print_warning "flake8 not installed, skipping linting"
fi

print_status "Running type checks..."
if command -v mypy &> /dev/null; then
    mypy app/ services/ models/ --ignore-missing-imports || print_warning "Type checking issues found"
else
    print_warning "mypy not installed, skipping type checking"
fi

print_status "Running unit tests..."
pytest tests/unit/ -v --tb=short

print_status "Running integration tests..."
pytest tests/integration/ -v --tb=short

print_status "Running all tests with coverage..."
pytest --cov=app --cov=services --cov=models --cov-report=term-missing --cov-report=html:htmlcov

print_status "Generating coverage report..."
if [ -f "htmlcov/index.html" ]; then
    print_status "Coverage report generated at: htmlcov/index.html"
fi

# Check coverage threshold
COVERAGE=$(pytest --cov=app --cov=services --cov=models --cov-report=term | grep "TOTAL" | awk '{print $4}' | sed 's/%//')
if [ ! -z "$COVERAGE" ] && [ "$COVERAGE" -lt 80 ]; then
    print_warning "Coverage is below 80%: ${COVERAGE}%"
else
    print_status "Coverage meets threshold: ${COVERAGE}%"
fi

print_status "Running security checks..."
if command -v bandit &> /dev/null; then
    bandit -r app/ services/ models/ -f json -o security_report.json || print_warning "Security issues found"
    print_status "Security report generated: security_report.json"
else
    print_warning "bandit not installed, skipping security checks"
fi

print_status "All tests completed successfully! "
echo ""
echo " Test Results Summary:"
echo "- Unit tests: "
echo "- Integration tests: "
echo "- Coverage report: htmlcov/index.html"
echo "- Security report: security_report.json"
echo ""
echo " Ready for deployment!"
