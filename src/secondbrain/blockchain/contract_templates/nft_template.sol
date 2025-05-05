// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/token/ERC721/extensions/ERC721URIStorage.sol";
import "@openzeppelin/contracts/token/ERC721/extensions/ERC721Enumerable.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/Counters.sol";

contract {{ContractName}} is ERC721, ERC721URIStorage, ERC721Enumerable, Ownable {
    using Counters for Counters.Counter;
    Counters.Counter private _tokenIds;
    
    uint256 public constant MINT_PRICE = 0.05 ether;
    uint256 public constant MAX_SUPPLY = 10000;
    
    string public baseURI;
    
    constructor() ERC721("{{ContractName}}", "{{ContractSymbol}}") Ownable(msg.sender) {
        baseURI = "";
    }
    
    function mint(string memory tokenURI) public payable returns (uint256) {
        require(msg.value >= MINT_PRICE, "Insufficient payment");
        require(totalSupply() < MAX_SUPPLY, "Max supply reached");
        
        _tokenIds.increment();
        uint256 newTokenId = _tokenIds.current();
        _safeMint(msg.sender, newTokenId);
        _setTokenURI(newTokenId, tokenURI);
        
        return newTokenId;
    }
    
    function setBaseURI(string memory _baseURI) public onlyOwner {
        baseURI = _baseURI;
    }
    
    function _baseURI() internal view override returns (string memory) {
        return baseURI;
    }
    
    function withdraw() public onlyOwner {
        uint256 balance = address(this).balance;
        payable(owner()).transfer(balance);
    }
    
    // Override required functions
    function _update(address to, uint256 tokenId, address auth)
        internal
        override(ERC721, ERC721Enumerable)
        returns (address)
    {
        return super._update(to, tokenId, auth);
    }
    
    function _increaseBalance(address account, uint128 value)
        internal
        override(ERC721, ERC721Enumerable)
    {
        super._increaseBalance(account, value);
    }
    
    function tokenURI(uint256 tokenId)
        public
        view
        override(ERC721, ERC721URIStorage)
        returns (string memory)
    {
        return super.tokenURI(tokenId);
    }
    
    function supportsInterface(bytes4 interfaceId)
        public
        view
        override(ERC721, ERC721Enumerable, ERC721URIStorage)
        returns (bool)
    {
        return super.supportsInterface(interfaceId);
    }
} 