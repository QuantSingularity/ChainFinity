// CrossChainManager tests (Hardhat 2, ethers v6, CommonJS).
//
// Uses MockCCIPRouter (contracts/mocks/MockCCIPRouter.sol) to stand in for
// the real Chainlink CCIP router: it charges a configurable fixed fee on
// ccipSend, and exposes `deliver` so a test can play the role of the
// off-chain CCIP network relaying a message into `ccipReceive`.
const { expect } = require("chai");
const hre = require("hardhat");
const { ethers } = hre;

const TOKENS = (n) => ethers.parseEther(n.toString());

// Chain selectors pre-registered by the constructor.
const ETH_SELECTOR = 5009297550715157269n;
const ARBITRUM_SELECTOR = 4949039107694359620n;
const UNSUPPORTED_SELECTOR = 999999999999999999n;

describe("CrossChainManager", () => {
  let manager, token, router;
  let admin, operator, emergency, user, remoteManager, other;

  beforeEach(async () => {
    [admin, operator, emergency, user, remoteManager, other] =
      await ethers.getSigners();

    const Token = await ethers.getContractFactory("MockERC20");
    token = await Token.deploy("Mock", "MCK", TOKENS(1_000_000));
    await token.waitForDeployment();

    const Router = await ethers.getContractFactory("MockCCIPRouter");
    router = await Router.deploy(TOKENS(0)); // fee configured per-test
    await router.waitForDeployment();

    const Manager = await ethers.getContractFactory("CrossChainManager");
    manager = await Manager.deploy(
      admin.address,
      operator.address,
      emergency.address,
      await router.getAddress(),
    );
    await manager.waitForDeployment();

    // Trust "remoteManager" as the CrossChainManager deployment on Arbitrum.
    await manager
      .connect(admin)
      .setTrustedRemote(ARBITRUM_SELECTOR, remoteManager.address);

    await token.transfer(user.address, TOKENS(500_000));
    await token
      .connect(user)
      .approve(await manager.getAddress(), TOKENS(500_000));
  });

  describe("initiateTransfer", () => {
    it("pulls tokens, charges the CCIP fee, and refunds any excess", async () => {
      await router.setFixedFee(ethers.parseEther("0.01"));

      const amount = TOKENS(1000);
      const before = await ethers.provider.getBalance(user.address);

      const tx = await manager.connect(user).initiateTransfer(
        await token.getAddress(),
        amount,
        ARBITRUM_SELECTOR,
        other.address,
        { value: ethers.parseEther("1") }, // overpay on purpose
      );
      const receipt = await tx.wait();
      const gasCost = receipt.gasUsed * receipt.gasPrice;

      await expect(tx).to.emit(manager, "TransferInitiated");

      // 0.2% default LP fee is retained by the contract; the rest is
      // escrowed as bridge liquidity - either way tokens leave the user.
      expect(await token.balanceOf(await manager.getAddress())).to.equal(
        amount,
      );

      const after = await ethers.provider.getBalance(user.address);
      // Only the router's fixed fee (0.01 ETH) plus gas should have left the
      // user's balance - the 1 ETH - 0.01 ETH excess must be refunded.
      const spent = before - after;
      expect(spent - gasCost).to.equal(ethers.parseEther("0.01"));
    });

    it("rejects transfers to a chain with no trusted remote registered", async () => {
      // Ethereum mainnet selector is "supported" by default but has no
      // trusted remote configured in this test.
      await expect(
        manager
          .connect(user)
          .initiateTransfer(
            await token.getAddress(),
            TOKENS(100),
            ETH_SELECTOR,
            other.address,
          ),
      ).to.be.revertedWith("No trusted remote for chain");
    });

    it("rejects transfers to an unsupported chain", async () => {
      await expect(
        manager
          .connect(user)
          .initiateTransfer(
            await token.getAddress(),
            TOKENS(100),
            UNSUPPORTED_SELECTOR,
            other.address,
          ),
      ).to.be.revertedWith("Unsupported target chain");
    });

    it("enforces the per-address cooldown between transfers", async () => {
      await manager
        .connect(user)
        .initiateTransfer(
          await token.getAddress(),
          TOKENS(100),
          ARBITRUM_SELECTOR,
          other.address,
        );

      await expect(
        manager
          .connect(user)
          .initiateTransfer(
            await token.getAddress(),
            TOKENS(100),
            ARBITRUM_SELECTOR,
            other.address,
          ),
      ).to.be.revertedWith("Transfer cooldown active");
    });

    it("rejects amounts above the per-transfer limit", async () => {
      await manager
        .connect(admin)
        .updateRateLimit(TOKENS(500), 0 /* no cooldown, for this test */);

      await expect(
        manager
          .connect(user)
          .initiateTransfer(
            await token.getAddress(),
            TOKENS(1000),
            ARBITRUM_SELECTOR,
            other.address,
          ),
      ).to.be.revertedWith("Amount exceeds transfer limit");
    });

    it("enforces the daily circuit breaker across multiple transfers", async () => {
      await manager.connect(admin).updateRateLimit(TOKENS(1_000_000), 0);
      await manager.connect(admin).updateCircuitBreaker(TOKENS(150));

      await manager
        .connect(user)
        .initiateTransfer(
          await token.getAddress(),
          TOKENS(100),
          ARBITRUM_SELECTOR,
          other.address,
        );

      await expect(
        manager
          .connect(user)
          .initiateTransfer(
            await token.getAddress(),
            TOKENS(100),
            ARBITRUM_SELECTOR,
            other.address,
          ),
      ).to.be.revertedWith("Daily transfer limit reached");
    });
  });

  describe("ccipReceive", () => {
    async function encodeMessage(receiver, tokenAddr, amount) {
      return ethers.AbiCoder.defaultAbiCoder().encode(
        ["address", "address", "address", "uint256"],
        [user.address, receiver, tokenAddr, amount],
      );
    }

    beforeEach(async () => {
      // Fund the manager so it can pay out an inbound transfer, mirroring
      // tokens that would already be escrowed as bridge liquidity.
      await token.transfer(await manager.getAddress(), TOKENS(1000));
    });

    it("pays out a message relayed by the router from a trusted remote", async () => {
      const data = await encodeMessage(
        other.address,
        await token.getAddress(),
        TOKENS(500),
      );

      await expect(
        router.deliver(
          await manager.getAddress(),
          ARBITRUM_SELECTOR,
          remoteManager.address,
          data,
        ),
      ).to.changeTokenBalance(token, other, TOKENS(500));
    });

    it("reverts if called by anything other than the router", async () => {
      const data = await encodeMessage(
        other.address,
        await token.getAddress(),
        TOKENS(500),
      );
      const message = {
        messageId: ethers.ZeroHash,
        sourceChainSelector: ARBITRUM_SELECTOR,
        sender: ethers.AbiCoder.defaultAbiCoder().encode(
          ["address"],
          [remoteManager.address],
        ),
        data,
        destTokenAmounts: [],
      };

      await expect(
        manager.connect(other).ccipReceive(message),
      ).to.be.revertedWith("Sender not router");
    });

    it("reverts a message from an untrusted sender on a supported chain", async () => {
      const data = await encodeMessage(
        other.address,
        await token.getAddress(),
        TOKENS(500),
      );

      // `other` is not the registered trusted remote for Arbitrum.
      await expect(
        router.deliver(
          await manager.getAddress(),
          ARBITRUM_SELECTOR,
          other.address,
          data,
        ),
      ).to.be.revertedWith("Untrusted remote sender");
    });

    it("reverts a message from an unsupported source chain", async () => {
      const data = await encodeMessage(
        other.address,
        await token.getAddress(),
        TOKENS(500),
      );

      await expect(
        router.deliver(
          await manager.getAddress(),
          UNSUPPORTED_SELECTOR,
          remoteManager.address,
          data,
        ),
      ).to.be.revertedWith("Unsupported source chain");
    });
  });

  describe("fee distribution", () => {
    it("distributes collected LP fees pro-rata and leaves bridge principal untouched", async () => {
      await manager.connect(admin).addLiquidityProvider(user.address, 1); // 100% of shares
      const otherToken = await token.getAddress();

      await manager
        .connect(user)
        .initiateTransfer(
          otherToken,
          TOKENS(1000),
          ARBITRUM_SELECTOR,
          other.address,
        );

      // 0.2% default LP fee on 1000 tokens = 2 tokens.
      expect(await manager.collectedFees(otherToken)).to.equal(TOKENS(2));

      const before = await token.balanceOf(user.address);
      await manager.connect(operator).distributeFees(otherToken);
      const after = await token.balanceOf(user.address);

      expect(after - before).to.equal(TOKENS(2));
      // Only the fee pot moved - bridge principal (998 tokens) stays put.
      expect(await token.balanceOf(await manager.getAddress())).to.equal(
        TOKENS(998),
      );
    });

    it("reverts distributing fees for a token with nothing collected", async () => {
      await manager.connect(admin).addLiquidityProvider(user.address, 1);
      await expect(
        manager.connect(operator).distributeFees(await token.getAddress()),
      ).to.be.revertedWith("No fees to distribute");
    });
  });
});
