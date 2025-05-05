from enum import Enum
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Callable, Any, Optional, Dict
from functools import wraps
import time
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

logger = logging.getLogger(__name__)

class CircuitState(Enum):
    CLOSED = "closed"  # Normal operation
    OPEN = "open"      # Service unavailable
    HALF_OPEN = "half_open"  # Testing recovery

class CircuitBreaker:
    """Circuit breaker pattern implementation."""
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        half_open_timeout: int = 30,
        exception_types: tuple = (Exception,)
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_timeout = half_open_timeout
        self.exception_types = exception_types
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
        self.last_success_time = None
        self._lock = asyncio.Lock()
        self.metrics: Dict[str, int] = {
            "success_count": 0,
            "failure_count": 0,
            "timeout_count": 0,
            "rejection_count": 0
        }

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection."""
        async with self._lock:
            if self.state == CircuitState.OPEN:
                if await self._should_attempt_reset():
                    self.state = CircuitState.HALF_OPEN
                else:
                    self.metrics["rejection_count"] += 1
                    raise CircuitBreakerOpen("Circuit breaker is OPEN")

        try:
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)

            await self._handle_success()
            return result

        except self.exception_types as e:
            await self._handle_failure(e)
            raise

    async def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        if not self.last_failure_time:
            return True
        
        elapsed = datetime.now() - self.last_failure_time
        return elapsed.total_seconds() >= self.recovery_timeout

    async def _handle_success(self):
        """Handle successful execution."""
        async with self._lock:
            self.metrics["success_count"] += 1
            self.last_success_time = datetime.now()
            
            if self.state == CircuitState.HALF_OPEN:
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                logger.info("Circuit breaker reset to CLOSED state")

    async def _handle_failure(self, exception: Exception):
        """Handle execution failure."""
        async with self._lock:
            self.failure_count += 1
            self.metrics["failure_count"] += 1
            self.last_failure_time = datetime.now()

            if self.state == CircuitState.CLOSED and self.failure_count >= self.failure_threshold:
                self.state = CircuitState.OPEN
                logger.warning(f"Circuit breaker OPENED due to {self.failure_count} failures")

            elif self.state == CircuitState.HALF_OPEN:
                self.state = CircuitState.OPEN
                logger.warning("Circuit breaker returned to OPEN state after failed recovery attempt")

class CircuitBreakerOpen(Exception):
    """Exception raised when circuit breaker is open."""
    pass

def with_circuit_breaker(circuit_breaker: CircuitBreaker):
    """Decorator to wrap function with circuit breaker."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await circuit_breaker.call(func, *args, **kwargs)
        return wrapper
    return decorator

class RetryWithBackoff:
    """Retry pattern with exponential backoff."""
    
    @staticmethod
    def decorator(
        max_attempts: int = 3,
        max_delay: float = 10,
        base_delay: float = 1,
        exception_types: tuple = (Exception,)
    ):
        return retry(
            stop=stop_after_attempt(max_attempts),
            wait=wait_exponential(multiplier=base_delay, max=max_delay),
            retry=retry_if_exception_type(exception_types),
            before_sleep=lambda retry_state: logger.warning(
                f"Retrying after {retry_state.outcome.exception()}, "
                f"attempt {retry_state.attempt_number}"
            )
        )

class Bulkhead:
    """Bulkhead pattern implementation for concurrent execution control."""
    
    def __init__(self, max_concurrent_calls: int = 10, timeout: float = 30):
        self.semaphore = asyncio.Semaphore(max_concurrent_calls)
        self.timeout = timeout
        self.metrics = {
            "current_concurrent": 0,
            "max_concurrent_reached": 0,
            "timeout_count": 0
        }

    async def execute(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with bulkhead protection."""
        try:
            async with asyncio.timeout(self.timeout):
                async with self.semaphore:
                    self.metrics["current_concurrent"] += 1
                    if self.metrics["current_concurrent"] > self.metrics["max_concurrent_reached"]:
                        self.metrics["max_concurrent_reached"] = self.metrics["current_concurrent"]
                    
                    try:
                        if asyncio.iscoroutinefunction(func):
                            return await func(*args, **kwargs)
                        return func(*args, **kwargs)
                    finally:
                        self.metrics["current_concurrent"] -= 1
        except asyncio.TimeoutError:
            self.metrics["timeout_count"] += 1
            raise

def with_bulkhead(bulkhead: Bulkhead):
    """Decorator to wrap function with bulkhead pattern."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await bulkhead.execute(func, *args, **kwargs)
        return wrapper
    return decorator 