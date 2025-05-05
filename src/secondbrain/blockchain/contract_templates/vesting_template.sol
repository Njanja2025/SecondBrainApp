// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

contract {{ContractName}} is Ownable, ReentrancyGuard {
    using SafeERC20 for IERC20;

    struct VestingSchedule {
        bool initialized;
        address beneficiary;
        uint256 cliff;
        uint256 start;
        uint256 duration;
        uint256 slicePeriodSeconds;
        bool revocable;
        uint256 amountTotal;
        uint256 released;
        bool revoked;
    }

    // Token to be vested
    IERC20 private immutable _token;

    // Vesting schedules
    bytes32[] private vestingSchedulesIds;
    mapping(bytes32 => VestingSchedule) private vestingSchedules;
    mapping(address => uint256) private holdersVestingCount;

    // Total amount of vested tokens
    uint256 private vestingSchedulesTotalAmount;

    event VestingScheduleCreated(bytes32 indexed scheduleId, address indexed beneficiary);
    event TokensReleased(bytes32 indexed scheduleId, uint256 amount);
    event VestingScheduleRevoked(bytes32 indexed scheduleId);

    constructor(address token_) Ownable(msg.sender) {
        require(token_ != address(0), "Invalid token address");
        _token = IERC20(token_);
    }

    function createVestingSchedule(
        address beneficiary,
        uint256 start,
        uint256 cliff,
        uint256 duration,
        uint256 slicePeriodSeconds,
        bool revocable,
        uint256 amount
    ) public onlyOwner {
        require(beneficiary != address(0), "Invalid beneficiary");
        require(duration > 0, "Duration must be > 0");
        require(amount > 0, "Amount must be > 0");
        require(slicePeriodSeconds >= 1, "slicePeriodSeconds must be >= 1");
        require(duration >= cliff, "Duration must be >= cliff");
        
        bytes32 scheduleId = computeScheduleId(beneficiary, start, cliff, duration, amount);
        require(!vestingSchedules[scheduleId].initialized, "Schedule already exists");

        uint256 balance = _token.balanceOf(address(this));
        require(balance >= vestingSchedulesTotalAmount + amount, "Insufficient token balance");

        vestingSchedules[scheduleId] = VestingSchedule(
            true,
            beneficiary,
            cliff,
            start,
            duration,
            slicePeriodSeconds,
            revocable,
            amount,
            0,
            false
        );
        vestingSchedulesTotalAmount += amount;
        vestingSchedulesIds.push(scheduleId);
        holdersVestingCount[beneficiary] += 1;

        emit VestingScheduleCreated(scheduleId, beneficiary);
    }

    function release(bytes32 scheduleId) public nonReentrant {
        VestingSchedule storage schedule = vestingSchedules[scheduleId];
        require(schedule.initialized, "Schedule does not exist");
        require(!schedule.revoked, "Schedule was revoked");

        uint256 vestedAmount = _computeReleasableAmount(schedule);
        require(vestedAmount > 0, "No tokens to release");

        schedule.released += vestedAmount;
        vestingSchedulesTotalAmount -= vestedAmount;
        
        _token.safeTransfer(schedule.beneficiary, vestedAmount);
        emit TokensReleased(scheduleId, vestedAmount);
    }

    function revoke(bytes32 scheduleId) public onlyOwner {
        VestingSchedule storage schedule = vestingSchedules[scheduleId];
        require(schedule.initialized, "Schedule does not exist");
        require(!schedule.revoked, "Schedule already revoked");
        require(schedule.revocable, "Schedule is not revocable");

        uint256 vestedAmount = _computeReleasableAmount(schedule);
        if (vestedAmount > 0) {
            release(scheduleId);
        }

        uint256 unreleased = schedule.amountTotal - schedule.released;
        vestingSchedulesTotalAmount -= unreleased;
        schedule.revoked = true;

        _token.safeTransfer(owner(), unreleased);
        emit VestingScheduleRevoked(scheduleId);
    }

    function computeScheduleId(
        address beneficiary,
        uint256 start,
        uint256 cliff,
        uint256 duration,
        uint256 amount
    ) public pure returns (bytes32) {
        return keccak256(abi.encodePacked(beneficiary, start, cliff, duration, amount));
    }

    function getVestingSchedule(bytes32 scheduleId) public view returns (VestingSchedule memory) {
        return vestingSchedules[scheduleId];
    }

    function getVestingSchedulesCount() public view returns (uint256) {
        return vestingSchedulesIds.length;
    }

    function getToken() public view returns (address) {
        return address(_token);
    }

    function _computeReleasableAmount(VestingSchedule memory schedule) internal view returns (uint256) {
        if (block.timestamp < schedule.start + schedule.cliff) {
            return 0;
        }

        uint256 timeFromStart = block.timestamp - schedule.start;
        uint256 vestedSeconds = timeFromStart > schedule.duration ? schedule.duration : timeFromStart;
        uint256 vestedAmount = (schedule.amountTotal * vestedSeconds) / schedule.duration;
        return vestedAmount - schedule.released;
    }
} 