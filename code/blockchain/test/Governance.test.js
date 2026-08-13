// InstitutionalGovernance tests (Hardhat 2, ethers v6, CommonJS).
const { expect } = require("chai");
const hre = require("hardhat");
const { ethers } = hre;

const TOKENS = (n) => ethers.parseEther(n.toString());
const DAY = 24 * 60 * 60;

const PROPOSAL_TYPE_PARAMETER = 0;
const VOTING_SIMPLE = 0;
const STATUS = {
  Pending: 0,
  Active: 1,
  Succeeded: 2,
  Defeated: 3,
  Queued: 4,
  Executed: 5,
  Cancelled: 6,
};
const CHOICE = { Against: 0, For: 1, Abstain: 2 };

async function increaseTime(seconds) {
  await hre.network.provider.send("evm_increaseTime", [seconds]);
  await hre.network.provider.send("evm_mine");
}

describe("InstitutionalGovernance", () => {
  let governance, token;
  let admin, treasury, proposer, voter1, voter2, guardian, outsider;

  beforeEach(async () => {
    [admin, treasury, proposer, voter1, voter2, guardian, outsider] =
      await ethers.getSigners();

    const Token = await ethers.getContractFactory("MockERC20");
    // 1,000,000 total supply => 4% default quorum = 40,000 tokens.
    token = await Token.deploy("Gov", "GOV", TOKENS(1_000_000));
    await token.waitForDeployment();

    const Governance = await ethers.getContractFactory(
      "InstitutionalGovernance",
    );
    governance = await Governance.deploy(
      await token.getAddress(),
      treasury.address,
      admin.address,
    );
    await governance.waitForDeployment();

    // Proposer needs >= proposalThreshold (100,000 tokens by default).
    await token.transfer(proposer.address, TOKENS(150_000));
    await token.transfer(voter1.address, TOKENS(50_000));
    await token.transfer(voter2.address, TOKENS(30_000));

    await governance
      .connect(admin)
      .grantRole(await governance.PROPOSER_ROLE(), proposer.address);
    await governance
      .connect(admin)
      .grantRole(await governance.GUARDIAN_ROLE(), guardian.address);
  });

  async function propose(overrides = {}) {
    const args = {
      proposalType: PROPOSAL_TYPE_PARAMETER,
      votingMechanism: VOTING_SIMPLE,
      title: "Test proposal",
      description: "A test proposal",
      targets: [treasury.address],
      values: [0],
      calldatas: ["0x"],
      requiresCompliance: false,
      ...overrides,
    };

    const tx = await governance
      .connect(proposer)
      .propose(
        args.proposalType,
        args.votingMechanism,
        args.title,
        args.description,
        args.targets,
        args.values,
        args.calldatas,
        args.requiresCompliance,
      );
    await tx.wait();
    return 1n; // first proposal ID (Counters starts at 1 after increment)
  }

  describe("propose", () => {
    it("reverts for a caller without enough voting power or proposer authorization", async () => {
      await expect(
        governance
          .connect(outsider)
          .propose(
            PROPOSAL_TYPE_PARAMETER,
            VOTING_SIMPLE,
            "t",
            "d",
            [],
            [],
            [],
            false,
          ),
      ).to.be.revertedWith("Not authorized to propose");
    });

    it("creates a pending proposal with a quorum computed from token supply", async () => {
      const proposalId = await propose();
      const p = await governance.proposals(proposalId);
      expect(p.status).to.equal(STATUS.Pending);
      // 4% of 1,000,000 = 40,000
      expect(p.quorumRequired).to.equal(TOKENS(40_000));
    });
  });

  describe("voting", () => {
    it("rejects votes before the voting delay has elapsed", async () => {
      const proposalId = await propose();
      await expect(
        governance.connect(voter1).castVote(proposalId, CHOICE.For, ""),
      ).to.be.revertedWith("Voting not started");
    });

    it("accepts votes once active and tallies weight by token balance", async () => {
      const proposalId = await propose();
      await increaseTime(DAY + 1);

      await expect(
        governance.connect(voter1).castVote(proposalId, CHOICE.For, "yes"),
      )
        .to.emit(governance, "VoteCast")
        .withArgs(
          voter1.address,
          proposalId,
          CHOICE.For,
          TOKENS(50_000),
          "yes",
        );

      const p = await governance.proposals(proposalId);
      expect(p.forVotes).to.equal(TOKENS(50_000));
      expect(p.status).to.equal(STATUS.Active);
    });

    it("rejects a second vote from the same address", async () => {
      const proposalId = await propose();
      await increaseTime(DAY + 1);
      await governance.connect(voter1).castVote(proposalId, CHOICE.For, "");
      await expect(
        governance.connect(voter1).castVote(proposalId, CHOICE.Against, ""),
      ).to.be.revertedWith("Already voted");
    });

    it("rejects votes after the voting period ends", async () => {
      const proposalId = await propose();
      await increaseTime(DAY + 7 * DAY + 1);
      await expect(
        governance.connect(voter1).castVote(proposalId, CHOICE.For, ""),
      ).to.be.revertedWith("Voting ended");
    });
  });

  describe("finalization and execution", () => {
    it("queues a proposal that clears quorum and the approval threshold", async () => {
      const proposalId = await propose();
      await increaseTime(DAY + 1);

      // For: 50,000 + 150,000 (proposer) = 200,000; Against: 30,000.
      // Decisive votes: 230,000, well above the 40,000 quorum.
      // Approval: 200,000 / 230,000 ≈ 87% >= 51% threshold.
      await governance.connect(voter1).castVote(proposalId, CHOICE.For, "");
      await governance.connect(voter2).castVote(proposalId, CHOICE.Against, "");
      await governance.connect(proposer).castVote(proposalId, CHOICE.For, "");

      await increaseTime(7 * DAY + 1);
      await governance.finalizeProposal(proposalId);

      const p = await governance.proposals(proposalId);
      expect(p.status).to.equal(STATUS.Queued);
    });

    it("defeats a proposal that fails to reach quorum", async () => {
      const proposalId = await propose();
      await increaseTime(DAY + 1);

      // voter2 alone (30,000) is short of the 40,000 quorum.
      await governance.connect(voter2).castVote(proposalId, CHOICE.For, "");

      await increaseTime(7 * DAY + 1);
      await governance.finalizeProposal(proposalId);

      const p = await governance.proposals(proposalId);
      expect(p.status).to.equal(STATUS.Defeated);
    });

    it("defeats a proposal that clears quorum but not the approval threshold", async () => {
      const proposalId = await propose();
      await increaseTime(DAY + 1);

      // Decisive votes: 80,000 (>= 40,000 quorum), but only 37.5% For.
      await governance.connect(voter1).castVote(proposalId, CHOICE.Against, "");
      await governance.connect(voter2).castVote(proposalId, CHOICE.For, "");

      await increaseTime(7 * DAY + 1);
      await governance.finalizeProposal(proposalId);

      const p = await governance.proposals(proposalId);
      expect(p.status).to.equal(STATUS.Defeated);
    });

    it("executes a queued proposal once the execution delay has passed", async () => {
      const proposalId = await propose();
      await increaseTime(DAY + 1);
      await governance.connect(proposer).castVote(proposalId, CHOICE.For, "");
      await increaseTime(7 * DAY + 1);
      await governance.finalizeProposal(proposalId);

      await expect(governance.execute(proposalId)).to.be.revertedWith(
        "Execution time not reached",
      );

      await increaseTime(2 * DAY + 1);
      await expect(governance.execute(proposalId))
        .to.emit(governance, "ProposalExecuted")
        .withArgs(proposalId, admin.address);

      const p = await governance.proposals(proposalId);
      expect(p.status).to.equal(STATUS.Executed);
    });
  });

  describe("cancel", () => {
    it("allows the proposer to cancel their own proposal", async () => {
      const proposalId = await propose();
      await expect(governance.connect(proposer).cancel(proposalId)).to.emit(
        governance,
        "ProposalCancelled",
      );
      const p = await governance.proposals(proposalId);
      expect(p.status).to.equal(STATUS.Cancelled);
    });

    it("allows a guardian to cancel someone else's proposal", async () => {
      const proposalId = await propose();
      await expect(governance.connect(guardian).cancel(proposalId)).to.emit(
        governance,
        "ProposalCancelled",
      );
    });

    it("rejects cancellation from an unrelated account", async () => {
      const proposalId = await propose();
      await expect(
        governance.connect(outsider).cancel(proposalId),
      ).to.be.revertedWith("Not authorized to cancel");
    });
  });

  describe("delegation", () => {
    it("moves voting power to the delegate without double-counting", async () => {
      await governance.connect(voter1).delegate(voter2.address);

      expect(await governance.votingPower(voter2.address)).to.equal(
        TOKENS(50_000),
      );
      expect(await governance.delegatedOut(voter1.address)).to.equal(
        TOKENS(50_000),
      );
    });

    it("returns power to the delegator on revoke", async () => {
      await governance.connect(voter1).delegate(voter2.address);
      await governance.connect(voter1).revokeDelegation();

      expect(await governance.votingPower(voter2.address)).to.equal(0);
      expect(await governance.delegatedOut(voter1.address)).to.equal(0);
    });

    it("re-delegating moves power off the previous delegate cleanly", async () => {
      await governance.connect(voter1).delegate(voter2.address);
      await governance.connect(voter1).delegate(proposer.address);

      expect(await governance.votingPower(voter2.address)).to.equal(0);
      expect(await governance.votingPower(proposer.address)).to.equal(
        TOKENS(50_000),
      );
    });
  });
});
