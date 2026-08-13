require("@nomicfoundation/hardhat-toolbox");
require("dotenv").config();

const path = require("path");
const { subtask } = require("hardhat/config");
const {
  TASK_COMPILE_SOLIDITY_GET_SOLC_BUILD,
} = require("hardhat/builtin-tasks/task-names");

/**
 * Hardhat 2 (CommonJS) configuration.
 *
 * The previous configuration combined hardhat ^3 with `"type": "module"` and
 * OpenZeppelin ^5 while every contract in this repository targets the
 * OpenZeppelin v4 API (security/ paths, SafeMath, Counters, IGovernor
 * override lists) - nothing compiled. Dependencies are now pinned to the
 * versions the contracts are written against.
 *
 * By default Hardhat downloads the solc binary for the configured version
 * from binaries.soliditylang.org on first compile. Sandboxed/offline CI
 * environments without access to that host fail with HH502. The `solc`
 * npm package ships the exact same compiler (as soljson.js) inside
 * node_modules, installed from the regular npm registry, so this override
 * points Hardhat at that local file instead of fetching anything.
 */
subtask(TASK_COMPILE_SOLIDITY_GET_SOLC_BUILD).setAction(
  async (args, _hre, runSuper) => {
    if (args.solcVersion === "0.8.19") {
      const compilerPath = path.join(
        __dirname,
        "node_modules",
        "solc",
        "soljson.js",
      );
      return {
        compilerPath,
        isSolcJs: true,
        version: args.solcVersion,
        longVersion: `${args.solcVersion}+commit.local`,
      };
    }
    return runSuper(args);
  },
);

// scripts/deploy_chainfinity.sh (at the repo root) selects a network name
// per environment: "localhost" for development, "testnet" for staging, and
// "mainnet" for production, then runs
// `npx hardhat run scripts/deploy.js --network <name>`. Previously only the
// default in-process "hardhat" network was defined, so anything but
// development would fail immediately with "network testnet doesn't exist"/
// "network mainnet doesn't exist". These three are wired to env vars so the
// same config file works for a local node, a public testnet, and mainnet
// without code changes - only the .env differs per environment. All three
// are optional at compile/unit-test time (only `npx hardhat compile` and
// `npx hardhat test`, which use the built-in `hardhat` network, are
// required to work with zero env vars set).
const DEPLOYER_PRIVATE_KEY = process.env.DEPLOYER_PRIVATE_KEY;
const accounts = DEPLOYER_PRIVATE_KEY ? [DEPLOYER_PRIVATE_KEY] : [];

module.exports = {
  solidity: {
    version: "0.8.19",
    settings: {
      optimizer: {
        enabled: true,
        runs: 200,
      },
      // InstitutionalGovernance/InstitutionalDeFiProtocol have enough local
      // variables in a few functions to trip "stack too deep" under the
      // legacy codegen pipeline. Compiling via IR fixes that without having
      // to artificially split those functions up.
      viaIR: true,
    },
  },
  networks: {
    hardhat: {
      chainId: 31337,
    },
    // `npx hardhat node` (see scripts/run_chainfinity.sh) starts a JSON-RPC
    // node on 127.0.0.1:8545 using Hardhat's default funded accounts, which
    // this network points at.
    localhost: {
      url: process.env.LOCALHOST_RPC_URL || "http://127.0.0.1:8545",
      chainId: 31337,
    },
    testnet: {
      url: process.env.TESTNET_RPC_URL || "",
      chainId: process.env.TESTNET_CHAIN_ID
        ? parseInt(process.env.TESTNET_CHAIN_ID, 10)
        : 11155111, // Sepolia
      accounts,
    },
    mainnet: {
      url: process.env.MAINNET_RPC_URL || "",
      chainId: 1,
      accounts,
    },
  },
};
