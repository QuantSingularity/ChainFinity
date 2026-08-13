// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/security/Pausable.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/utils/math/SafeMath.sol";
import "@openzeppelin/contracts/utils/math/Math.sol";
import "@openzeppelin/contracts/utils/cryptography/ECDSA.sol";
import "@openzeppelin/contracts/utils/Counters.sol";
import "@openzeppelin/contracts/utils/Address.sol";

/**
 * @title InstitutionalGovernance
 * @dev Advanced governance contract for institutional-grade decision making
 * @notice Supports multiple voting mechanisms, delegation, and compliance features
 */
contract InstitutionalGovernance is ReentrancyGuard, Pausable, AccessControl {
    using SafeMath for uint256;
    using Counters for Counters.Counter;
    using ECDSA for bytes32;
    using Address for address;

    // Role definitions
    bytes32 public constant ADMIN_ROLE = keccak256("ADMIN_ROLE");
    bytes32 public constant PROPOSER_ROLE = keccak256("PROPOSER_ROLE");
    bytes32 public constant EXECUTOR_ROLE = keccak256("EXECUTOR_ROLE");
    bytes32 public constant GUARDIAN_ROLE = keccak256("GUARDIAN_ROLE");
    bytes32 public constant COMPLIANCE_ROLE = keccak256("COMPLIANCE_ROLE");

    // Voting mechanisms
    enum VotingMechanism {
        SimpleVoting, // One token = one vote
        QuadraticVoting, // Square root of tokens
        WeightedVoting, // Custom weights
        DelegatedVoting, // Delegation support
        MultiSigVoting // Multi-signature style
    }

    // Proposal types
    enum ProposalType {
        Parameter, // Parameter changes
        Treasury, // Treasury operations
        Upgrade, // Contract upgrades
        Emergency, // Emergency actions
        Strategic, // Strategic decisions
        Compliance // Compliance changes
    }

    // Proposal status
    enum ProposalStatus {
        Pending, // Waiting for voting period
        Active, // Currently voting
        Succeeded, // Passed voting
        Defeated, // Failed voting
        Queued, // Queued for execution
        Executed, // Successfully executed
        Cancelled, // Cancelled
        Expired // Expired without execution
    }

    // Vote choice
    enum VoteChoice {
        Against,
        For,
        Abstain
    }

    // Proposal structure
    struct Proposal {
        uint256 id;
        address proposer;
        ProposalType proposalType;
        VotingMechanism votingMechanism;
        string title;
        string description;
        bytes32 descriptionHash;
        address[] targets;
        uint256[] values;
        bytes[] calldatas;
        uint256 startTime;
        uint256 endTime;
        uint256 executionTime;
        uint256 forVotes;
        uint256 againstVotes;
        uint256 abstainVotes;
        uint256 totalVotingPower;
        uint256 quorumRequired;
        uint256 approvalThreshold;
        ProposalStatus status;
        bool requiresCompliance;
        mapping(address => Vote) votes;
        mapping(address => uint256) delegatedVotes;
    }

    // Vote structure
    struct Vote {
        bool hasVoted;
        VoteChoice choice;
        uint256 weight;
        uint256 timestamp;
        string reason;
    }

    // Delegation structure
    struct Delegation {
        address delegate;
        uint256 amount;
        uint256 timestamp;
        bool isActive;
    }

    // Governance parameters
    struct GovernanceParams {
        uint256 votingDelay; // Delay before voting starts
        uint256 votingPeriod; // Duration of voting
        uint256 executionDelay; // Delay before execution
        uint256 proposalThreshold; // Minimum tokens to propose
        uint256 quorumNumerator; // Quorum percentage (numerator)
        uint256 quorumDenominator; // Quorum percentage (denominator)
        uint256 approvalThreshold; // Approval threshold percentage
        uint256 maxProposalActions; // Maximum actions per proposal
    }

    // Events
    event ProposalCreated(
        uint256 indexed proposalId,
        address indexed proposer,
        ProposalType proposalType,
        string title,
        uint256 startTime,
        uint256 endTime
    );

    event VoteCast(
        address indexed voter,
        uint256 indexed proposalId,
        VoteChoice choice,
        uint256 weight,
        string reason
    );

    event ProposalExecuted(
        uint256 indexed proposalId,
        address indexed executor
    );

    event ProposalCancelled(
        uint256 indexed proposalId,
        address indexed canceller
    );

    event DelegationCreated(
        address indexed delegator,
        address indexed delegate,
        uint256 amount
    );

    event DelegationRevoked(
        address indexed delegator,
        address indexed delegate
    );

    event GovernanceParamsUpdated(
        uint256 votingDelay,
        uint256 votingPeriod,
        uint256 quorumNumerator
    );

    event ComplianceCheckRequired(
        uint256 indexed proposalId,
        address indexed checker
    );

    // State variables
    IERC20 public governanceToken;
    Counters.Counter private _proposalIds;

    mapping(uint256 => Proposal) public proposals;
    mapping(address => mapping(address => Delegation)) public delegations;
    // Voting power RECEIVED through delegation.
    mapping(address => uint256) public votingPower;
    // Voting power the delegator has DELEGATED OUT (so it is not double
    // counted as both their own balance and the delegate's received power).
    mapping(address => uint256) public delegatedOut;
    // The single active delegate per delegator (replaces the broken
    // address(0)..address(9) scan in revokeDelegation).
    mapping(address => address) public activeDelegate;
    mapping(address => bool) public authorizedProposers;
    mapping(ProposalType => GovernanceParams) public typeParams;

    GovernanceParams public defaultParams;
    address public treasury;
    address public complianceOracle;
    uint256 public constant MAX_VOTING_PERIOD = 30 days;
    uint256 public constant MIN_VOTING_PERIOD = 1 hours;

    // Modifiers
    modifier onlyAuthorizedProposer() {
        require(
            hasRole(PROPOSER_ROLE, msg.sender) ||
                authorizedProposers[msg.sender],
            "Not authorized to propose"
        );
        _;
    }

    modifier validProposal(uint256 proposalId) {
        require(
            proposalId > 0 && proposalId <= _proposalIds.current(),
            "Invalid proposal ID"
        );
        _;
    }

    modifier onlyActiveProposal(uint256 proposalId) {
        Proposal storage p = proposals[proposalId];
        require(block.timestamp >= p.startTime, "Voting not started");
        require(block.timestamp <= p.endTime, "Voting ended");
        // Transition Pending -> Active on first interaction inside the
        // voting window. Previously no code ever set Active, so voting was
        // permanently impossible.
        if (p.status == ProposalStatus.Pending) {
            p.status = ProposalStatus.Active;
        }
        require(p.status == ProposalStatus.Active, "Proposal not active");
        _;
    }

    /**
     * @dev Constructor
     * @param _governanceToken Governance token address
     * @param _treasury Treasury address
     * @param _admin Admin address
     */
    constructor(address _governanceToken, address _treasury, address _admin) {
        require(_governanceToken != address(0), "Invalid governance token");
        require(_treasury != address(0), "Invalid treasury");
        require(_admin != address(0), "Invalid admin");

        governanceToken = IERC20(_governanceToken);
        treasury = _treasury;

        _grantRole(DEFAULT_ADMIN_ROLE, _admin);
        _grantRole(ADMIN_ROLE, _admin);
        _grantRole(PROPOSER_ROLE, _admin);
        _grantRole(EXECUTOR_ROLE, _admin);
        _grantRole(GUARDIAN_ROLE, _admin);
        _grantRole(COMPLIANCE_ROLE, _admin);

        // Set default governance parameters
        defaultParams = GovernanceParams({
            votingDelay: 1 days,
            votingPeriod: 7 days,
            executionDelay: 2 days,
            proposalThreshold: 100000 * 10 ** 18, // 100K tokens
            quorumNumerator: 4, // 4%
            quorumDenominator: 100,
            approvalThreshold: 51, // 51%
            maxProposalActions: 10
        });
    }

    /**
     * @dev Create a new proposal
     * @param proposalType Type of proposal
     * @param votingMechanism Voting mechanism to use
     * @param title Proposal title
     * @param description Proposal description
     * @param targets Target contract addresses
     * @param values ETH values for each call
     * @param calldatas Encoded function calls
     * @param requiresCompliance Whether compliance check is required
     */
    function propose(
        ProposalType proposalType,
        VotingMechanism votingMechanism,
        string memory title,
        string memory description,
        address[] memory targets,
        uint256[] memory values,
        bytes[] memory calldatas,
        bool requiresCompliance
    ) external onlyAuthorizedProposer whenNotPaused returns (uint256) {
        require(bytes(title).length > 0, "Title cannot be empty");
        require(
            targets.length == values.length &&
                targets.length == calldatas.length,
            "Actions length mismatch"
        );
        require(
            targets.length <= defaultParams.maxProposalActions,
            "Too many actions"
        );
        require(
            _getVotingPower(msg.sender) >= defaultParams.proposalThreshold,
            "Insufficient voting power"
        );

        _proposalIds.increment();
        uint256 proposalId = _proposalIds.current();

        GovernanceParams memory params =
            typeParams[proposalType].votingPeriod > 0
                ? typeParams[proposalType]
                : defaultParams;

        uint256 startTime = block.timestamp.add(params.votingDelay);
        uint256 endTime = startTime.add(params.votingPeriod);

        // A struct containing mappings cannot be assigned via a struct
        // literal; populate it field-by-field through a storage reference.
        Proposal storage proposal = proposals[proposalId];
        proposal.id = proposalId;
        proposal.proposer = msg.sender;
        proposal.proposalType = proposalType;
        proposal.votingMechanism = votingMechanism;
        proposal.title = title;
        proposal.description = description;
        proposal.descriptionHash = keccak256(abi.encodePacked(description));
        proposal.targets = targets;
        proposal.values = values;
        proposal.calldatas = calldatas;
        proposal.startTime = startTime;
        proposal.endTime = endTime;
        proposal.executionTime = 0;
        proposal.forVotes = 0;
        proposal.againstVotes = 0;
        proposal.abstainVotes = 0;
        proposal.totalVotingPower = _getGovernanceTokenTotalSupply();
        proposal.quorumRequired = _calculateQuorum(params);
        proposal.approvalThreshold = params.approvalThreshold;
        proposal.status = ProposalStatus.Pending;
        proposal.requiresCompliance = requiresCompliance;

        emit ProposalCreated(
            proposalId,
            msg.sender,
            proposalType,
            title,
            startTime,
            endTime
        );

        return proposalId;
    }

    /**
     * @dev Cast a vote on a proposal
     * @param proposalId Proposal ID
     * @param choice Vote choice
     * @param reason Reason for voting
     */
    function castVote(
        uint256 proposalId,
        VoteChoice choice,
        string memory reason
    ) external nonReentrant onlyActiveProposal(proposalId) {
        Proposal storage proposal = proposals[proposalId];
        require(!proposal.votes[msg.sender].hasVoted, "Already voted");

        uint256 weight = _getVotingWeight(
            proposalId,
            msg.sender,
            proposal.votingMechanism
        );
        require(weight > 0, "No voting power");

        proposal.votes[msg.sender] = Vote({
            hasVoted: true,
            choice: choice,
            weight: weight,
            timestamp: block.timestamp,
            reason: reason
        });

        if (choice == VoteChoice.For) {
            proposal.forVotes = proposal.forVotes.add(weight);
        } else if (choice == VoteChoice.Against) {
            proposal.againstVotes = proposal.againstVotes.add(weight);
        } else if (choice == VoteChoice.Abstain) {
            proposal.abstainVotes = proposal.abstainVotes.add(weight);
        }

        _checkProposalStatus(proposalId);

        emit VoteCast(msg.sender, proposalId, choice, weight, reason);
    }

    /**
     * @dev Delegate voting power to another address
     * @param delegateAddress Delegate address
     */
    function delegate(address delegateAddress) external nonReentrant {
        require(delegateAddress != address(0), "Invalid delegate address");
        require(delegateAddress != msg.sender, "Cannot delegate to self");

        uint256 balance = governanceToken.balanceOf(msg.sender);

        // A delegator may only have one active delegate at a time; revoke
        // the previous one FIRST so its share of the balance is freed up
        // again before we check how much is available to re-delegate.
        // Checking availability before this revocation would make it
        // impossible to switch delegates in one call once the caller's
        // entire balance was already delegated out.
        address previous = activeDelegate[msg.sender];
        if (
            previous != address(0) && delegations[msg.sender][previous].isActive
        ) {
            uint256 prevAmount = delegations[msg.sender][previous].amount;
            _revokeDelegation(msg.sender, previous);
            votingPower[previous] = votingPower[previous].sub(prevAmount);
            delegatedOut[msg.sender] = delegatedOut[msg.sender].sub(prevAmount);
        }

        // Only the caller's own (now non-delegated) balance can be delegated.
        uint256 available = balance.sub(delegatedOut[msg.sender]);
        require(available > 0, "No voting power to delegate");

        uint256 amount = available;

        delegations[msg.sender][delegateAddress] = Delegation({
            delegate: delegateAddress,
            amount: amount,
            timestamp: block.timestamp,
            isActive: true
        });
        activeDelegate[msg.sender] = delegateAddress;

        // Credit the delegate's RECEIVED power and record the delegator's
        // delegated-out amount (no underflow: delegatedOut starts at 0).
        votingPower[delegateAddress] = votingPower[delegateAddress].add(amount);
        delegatedOut[msg.sender] = delegatedOut[msg.sender].add(amount);

        emit DelegationCreated(msg.sender, delegateAddress, amount);
    }

    /**
     * @dev Revoke delegation
     */
    function revokeDelegation() external nonReentrant {
        address currentDelegate = activeDelegate[msg.sender];
        require(
            currentDelegate != address(0),
            "No active delegation to revoke"
        );
        require(
            delegations[msg.sender][currentDelegate].isActive,
            "No active delegation to revoke"
        );

        uint256 amount = delegations[msg.sender][currentDelegate].amount;

        _revokeDelegation(msg.sender, currentDelegate);
        activeDelegate[msg.sender] = address(0);

        // Return the delegated power: reduce the delegate's received power
        // and clear the delegator's delegated-out balance.
        votingPower[currentDelegate] = votingPower[currentDelegate].sub(amount);
        delegatedOut[msg.sender] = delegatedOut[msg.sender].sub(amount);

        emit DelegationRevoked(msg.sender, currentDelegate);
    }

    /**
     * @dev Internal function to revoke delegation
     */
    function _revokeDelegation(
        address delegator,
        address delegateAddress
    ) internal {
        delegations[delegator][delegateAddress].isActive = false;
        delegations[delegator][delegateAddress].amount = 0;
        delegations[delegator][delegateAddress].delegate = address(0);
    }

    /**
     * @dev Execute a successful proposal
     * @param proposalId Proposal ID
     */
    function execute(
        uint256 proposalId
    ) external payable nonReentrant validProposal(proposalId) {
        Proposal storage proposal = proposals[proposalId];
        require(
            proposal.status == ProposalStatus.Queued,
            "Proposal not queued"
        );
        require(
            block.timestamp >= proposal.executionTime,
            "Execution time not reached"
        );

        proposal.status = ProposalStatus.Executed;

        for (uint256 i = 0; i < proposal.targets.length; i++) {
            address target = proposal.targets[i];
            uint256 value = proposal.values[i];
            bytes memory calldata_ = proposal.calldatas[i];

            (bool success, ) = target.call{value: value}(calldata_);
            require(success, "Execution failed");
        }

        emit ProposalExecuted(proposalId, msg.sender);
    }

    /**
     * @dev Cancel a proposal
     * @param proposalId Proposal ID
     */
    function cancel(
        uint256 proposalId
    ) external nonReentrant validProposal(proposalId) {
        Proposal storage proposal = proposals[proposalId];
        require(
            proposal.status != ProposalStatus.Executed,
            "Cannot cancel executed proposal"
        );
        require(
            proposal.status != ProposalStatus.Cancelled,
            "Already cancelled"
        );

        // Only proposer or guardian can cancel
        require(
            msg.sender == proposal.proposer ||
                hasRole(GUARDIAN_ROLE, msg.sender),
            "Not authorized to cancel"
        );

        proposal.status = ProposalStatus.Cancelled;

        emit ProposalCancelled(proposalId, msg.sender);
    }

    /**
     * @dev Finalize a proposal once its voting period has ended. Callable by
     *      anyone; without this a proposal that received its last vote before
     *      endTime could remain stuck in Active forever.
     */
    function finalizeProposal(
        uint256 proposalId
    ) external validProposal(proposalId) {
        Proposal storage proposal = proposals[proposalId];
        // Lazily activate so a proposal that never received a vote can still
        // be resolved (to Defeated) after its window closes.
        if (
            proposal.status == ProposalStatus.Pending &&
            block.timestamp >= proposal.startTime
        ) {
            proposal.status = ProposalStatus.Active;
        }
        require(proposal.status == ProposalStatus.Active, "Not active");
        require(block.timestamp > proposal.endTime, "Voting not ended");
        _checkProposalStatus(proposalId);
    }

    /**
     * @dev Internal function to check and update proposal status
     */
    function _checkProposalStatus(uint256 proposalId) internal {
        Proposal storage proposal = proposals[proposalId];
        if (proposal.status != ProposalStatus.Active) return;

        uint256 totalVotes = proposal.forVotes.add(proposal.againstVotes).add(
            proposal.abstainVotes
        );

        if (block.timestamp > proposal.endTime) {
            uint256 decisiveVotes = proposal.forVotes.add(
                proposal.againstVotes
            );
            if (totalVotes >= proposal.quorumRequired && decisiveVotes > 0) {
                uint256 approvalPercentage = proposal.forVotes.mul(100).div(
                    decisiveVotes
                );
                if (approvalPercentage >= proposal.approvalThreshold) {
                    proposal.status = ProposalStatus.Succeeded;
                    if (proposal.requiresCompliance) {
                        emit ComplianceCheckRequired(
                            proposalId,
                            complianceOracle
                        );
                    } else {
                        proposal.executionTime = block.timestamp.add(
                            defaultParams.executionDelay
                        );
                        proposal.status = ProposalStatus.Queued;
                    }
                } else {
                    proposal.status = ProposalStatus.Defeated;
                }
            } else {
                proposal.status = ProposalStatus.Defeated;
            }
        }
    }

    /**
     * @dev Internal function to calculate quorum
     */
    function _calculateQuorum(
        GovernanceParams memory params
    ) internal view returns (uint256) {
        return
            _getGovernanceTokenTotalSupply().mul(params.quorumNumerator).div(
                params.quorumDenominator
            );
    }

    /**
     * @dev Internal function to get voting power
     */
    function _getVotingPower(address user) internal view returns (uint256) {
        // Own (non-delegated-out) balance plus power received via delegation.
        uint256 own = governanceToken.balanceOf(user).sub(delegatedOut[user]);
        return own.add(votingPower[user]);
    }

    /**
     * @dev Internal function to get voting weight based on mechanism
     */
    function _getVotingWeight(
        uint256 /* proposalId */,
        address user,
        VotingMechanism mechanism
    ) internal view returns (uint256) {
        uint256 power = _getVotingPower(user);

        if (mechanism == VotingMechanism.SimpleVoting) {
            return power;
        } else if (mechanism == VotingMechanism.QuadraticVoting) {
            // Simplified quadratic voting: square root of power
            return Math.sqrt(power);
        } else if (mechanism == VotingMechanism.DelegatedVoting) {
            // Delegated voting is handled by _getVotingPower
            return power;
        } else if (mechanism == VotingMechanism.WeightedVoting) {
            // Placeholder for custom weighted voting logic
            return power;
        } else if (mechanism == VotingMechanism.MultiSigVoting) {
            // Placeholder for multi-sig logic (e.g., check if user is a required signer)
            return power > 0 ? 1 : 0;
        }

        return 0;
    }

    /**
     * @dev Internal function to get governance token total supply
     */
    function _getGovernanceTokenTotalSupply() internal view returns (uint256) {
        return governanceToken.totalSupply();
    }

    // --- Admin Functions ---

    /**
     * @dev Update governance parameters for a specific proposal type
     */
    function updateTypeParams(
        ProposalType proposalType,
        uint256 votingDelay,
        uint256 votingPeriod,
        uint256 executionDelay,
        uint256 proposalThreshold,
        uint256 quorumNumerator,
        uint256 quorumDenominator,
        uint256 approvalThreshold,
        uint256 maxProposalActions
    ) external onlyRole(ADMIN_ROLE) {
        require(
            votingPeriod >= MIN_VOTING_PERIOD &&
                votingPeriod <= MAX_VOTING_PERIOD,
            "Invalid voting period"
        );
        require(quorumDenominator > 0, "Invalid quorum denominator");

        typeParams[proposalType] = GovernanceParams({
            votingDelay: votingDelay,
            votingPeriod: votingPeriod,
            executionDelay: executionDelay,
            proposalThreshold: proposalThreshold,
            quorumNumerator: quorumNumerator,
            quorumDenominator: quorumDenominator,
            approvalThreshold: approvalThreshold,
            maxProposalActions: maxProposalActions
        });

        emit GovernanceParamsUpdated(
            votingDelay,
            votingPeriod,
            quorumNumerator
        );
    }

    /**
     * @dev Set compliance check status for a proposal
     */
    function setComplianceStatus(
        uint256 proposalId,
        bool passed
    ) external onlyRole(COMPLIANCE_ROLE) validProposal(proposalId) {
        Proposal storage proposal = proposals[proposalId];
        require(proposal.requiresCompliance, "Compliance check not required");
        require(
            proposal.status == ProposalStatus.Succeeded,
            "Proposal not succeeded"
        );

        if (passed) {
            proposal.executionTime = block.timestamp.add(
                defaultParams.executionDelay
            );
            proposal.status = ProposalStatus.Queued;
        } else {
            proposal.status = ProposalStatus.Defeated;
        }
    }

    /**
     * @dev Pause the contract
     */
    function pause() external onlyRole(GUARDIAN_ROLE) {
        _pause();
    }

    /**
     * @dev Unpause the contract
     */
    function unpause() external onlyRole(ADMIN_ROLE) {
        _unpause();
    }
}
