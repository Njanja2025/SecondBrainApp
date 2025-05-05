import asyncio
import logging
from typing import Dict, List, Optional, Set
from datetime import datetime, timedelta
import json
import aiohttp
from dataclasses import dataclass, asdict
import socket
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

@dataclass
class ServiceInstance:
    """Service instance information."""
    id: str
    name: str
    host: str
    port: int
    health_check_url: str
    metadata: Dict
    last_heartbeat: datetime
    status: str = "unknown"  # unknown, healthy, unhealthy

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        data = asdict(self)
        data['last_heartbeat'] = data['last_heartbeat'].isoformat()
        return data

    @classmethod
    def from_dict(cls, data: dict) -> 'ServiceInstance':
        """Create from dictionary."""
        data['last_heartbeat'] = datetime.fromisoformat(data['last_heartbeat'])
        return cls(**data)

class ServiceRegistry:
    """Service registry for service discovery."""
    
    def __init__(
        self,
        heartbeat_interval: int = 30,
        cleanup_interval: int = 60,
        instance_timeout: int = 90
    ):
        self.services: Dict[str, Dict[str, ServiceInstance]] = {}
        self.heartbeat_interval = heartbeat_interval
        self.cleanup_interval = cleanup_interval
        self.instance_timeout = instance_timeout
        self.watchers: Dict[str, Set[asyncio.Queue]] = {}
        self._lock = asyncio.Lock()
        self._running = False
        self._background_tasks: Set[asyncio.Task] = set()

    async def register(self, instance: ServiceInstance) -> bool:
        """Register a service instance."""
        async with self._lock:
            if instance.name not in self.services:
                self.services[instance.name] = {}
                self.watchers[instance.name] = set()

            self.services[instance.name][instance.id] = instance
            await self._notify_watchers(instance.name, "register", instance)
            logger.info(f"Registered service: {instance.name} ({instance.id})")
            return True

    async def deregister(self, service_name: str, instance_id: str) -> bool:
        """Deregister a service instance."""
        async with self._lock:
            if service_name in self.services and instance_id in self.services[service_name]:
                instance = self.services[service_name].pop(instance_id)
                if not self.services[service_name]:
                    del self.services[service_name]
                await self._notify_watchers(service_name, "deregister", instance)
                logger.info(f"Deregistered service: {service_name} ({instance_id})")
                return True
            return False

    async def get_instances(self, service_name: str) -> List[ServiceInstance]:
        """Get all instances of a service."""
        return list(self.services.get(service_name, {}).values())

    async def get_healthy_instances(self, service_name: str) -> List[ServiceInstance]:
        """Get healthy instances of a service."""
        instances = await self.get_instances(service_name)
        return [i for i in instances if i.status == "healthy"]

    @asynccontextmanager
    async def watch_service(self, service_name: str):
        """Watch for service changes."""
        queue = asyncio.Queue()
        try:
            if service_name not in self.watchers:
                self.watchers[service_name] = set()
            self.watchers[service_name].add(queue)
            yield queue
        finally:
            self.watchers[service_name].remove(queue)

    async def _notify_watchers(
        self,
        service_name: str,
        event_type: str,
        instance: ServiceInstance
    ):
        """Notify watchers of service changes."""
        if service_name in self.watchers:
            event = {
                "type": event_type,
                "service": service_name,
                "instance": instance.to_dict()
            }
            for queue in self.watchers[service_name]:
                await queue.put(event)

    async def heartbeat(self, service_name: str, instance_id: str) -> bool:
        """Update service instance heartbeat."""
        async with self._lock:
            if (service_name in self.services and 
                instance_id in self.services[service_name]):
                instance = self.services[service_name][instance_id]
                instance.last_heartbeat = datetime.now()
                return True
            return False

    async def _check_health(self, instance: ServiceInstance) -> bool:
        """Check health of a service instance."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    instance.health_check_url,
                    timeout=5
                ) as response:
                    healthy = response.status == 200
                    instance.status = "healthy" if healthy else "unhealthy"
                    return healthy
        except Exception as e:
            logger.warning(f"Health check failed for {instance.id}: {e}")
            instance.status = "unhealthy"
            return False

    async def _cleanup_expired(self):
        """Remove expired service instances."""
        async with self._lock:
            now = datetime.now()
            for service_name in list(self.services.keys()):
                for instance_id in list(self.services[service_name].keys()):
                    instance = self.services[service_name][instance_id]
                    if (now - instance.last_heartbeat).total_seconds() > self.instance_timeout:
                        await self.deregister(service_name, instance_id)

    async def start(self):
        """Start the service registry."""
        self._running = True
        
        # Start health check task
        health_check_task = asyncio.create_task(self._health_check_loop())
        self._background_tasks.add(health_check_task)
        health_check_task.add_done_callback(self._background_tasks.discard)
        
        # Start cleanup task
        cleanup_task = asyncio.create_task(self._cleanup_loop())
        self._background_tasks.add(cleanup_task)
        cleanup_task.add_done_callback(self._background_tasks.discard)

    async def stop(self):
        """Stop the service registry."""
        self._running = False
        for task in self._background_tasks:
            task.cancel()
        await asyncio.gather(*self._background_tasks, return_exceptions=True)

    async def _health_check_loop(self):
        """Periodic health check loop."""
        while self._running:
            try:
                for service_instances in self.services.values():
                    for instance in service_instances.values():
                        await self._check_health(instance)
                await asyncio.sleep(self.heartbeat_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in health check loop: {e}")
                await asyncio.sleep(5)

    async def _cleanup_loop(self):
        """Periodic cleanup loop."""
        while self._running:
            try:
                await self._cleanup_expired()
                await asyncio.sleep(self.cleanup_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")
                await asyncio.sleep(5)

class ServiceRegistryClient:
    """Client for interacting with service registry."""
    
    def __init__(self, registry: ServiceRegistry):
        self.registry = registry
        self._instance: Optional[ServiceInstance] = None

    async def register_service(
        self,
        name: str,
        port: int,
        health_check_path: str = "/health",
        metadata: Optional[Dict] = None
    ) -> ServiceInstance:
        """Register service with the registry."""
        host = socket.gethostname()
        instance = ServiceInstance(
            id=f"{name}-{host}-{port}",
            name=name,
            host=host,
            port=port,
            health_check_url=f"http://{host}:{port}{health_check_path}",
            metadata=metadata or {},
            last_heartbeat=datetime.now()
        )
        
        await self.registry.register(instance)
        self._instance = instance
        return instance

    async def deregister_service(self):
        """Deregister service from the registry."""
        if self._instance:
            await self.registry.deregister(
                self._instance.name,
                self._instance.id
            )
            self._instance = None

    async def start_heartbeat(self):
        """Start sending heartbeats."""
        while True:
            if self._instance:
                await self.registry.heartbeat(
                    self._instance.name,
                    self._instance.id
                )
            await asyncio.sleep(self.registry.heartbeat_interval) 