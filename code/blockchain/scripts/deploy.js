// Deployment helper for ChainFinity contracts (Hardhat 2 + ethers v6).
//
// AssetVault and CrossChainManager take their admin/operator/emergency
// addresses as constructor arguments and are deployed directly (no proxy
// anywhere in this repo), so deployment and role assignment happen
// atomically in one transaction - see the constructor comments on those
// contracts for why that matters.
const fs = require("fs");
const path = require("path");
const hre = require("hardhat");

async function deployAssetVault() {
  const ethers = hre.ethers;
  const [admin, operator, emergency, feeCollector] = await ethers.getSigners();

  const Vault = await ethers.getContractFactory("AssetVault");
  const vault = await Vault.deploy(
    admin.address,
    operator.address,
    emergency.address,
    feeCollector.address,
  );
  await vault.waitForDeployment();

  return { vault, admin, operator, emergency, feeCollector };
}

/**
 * @param routerAddress Address of the Chainlink CCIP router on the target
 *   network (see https://docs.chain.link/ccip/directory). If omitted (e.g.
 *   for a local Hardhat network), a MockCCIPRouter is deployed so the script
 *   still runs end-to-end.
 */
async function deployCrossChainManager(routerAddress) {
  const ethers = hre.ethers;
  const [admin, operator, emergency] = await ethers.getSigners();

  let router = routerAddress;
  if (!router) {
    const MockRouter = await ethers.getContractFactory("MockCCIPRouter");
    const mockRouter = await MockRouter.deploy(0);
    await mockRouter.waitForDeployment();
    router = await mockRouter.getAddress();
  }

  const Manager = await ethers.getContractFactory("CrossChainManager");
  const manager = await Manager.deploy(
    admin.address,
    operator.address,
    emergency.address,
    router,
  );
  await manager.waitForDeployment();

  return { manager, router, admin, operator, emergency };
}

async function deployDeFiProtocol(treasury, insurance, priceOracle) {
  const ethers = hre.ethers;
  const [admin] = await ethers.getSigners();

  const DeFiProtocol = await ethers.getContractFactory(
    "InstitutionalDeFiProtocol",
  );
  const protocol = await DeFiProtocol.deploy(
    admin.address,
    treasury,
    insurance,
    priceOracle || ethers.ZeroAddress,
  );
  await protocol.waitForDeployment();

  return { protocol, admin };
}

async function deployGovernance() {
  const ethers = hre.ethers;
  const [admin, treasury] = await ethers.getSigners();

  const GovernanceToken = await ethers.getContractFactory("GovernanceToken");
  const token = await GovernanceToken.deploy();
  await token.waitForDeployment();

  const Governance = await ethers.getContractFactory("InstitutionalGovernance");
  const governance = await Governance.deploy(
    await token.getAddress(),
    treasury.address,
    admin.address,
  );
  await governance.waitForDeployment();

  return { governance, token, admin, treasury };
}

/**
 * Write contracts.<network>.json into deployments/, giving downstream
 * consumers (the backend's Web3Client, the deploy_chainfinity.sh pipeline,
 * frontends) a single source of truth for "what got deployed where" instead
 * of every consumer hardcoding addresses separately. Each entry carries the
 * ABI alongside the address, so nothing needs to reach into artifacts/
 * (which isn't a stable/shippable path) to make contract calls.
 */
async function writeDeploymentManifest(networkName, contracts) {
  const ethers = hre.ethers;
  const network = await ethers.provider.getNetwork();

  const entries = {};
  for (const [name, instance] of Object.entries(contracts)) {
    entries[name] = {
      address: await instance.getAddress(),
      abi: JSON.parse(instance.interface.formatJson()),
    };
  }

  const manifest = {
    network: networkName,
    chainId: Number(network.chainId),
    // The RPC endpoint these contracts were just deployed to (undefined
    // for the in-process "hardhat" network, which has no URL of its own).
    // Lets the backend's Web3Client connect to the same node it's reading
    // addresses/ABIs from without a separate ETH_RPC_URL override for
    // local dev - see services/blockchain/web3_client.py's
    // _resolve_rpc_url.
    rpcUrl: hre.network.config.url || null,
    deployedAt: new Date().toISOString(),
    contracts: entries,
  };

  const outDir = path.join(__dirname, "..", "deployments");
  fs.mkdirSync(outDir, { recursive: true });
  const outFile = path.join(outDir, `contracts.${networkName}.json`);
  fs.writeFileSync(outFile, JSON.stringify(manifest, null, 2));
  console.log(`\nWrote deployment manifest: ${outFile}`);

  return manifest;
}

async function main() {
  const networkName = hre.network.name;

  const { vault } = await deployAssetVault();
  console.log("AssetVault deployed to:", await vault.getAddress());

  const { manager, router } = await deployCrossChainManager(
    process.env.CCIP_ROUTER_ADDRESS,
  );
  console.log("CrossChainManager deployed to:", await manager.getAddress());
  console.log("  using CCIP router:", router);

  const { protocol } = await deployDeFiProtocol(
    process.env.TREASURY_ADDRESS || (await vault.getAddress()),
    process.env.INSURANCE_ADDRESS || (await vault.getAddress()),
    process.env.PRICE_ORACLE_ADDRESS,
  );
  console.log(
    "InstitutionalDeFiProtocol deployed to:",
    await protocol.getAddress(),
  );

  const { governance, token } = await deployGovernance();
  console.log("GovernanceToken deployed to:", await token.getAddress());
  console.log(
    "InstitutionalGovernance deployed to:",
    await governance.getAddress(),
  );

  await writeDeploymentManifest(networkName, {
    AssetVault: vault,
    CrossChainManager: manager,
    InstitutionalDeFiProtocol: protocol,
    GovernanceToken: token,
    InstitutionalGovernance: governance,
  });
}

module.exports = {
  deployAssetVault,
  deployCrossChainManager,
  deployDeFiProtocol,
  deployGovernance,
  writeDeploymentManifest,
  main,
};

if (require.main === module) {
  main().catch((error) => {
    console.error(error);
    process.exitCode = 1;
  });
}
