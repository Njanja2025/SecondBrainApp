// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract {{ContractName}} is ReentrancyGuard, Ownable {
    using SafeERC20 for IERC20;

    struct Pool {
        IERC20 token0;
        IERC20 token1;
        uint256 reserve0;
        uint256 reserve1;
        uint256 totalShares;
        mapping(address => uint256) shares;
        uint32 fee;  // Fee in basis points (1/10000)
    }

    // Events
    event PoolCreated(address indexed token0, address indexed token1, uint32 fee);
    event LiquidityAdded(
        address indexed provider,
        address indexed token0,
        address indexed token1,
        uint256 amount0,
        uint256 amount1,
        uint256 shares
    );
    event LiquidityRemoved(
        address indexed provider,
        address indexed token0,
        address indexed token1,
        uint256 amount0,
        uint256 amount1,
        uint256 shares
    );
    event Swap(
        address indexed user,
        address indexed tokenIn,
        address indexed tokenOut,
        uint256 amountIn,
        uint256 amountOut
    );

    // State variables
    mapping(bytes32 => Pool) public pools;
    bytes32[] public poolIds;

    constructor() Ownable(msg.sender) {}

    function createPool(
        address token0,
        address token1,
        uint32 fee
    ) external onlyOwner {
        require(token0 != address(0) && token1 != address(0), "Invalid tokens");
        require(token0 != token1, "Identical tokens");
        require(fee <= 1000, "Fee too high"); // Max 10%

        bytes32 poolId = _computePoolId(token0, token1);
        require(address(pools[poolId].token0) == address(0), "Pool exists");

        pools[poolId].token0 = IERC20(token0);
        pools[poolId].token1 = IERC20(token1);
        pools[poolId].fee = fee;
        poolIds.push(poolId);

        emit PoolCreated(token0, token1, fee);
    }

    function addLiquidity(
        address token0,
        address token1,
        uint256 amount0Desired,
        uint256 amount1Desired,
        uint256 amount0Min,
        uint256 amount1Min
    ) external nonReentrant returns (uint256 shares) {
        bytes32 poolId = _computePoolId(token0, token1);
        Pool storage pool = pools[poolId];
        require(address(pool.token0) != address(0), "Pool not found");

        uint256 amount0;
        uint256 amount1;

        if (pool.reserve0 == 0) {
            amount0 = amount0Desired;
            amount1 = amount1Desired;
            shares = _sqrt(amount0 * amount1);
        } else {
            uint256 amount1Optimal = (amount0Desired * pool.reserve1) / pool.reserve0;
            if (amount1Optimal <= amount1Desired) {
                require(amount1Optimal >= amount1Min, "Insufficient token1 amount");
                amount0 = amount0Desired;
                amount1 = amount1Optimal;
            } else {
                uint256 amount0Optimal = (amount1Desired * pool.reserve0) / pool.reserve1;
                require(amount0Optimal >= amount0Min, "Insufficient token0 amount");
                amount0 = amount0Optimal;
                amount1 = amount1Desired;
            }
            shares = _min(
                (amount0 * pool.totalShares) / pool.reserve0,
                (amount1 * pool.totalShares) / pool.reserve1
            );
        }

        require(shares > 0, "Insufficient liquidity shares");

        pool.token0.safeTransferFrom(msg.sender, address(this), amount0);
        pool.token1.safeTransferFrom(msg.sender, address(this), amount1);

        pool.reserve0 += amount0;
        pool.reserve1 += amount1;
        pool.totalShares += shares;
        pool.shares[msg.sender] += shares;

        emit LiquidityAdded(msg.sender, token0, token1, amount0, amount1, shares);
    }

    function removeLiquidity(
        address token0,
        address token1,
        uint256 shares,
        uint256 amount0Min,
        uint256 amount1Min
    ) external nonReentrant returns (uint256 amount0, uint256 amount1) {
        bytes32 poolId = _computePoolId(token0, token1);
        Pool storage pool = pools[poolId];
        require(address(pool.token0) != address(0), "Pool not found");
        require(pool.shares[msg.sender] >= shares, "Insufficient shares");

        amount0 = (shares * pool.reserve0) / pool.totalShares;
        amount1 = (shares * pool.reserve1) / pool.totalShares;
        require(amount0 >= amount0Min, "Insufficient token0 output");
        require(amount1 >= amount1Min, "Insufficient token1 output");

        pool.shares[msg.sender] -= shares;
        pool.totalShares -= shares;
        pool.reserve0 -= amount0;
        pool.reserve1 -= amount1;

        pool.token0.safeTransfer(msg.sender, amount0);
        pool.token1.safeTransfer(msg.sender, amount1);

        emit LiquidityRemoved(msg.sender, token0, token1, amount0, amount1, shares);
    }

    function swap(
        address tokenIn,
        address tokenOut,
        uint256 amountIn,
        uint256 minAmountOut
    ) external nonReentrant returns (uint256 amountOut) {
        bytes32 poolId = _computePoolId(tokenIn, tokenOut);
        Pool storage pool = pools[poolId];
        require(address(pool.token0) != address(0), "Pool not found");

        bool isToken0 = tokenIn == address(pool.token0);
        (IERC20 tokenInContract, IERC20 tokenOutContract) = isToken0
            ? (pool.token0, pool.token1)
            : (pool.token1, pool.token0);
        (uint256 reserveIn, uint256 reserveOut) = isToken0
            ? (pool.reserve0, pool.reserve1)
            : (pool.reserve1, pool.reserve0);

        tokenInContract.safeTransferFrom(msg.sender, address(this), amountIn);

        uint256 amountInWithFee = amountIn * (10000 - pool.fee);
        amountOut = (amountInWithFee * reserveOut) / ((reserveIn * 10000) + amountInWithFee);
        require(amountOut >= minAmountOut, "Insufficient output amount");

        if (isToken0) {
            pool.reserve0 += amountIn;
            pool.reserve1 -= amountOut;
        } else {
            pool.reserve1 += amountIn;
            pool.reserve0 -= amountOut;
        }

        tokenOutContract.safeTransfer(msg.sender, amountOut);

        emit Swap(msg.sender, tokenIn, tokenOut, amountIn, amountOut);
    }

    // View functions
    function getPool(address token0, address token1)
        external
        view
        returns (
            uint256 reserve0,
            uint256 reserve1,
            uint256 totalShares,
            uint32 fee
        )
    {
        bytes32 poolId = _computePoolId(token0, token1);
        Pool storage pool = pools[poolId];
        return (pool.reserve0, pool.reserve1, pool.totalShares, pool.fee);
    }

    function getShares(
        address token0,
        address token1,
        address provider
    ) external view returns (uint256) {
        bytes32 poolId = _computePoolId(token0, token1);
        return pools[poolId].shares[provider];
    }

    // Internal functions
    function _computePoolId(address token0, address token1) internal pure returns (bytes32) {
        return token0 < token1
            ? keccak256(abi.encodePacked(token0, token1))
            : keccak256(abi.encodePacked(token1, token0));
    }

    function _sqrt(uint256 y) internal pure returns (uint256 z) {
        if (y > 3) {
            z = y;
            uint256 x = y / 2 + 1;
            while (x < z) {
                z = x;
                x = (y / x + x) / 2;
            }
        } else if (y != 0) {
            z = 1;
        }
    }

    function _min(uint256 x, uint256 y) internal pure returns (uint256) {
        return x < y ? x : y;
    }
} 