# Cross-Chain Transfer Example

This example demonstrates how to perform cross-chain asset transfers using ChainFinity's CrossChainManager smart contract with Chainlink CCIP integration.

## Overview

The CrossChainManager contract enables secure cross-chain token transfers between supported blockchain networks (Ethereum, Polygon, BSC, Arbitrum) using Chainlink's Cross-Chain Interoperability Protocol (CCIP).

## Prerequisites

- MetaMask or compatible Web3 wallet
- Test tokens on source chain
- ETH/MATIC/BNB for gas fees on both chains
- Basic understanding of Ethereum transactions

## Supported Networks

| Network          | Chain ID | CCIP Selector        | Status |
| ---------------- | -------- | -------------------- | ------ |
| Ethereum Mainnet | 1        | 5009297550715157269  | Active |
| Arbitrum         | 42161    | 4949039107694359620  | Active |
| Polygon          | 137      | 4051577828743386545  | Active |
| BSC              | 56       | 11344663589394136015 | Active |

## Step 1: Setup and Configuration

### Install Dependencies

```bash
npm install ethers@6
```

### Contract Configuration

```javascript
const { ethers } = require("ethers");

// Contract addresses (update with deployed addresses)
const CROSS_CHAIN_MANAGER_ADDRESS = "0x..."; // CrossChainManager contract
const TOKEN_ADDRESS = "0x..."; // Token to transfer (ERC20)

// Contract ABIs
const CROSS_CHAIN_MANAGER_ABI = [
  "function initiateCrossChainTransfer(address token, uint256 amount, uint64 targetChainSelector, address targetAddress) external returns (bytes32)",
  "function transfers(bytes32 transferId) external view returns (address sender, address token, uint256 amount, uint256 targetChainId, address targetAddress, uint256 timestamp, bool completed, bytes32 ccipMessageId)",
  "function supportedChains(uint64 chainSelector) external view returns (bool)",
  "function transferLimit() external view returns (uint256)",
  "function transferCooldown() external view returns (uint256)",
];

const ERC20_ABI = [
  "function approve(address spender, uint256 amount) external returns (bool)",
  "function allowance(address owner, address spender) external view returns (uint256)",
  "function balanceOf(address account) external view returns (uint256)",
];
```

## Step 2: Connect to Blockchain

```javascript
// Connect to Ethereum provider
const provider = new ethers.JsonRpcProvider(process.env.ETH_RPC_URL);

// Connect wallet
const wallet = new ethers.Wallet(process.env.PRIVATE_KEY, provider);

// Initialize contracts
const crossChainManager = new ethers.Contract(
  CROSS_CHAIN_MANAGER_ADDRESS,
  CROSS_CHAIN_MANAGER_ABI,
  wallet,
);

const token = new ethers.Contract(TOKEN_ADDRESS, ERC20_ABI, wallet);
```

## Step 3: Check Prerequisites

```javascript
async function checkPrerequisites(amount, targetChainSelector) {
  // 1. Check if target chain is supported
  const isSupported =
    await crossChainManager.supportedChains(targetChainSelector);
  if (!isSupported) {
    throw new Error(`Chain selector ${targetChainSelector} is not supported`);
  }

  // 2. Check token balance
  const balance = await token.balanceOf(wallet.address);
  console.log(`Token balance: ${ethers.formatEther(balance)}`);

  if (balance < amount) {
    throw new Error(
      `Insufficient balance. Have: ${ethers.formatEther(balance)}, Need: ${ethers.formatEther(amount)}`,
    );
  }

  // 3. Check transfer limits
  const transferLimit = await crossChainManager.transferLimit();
  console.log(`Transfer limit: ${ethers.formatEther(transferLimit)}`);

  if (amount > transferLimit) {
    throw new Error(`Amount exceeds transfer limit`);
  }

  // 4. Check ETH balance for gas
  const ethBalance = await provider.getBalance(wallet.address);
  console.log(`ETH balance: ${ethers.formatEther(ethBalance)}`);

  if (ethBalance < ethers.parseEther("0.01")) {
    console.warn("Low ETH balance for gas fees");
  }

  return true;
}
```

## Step 4: Approve Token Transfer

