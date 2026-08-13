#!/bin/sh
# Starts a Hardhat JSON-RPC node, deploys the ChainFinity contracts to it
# once it's ready, then hands off to the node process so the container
# keeps running as the RPC endpoint.
#
# The deployment manifest (contracts.localhost.json - address + ABI per
# contract) ends up on the blockchain_deployments volume, which
# docker-compose.yml also mounts into the backend service so
# BLOCKCHAIN_DEPLOYMENT_FILE finds it with zero manual wiring.
set -e

npx hardhat node --hostname 0.0.0.0 &
NODE_PID=$!

echo "Waiting for the Hardhat node to accept RPC requests..."
for i in $(seq 1 60); do
  if curl -fsS -X POST -H "Content-Type: application/json" \
      --data '{"jsonrpc":"2.0","method":"eth_chainId","params":[],"id":1}' \
      http://127.0.0.1:8545 > /dev/null 2>&1; then
    echo "Hardhat node is ready after ${i}s."
    break
  fi
  sleep 1
done

echo "Deploying ChainFinity contracts to the local node..."
npx hardhat run scripts/deploy.js --network localhost

echo "Deployment complete. Node is running at http://0.0.0.0:8545"
wait "$NODE_PID"
