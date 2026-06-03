// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract ColdChainEscrow {
    address public buyer;
    address public seller;
    address public oracle;

    enum TripState { NotStarted, InProgress, Completed }
    TripState public state;

    uint256 public constant MIN_TEMP = 2;
    uint256 public constant MAX_TEMP = 8;

    bool public tempBreached;
    uint256 public lastTemperature;

    event TemperatureRecorded(uint256 temp, bool safe);
    event TripStarted();
    event PaymentReleased(address seller);
    event PaymentRefunded(address buyer);

    modifier onlyOracle() {
        require(msg.sender == oracle, "Only oracle");
        _;
    }

    modifier inState(TripState _state) {
        require(state == _state, "Invalid state");
        _;
    }

    constructor(address _seller, address _oracle) {
        buyer = msg.sender;
        seller = _seller;
        oracle = _oracle;
    }

    function startTrip() external payable inState(TripState.NotStarted) {
        require(msg.sender == buyer, "Only buyer");
        require(msg.value > 0, "Must send ETH");
        state = TripState.InProgress;
        emit TripStarted();
    }

    function recordTemperature(uint256 _temp) external onlyOracle inState(TripState.InProgress) {
        lastTemperature = _temp;
        bool safe = (_temp >= MIN_TEMP && _temp <= MAX_TEMP);
        if (!safe) {
            tempBreached = true;
        }
        emit TemperatureRecorded(_temp, safe);
    }

    function endTrip() external onlyOracle inState(TripState.InProgress) {
        state = TripState.Completed;
        if (tempBreached) {
            (bool refundOk, ) = buyer.call{value: address(this).balance}("");
            require(refundOk, "Refund failed");
            emit PaymentRefunded(buyer);
        } else {
            (bool payOk, ) = seller.call{value: address(this).balance}("");
            require(payOk, "Payment failed");
            emit PaymentReleased(seller);
        }
    }

    function getBalance() external view returns (uint256) {
        return address(this).balance;
    }
}