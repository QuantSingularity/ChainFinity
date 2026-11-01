# ChainFinity Troubleshooting Guide

Common issues and their solutions for ChainFinity platform.

## Table of Contents

- [Installation Issues](#installation-issues)
- [Database Connection Issues](#database-connection-issues)
- [Authentication Issues](#authentication-issues)
- [API Issues](#api-issues)
- [Blockchain Issues](#blockchain-issues)
- [Frontend Issues](#frontend-issues)
- [Performance Issues](#performance-issues)
- [Deployment Issues](#deployment-issues)

## Installation Issues

### Issue: Port Already in Use

**Error:**

```text
Error: listen EADDRINUSE: address already in use :::8000
```

**Solution:**

```bash
# Find process using the port
lsof -ti:8000

# Kill the process
lsof -ti:8000 | xargs kill -9

# Or use a different port
export PORT=8001
uvicorn app.main:app --port 8001
```

### Issue: npm install Fails

**Error:**

```text
npm ERR! code ERESOLVE
npm ERR! ERESOLVE unable to resolve dependency tree
```

**Solution:**

```bash
# Clear npm cache
npm cache clean --force

# Remove node_modules and package-lock
rm -rf node_modules package-lock.json

# Reinstall with legacy peer deps
npm install --legacy-peer-deps

# Or use npm 6
npm install -g npm@6
npm install
```

### Issue: Python Package Conflicts

**Error:**

```text
ERROR: pip's dependency resolver does not currently take into account all the packages that are installed
```

**Solution:**

```bash
# Deactivate current environment
deactivate

# Remove virtual environment
rm -rf venv

# Create fresh virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install requirements
pip install -r requirements.txt
```

### Issue: Docker Permission Denied

**Error:**

```text
permission denied while trying to connect to the Docker daemon socket
```

**Solution:**

```bash
# Add user to docker group
sudo usermod -aG docker $USER

# Log out and log back in, or run:
newgrp docker

# Verify
docker ps
```

## Database Connection Issues

### Issue: PostgreSQL Connection Refused

**Error:**

```text
asyncpg.exceptions.ConnectionDoesNotExistError: connection is closed
```

**Solutions:**

**1. Check if PostgreSQL is running:**

```bash
# Check status
pg_isready -h localhost -p 5432

# Start PostgreSQL (Linux)
sudo systemctl start postgresql

# Start PostgreSQL (macOS)
brew services start postgresql

# Start with Docker
docker-compose up -d postgres
```

**2. Verify connection string:**

```bash
# Check .env file
cat code/backend/.env | grep DATABASE_URL

# Correct format:
# DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/chainfinity
```

**3. Check PostgreSQL logs:**

```bash
# Linux
sudo tail -f /var/log/postgresql/postgresql-15-main.log

# Docker
docker logs chainfinity_postgres
```

**4. Test connection manually:**

```bash
psql -h localhost -U postgres -d chainfinity
```

### Issue: Database Does Not Exist

**Error:**

```text
asyncpg.exceptions.InvalidCatalogNameError: database "chainfinity" does not exist
```

**Solution:**

```bash
# Create database
psql -h localhost -U postgres -c "CREATE DATABASE chainfinity;"

# Run migrations
cd code/backend
alembic upgrade head
```

### Issue: Redis Connection Failed

**Error:**

```text
redis.exceptions.ConnectionError: Error connecting to Redis
```

**Solutions:**

**1. Check if Redis is running:**

```bash
# Test connection
redis-cli ping
# Expected output: PONG

# Start Redis (Linux)
sudo systemctl start redis

# Start Redis (macOS)
brew services start redis

# Start with Docker
docker-compose up -d redis
```

**2. Verify Redis URL:**

```bash
# Check .env file
cat code/backend/.env | grep REDIS_URL

# Correct format:
# REDIS_URL=redis://localhost:6379/0
```

**3. Check Redis logs:**

```bash
# Docker
docker logs chainfinity_redis

# System
sudo journalctl -u redis
```

## Authentication Issues

### Issue: JWT Token Invalid

**Error:**

```json
{ "detail": "Could not validate credentials" }
```

**Solutions:**

**1. Token expired:**

```python
# Refresh token
import requests

response = requests.post(
    'http://localhost:8000/api/v1/auth/refresh',
    json={'refresh_token': refresh_token}
)
new_access_token = response.json()['access_token']
```

**2. Invalid SECRET_KEY:**

```bash
# Generate new SECRET_KEY
openssl rand -hex 32

# Update .env
echo "SECRET_KEY=your_new_secret_key" >> code/backend/.env

# Restart backend
```

**3. Token format error:**

```bash
# Correct format
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# NOT: Authorization: eyJhbGci... (missing "Bearer ")
```

### Issue: Login Fails with Correct Credentials

**Possible causes:**

**1. Account not activated:**

```sql
-- Check user status
SELECT email, is_active, email_verified FROM users WHERE email = 'user@example.com';

-- Activate account
UPDATE users SET is_active = true WHERE email = 'user@example.com';
```

**2. Account locked:**

```sql
-- Check lockout status
SELECT email, failed_login_attempts, locked_until FROM users WHERE email = 'user@example.com';

-- Unlock account
UPDATE users SET failed_login_attempts = 0, locked_until = NULL WHERE email = 'user@example.com';
```

**3. Password hash mismatch:**

```bash
# Reset password through API
curl -X POST http://localhost:8000/api/v1/auth/reset-password \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com"}'
```

## API Issues

### Issue: 429 Too Many Requests

**Error:**

```json
{ "detail": "Rate limit exceeded. Try again later." }
```

**Solutions:**

**1. Wait and retry:**

```python
import time
import requests

max_retries = 3
for i in range(max_retries):
    response = requests.get(url, headers=headers)
    if response.status_code != 429:
        break
    time.sleep(60)  # Wait 1 minute
```

**2. Adjust rate limit (development only):**

```bash
# In .env
RATE_LIMIT_PER_MINUTE=120
```

**3. Use exponential backoff:**

```python
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

session = requests.Session()
retry = Retry(
    total=3,
    backoff_factor=0.3,
    status_forcelist=[429, 500, 502, 503, 504]
)
adapter = HTTPAdapter(max_retries=retry)
session.mount('http://', adapter)
session.mount('https://', adapter)
```

### Issue: CORS Error in Browser

**Error:**

```text
Access to XMLHttpRequest at 'http://localhost:8000/api/v1/...' from origin 'http://localhost:3000' has been blocked by CORS policy
```

**Solutions:**

**1. Update CORS configuration:**

```bash
# In .env
CORS_ORIGINS=http://localhost:3000,http://localhost:3001

# Restart backend
```

**2. Check CORS headers:**

```bash
curl -H "Origin: http://localhost:3000" \
     -H "Access-Control-Request-Method: POST" \
     -H "Access-Control-Request-Headers: Content-Type" \
     -X OPTIONS \
     http://localhost:8000/api/v1/portfolios \
     -v
```

### Issue: 422 Validation Error

**Error:**

```json
{
  "success": false,
  "error": "Validation error",
  "details": [
    {
      "field": "body -> password",
      "message": "ensure this value has at least 8 characters",
      "type": "value_error.any_str.min_length"
    }
  ]
}
```

**Solution:**
Ensure request body matches API schema requirements. Check [API documentation](./API.md) for correct format.

```python
# Incorrect
{"pass": "abc"}

# Correct
{"password": "SecureP@ss123"}
```

## Blockchain Issues

### Issue: Transaction Reverted

**Error:**

```text
Error: transaction reverted without a reason string
```

**Solutions:**

**1. Check gas limit:**

```javascript
const tx = await contract.someFunction({
  gasLimit: 500000, // Increase if needed
});
```

**2. Check require statements:**

```solidity
// Add detailed error messages
require(amount > 0, "Amount must be positive");
require(balance >= amount, "Insufficient balance");
```

**3. Debug with Hardhat console:**

```javascript
const hardhat = require("hardhat");
await hardhat.network.provider.send("hardhat_setLoggingEnabled", [true]);
```

### Issue: Insufficient Funds for Gas

**Error:**

```text
Error: insufficient funds for gas * price + value
```

**Solutions:**

**1. Fund account:**

```bash
# Get testnet ETH from faucet
# Sepolia: https://sepoliafaucet.com/
# Goerli: https://goerlifaucet.com/
```

**2. Lower gas price:**

```javascript
const tx = await contract.someFunction({
  gasPrice: ethers.utils.parseUnits("20", "gwei"),
});
```

### Issue: Contract Not Deployed

**Error:**

```text
Error: contract not deployed
```

**Solution:**

```bash
# Deploy contracts
cd code/blockchain
npx hardhat run scripts/deploy.js --network localhost

# Update contract addresses in .env
```

### Issue: Wrong Network

**Error:**

```text
Error: network mismatch (chainId 1337, expected 1)
```

**Solution:**

```javascript
// Check network in MetaMask or wallet
const network = await provider.getNetwork();
console.log("Connected to network:", network.chainId);

// Switch network programmatically
await window.ethereum.request({
  method: "wallet_switchEthereumChain",
  params: [{ chainId: "0x1" }], // Mainnet
});
```

## Frontend Issues

### Issue: Module Not Found

**Error:**

```text
Module not found: Can't resolve 'react-router-dom'
```

**Solution:**

```bash
# Install missing dependency
cd web-frontend
npm install react-router-dom

# Or reinstall all dependencies
rm -rf node_modules package-lock.json
npm install
```

### Issue: Blank White Screen

**Possible causes:**

**1. JavaScript error:**

```bash
# Check browser console (F12)
# Look for error messages
```

**2. API connection failed:**

```bash
# Verify backend is running
curl http://localhost:8000/health

# Check API URL in .env
cat web-frontend/.env | grep REACT_APP_API_URL
```

**3. Build issue:**

```bash
# Clear cache and rebuild
cd web-frontend
rm -rf build node_modules
npm install
npm start
```

### Issue: MetaMask Not Connecting

**Error:**

```text
No Ethereum provider found. Install MetaMask.
```

**Solutions:**

**1. Install MetaMask:**

- Download from <https://metamask.io/>

**2. Detect provider correctly:**

```javascript
const detectProvider = async () => {
  if (window.ethereum) {
    return window.ethereum;
  }

  // Wait for provider injection
  let provider = null;
  for (let i = 0; i < 10; i++) {
    await new Promise((resolve) => setTimeout(resolve, 100));
    if (window.ethereum) {
      provider = window.ethereum;
      break;
    }
  }

  return provider;
};
```

**3. Request account access:**

```javascript
await window.ethereum.request({ method: "eth_requestAccounts" });
```

## Performance Issues

### Issue: Slow API Response

**Diagnosis:**

```bash
# Check API response times
time curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/portfolios
```

**Solutions:**

**1. Enable caching:**

```bash
# In .env
CACHE_TTL=3600  # Cache for 1 hour
```

**2. Optimize database queries:**

```python
# Use eager loading
from sqlalchemy.orm import selectinload

query = select(Portfolio).options(
    selectinload(Portfolio.assets)
)
```

**3. Add database indexes:**

```sql
CREATE INDEX idx_portfolios_user_id ON portfolios(user_id);
CREATE INDEX idx_transactions_user_id ON transactions(user_id);
```

**4. Check database connection pool:**

```bash
# In .env
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=30
```

### Issue: High Memory Usage

**Diagnosis:**

```bash
# Check process memory
ps aux | grep uvicorn

# Docker container memory
docker stats chainfinity_api
```

**Solutions:**

**1. Limit worker processes:**

```bash
# In production
WORKERS=4  # Not too many
```

**2. Optimize queries:**

```python
# Use pagination
limit = 20
offset = (page - 1) * limit
query = query.limit(limit).offset(offset)
```

**3. Clear cache regularly:**

```bash
# Flush Redis cache
redis-cli FLUSHDB
```

## Deployment Issues

### Issue: Docker Build Fails

**Error:**

```text
ERROR [internal] load metadata for docker.io/library/python:3.11-slim
```

**Solutions:**

**1. Check Docker daemon:**

```bash
sudo systemctl status docker
sudo systemctl start docker
```

**2. Login to Docker registry:**

```bash
docker login
```

**3. Pull base image manually:**

```bash
docker pull python:3.11-slim
```

### Issue: Kubernetes Pod Not Starting

**Error:**

```text
CrashLoopBackOff
```

**Diagnosis:**

```bash
# Check pod status
kubectl get pods -n chainfinity

# View pod logs
kubectl logs -f pod-name -n chainfinity

# Describe pod
kubectl describe pod pod-name -n chainfinity
```

**Common solutions:**

**1. Missing environment variables:**

```yaml
# Update deployment.yaml with required env vars
env:
  - name: DATABASE_URL
    valueFrom:
      secretKeyRef:
        name: chainfinity-secrets
        key: database-url
```

**2. Resource limits too low:**

```yaml
resources:
  requests:
    memory: "512Mi"
    cpu: "500m"
  limits:
    memory: "2Gi"
    cpu: "2000m"
```

### Issue: Database Migrations Fail

**Error:**

```text
alembic.util.exc.CommandError: Can't locate revision identified by 'abc123'
```

**Solutions:**

**1. Check migration history:**

```bash
cd code/backend
alembic history
alembic current
```

**2. Reset migrations (development only):**

```bash
# Drop and recreate database
dropdb chainfinity
createdb chainfinity

# Run all migrations
alembic upgrade head
```

**3. Stamp database (if migrations already applied manually):**

```bash
alembic stamp head
```

## Getting More Help

If you can't find a solution here:

1. **Check logs:**

   ```bash
   # Backend logs
   tail -f logs/backend.log

   # Docker logs
   docker-compose logs -f

   # Kubernetes logs
   kubectl logs -f deployment/chainfinity-api -n chainfinity
   ```

2. **Enable debug mode:**

   ```bash
   # In .env
   DEBUG=true
   LOG_LEVEL=DEBUG
   ```

3. **Search existing issues:**
   - <https://github.com/abrar2030/ChainFinity/issues>

4. **Create a new issue:**
   - Include error messages
   - Include steps to reproduce
   - Include environment details
   - Include relevant logs

5. **Join community:**
   - GitHub Discussions
   - Project README for contact info

## Quick Reference

### Restart Everything

```bash
# Stop all services
docker-compose down

# Clear cache
redis-cli FLUSHDB

# Start fresh
docker-compose up -d
./scripts/run_chainfinity.sh
```

### Health Check Commands

```bash
# Check backend
curl http://localhost:8000/health

# Check database
pg_isready -h localhost

# Check Redis
redis-cli ping

# Check frontend
curl http://localhost:3000
```

### Log Locations

| Component  | Log Location              |
| ---------- | ------------------------- |
| Backend    | `logs/backend.log`        |
| Frontend   | Browser console (F12)     |
| PostgreSQL | `/var/log/postgresql/`    |
| Redis      | `/var/log/redis/`         |
| Docker     | `docker logs <container>` |
| Kubernetes | `kubectl logs <pod>`      |
