// InstitutionalDeFiProtocol tests (Hardhat 2, ethers v6, CommonJS).
const { expect } = require("chai");
const hre = require("hardhat");
const { ethers } = hre;

const TOKENS = (n) => ethers.parseEther(n.toString());

// PoolType.Staking, RiskLevel.Medium (see the contract's enum ordering).
const POOL_TYPE_STAKING = 1;
const RISK_MEDIUM = 1;

describe("InstitutionalDeFiProtocol", () => {
  let protocol, stakingToken, rewardToken;
  let admin, treasury, insurance, oracle, user, user2;

  beforeEach(async () => {
    [admin, treasury, insurance, oracle, user, user2] =
      await ethers.getSigners();

    const Token = await ethers.getContractFactory("MockERC20");
    stakingToken = await Token.deploy("Stake", "STK", TOKENS(1_000_000));
    await stakingToken.waitForDeployment();
    rewardToken = await Token.deploy("Reward", "RWD", TOKENS(1_000_000));
    await rewardToken.waitForDeployment();

    const Protocol = await ethers.getContractFactory(
      "InstitutionalDeFiProtocol",
    );
    protocol = await Protocol.deploy(
      admin.address,
      treasury.address,
      insurance.address,
      oracle.address,
    );
    await protocol.waitForDeployment();

    await protocol
      .connect(admin)
      .setTokenAuthorization(await stakingToken.getAddress(), true);
    await protocol
      .connect(admin)
      .setTokenAuthorization(await rewardToken.getAddress(), true);

    await stakingToken.transfer(user.address, TOKENS(10_000));
    await stakingToken.transfer(user2.address, TOKENS(10_000));
    await stakingToken
      .connect(user)
      .approve(await protocol.getAddress(), TOKENS(10_000));
    await stakingToken
      .connect(user2)
      .approve(await protocol.getAddress(), TOKENS(10_000));

    // Fund the protocol so it can pay out staking rewards.
    await rewardToken.transfer(await protocol.getAddress(), TOKENS(100_000));
  });

  async function createPool(overrides = {}) {
    const args = {
      stakingToken: await stakingToken.getAddress(),
      rewardToken: await rewardToken.getAddress(),
      poolType: POOL_TYPE_STAKING,
      riskLevel: RISK_MEDIUM,
      rewardRate: TOKENS(1), // 1 token/sec
      rewardsDuration: 30 * 24 * 60 * 60,
      minimumStake: TOKENS(10),
      maximumStake: TOKENS(5_000),
      lockupPeriod: 7 * 24 * 60 * 60,
      requiresKYC: false,
      ...overrides,
    };

    const tx = await protocol
      .connect(admin)
      .createPool(
        args.stakingToken,
        args.rewardToken,
        args.poolType,
        args.riskLevel,
        args.rewardRate,
        args.rewardsDuration,
        args.minimumStake,
        args.maximumStake,
        args.lockupPeriod,
        args.requiresKYC,
      );
    await tx.wait();
    return 0; // first pool created in a fresh protocol instance
  }

  describe("createPool", () => {
    it("rejects an unauthorized staking token", async () => {
      const Token = await ethers.getContractFactory("MockERC20");
      const rogueToken = await Token.deploy("Rogue", "RG", TOKENS(1000));
      await expect(
        protocol
          .connect(admin)
          .createPool(
            await rogueToken.getAddress(),
            await rewardToken.getAddress(),
            POOL_TYPE_STAKING,
            RISK_MEDIUM,
            TOKENS(1),
            1000,
            TOKENS(1),
            TOKENS(100),
            0,
            false,
          ),
      ).to.be.revertedWith("Staking token not authorized");
    });

    it("creates a pool with default risk parameters", async () => {
      const poolId = await createPool();
      const params = await protocol.riskParameters(poolId);
      expect(params.maxUserStake).to.equal(TOKENS(5_000));
      expect(params.collateralRatio).to.equal(150);
    });
  });

  describe("stake / withdraw / claimReward", () => {
    it("stakes tokens and tracks total staked", async () => {
      const poolId = await createPool();
      await protocol.connect(user).stake(poolId, TOKENS(100));

      const info = await protocol.pools(poolId);
      expect(info.totalStaked).to.equal(TOKENS(100));
    });

    it("rejects stakes below the pool minimum", async () => {
      const poolId = await createPool();
      await expect(
        protocol.connect(user).stake(poolId, TOKENS(1)),
      ).to.be.revertedWith("Below minimum stake");
    });

    it("rejects stakes that would exceed the per-user max stake risk limit", async () => {
      const poolId = await createPool({ maximumStake: TOKENS(50) });
      await expect(
        protocol.connect(user).stake(poolId, TOKENS(100)),
      ).to.be.revertedWith("Max user stake exceeded");
    });

    it("blocks staking for a blacklisted address", async () => {
      const poolId = await createPool();
      await protocol.connect(admin).setBlacklisted(user.address, true);
      await expect(
        protocol.connect(user).stake(poolId, TOKENS(100)),
      ).to.be.revertedWith("Address is blacklisted");
    });

    it("requires KYC verification when the pool demands it", async () => {
      const poolId = await createPool({ requiresKYC: true });
      await expect(
        protocol.connect(user).stake(poolId, TOKENS(100)),
      ).to.be.revertedWith("KYC verification required");

      await protocol.connect(admin).setKYCStatus(poolId, user.address, true);
      await expect(protocol.connect(user).stake(poolId, TOKENS(100))).to.not.be
        .reverted;
    });

    it("charges the early withdrawal fee to treasury during the lockup period", async () => {
      const poolId = await createPool();
      await protocol.connect(user).stake(poolId, TOKENS(100));

      const treasuryBefore = await stakingToken.balanceOf(treasury.address);
      await protocol.connect(user).withdraw(poolId, TOKENS(100));
      const treasuryAfter = await stakingToken.balanceOf(treasury.address);

      // Medium risk => 1% early withdrawal fee (see
      // _getDefaultEarlyWithdrawalFee).
      expect(treasuryAfter - treasuryBefore).to.equal(TOKENS(1));
    });

    it("charges no early withdrawal fee once the lockup has elapsed", async () => {
      const poolId = await createPool({ lockupPeriod: 60 });
      await protocol.connect(user).stake(poolId, TOKENS(100));

      await hre.network.provider.send("evm_increaseTime", [61]);
      await hre.network.provider.send("evm_mine");

      const treasuryBefore = await stakingToken.balanceOf(treasury.address);
      await protocol.connect(user).withdraw(poolId, TOKENS(100));
      const treasuryAfter = await stakingToken.balanceOf(treasury.address);

      expect(treasuryAfter).to.equal(treasuryBefore);
    });

    it("accrues rewards linearly over time for a single staker", async () => {
      const poolId = await createPool({ rewardRate: TOKENS(1) });
      await protocol.connect(user).stake(poolId, TOKENS(100));

      await hre.network.provider.send("evm_increaseTime", [100]);
      await hre.network.provider.send("evm_mine");

      const earned = await protocol.earned(poolId, user.address);
      // 1 token/sec for ~100s, with a couple of seconds of tolerance for
      // the block timestamps involved in staking and mining.
      expect(earned).to.be.closeTo(TOKENS(100), TOKENS(2));
    });

    it("pays claimed rewards net of the performance fee to treasury", async () => {
      const poolId = await createPool({ rewardRate: TOKENS(1) });
      await protocol.connect(user).stake(poolId, TOKENS(100));

      await hre.network.provider.send("evm_increaseTime", [100]);
      await hre.network.provider.send("evm_mine");

      const before = await rewardToken.balanceOf(user.address);
      await protocol.connect(user).claimReward(poolId);
      const after = await rewardToken.balanceOf(user.address);

      // Staking pools default to a 1% performance fee, so the user should
      // net slightly under 100 reward tokens for ~100s at 1 token/sec.
      expect(after - before).to.be.closeTo(TOKENS(99), TOKENS(2));
    });
  });

  describe("emergencyWithdraw", () => {
    it("returns a user's full stake when invoked by EMERGENCY_ROLE", async () => {
      const poolId = await createPool();
      await protocol.connect(user).stake(poolId, TOKENS(100));

      const before = await stakingToken.balanceOf(user.address);
      // The deploying admin holds EMERGENCY_ROLE (granted in the constructor).
      await protocol.connect(admin).emergencyWithdraw(poolId, user.address);
      const after = await stakingToken.balanceOf(user.address);

      expect(after - before).to.equal(TOKENS(100));
    });

    it("reverts for a caller without EMERGENCY_ROLE", async () => {
      const poolId = await createPool();
      await protocol.connect(user).stake(poolId, TOKENS(100));
      await expect(
        protocol.connect(user2).emergencyWithdraw(poolId, user.address),
      ).to.be.reverted;
    });
  });

  describe("AMM liquidity pool", () => {
    let poolId;

    beforeEach(async () => {
      const tx = await protocol.connect(admin).createLiquidityPool(
        await stakingToken.getAddress(),
        await rewardToken.getAddress(),
        30, // 0.3% fee
      );
      await tx.wait();
      poolId = 0;

      await rewardToken.transfer(user.address, TOKENS(10_000));
      await rewardToken
        .connect(user)
        .approve(await protocol.getAddress(), TOKENS(10_000));
    });

    it("mints liquidity as sqrt(amount0 * amount1) for the first deposit", async () => {
      await protocol
        .connect(user)
        .addLiquidity(poolId, TOKENS(100), TOKENS(400), 0);

      const pool = await protocol.liquidityPools(poolId);
      expect(pool.totalLiquidity).to.equal(TOKENS(200)); // sqrt(100*400)=200
    });

    it("swaps token0 for token1 along the constant-product curve", async () => {
      await protocol
        .connect(user)
        .addLiquidity(poolId, TOKENS(10_000), TOKENS(10_000), 0);

      const before = await rewardToken.balanceOf(user2.address);
      await stakingToken.transfer(user2.address, TOKENS(100));
      await stakingToken
        .connect(user2)
        .approve(await protocol.getAddress(), TOKENS(100));

      await protocol
        .connect(user2)
        .swap(poolId, await stakingToken.getAddress(), TOKENS(100), 0);

      const after = await rewardToken.balanceOf(user2.address);
      expect(after).to.be.greaterThan(before);
    });

    it("returns proportional reserves on removeLiquidity", async () => {
      await protocol
        .connect(user)
        .addLiquidity(poolId, TOKENS(100), TOKENS(400), 0);

      const before0 = await stakingToken.balanceOf(user.address);
      const before1 = await rewardToken.balanceOf(user.address);

      await protocol.connect(user).removeLiquidity(poolId, TOKENS(200), 0, 0); // full withdrawal

      const after0 = await stakingToken.balanceOf(user.address);
      const after1 = await rewardToken.balanceOf(user.address);

      expect(after0 - before0).to.equal(TOKENS(100));
      expect(after1 - before1).to.equal(TOKENS(400));
    });
  });
});
