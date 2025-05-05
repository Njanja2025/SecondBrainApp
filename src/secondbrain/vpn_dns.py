import asyncio
import logging
import subprocess
from typing import List, Optional, Dict
from pathlib import Path
import platform
import tempfile

logger = logging.getLogger(__name__)

class DNSManager:
    """Manages DNS settings to prevent leaks and enable custom routing."""
    
    def __init__(self):
        self.system = platform.system().lower()
        self._original_dns: Dict[str, List[str]] = {}
        self._original_resolv_conf: Optional[str] = None
        self._lock = asyncio.Lock()
        self._enabled = False

    async def configure_dns(
        self,
        vpn_dns_servers: List[str],
        interface: str,
        backup_dns: List[str] = ["8.8.8.8", "1.1.1.1"]
    ):
        """
        Configure system DNS settings for VPN.
        
        Args:
            vpn_dns_servers: List of VPN provider's DNS servers
            interface: Network interface name
            backup_dns: Backup DNS servers to use if VPN DNS fails
        """
        if self._enabled:
            return

        async with self._lock:
            try:
                # Backup current DNS settings
                await self._backup_dns_settings()
                
                if self.system == "darwin":
                    await self._configure_dns_macos(vpn_dns_servers, interface, backup_dns)
                elif self.system == "linux":
                    await self._configure_dns_linux(vpn_dns_servers, backup_dns)
                else:
                    raise NotImplementedError(f"DNS configuration not implemented for {self.system}")
                
                self._enabled = True
                logger.info("DNS protection enabled")
                
            except Exception as e:
                logger.error(f"Failed to configure DNS: {e}")
                await self.restore_dns()
                raise

    async def restore_dns(self):
        """Restore original DNS settings."""
        if not self._enabled:
            return

        async with self._lock:
            try:
                if self.system == "darwin":
                    await self._restore_dns_macos()
                elif self.system == "linux":
                    await self._restore_dns_linux()
                
                self._enabled = False
                logger.info("DNS settings restored")
                
            except Exception as e:
                logger.error(f"Failed to restore DNS settings: {e}")
                raise

    async def _backup_dns_settings(self):
        """Backup current DNS settings."""
        if self.system == "darwin":
            # Get network services
            proc = await asyncio.create_subprocess_exec(
                "networksetup", "-listallnetworkservices",
                stdout=asyncio.subprocess.PIPE
            )
            stdout, _ = await proc.communicate()
            services = stdout.decode().splitlines()[1:]  # Skip first line

            # Backup DNS for each service
            for service in services:
                proc = await asyncio.create_subprocess_exec(
                    "networksetup", "-getdnsservers", service,
                    stdout=asyncio.subprocess.PIPE
                )
                stdout, _ = await proc.communicate()
                dns_servers = stdout.decode().strip().splitlines()
                self._original_dns[service] = dns_servers

        elif self.system == "linux":
            # Backup resolv.conf
            try:
                with open("/etc/resolv.conf", "r") as f:
                    self._original_resolv_conf = f.read()
            except Exception as e:
                logger.error(f"Failed to backup resolv.conf: {e}")

    async def _configure_dns_macos(
        self,
        vpn_dns_servers: List[str],
        interface: str,
        backup_dns: List[str]
    ):
        """Configure DNS on macOS."""
        # Set DNS servers for VPN interface
        dns_servers = " ".join(vpn_dns_servers + backup_dns)
        proc = await asyncio.create_subprocess_exec(
            "sudo", "networksetup", "-setdnsservers", interface, *dns_servers.split(),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await proc.communicate()

        # Flush DNS cache
        proc = await asyncio.create_subprocess_exec(
            "sudo", "killall", "-HUP", "mDNSResponder",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await proc.communicate()

    async def _restore_dns_macos(self):
        """Restore DNS settings on macOS."""
        for service, dns_servers in self._original_dns.items():
            servers_arg = ["empty"] if not dns_servers else dns_servers
            proc = await asyncio.create_subprocess_exec(
                "sudo", "networksetup", "-setdnsservers", service, *servers_arg,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await proc.communicate()

    async def _configure_dns_linux(self, vpn_dns_servers: List[str], backup_dns: List[str]):
        """Configure DNS on Linux."""
        resolv_conf = "# Generated by VPN Manager\n"
        
        # Add VPN DNS servers
        for dns in vpn_dns_servers:
            resolv_conf += f"nameserver {dns}\n"
        
        # Add backup DNS servers
        for dns in backup_dns:
            resolv_conf += f"nameserver {dns}\n"
        
        # Write new resolv.conf
        with tempfile.NamedTemporaryFile(mode='w') as f:
            f.write(resolv_conf)
            f.flush()
            
            proc = await asyncio.create_subprocess_exec(
                "sudo", "cp", f.name, "/etc/resolv.conf",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await proc.communicate()

    async def _restore_dns_linux(self):
        """Restore DNS settings on Linux."""
        if self._original_resolv_conf:
            with tempfile.NamedTemporaryFile(mode='w') as f:
                f.write(self._original_resolv_conf)
                f.flush()
                
                proc = await asyncio.create_subprocess_exec(
                    "sudo", "cp", f.name, "/etc/resolv.conf",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await proc.communicate()

class SplitTunnel:
    """Manages split tunneling configuration."""
    
    def __init__(self):
        self.system = platform.system().lower()
        self._routes: List[str] = []
        self._lock = asyncio.Lock()

    async def add_route(
        self,
        subnet: str,
        gateway: Optional[str] = None,
        interface: Optional[str] = None
    ):
        """
        Add a route for split tunneling.
        
        Args:
            subnet: Subnet in CIDR notation (e.g. "192.168.1.0/24")
            gateway: Gateway IP address (optional)
            interface: Network interface (optional)
        """
        async with self._lock:
            try:
                if self.system == "darwin":
                    await self._add_route_macos(subnet, gateway, interface)
                elif self.system == "linux":
                    await self._add_route_linux(subnet, gateway, interface)
                else:
                    raise NotImplementedError(f"Split tunneling not implemented for {self.system}")
                
                self._routes.append(subnet)
                logger.info(f"Added split tunnel route for {subnet}")
                
            except Exception as e:
                logger.error(f"Failed to add route: {e}")
                raise

    async def remove_route(self, subnet: str):
        """Remove a split tunneling route."""
        if subnet not in self._routes:
            return

        async with self._lock:
            try:
                if self.system == "darwin":
                    await self._remove_route_macos(subnet)
                elif self.system == "linux":
                    await self._remove_route_linux(subnet)
                
                self._routes.remove(subnet)
                logger.info(f"Removed split tunnel route for {subnet}")
                
            except Exception as e:
                logger.error(f"Failed to remove route: {e}")
                raise

    async def _add_route_macos(
        self,
        subnet: str,
        gateway: Optional[str] = None,
        interface: Optional[str] = None
    ):
        """Add route on macOS."""
        cmd = ["sudo", "route", "add", "-net", subnet]
        if gateway:
            cmd.extend([gateway])
        if interface:
            cmd.extend(["-interface", interface])
        
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await proc.communicate()

    async def _remove_route_macos(self, subnet: str):
        """Remove route on macOS."""
        proc = await asyncio.create_subprocess_exec(
            "sudo", "route", "delete", "-net", subnet,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await proc.communicate()

    async def _add_route_linux(
        self,
        subnet: str,
        gateway: Optional[str] = None,
        interface: Optional[str] = None
    ):
        """Add route on Linux."""
        cmd = ["sudo", "ip", "route", "add", subnet]
        if gateway:
            cmd.extend(["via", gateway])
        if interface:
            cmd.extend(["dev", interface])
        
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await proc.communicate()

    async def _remove_route_linux(self, subnet: str):
        """Remove route on Linux."""
        proc = await asyncio.create_subprocess_exec(
            "sudo", "ip", "route", "del", subnet,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await proc.communicate() 