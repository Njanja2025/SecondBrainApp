// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/security/Pausable.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";

/**
 * @title NjanjaCoin
 * @dev Enhanced ERC20 token with security features and governance capabilities
 */
contract NjanjaCoin is ERC20, Pausable, Ownable, ReentrancyGuard {
    // Token parameters
    uint8 private constant _decimals = 18;
    uint256 private constant _maxSupply = 1000000000 * 10**18; // 1 billion tokens
    
    // Governance parameters
    uint256 public constant MIN_PROPOSAL_THRESHOLD = 100000 * 10**18; // 100,000 tokens
    uint256 public constant VOTING_PERIOD = 3 days;
    
    // Anti-whale parameters
    uint256 public maxTransferAmount;
    mapping(address => bool) public isExemptFromLimit;
    
    // Staking parameters
    mapping(address => uint256) public stakedBalance;
    mapping(address => uint256) public stakingTimestamp;
    uint256 public constant STAKING_PERIOD = 30 days;
    uint256 public constant STAKING_APY = 12; // 12% APY
    
    // Events
    event Staked(address indexed user, uint256 amount);
    event Unstaked(address indexed user, uint256 amount, uint256 reward);
    event MaxTransferAmountUpdated(uint256 newAmount);
    event ExemptionStatusUpdated(address indexed account, bool status);
    
    /**
     * @dev Constructor
     * @param initialSupply Initial token supply
     */
    constructor(uint256 initialSupply) ERC20("NjanjaCoin", "NJNC") {
        require(initialSupply <= _maxSupply, "Initial supply exceeds maximum");
        _mint(msg.sender, initialSupply);
        maxTransferAmount = initialSupply / 100; // 1% of initial supply
        isExemptFromLimit[msg.sender] = true;
    }
    
    /**
     * @dev Pause token transfers
     */
    function pause() public onlyOwner {
        _pause();
    }
    
    /**
     * @dev Unpause token transfers
     */
    function unpause() public onlyOwner {
        _unpause();
    }
    
    /**
     * @dev Update max transfer amount
     * @param newAmount New maximum transfer amount
     */
    function updateMaxTransferAmount(uint256 newAmount) public onlyOwner {
        require(newAmount > 0, "Invalid amount");
        maxTransferAmount = newAmount;
        emit MaxTransferAmountUpdated(newAmount);
    }
    
    /**
     * @dev Update exemption status for an account
     * @param account Address to update
     * @param status New exemption status
     */
    function updateExemptionStatus(address account, bool status) public onlyOwner {
        isExemptFromLimit[account] = status;
        emit ExemptionStatusUpdated(account, status);
    }
    
    /**
     * @dev Stake tokens
     * @param amount Amount to stake
     */
    function stake(uint256 amount) public nonReentrant whenNotPaused {
        require(amount > 0, "Cannot stake 0");
        require(balanceOf(msg.sender) >= amount, "Insufficient balance");
        
        // Transfer tokens to contract
        _transfer(msg.sender, address(this), amount);
        
        // Update staking info
        stakedBalance[msg.sender] += amount;
        stakingTimestamp[msg.sender] = block.timestamp;
        
        emit Staked(msg.sender, amount);
    }
    
    /**
     * @dev Unstake tokens and claim rewards
     */
    function unstake() public nonReentrant {
        uint256 stakedAmount = stakedBalance[msg.sender];
        require(stakedAmount > 0, "No tokens staked");
        
        uint256 stakingDuration = block.timestamp - stakingTimestamp[msg.sender];
        require(stakingDuration >= STAKING_PERIOD, "Staking period not completed");
        
        // Calculate reward
        uint256 reward = (stakedAmount * STAKING_APY * stakingDuration) / (365 days * 100);
        
        // Reset staking info
        stakedBalance[msg.sender] = 0;
        stakingTimestamp[msg.sender] = 0;
        
        // Transfer tokens and reward
        _transfer(address(this), msg.sender, stakedAmount + reward);
        
        emit Unstaked(msg.sender, stakedAmount, reward);
    }
    
    /**
     * @dev Get staking info for an account
     * @param account Address to check
     * @return Staked amount and time remaining
     */
    function getStakingInfo(address account) public view returns (uint256, uint256) {
        uint256 timeStaked = block.timestamp - stakingTimestamp[account];
        uint256 timeRemaining = timeStaked >= STAKING_PERIOD ? 0 : STAKING_PERIOD - timeStaked;
        return (stakedBalance[account], timeRemaining);
    }
    
    /**
     * @dev Override transfer function to implement limits
     */
    function _transfer(
        address sender,
        address recipient,
        uint256 amount
    ) internal virtual override whenNotPaused {
        require(sender != address(0), "Transfer from zero address");
        require(recipient != address(0), "Transfer to zero address");
        
        // Check transfer limits unless exempt
        if (!isExemptFromLimit[sender] && !isExemptFromLimit[recipient]) {
            require(amount <= maxTransferAmount, "Transfer amount exceeds limit");
        }
        
        super._transfer(sender, recipient, amount);
    }
    
    /**
     * @dev Burn tokens
     * @param amount Amount to burn
     */
    function burn(uint256 amount) public {
        _burn(msg.sender, amount);
    }
    
    /**
     * @dev Get current APY for staking
     */
    function getStakingAPY() public pure returns (uint256) {
        return STAKING_APY;
    }
    
    /**
     * @dev Get token decimals
     */
    function decimals() public pure override returns (uint8) {
        return _decimals;
    }
} 