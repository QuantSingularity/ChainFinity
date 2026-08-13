// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/access/AccessControlEnumerable.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "@openzeppelin/contracts/security/Pausable.sol";
import {IRouterClient} from "@chainlink/contracts-ccip/contracts/interfaces/IRouterClient.sol";
import {IAny2EVMMessageReceiver} from "@chainlink/contracts-ccip/contracts/interfaces/IAny2EVMMessageReceiver.sol";
import {Client} from "@chainlink/contracts-ccip/contracts/libraries/Client.sol";

/**
 * @title CrossChainManager
 * @dev Manages cross-chain transfers with Chainlink CCIP integration, rate
 *      limiting, and circuit breakers.
 *
 * Security model (fixes applied during review):
 *  - ccipReceive validates BOTH the source chain selector and that the
 *    message sender is the registered trusted CrossChainManager on that
 *    chain. The previous implementation accepted any CCIP message and paid
 *    out arbitrary tokens to an attacker-chosen receiver.
 *  - The receiver address travels inside the message data (the
 *    Client.Any2EVMMessage struct has no `receiver` field; the old code
 *    referenced one and could not compile).
 *  - LP fees are tracked per-token in `collectedFees` and only that amount
 *    is ever distributed. The old distributeFees paid out the contract's
 *    ENTIRE balance - including users' in-flight bridge principal - and
 *    iterated OPERATOR_ROLE members instead of liquidity providers.
 *  - initiateTransfer is payable: the caller funds the CCIP fee, with any
 *    excess refunded, instead of silently draining contract ETH.
 */
