import asyncio
import logging
from typing import Optional, Callable
from .resilience import CircuitBreaker, CircuitState, with_circuit_breaker

logger = logging.getLogger(__name__)


class VPNManager:
    """Manages VPN connection with automatic failover."""

    def __init__(
        self,
        connect_vpn_func: Callable,
        disconnect_vpn_func: Callable,
        failure_threshold: int = 3,
        recovery_timeout: int = 30,
    ):
        self.connect_vpn = connect_vpn_func
        self.disconnect_vpn = disconnect_vpn_func
        self.vpn_active = False
        self._lock = asyncio.Lock()

        # Circuit breaker for monitoring regular connection
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
            exception_types=(ConnectionError, TimeoutError),
        )

    async def execute_with_vpn_failover(self, func: Callable, *args, **kwargs):
        """Execute function with automatic VPN failover on connection issues."""
        try:
            # Try with regular connection first
            return await self.circuit_breaker.call(func, *args, **kwargs)
        except Exception as e:
            if self.circuit_breaker.state == CircuitState.OPEN:
                logger.warning("Regular connection failing, switching to VPN")
                await self._ensure_vpn_active()
                # Retry the operation through VPN
                return await func(*args, **kwargs)
            raise

    async def _ensure_vpn_active(self):
        """Ensure VPN is connected."""
        async with self._lock:
            if not self.vpn_active:
                try:
                    await self.connect_vpn()
                    self.vpn_active = True
                    logger.info("VPN connection established")
                except Exception as e:
                    logger.error(f"Failed to establish VPN connection: {e}")
                    raise

    async def disconnect(self):
        """Disconnect from VPN if active."""
        async with self._lock:
            if self.vpn_active:
                try:
                    await self.disconnect_vpn()
                    self.vpn_active = False
                    logger.info("VPN connection terminated")
                except Exception as e:
                    logger.error(f"Failed to disconnect VPN: {e}")
                    raise


def with_vpn_failover(vpn_manager: VPNManager):
    """Decorator to wrap function with VPN failover capability."""

    def decorator(func):
        async def wrapper(*args, **kwargs):
            return await vpn_manager.execute_with_vpn_failover(func, *args, **kwargs)

        return wrapper

    return decorator