```javascript
async function approveTokens(amount) {
  console.log("Checking allowance...");

  // Check current allowance
  const currentAllowance = await token.allowance(
    wallet.address,
    CROSS_CHAIN_MANAGER_ADDRESS,
  );

  console.log(`Current allowance: ${ethers.formatEther(currentAllowance)}`);

  // If allowance is sufficient, skip approval
  if (currentAllowance >= amount) {
    console.log("Sufficient allowance already exists");
    return;
  }

  // Approve tokens
  console.log("Approving tokens...");
  const approveTx = await token.approve(CROSS_CHAIN_MANAGER_ADDRESS, amount);

  console.log(`Approval transaction sent: ${approveTx.hash}`);
  console.log("Waiting for confirmation...");

  const approveReceipt = await approveTx.wait();
  console.log(`✓ Tokens approved in block ${approveReceipt.blockNumber}`);
}
```

## Step 5: Initiate Cross-Chain Transfer

```javascript
async function initiateCrossChainTransfer(
  tokenAddress,
  amount,
  targetChainSelector,
  targetAddress,
) {
  console.log("\n=== Initiating Cross-Chain Transfer ===");
  console.log(`Token: ${tokenAddress}`);
  console.log(`Amount: ${ethers.formatEther(amount)}`);
  console.log(`Target Chain Selector: ${targetChainSelector}`);
  console.log(`Target Address: ${targetAddress}`);

  // Initiate transfer
  const tx = await crossChainManager.initiateCrossChainTransfer(
    tokenAddress,
    amount,
    targetChainSelector,
    targetAddress,
    {
      gasLimit: 500000, // Adjust as needed
    },
  );

  console.log(`\nTransaction sent: ${tx.hash}`);
  console.log("Waiting for confirmation...");

  const receipt = await tx.wait();
  console.log(`✓ Transfer initiated in block ${receipt.blockNumber}`);

  // Extract transfer ID from event
  const transferInitiatedEvent = receipt.logs.find(
    (log) =>
      log.topics[0] ===
      ethers.id(
        "TransferInitiated(bytes32,address,address,uint256,uint64,address,bytes32)",
      ),
  );

  if (transferInitiatedEvent) {
    const transferId = transferInitiatedEvent.topics[1];
    console.log(`\nTransfer ID: ${transferId}`);
    return transferId;
  }

  throw new Error("TransferInitiated event not found");
}
```

## Step 6: Monitor Transfer Status

```javascript
async function monitorTransferStatus(transferId) {
  console.log("\n=== Monitoring Transfer Status ===");

  const maxAttempts = 60;
  const pollInterval = 10000; // 10 seconds

  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    console.log(`\nAttempt ${attempt}/${maxAttempts}...`);

    // Get transfer details
    const transfer = await crossChainManager.transfers(transferId);

    console.log("Transfer details:");
    console.log(`  Sender: ${transfer.sender}`);
    console.log(`  Token: ${transfer.token}`);
    console.log(`  Amount: ${ethers.formatEther(transfer.amount)}`);
    console.log(`  Target Chain: ${transfer.targetChainId}`);
    console.log(`  Target Address: ${transfer.targetAddress}`);
    console.log(`  Completed: ${transfer.completed}`);
    console.log(`  CCIP Message ID: ${transfer.ccipMessageId}`);

    if (transfer.completed) {
      console.log("\n✓ Transfer completed successfully!");
      return true;
    }

    // Wait before next check
    if (attempt < maxAttempts) {
      console.log(`Waiting ${pollInterval / 1000} seconds...`);
      await new Promise((resolve) => setTimeout(resolve, pollInterval));
    }
  }

  console.log("\n⚠ Transfer monitoring timeout. Check manually.");
  return false;
}
```

## Complete Example

