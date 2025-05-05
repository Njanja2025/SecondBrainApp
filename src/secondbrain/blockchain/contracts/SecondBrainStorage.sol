// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/security/Pausable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";

/**
 * @title SecondBrainStorage
 * @dev Secure storage contract for SecondBrain data
 */
contract SecondBrainStorage is AccessControl, Pausable, ReentrancyGuard {
    // Roles
    bytes32 public constant WRITER_ROLE = keccak256("WRITER_ROLE");
    bytes32 public constant READER_ROLE = keccak256("READER_ROLE");
    
    // Events
    event DataStored(bytes32 indexed key, address indexed storer);
    event DataUpdated(bytes32 indexed key, address indexed updater);
    event DataDeleted(bytes32 indexed key, address indexed deleter);
    
    // Structs
    struct DataEntry {
        bytes data;
        uint256 timestamp;
        address storer;
        bool encrypted;
    }
    
    // State variables
    mapping(bytes32 => DataEntry) private dataStore;
    mapping(address => mapping(bytes32 => bool)) private userAccess;
    uint256 public entryCount;
    
    /**
     * @dev Constructor
     */
    constructor() {
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(WRITER_ROLE, msg.sender);
        _grantRole(READER_ROLE, msg.sender);
    }
    
    /**
     * @dev Store new data
     * @param key Hash key for the data
     * @param data Data to store
     * @param encrypted Whether the data is encrypted
     */
    function storeData(
        bytes32 key,
        bytes calldata data,
        bool encrypted
    ) external onlyRole(WRITER_ROLE) whenNotPaused nonReentrant {
        require(data.length > 0, "Empty data not allowed");
        require(dataStore[key].timestamp == 0, "Key already exists");
        
        dataStore[key] = DataEntry({
            data: data,
            timestamp: block.timestamp,
            storer: msg.sender,
            encrypted: encrypted
        });
        
        entryCount++;
        emit DataStored(key, msg.sender);
    }
    
    /**
     * @dev Update existing data
     * @param key Hash key for the data
     * @param data New data
     * @param encrypted Whether the data is encrypted
     */
    function updateData(
        bytes32 key,
        bytes calldata data,
        bool encrypted
    ) external onlyRole(WRITER_ROLE) whenNotPaused nonReentrant {
        require(data.length > 0, "Empty data not allowed");
        require(dataStore[key].timestamp > 0, "Key does not exist");
        
        dataStore[key] = DataEntry({
            data: data,
            timestamp: block.timestamp,
            storer: msg.sender,
            encrypted: encrypted
        });
        
        emit DataUpdated(key, msg.sender);
    }
    
    /**
     * @dev Delete data
     * @param key Hash key for the data
     */
    function deleteData(bytes32 key) external onlyRole(WRITER_ROLE) whenNotPaused nonReentrant {
        require(dataStore[key].timestamp > 0, "Key does not exist");
        
        delete dataStore[key];
        entryCount--;
        
        emit DataDeleted(key, msg.sender);
    }
    
    /**
     * @dev Read data
     * @param key Hash key for the data
     */
    function readData(bytes32 key) external view onlyRole(READER_ROLE) returns (
        bytes memory data,
        uint256 timestamp,
        address storer,
        bool encrypted
    ) {
        DataEntry storage entry = dataStore[key];
        require(entry.timestamp > 0, "Key does not exist");
        
        return (
            entry.data,
            entry.timestamp,
            entry.storer,
            entry.encrypted
        );
    }
    
    /**
     * @dev Grant specific data access to an address
     * @param user Address to grant access to
     * @param key Data key
     */
    function grantDataAccess(address user, bytes32 key) external onlyRole(DEFAULT_ADMIN_ROLE) {
        require(user != address(0), "Invalid user address");
        require(dataStore[key].timestamp > 0, "Key does not exist");
        
        userAccess[user][key] = true;
    }
    
    /**
     * @dev Revoke specific data access from an address
     * @param user Address to revoke access from
     * @param key Data key
     */
    function revokeDataAccess(address user, bytes32 key) external onlyRole(DEFAULT_ADMIN_ROLE) {
        userAccess[user][key] = false;
    }
    
    /**
     * @dev Check if user has access to specific data
     * @param user Address to check
     * @param key Data key
     */
    function hasDataAccess(address user, bytes32 key) external view returns (bool) {
        return userAccess[user][key] || hasRole(READER_ROLE, user);
    }
    
    /**
     * @dev Pause contract
     */
    function pause() external onlyRole(DEFAULT_ADMIN_ROLE) {
        _pause();
    }
    
    /**
     * @dev Unpause contract
     */
    function unpause() external onlyRole(DEFAULT_ADMIN_ROLE) {
        _unpause();
    }
} 