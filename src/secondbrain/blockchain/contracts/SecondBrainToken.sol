// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/Pausable.sol";

/**
 * @title SecondBrainToken
 * @dev ERC20 Token for SecondBrain with advanced features
 */
contract SecondBrainToken is ERC20, Ownable, Pausable {
    // Events
    event MinterAdded(address indexed account);
    event MinterRemoved(address indexed account);
    
    // State variables
    mapping(address => bool) public minters;
    uint256 public maxSupply;
    
    /**
     * @dev Constructor
     * @param _name Token name
     * @param _symbol Token symbol
     * @param _maxSupply Maximum token supply
     */
    constructor(
        string memory _name,
        string memory _symbol,
        uint256 _maxSupply
    ) ERC20(_name, _symbol) Ownable(msg.sender) {
        maxSupply = _maxSupply;
        minters[msg.sender] = true;
    }
    
    /**
     * @dev Modifier to check if caller is a minter
     */
    modifier onlyMinter() {
        require(minters[msg.sender], "Caller is not a minter");
        _;
    }
    
    /**
     * @dev Add a new minter
     * @param _minter Address to add as minter
     */
    function addMinter(address _minter) external onlyOwner {
        require(_minter != address(0), "Invalid minter address");
        require(!minters[_minter], "Account is already a minter");
        
        minters[_minter] = true;
        emit MinterAdded(_minter);
    }
    
    /**
     * @dev Remove a minter
     * @param _minter Address to remove from minters
     */
    function removeMinter(address _minter) external onlyOwner {
        require(minters[_minter], "Account is not a minter");
        require(_minter != owner(), "Cannot remove owner as minter");
        
        minters[_minter] = false;
        emit MinterRemoved(_minter);
    }
    
    /**
     * @dev Mint new tokens
     * @param _to Address to mint tokens to
     * @param _amount Amount of tokens to mint
     */
    function mint(address _to, uint256 _amount) external onlyMinter whenNotPaused {
        require(_to != address(0), "Invalid recipient address");
        require(totalSupply() + _amount <= maxSupply, "Would exceed max supply");
        
        _mint(_to, _amount);
    }
    
    /**
     * @dev Burn tokens
     * @param _amount Amount of tokens to burn
     */
    function burn(uint256 _amount) external whenNotPaused {
        _burn(msg.sender, _amount);
    }
    
    /**
     * @dev Pause token transfers
     */
    function pause() external onlyOwner {
        _pause();
    }
    
    /**
     * @dev Unpause token transfers
     */
    function unpause() external onlyOwner {
        _unpause();
    }
    
    /**
     * @dev Override transfer function to add pause check
     */
    function transfer(address to, uint256 amount) public override whenNotPaused returns (bool) {
        return super.transfer(to, amount);
    }
    
    /**
     * @dev Override transferFrom function to add pause check
     */
    function transferFrom(address from, address to, uint256 amount) public override whenNotPaused returns (bool) {
        return super.transferFrom(from, to, amount);
    }
} 