```javascript
async function main() {
  try {
    // Configuration
    const amount = ethers.parseEther("10"); // 10 tokens
    const targetChainSelector = 4051577828743386545n; // Polygon
    const targetAddress = "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0";

    console.log("=== ChainFinity Cross-Chain Transfer ===\n");
    console.log(`Source: Ethereum`);
    console.log(`Target: Polygon`);
    console.log(`Amount: ${ethers.formatEther(amount)} tokens`);
    console.log(`Recipient: ${targetAddress}\n`);

    // Step 1: Check prerequisites
    console.log("Step 1: Checking prerequisites...");
    await checkPrerequisites(amount, targetChainSelector);
    console.log("✓ Prerequisites check passed\n");

    // Step 2: Approve tokens
    console.log("Step 2: Approving tokens...");
    await approveTokens(amount);
    console.log("✓ Token approval completed\n");

    // Step 3: Initiate transfer
    console.log("Step 3: Initiating cross-chain transfer...");
    const transferId = await initiateCrossChainTransfer(
      TOKEN_ADDRESS,
      amount,
      targetChainSelector,
      targetAddress,
    );
    console.log("✓ Transfer initiated\n");

    // Step 4: Monitor status
    console.log("Step 4: Monitoring transfer status...");
    await monitorTransferStatus(transferId);

    console.log("\n=== Transfer Complete ===");
    console.log(`Transfer ID: ${transferId}`);
    console.log("Check your wallet on the target chain!");
  } catch (error) {
    console.error("\n❌ Error:", error.message);
    if (error.reason) console.error("Reason:", error.reason);
    if (error.code) console.error("Code:", error.code);
    process.exit(1);
  }
}

// Run the example
main();
```

## Expected Output

```
=== ChainFinity Cross-Chain Transfer ===

Source: Ethereum
Target: Polygon
Amount: 10.0 tokens
Recipient: 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0

Step 1: Checking prerequisites...
Token balance: 100.0
Transfer limit: 1000.0
ETH balance: 0.5
✓ Prerequisites check passed

Step 2: Approving tokens...
Checking allowance...
Current allowance: 0.0
Approving tokens...
Approval transaction sent: 0x123...
Waiting for confirmation...
✓ Tokens approved in block 12345678

Step 3: Initiating cross-chain transfer...

=== Initiating Cross-Chain Transfer ===
Token: 0x...
Amount: 10.0
Target Chain Selector: 4051577828743386545
Target Address: 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0

Transaction sent: 0x456...
Waiting for confirmation...
✓ Transfer initiated in block 12345679

Transfer ID: 0x789...

Step 4: Monitoring transfer status...

=== Monitoring Transfer Status ===

Attempt 1/60...
Transfer details:
  Sender: 0x...
  Token: 0x...
  Amount: 10.0
  Target Chain: 137
  Target Address: 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0
  Completed: false
  CCIP Message ID: 0x...

Waiting 10 seconds...

[... monitoring continues ...]

✓ Transfer completed successfully!

=== Transfer Complete ===
Transfer ID: 0x789...
Check your wallet on the target chain!
```

## Error Handling

Common errors and solutions:

```javascript
// Handle insufficient balance
try {
  await initiateCrossChainTransfer(...);
} catch (error) {
  if (error.code === "INSUFFICIENT_FUNDS") {
    console.error("Insufficient token balance");
  }
}

// Handle unsupported chain
try {
  await checkPrerequisites(amount, chainSelector);
} catch (error) {
  if (error.message.includes("not supported")) {
    console.error("Target chain not supported");
  }
}

// Handle rate limiting
try {
  await initiateCrossChainTransfer(...);
} catch (error) {
  if (error.message.includes("cooldown")) {
    console.error("Transfer cooldown period not elapsed");
  }
}
```

## Security Considerations

1. **Never share private keys** - Store in environment variables
2. **Verify contract addresses** - Double-check before use
3. **Test on testnets first** - Use Sepolia/Mumbai for testing
4. **Check gas prices** - Monitor network congestion
5. **Verify recipient address** - Cross-chain transfers are irreversible
6. **Monitor transaction status** - Ensure completion before proceeding

## Testing

```bash
# Set environment variables
export PRIVATE_KEY="your_private_key"
export ETH_RPC_URL="https://mainnet.infura.io/v3/YOUR_PROJECT_ID"

# Run the example
node examples/cross-chain-transfer.js

# Or test on testnet
export ETH_RPC_URL="https://sepolia.infura.io/v3/YOUR_PROJECT_ID"
node examples/cross-chain-transfer.js
```

## Next Steps

- Review [Smart Contract Documentation](../ARCHITECTURE.md#blockchain-components)
- Check [Chainlink CCIP Documentation](https://docs.chain.link/ccip)
- Explore [Risk Management Example](./risk-analysis.md)
- See [Portfolio Management Example](./portfolio-management.md)

## Related Documentation

- [API Reference](../API.md#blockchain-endpoints)
- [Configuration Guide](../CONFIGURATION.md#blockchain-configuration)
- [Troubleshooting](../TROUBLESHOOTING.md#blockchain-issues)