contract CrossChainManager is
    ReentrancyGuard,
    AccessControlEnumerable,
    Pausable,
    IAny2EVMMessageReceiver
{
    using SafeERC20 for IERC20;

    // Role definitions
    bytes32 public constant ADMIN_ROLE = keccak256("ADMIN_ROLE");
    bytes32 public constant OPERATOR_ROLE = keccak256("OPERATOR_ROLE");
    bytes32 public constant EMERGENCY_ROLE = keccak256("EMERGENCY_ROLE");

    // Chainlink CCIP Router
    IRouterClient public router;

    // Rate limiting
    uint256 public transferLimit;
    uint256 public transferCooldown;
    mapping(address => uint256) public lastTransferTime;

    // Circuit breaker
    uint256 public dailyTransferLimit;
    uint256 public dailyTransferTotal;
    uint256 public dailyResetTimestamp;

    // Fee sharing
    uint256 public liquidityProviderFee; // in basis points (1/100 of a percent)
    uint256 public constant MAX_LP_FEE = 500; // 5% cap
    mapping(address => uint256) public liquidityProviderShares;
    address[] public liquidityProviders;
    mapping(address => uint256) private _providerIndex; // index + 1; 0 = absent
    uint256 public totalLiquidityShares;

    // Fees collected per token, the ONLY funds distributeFees may pay out.
    mapping(address => uint256) public collectedFees;

    struct CrossChainTransfer {
        address sender;
        address token;
        uint256 amount;
        uint64 targetChainSelector;
        address targetAddress;
        uint256 timestamp;
        bool completed;
        bytes32 ccipMessageId;
    }

    mapping(bytes32 => CrossChainTransfer) public transfers;
    mapping(uint64 => bool) public supportedChains; // Chainlink CCIP chain selectors
    // Trusted CrossChainManager deployment per source chain selector.
    mapping(uint64 => address) public trustedRemotes;
    uint256 public transferCount;

    // Events
    event TransferInitiated(
        bytes32 indexed transferId,
        address indexed sender,
        address indexed token,
        uint256 amount,
        uint64 targetChainSelector,
        address targetAddress,
        bytes32 ccipMessageId
    );
    event TransferCompleted(bytes32 indexed messageId);
    event ChainSupported(uint64 chainSelector, bool supported);
    event TrustedRemoteSet(uint64 chainSelector, address remote);
    event RateLimitUpdated(uint256 transferLimit, uint256 transferCooldown);
    event CircuitBreakerUpdated(uint256 dailyTransferLimit);
    event LiquidityProviderAdded(address indexed provider, uint256 shares);
    event LiquidityProviderRemoved(address indexed provider);
    event FeesDistributed(address indexed token, uint256 totalFees);
    event MessageReceived(
        bytes32 indexed messageId,
        uint64 sourceChainSelector
    );

    /**
     * @dev Constructor.
     *
     * As with AssetVault, this contract is deployed directly (not behind a
     * proxy) everywhere in this repo. State that used to live in a separate
     * `initialize(...)` call - gated by OpenZeppelin's `Initializable` -
     * moved into the constructor so role assignment happens atomically with
     * deployment instead of leaving a front-runnable window where the
     * freshly deployed contract sits uninitialized on-chain.
     */
    constructor(
        address admin,
        address operator,
        address emergency,
        address routerAddress
    ) {
        require(admin != address(0), "Invalid admin");
        require(routerAddress != address(0), "Invalid router");

        _grantRole(DEFAULT_ADMIN_ROLE, admin);
        _grantRole(ADMIN_ROLE, admin);
        _grantRole(OPERATOR_ROLE, operator);
        _grantRole(EMERGENCY_ROLE, emergency);

        router = IRouterClient(routerAddress);

        // Initialize supported chains (Chainlink CCIP chain selectors)
        supportedChains[5009297550715157269] = true; // Ethereum Mainnet
        supportedChains[4949039107694359620] = true; // Arbitrum
        supportedChains[4051577828743386545] = true; // Polygon

        // Set default rate limits
        transferLimit = 100000 * 10 ** 18; // 100,000 tokens
        transferCooldown = 1 hours; // 1 hour cooldown
        dailyTransferLimit = 1000000 * 10 ** 18; // 1,000,000 tokens daily limit
        dailyResetTimestamp = block.timestamp + 1 days;

        // Set default fee sharing
        liquidityProviderFee = 20; // 0.2%
    }

    /**
     * @dev Initiate a cross-chain transfer using Chainlink CCIP.
     *      The caller must send enough native token to cover the CCIP fee;
     *      any excess is refunded.
     * @param token Token address
     * @param amount Amount to transfer
     * @param targetChainSelector Target chain (Chainlink selector)
     * @param targetAddress Receiver address on the destination chain
     */
    function initiateTransfer(
        address token,
        uint256 amount,
        uint64 targetChainSelector,
        address targetAddress
    ) external payable nonReentrant whenNotPaused returns (bytes32 transferId) {
        require(
            supportedChains[targetChainSelector],
            "Unsupported target chain"
        );
        require(
            trustedRemotes[targetChainSelector] != address(0),
            "No trusted remote for chain"
        );
        require(targetAddress != address(0), "Invalid target address");
        require(amount > 0, "Amount must be greater than 0");
        require(amount <= transferLimit, "Amount exceeds transfer limit");
        require(
            block.timestamp >= lastTransferTime[msg.sender] + transferCooldown,
            "Transfer cooldown active"
        );

        // Circuit breaker with daily window reset
        if (block.timestamp > dailyResetTimestamp) {
            dailyTransferTotal = 0;
            dailyResetTimestamp = block.timestamp + 1 days;
        }
        require(
            dailyTransferTotal + amount <= dailyTransferLimit,
            "Daily transfer limit reached"
        );

        // Update rate limiting state (effects before interactions)
        lastTransferTime[msg.sender] = block.timestamp;
        dailyTransferTotal += amount;

        // Calculate fees
        uint256 lpFee = (amount * liquidityProviderFee) / 10000;
        uint256 netAmount = amount - lpFee;
        collectedFees[token] += lpFee;

        // Pull tokens into this contract (escrowed as bridge liquidity)
        IERC20(token).safeTransferFrom(msg.sender, address(this), amount);

        // Prepare CCIP message. The receiver contract on the destination
        // chain is the trusted remote CrossChainManager; the end-user
        // receiver address travels inside `data`.
        Client.EVM2AnyMessage memory message = Client.EVM2AnyMessage({
            receiver: abi.encode(trustedRemotes[targetChainSelector]),
            data: abi.encode(msg.sender, targetAddress, token, netAmount),
            tokenAmounts: new Client.EVMTokenAmount[](0),
            extraArgs: "",
            feeToken: address(0) // pay CCIP fee in native token
        });

        uint256 ccipFee = router.getFee(targetChainSelector, message);
        require(msg.value >= ccipFee, "Insufficient CCIP fee");

        bytes32 messageId = router.ccipSend{value: ccipFee}(
            targetChainSelector,
            message
        );

        // Refund excess native token
        if (msg.value > ccipFee) {
            (bool refunded, ) = msg.sender.call{value: msg.value - ccipFee}("");
            require(refunded, "Fee refund failed");
        }

        transferId = keccak256(
            abi.encodePacked(
                msg.sender,
                token,
                amount,
                targetChainSelector,
                targetAddress,
                block.timestamp,
                transferCount
            )
        );

        transfers[transferId] = CrossChainTransfer({
            sender: msg.sender,
            token: token,
            amount: netAmount,
            targetChainSelector: targetChainSelector,
            targetAddress: targetAddress,
            timestamp: block.timestamp,
            completed: false,
            ccipMessageId: messageId
        });

        transferCount++;

        emit TransferInitiated(
            transferId,
            msg.sender,
            token,
            netAmount,
            targetChainSelector,
            targetAddress,
            messageId
        );
    }

    /**
     * @dev Receive and process messages from Chainlink CCIP.
     *
     * Hardened against the original fund-drain vector: only messages
     * relayed by the router, originating from a supported chain, AND sent
     * by that chain's registered trusted remote are processed.
     */
    function ccipReceive(
        Client.Any2EVMMessage calldata message
    ) external override nonReentrant whenNotPaused {
        require(msg.sender == address(router), "Sender not router");
        require(
            supportedChains[message.sourceChainSelector],
            "Unsupported source chain"
        );
        address remoteSender = abi.decode(message.sender, (address));
        require(
            remoteSender != address(0) &&
                remoteSender == trustedRemotes[message.sourceChainSelector],
            "Untrusted remote sender"
        );

        (
            ,
            /* address originalSender */ address receiver,
            address token,
            uint256 amount
        ) = abi.decode(message.data, (address, address, address, uint256));
        require(receiver != address(0), "Invalid receiver");

        IERC20(token).safeTransfer(receiver, amount);

        emit MessageReceived(message.messageId, message.sourceChainSelector);
        emit TransferCompleted(message.messageId);
    }

    /**
     * @dev Add or update a supported chain
     */
    function setSupportedChain(
        uint64 chainSelector,
        bool supported
    ) external onlyRole(ADMIN_ROLE) {
        supportedChains[chainSelector] = supported;
        emit ChainSupported(chainSelector, supported);
    }

    /**
     * @dev Register the trusted CrossChainManager deployment for a chain.
     */
    function setTrustedRemote(
        uint64 chainSelector,
        address remote
    ) external onlyRole(ADMIN_ROLE) {
        trustedRemotes[chainSelector] = remote;
        emit TrustedRemoteSet(chainSelector, remote);
    }

    /**
     * @dev Update rate limits
     */
    function updateRateLimit(
        uint256 newTransferLimit,
        uint256 newTransferCooldown
    ) external onlyRole(ADMIN_ROLE) {
        transferLimit = newTransferLimit;
        transferCooldown = newTransferCooldown;
        emit RateLimitUpdated(newTransferLimit, newTransferCooldown);
    }

    /**
     * @dev Update circuit breaker
     */
    function updateCircuitBreaker(
        uint256 newDailyTransferLimit
    ) external onlyRole(ADMIN_ROLE) {
        dailyTransferLimit = newDailyTransferLimit;
        emit CircuitBreakerUpdated(newDailyTransferLimit);
    }

    /**
     * @dev Update the LP fee (capped to prevent admin fee abuse).
     */
    function updateLiquidityProviderFee(
        uint256 newFeeBps
    ) external onlyRole(ADMIN_ROLE) {
        require(newFeeBps <= MAX_LP_FEE, "Fee too high");
        liquidityProviderFee = newFeeBps;
    }

    /**
     * @dev Add (or top up) a liquidity provider.
     */
    function addLiquidityProvider(
        address provider,
        uint256 shares
    ) external onlyRole(ADMIN_ROLE) {
        require(provider != address(0), "Invalid provider address");
        require(shares > 0, "Shares must be greater than 0");

        if (_providerIndex[provider] == 0) {
            liquidityProviders.push(provider);
            _providerIndex[provider] = liquidityProviders.length;
        }
        liquidityProviderShares[provider] += shares;
        totalLiquidityShares += shares;

        emit LiquidityProviderAdded(provider, shares);
    }

    /**
     * @dev Remove a liquidity provider entirely.
     */
    function removeLiquidityProvider(
        address provider
    ) external onlyRole(ADMIN_ROLE) {
        require(
            liquidityProviderShares[provider] > 0,
            "Provider does not exist"
        );

        totalLiquidityShares -= liquidityProviderShares[provider];
        liquidityProviderShares[provider] = 0;

        // Swap-and-pop from the providers array
        uint256 index = _providerIndex[provider];
        if (index != 0) {
            uint256 lastIndex = liquidityProviders.length;
            if (index != lastIndex) {
                address lastProvider = liquidityProviders[lastIndex - 1];
                liquidityProviders[index - 1] = lastProvider;
                _providerIndex[lastProvider] = index;
            }
            liquidityProviders.pop();
            _providerIndex[provider] = 0;
        }

        emit LiquidityProviderRemoved(provider);
    }

    /**
     * @dev Number of registered liquidity providers.
     */
    function liquidityProviderCount() external view returns (uint256) {
        return liquidityProviders.length;
    }

    /**
     * @dev Distribute collected fees (and ONLY collected fees) for a token
     *      to liquidity providers pro-rata by shares.
     */
    function distributeFees(
        address token
    ) external nonReentrant onlyRole(OPERATOR_ROLE) {
        require(totalLiquidityShares > 0, "No liquidity providers");

        uint256 fees = collectedFees[token];
        require(fees > 0, "No fees to distribute");

        // Effects before interactions: zero the pot first.
        collectedFees[token] = 0;

        uint256 totalDistributed = 0;
        uint256 providerCount = liquidityProviders.length;
        for (uint256 i = 0; i < providerCount; i++) {
            address provider = liquidityProviders[i];
            uint256 shares = liquidityProviderShares[provider];
            if (shares == 0) continue;
            uint256 providerShare = (fees * shares) / totalLiquidityShares;
            if (providerShare > 0) {
                IERC20(token).safeTransfer(provider, providerShare);
                totalDistributed += providerShare;
            }
        }

        // Rounding dust stays earmarked for the next distribution.
        if (fees > totalDistributed) {
            collectedFees[token] = fees - totalDistributed;
        }

        emit FeesDistributed(token, totalDistributed);
    }

    /**
     * @dev Pause the contract
     */
    function pause() external onlyRole(EMERGENCY_ROLE) {
        _pause();
    }

    /**
     * @dev Unpause the contract
     */
    function unpause() external onlyRole(ADMIN_ROLE) {
        _unpause();
    }

    /**
     * @dev Get transfer details
     */
    function getTransfer(
        bytes32 transferId
    ) external view returns (CrossChainTransfer memory) {
        return transfers[transferId];
    }

    /**
     * @dev IERC165 support (AccessControlEnumerable + CCIP receiver).
     */
    function supportsInterface(
        bytes4 interfaceId
    ) public view virtual override(AccessControlEnumerable) returns (bool) {
        return
            interfaceId == type(IAny2EVMMessageReceiver).interfaceId ||
            super.supportsInterface(interfaceId);
    }

    /**
     * @dev Accept ETH refunds (e.g. router overpayment returns).
     */
    receive() external payable {}
}
