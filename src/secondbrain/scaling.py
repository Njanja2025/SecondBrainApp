import asyncio
import logging
import docker
from typing import Dict, List, Optional
import psutil
from datetime import datetime, timedelta
import aiohttp
import json

logger = logging.getLogger(__name__)

class AutoScaler:
    """Manage automatic scaling of application components."""
    
    def __init__(
        self,
        min_instances: int = 1,
        max_instances: int = 5,
        cpu_threshold: float = 80.0,
        memory_threshold: float = 80.0,
        scale_up_cooldown: int = 300,  # 5 minutes
        scale_down_cooldown: int = 600,  # 10 minutes
    ):
        self.docker_client = docker.from_env()
        self.min_instances = min_instances
        self.max_instances = max_instances
        self.cpu_threshold = cpu_threshold
        self.memory_threshold = memory_threshold
        self.scale_up_cooldown = scale_up_cooldown
        self.scale_down_cooldown = scale_down_cooldown
        self.last_scale_up = datetime.min
        self.last_scale_down = datetime.min
        self.service_metrics: Dict[str, List[float]] = {}
        
    async def get_service_metrics(self, service_name: str) -> Dict[str, float]:
        """Get current metrics for a service."""
        try:
            containers = self.docker_client.containers.list(
                filters={
                    "label": f"com.docker.swarm.service.name={service_name}"
                }
            )
            
            total_cpu = 0.0
            total_memory = 0.0
            
            for container in containers:
                stats = container.stats(stream=False)
                
                # Calculate CPU usage
                cpu_delta = stats["cpu_stats"]["cpu_usage"]["total_usage"] - \
                           stats["precpu_stats"]["cpu_usage"]["total_usage"]
                system_delta = stats["cpu_stats"]["system_cpu_usage"] - \
                             stats["precpu_stats"]["system_cpu_usage"]
                cpu_usage = (cpu_delta / system_delta) * 100.0
                
                # Calculate memory usage
                memory_usage = (
                    stats["memory_stats"]["usage"] /
                    stats["memory_stats"]["limit"]
                ) * 100.0
                
                total_cpu += cpu_usage
                total_memory += memory_usage
                
            avg_cpu = total_cpu / len(containers) if containers else 0
            avg_memory = total_memory / len(containers) if containers else 0
            
            return {
                "cpu_percent": avg_cpu,
                "memory_percent": avg_memory,
                "instance_count": len(containers)
            }
            
        except Exception as e:
            logger.error(f"Error getting service metrics: {e}")
            return {
                "cpu_percent": 0.0,
                "memory_percent": 0.0,
                "instance_count": 0
            }
            
    async def should_scale_up(self, metrics: Dict[str, float]) -> bool:
        """Determine if service should scale up."""
        if datetime.now() - self.last_scale_up < timedelta(seconds=self.scale_up_cooldown):
            return False
            
        return (
            metrics["cpu_percent"] > self.cpu_threshold or
            metrics["memory_percent"] > self.memory_threshold
        ) and metrics["instance_count"] < self.max_instances
        
    async def should_scale_down(self, metrics: Dict[str, float]) -> bool:
        """Determine if service should scale down."""
        if datetime.now() - self.last_scale_down < timedelta(seconds=self.scale_down_cooldown):
            return False
            
        return (
            metrics["cpu_percent"] < self.cpu_threshold / 2 and
            metrics["memory_percent"] < self.memory_threshold / 2
        ) and metrics["instance_count"] > self.min_instances
        
    async def scale_service(self, service_name: str, replicas: int) -> bool:
        """Scale a service to specified number of replicas."""
        try:
            service = self.docker_client.services.get(service_name)
            service.scale(replicas)
            logger.info(f"Scaled service {service_name} to {replicas} replicas")
            return True
        except Exception as e:
            logger.error(f"Error scaling service {service_name}: {e}")
            return False
            
    async def monitor_and_scale(self, service_name: str):
        """Monitor and automatically scale a service."""
        while True:
            try:
                metrics = await self.get_service_metrics(service_name)
                
                if await self.should_scale_up(metrics):
                    new_count = min(
                        metrics["instance_count"] + 1,
                        self.max_instances
                    )
                    if await self.scale_service(service_name, new_count):
                        self.last_scale_up = datetime.now()
                        
                elif await self.should_scale_down(metrics):
                    new_count = max(
                        metrics["instance_count"] - 1,
                        self.min_instances
                    )
                    if await self.scale_service(service_name, new_count):
                        self.last_scale_down = datetime.now()
                        
                # Store metrics history
                if service_name not in self.service_metrics:
                    self.service_metrics[service_name] = []
                    
                self.service_metrics[service_name].append(metrics["cpu_percent"])
                if len(self.service_metrics[service_name]) > 60:  # Keep last hour
                    self.service_metrics[service_name].pop(0)
                    
            except Exception as e:
                logger.error(f"Error in monitor_and_scale: {e}")
                
            await asyncio.sleep(60)  # Check every minute
            
    async def start_monitoring(self, services: List[str]):
        """Start monitoring multiple services."""
        tasks = [
            self.monitor_and_scale(service)
            for service in services
        ]
        await asyncio.gather(*tasks)

class LoadBalancer:
    """Load balancer for distributing requests across instances."""
    
    def __init__(self):
        self.instances: List[str] = []
        self.current_index = 0
        self.health_checks: Dict[str, bool] = {}
        
    async def add_instance(self, instance_url: str):
        """Add a new instance to the load balancer."""
        if instance_url not in self.instances:
            self.instances.append(instance_url)
            self.health_checks[instance_url] = True
            
    async def remove_instance(self, instance_url: str):
        """Remove an instance from the load balancer."""
        if instance_url in self.instances:
            self.instances.remove(instance_url)
            self.health_checks.pop(instance_url, None)
            
    async def get_next_instance(self) -> Optional[str]:
        """Get next available instance using round-robin."""
        if not self.instances:
            return None
            
        # Skip unhealthy instances
        for _ in range(len(self.instances)):
            self.current_index = (self.current_index + 1) % len(self.instances)
            instance = self.instances[self.current_index]
            if self.health_checks.get(instance, False):
                return instance
                
        return None
        
    async def check_instance_health(self, instance_url: str) -> bool:
        """Check if an instance is healthy."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{instance_url}/health") as response:
                    healthy = response.status == 200
                    self.health_checks[instance_url] = healthy
                    return healthy
        except Exception:
            self.health_checks[instance_url] = False
            return False
            
    async def monitor_health(self):
        """Continuously monitor instance health."""
        while True:
            for instance in list(self.instances):  # Copy list to avoid modification during iteration
                await self.check_instance_health(instance)
            await asyncio.sleep(30)  # Check every 30 seconds 