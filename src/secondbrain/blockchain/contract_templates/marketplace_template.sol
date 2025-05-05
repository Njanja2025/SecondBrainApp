// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC721/IERC721.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/Counters.sol";

contract {{ContractName}} is ReentrancyGuard, Ownable {
    using SafeERC20 for IERC20;
    using Counters for Counters.Counter;

    struct Listing {
        address seller;
        address nftContract;
        uint256 tokenId;
        uint256 price;
        bool isAuction;
        uint256 auctionEndTime;
        address highestBidder;
        uint256 highestBid;
        bool active;
        uint256 royaltyPercentage;
        address royaltyReceiver;
    }

    // Events
    event ListingCreated(
        uint256 indexed listingId,
        address indexed seller,
        address indexed nftContract,
        uint256 tokenId,
        uint256 price,
        bool isAuction
    );
    event ListingCancelled(uint256 indexed listingId);
    event ListingSold(
        uint256 indexed listingId,
        address indexed buyer,
        uint256 price
    );
    event BidPlaced(
        uint256 indexed listingId,
        address indexed bidder,
        uint256 amount
    );
    event RoyaltyPaid(
        address indexed nftContract,
        uint256 indexed tokenId,
        address indexed receiver,
        uint256 amount
    );

    // State variables
    Counters.Counter private _listingIds;
    mapping(uint256 => Listing) public listings;
    mapping(address => mapping(uint256 => uint256)) public tokenIdToListingId;
    IERC20 public paymentToken;
    uint256 public platformFee; // In basis points (1/10000)

    constructor(address _paymentToken, uint256 _platformFee) Ownable(msg.sender) {
        require(_paymentToken != address(0), "Invalid payment token");
        require(_platformFee <= 1000, "Platform fee too high"); // Max 10%
        paymentToken = IERC20(_paymentToken);
        platformFee = _platformFee;
    }

    function createListing(
        address nftContract,
        uint256 tokenId,
        uint256 price,
        bool isAuction,
        uint256 auctionDuration,
        uint256 royaltyPercentage,
        address royaltyReceiver
    ) external nonReentrant returns (uint256) {
        require(price > 0, "Price must be greater than 0");
        require(royaltyPercentage <= 1000, "Royalty too high"); // Max 10%
        
        IERC721 nft = IERC721(nftContract);
        require(
            nft.ownerOf(tokenId) == msg.sender,
            "Not token owner"
        );
        require(
            nft.getApproved(tokenId) == address(this) ||
            nft.isApprovedForAll(msg.sender, address(this)),
            "Not approved"
        );

        _listingIds.increment();
        uint256 listingId = _listingIds.current();

        listings[listingId] = Listing({
            seller: msg.sender,
            nftContract: nftContract,
            tokenId: tokenId,
            price: price,
            isAuction: isAuction,
            auctionEndTime: isAuction ? block.timestamp + auctionDuration : 0,
            highestBidder: address(0),
            highestBid: 0,
            active: true,
            royaltyPercentage: royaltyPercentage,
            royaltyReceiver: royaltyReceiver
        });

        tokenIdToListingId[nftContract][tokenId] = listingId;
        nft.transferFrom(msg.sender, address(this), tokenId);

        emit ListingCreated(
            listingId,
            msg.sender,
            nftContract,
            tokenId,
            price,
            isAuction
        );

        return listingId;
    }

    function buyNow(uint256 listingId) external nonReentrant {
        Listing storage listing = listings[listingId];
        require(listing.active, "Listing not active");
        require(!listing.isAuction, "Listing is an auction");
        
        _processPurchase(listingId, listing.price);
    }

    function placeBid(uint256 listingId, uint256 bidAmount) external nonReentrant {
        Listing storage listing = listings[listingId];
        require(listing.active, "Listing not active");
        require(listing.isAuction, "Not an auction");
        require(block.timestamp < listing.auctionEndTime, "Auction ended");
        require(bidAmount > listing.highestBid, "Bid too low");

        if (listing.highestBidder != address(0)) {
            // Refund previous bidder
            paymentToken.safeTransfer(listing.highestBidder, listing.highestBid);
        }

        paymentToken.safeTransferFrom(msg.sender, address(this), bidAmount);
        listing.highestBidder = msg.sender;
        listing.highestBid = bidAmount;

        emit BidPlaced(listingId, msg.sender, bidAmount);
    }

    function finalizeAuction(uint256 listingId) external nonReentrant {
        Listing storage listing = listings[listingId];
        require(listing.active, "Listing not active");
        require(listing.isAuction, "Not an auction");
        require(block.timestamp >= listing.auctionEndTime, "Auction not ended");

        if (listing.highestBidder != address(0)) {
            _processPurchase(listingId, listing.highestBid);
        } else {
            // No bids, return NFT to seller
            IERC721(listing.nftContract).transferFrom(
                address(this),
                listing.seller,
                listing.tokenId
            );
            listing.active = false;
        }
    }

    function cancelListing(uint256 listingId) external nonReentrant {
        Listing storage listing = listings[listingId];
        require(listing.active, "Listing not active");
        require(
            msg.sender == listing.seller || msg.sender == owner(),
            "Not authorized"
        );

        if (listing.isAuction && listing.highestBidder != address(0)) {
            // Refund highest bidder
            paymentToken.safeTransfer(listing.highestBidder, listing.highestBid);
        }

        IERC721(listing.nftContract).transferFrom(
            address(this),
            listing.seller,
            listing.tokenId
        );
        listing.active = false;

        emit ListingCancelled(listingId);
    }

    function _processPurchase(uint256 listingId, uint256 price) internal {
        Listing storage listing = listings[listingId];
        
        // Calculate fees
        uint256 platformFeeAmount = (price * platformFee) / 10000;
        uint256 royaltyAmount = (price * listing.royaltyPercentage) / 10000;
        uint256 sellerAmount = price - platformFeeAmount - royaltyAmount;

        // Transfer payments
        paymentToken.safeTransfer(owner(), platformFeeAmount);
        if (royaltyAmount > 0) {
            paymentToken.safeTransfer(listing.royaltyReceiver, royaltyAmount);
            emit RoyaltyPaid(
                listing.nftContract,
                listing.tokenId,
                listing.royaltyReceiver,
                royaltyAmount
            );
        }
        paymentToken.safeTransfer(listing.seller, sellerAmount);

        // Transfer NFT
        IERC721(listing.nftContract).transferFrom(
            address(this),
            msg.sender,
            listing.tokenId
        );

        listing.active = false;
        emit ListingSold(listingId, msg.sender, price);
    }

    // View functions
    function getListing(uint256 listingId)
        external
        view
        returns (
            address seller,
            address nftContract,
            uint256 tokenId,
            uint256 price,
            bool isAuction,
            uint256 auctionEndTime,
            address highestBidder,
            uint256 highestBid,
            bool active,
            uint256 royaltyPercentage,
            address royaltyReceiver
        )
    {
        Listing storage listing = listings[listingId];
        return (
            listing.seller,
            listing.nftContract,
            listing.tokenId,
            listing.price,
            listing.isAuction,
            listing.auctionEndTime,
            listing.highestBidder,
            listing.highestBid,
            listing.active,
            listing.royaltyPercentage,
            listing.royaltyReceiver
        );
    }

    function setPlatformFee(uint256 _platformFee) external onlyOwner {
        require(_platformFee <= 1000, "Platform fee too high"); // Max 10%
        platformFee = _platformFee;
    }

    function setPaymentToken(address _paymentToken) external onlyOwner {
        require(_paymentToken != address(0), "Invalid payment token");
        paymentToken = IERC20(_paymentToken);
    }
} 