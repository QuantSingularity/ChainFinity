// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import {IRouterClient} from "@chainlink/contracts-ccip/contracts/interfaces/IRouterClient.sol";
import {IAny2EVMMessageReceiver} from "@chainlink/contracts-ccip/contracts/interfaces/IAny2EVMMessageReceiver.sol";
import {Client} from "@chainlink/contracts-ccip/contracts/libraries/Client.sol";

/**
 * @title MockCCIPRouter
 * @dev Minimal CCIP router stand-in used only for tests. Charges a fixed
 *      fee for `getFee`/`ccipSend`, and exposes `deliver` so a test can play
 *      the role of the off-chain CCIP network relaying a message to a
 *      receiver's `ccipReceive`.
 */
contract MockCCIPRouter is IRouterClient {
    uint256 public fixedFee;
    uint256 public nonce;

    event MessageSent(
        bytes32 indexed messageId,
        uint64 destinationChainSelector
    );

    constructor(uint256 _fixedFee) {
        fixedFee = _fixedFee;
    }

    function setFixedFee(uint256 _fixedFee) external {
        fixedFee = _fixedFee;
    }

    function isChainSupported(uint64) external pure override returns (bool) {
        return true;
    }

    function getFee(
        uint64,
        Client.EVM2AnyMessage memory
    ) external view override returns (uint256) {
        return fixedFee;
    }

    function ccipSend(
        uint64 destinationChainSelector,
        Client.EVM2AnyMessage calldata
    ) external payable override returns (bytes32) {
        require(msg.value >= fixedFee, "Insufficient fee");

        bytes32 messageId = keccak256(
            abi.encodePacked(block.timestamp, msg.sender, nonce++)
        );

        emit MessageSent(messageId, destinationChainSelector);
        return messageId;
    }

    /**
     * @dev Test helper: deliver a message to `receiver` as if this router
     *      had relayed it from `sourceChainSelector`, sent by `sender`.
     */
    function deliver(
        address receiver,
        uint64 sourceChainSelector,
        address sender,
        bytes calldata data
    ) external returns (bytes32 messageId) {
        messageId = keccak256(
            abi.encodePacked(block.timestamp, sender, nonce++)
        );

        Client.Any2EVMMessage memory message = Client.Any2EVMMessage({
            messageId: messageId,
            sourceChainSelector: sourceChainSelector,
            sender: abi.encode(sender),
            data: data,
            destTokenAmounts: new Client.EVMTokenAmount[](0)
        });

        IAny2EVMMessageReceiver(receiver).ccipReceive(message);
    }
}
