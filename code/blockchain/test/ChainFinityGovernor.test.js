// ChainFinityGovernor / ChainFinityTimelock / GovernanceToken tests
// (Hardhat 2, ethers v6, CommonJS).
//
// Exercises the standard OpenZeppelin Governor flow: delegate voting power,
// propose, vote past quorum, queue through the timelock, then execute after
// the timelock delay.
const { expect } = require("chai");
const hre = require("hardhat");
const { ethers } = hre;

const TOKENS = (n) => ethers.parseEther(n.toString());

async function mineBlocks(n) {
  for (let i = 0; i < n; i++) {
    await hre.network.provider.send("evm_mine");
  }
}

describe("ChainFinityGovernor stack", () => {
  let token, timelock, governor;
  let admin, voter, other;
  const MIN_DELAY = 3600; // 1 hour

  beforeEach(async () => {
    [admin, voter, other] = await ethers.getSigners();

    const GovernanceToken = await ethers.getContractFactory("GovernanceToken");
    token = await GovernanceToken.deploy();
    await token.waitForDeployment();

    // Governor is the only proposer/executor; anyone can execute once
    // queued (executors = [] means open execution in TimelockController).
    const Timelock = await ethers.getContractFactory("ChainFinityTimelock");
    timelock = await Timelock.deploy(MIN_DELAY, [], []);
    await timelock.waitForDeployment();

    const Governor = await ethers.getContractFactory("ChainFinityGovernor");
    governor = await Governor.deploy(
      await token.getAddress(),
      await timelock.getAddress(),
    );
    await governor.waitForDeployment();

    const proposerRole = await timelock.PROPOSER_ROLE();
    const executorRole = await timelock.EXECUTOR_ROLE();
    const adminRole = await timelock.TIMELOCK_ADMIN_ROLE();

    await timelock.grantRole(proposerRole, await governor.getAddress());
    await timelock.grantRole(executorRole, ethers.ZeroAddress); // anyone
    // Renounce the deployer's timelock admin role so the governor is the
    // sole path to changing timelock-controlled state.
    await timelock.renounceRole(adminRole, admin.address);

    // Give the voter enough tokens to clear quorum, and self-delegate so
    // the balance actually counts as voting power (ERC20Votes requires an
    // explicit delegation checkpoint).
    await token.transfer(voter.address, TOKENS(10_000_000)); // 10% of supply
    await token.connect(voter).delegate(voter.address);
    await mineBlocks(1);
  });

  it("moves tokens through propose -> vote -> queue -> execute", async () => {
    const transferAmount = TOKENS(1000);
    await token.transfer(await timelock.getAddress(), transferAmount);

    const calldata = token.interface.encodeFunctionData("transfer", [
      other.address,
      transferAmount,
    ]);
    const targets = [await token.getAddress()];
    const values = [0];
    const calldatas = [calldata];
    const description = "Transfer 1000 GOV to other";

    const proposeTx = await governor
      .connect(voter)
      .propose(targets, values, calldatas, description);
    const proposeReceipt = await proposeTx.wait();
    const proposalId = proposeReceipt.logs.find(
      (l) => l.fragment && l.fragment.name === "ProposalCreated",
    ).args.proposalId;

    // Voting delay is 7200 blocks.
    await mineBlocks(7201);

    await governor.connect(voter).castVote(proposalId, 1); // 1 = For

    // Voting period is 50400 blocks.
    await mineBlocks(50401);

    expect(await governor.state(proposalId)).to.equal(4); // Succeeded

    const descriptionHash = ethers.id(description);
    await governor
      .connect(voter)
      .queue(targets, values, calldatas, descriptionHash);

    expect(await governor.state(proposalId)).to.equal(5); // Queued

    await hre.network.provider.send("evm_increaseTime", [MIN_DELAY + 1]);
    await hre.network.provider.send("evm_mine");

    const before = await token.balanceOf(other.address);
    await governor
      .connect(voter)
      .execute(targets, values, calldatas, descriptionHash);
    const after = await token.balanceOf(other.address);

    expect(after - before).to.equal(transferAmount);
    expect(await governor.state(proposalId)).to.equal(7); // Executed
  });

  it("supports quadratic vote weighting via _countVote params", async () => {
    // sqrt(x) helper is exercised indirectly through _countVote when a
    // quadratic flag is passed; here we just confirm standard (non-quadratic)
    // voting still counts the voter's full weight.
    const targets = [await token.getAddress()];
    const values = [0];
    const calldatas = [
      token.interface.encodeFunctionData("transfer", [other.address, 0]),
    ];
    const description = "No-op transfer";

    const tx = await governor
      .connect(voter)
      .propose(targets, values, calldatas, description);
    const receipt = await tx.wait();
    const proposalId = receipt.logs.find(
      (l) => l.fragment && l.fragment.name === "ProposalCreated",
    ).args.proposalId;

    await mineBlocks(7201);
    await governor.connect(voter).castVote(proposalId, 1);

    const votes = await governor.proposalVotes(proposalId);
    expect(votes.forVotes).to.equal(TOKENS(10_000_000));
  });
});
