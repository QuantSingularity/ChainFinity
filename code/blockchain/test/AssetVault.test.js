// AssetVault deposit/withdraw test (Hardhat 2, ethers v6, CommonJS).
//
// Exercises the real AssetVault flows: fee-adjusted deposits, small direct
// withdrawals, and the multi-sig escrow path for large withdrawals
// (including escrowing funds at request time and refunding on cancel).
// This file was previously misnamed CrossChainManager.test.js despite only
// testing AssetVault, and called a nonexistent vault.getBalance() - both
// fixed here. CrossChainManager, DeFiProtocol, and Governance each now have
// their own dedicated test files.
const { expect } = require("chai");
const hre = require("hardhat");
const { ethers } = hre;

const TOKENS = (n) => ethers.parseEther(n.toString());

describe("AssetVault", () => {
  let vault, token, admin, operator, emergency, feeCollector, user;

  beforeEach(async () => {
    [admin, operator, emergency, feeCollector, user] =
      await ethers.getSigners();

    const Token = await ethers.getContractFactory("MockERC20");
    token = await Token.deploy("Mock", "MCK", TOKENS(1_000_000));
    await token.waitForDeployment();

    const Vault = await ethers.getContractFactory("AssetVault");
    vault = await Vault.deploy(
      admin.address,
      operator.address,
      emergency.address,
      feeCollector.address,
    );
    await vault.waitForDeployment();

    // Fund the user and approve the vault.
    await token.transfer(user.address, TOKENS(500_000));
    await token
      .connect(user)
      .approve(await vault.getAddress(), TOKENS(500_000));
  });

  it("credits a deposit net of the deposit fee", async () => {
    await vault.connect(user).deposit(await token.getAddress(), TOKENS(1000));
    // depositFeeRate is 10 bps (0.1%): 1000 -> 999 net.
    const balance = await vault.getUserTokenBalance(
      user.address,
      await token.getAddress(),
    );
    expect(balance).to.equal(TOKENS(999));
  });

  it("processes a small withdrawal directly", async () => {
    await vault.connect(user).deposit(await token.getAddress(), TOKENS(1000));
    await vault.connect(user).withdraw(await token.getAddress(), TOKENS(500));
    const balance = await vault.getUserTokenBalance(
      user.address,
      await token.getAddress(),
    );
    expect(balance).to.equal(TOKENS(499)); // 999 deposited - 500 withdrawn
  });

  it("escrows large withdrawals and pays out after enough approvals", async () => {
    // Lower the threshold so a modest amount routes through the multi-sig path.
    await vault.connect(admin).updateThresholds(TOKENS(100), 2);
    await vault.connect(user).deposit(await token.getAddress(), TOKENS(1000));

    await expect(
      vault.connect(user).withdraw(await token.getAddress(), TOKENS(500)),
    ).to.emit(vault, "WithdrawalRequested");

    // Funds are escrowed immediately: internal balance drops right away.
    const escrowed = await vault.getUserTokenBalance(
      user.address,
      await token.getAddress(),
    );
    expect(escrowed).to.equal(TOKENS(499)); // 999 - 500 escrowed

    const before = await token.balanceOf(user.address);
    await vault.connect(operator).approveWithdrawal(0);
    // Second distinct operator approval. Grant the role to another signer.
    await vault
      .connect(admin)
      .grantRole(await vault.OPERATOR_ROLE(), emergency.address);
    await vault.connect(emergency).approveWithdrawal(0);

    const after = await token.balanceOf(user.address);
    expect(after).to.be.greaterThan(before);
  });

  it("refunds escrow when a pending withdrawal is cancelled", async () => {
    await vault.connect(admin).updateThresholds(TOKENS(100), 2);
    await vault.connect(user).deposit(await token.getAddress(), TOKENS(1000));
    await vault.connect(user).withdraw(await token.getAddress(), TOKENS(500));

    await expect(vault.connect(user).cancelWithdrawal(0)).to.emit(
      vault,
      "WithdrawalCancelled",
    );

    const balance = await vault.getUserTokenBalance(
      user.address,
      await token.getAddress(),
    );
    expect(balance).to.equal(TOKENS(999)); // escrow fully refunded
  });

  it("rejects setting required approvals to zero", async () => {
    await expect(
      vault.connect(admin).updateThresholds(TOKENS(100), 0),
    ).to.be.revertedWith("Approvals must be at least 1");
  });
});
