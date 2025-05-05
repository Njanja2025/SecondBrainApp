import asyncio
import logging
import subprocess
from typing import List, Optional
import platform

logger = logging.getLogger(__name__)

class KillSwitch:
    """VPN kill switch implementation."""
    
    def __init__(self):
        self.system = platform.system().lower()
        self._original_rules: List[str] = []
        self._lock = asyncio.Lock()
        self._enabled = False

    async def enable(self, vpn_interface: str, allowed_ips: Optional[List[str]] = None):
        """
        Enable kill switch to prevent traffic leaks.
        
        Args:
            vpn_interface: Name of the VPN interface (tun0, tap0, etc.)
            allowed_ips: List of IPs to allow (VPN servers, DNS, etc.)
        """
        if self._enabled:
            return

        async with self._lock:
            try:
                if self.system == "darwin":  # macOS
                    await self._enable_macos(vpn_interface, allowed_ips)
                elif self.system == "linux":
                    await self._enable_linux(vpn_interface, allowed_ips)
                else:
                    raise NotImplementedError(f"Kill switch not implemented for {self.system}")
                
                self._enabled = True
                logger.info("Kill switch enabled")
                
            except Exception as e:
                logger.error(f"Failed to enable kill switch: {e}")
                await self.disable()  # Cleanup on failure
                raise

    async def disable(self):
        """Disable kill switch and restore original firewall rules."""
        if not self._enabled:
            return

        async with self._lock:
            try:
                if self.system == "darwin":
                    await self._disable_macos()
                elif self.system == "linux":
                    await self._disable_linux()
                
                self._enabled = False
                logger.info("Kill switch disabled")
                
            except Exception as e:
                logger.error(f"Failed to disable kill switch: {e}")
                raise

    async def _enable_macos(self, vpn_interface: str, allowed_ips: Optional[List[str]] = None):
        """Enable kill switch on macOS using pf firewall."""
        # Backup current rules
        proc = await asyncio.create_subprocess_exec(
            "sudo", "pfctl", "-sr",
            stdout=asyncio.subprocess.PIPE
        )
        stdout, _ = await proc.communicate()
        self._original_rules = stdout.decode().splitlines()

        # Create new ruleset
        rules = [
            "block all",
            f"pass on {vpn_interface}",
            "pass on lo0"  # Allow loopback
        ]

        if allowed_ips:
            for ip in allowed_ips:
                rules.append(f"pass out to {ip}")

        # Write rules to temporary file
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w') as f:
            f.write("\n".join(rules))
            f.flush()

            # Load new rules
            proc = await asyncio.create_subprocess_exec(
                "sudo", "pfctl", "-f", f.name,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await proc.communicate()

        # Enable firewall
        proc = await asyncio.create_subprocess_exec(
            "sudo", "pfctl", "-e",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await proc.communicate()

    async def _disable_macos(self):
        """Disable kill switch on macOS."""
        if self._original_rules:
            # Restore original rules
            with tempfile.NamedTemporaryFile(mode='w') as f:
                f.write("\n".join(self._original_rules))
                f.flush()

                proc = await asyncio.create_subprocess_exec(
                    "sudo", "pfctl", "-f", f.name,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await proc.communicate()

        # Disable firewall
        proc = await asyncio.create_subprocess_exec(
            "sudo", "pfctl", "-d",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await proc.communicate()

    async def _enable_linux(self, vpn_interface: str, allowed_ips: Optional[List[str]] = None):
        """Enable kill switch on Linux using iptables."""
        # Backup current rules
        proc = await asyncio.create_subprocess_exec(
            "sudo", "iptables-save",
            stdout=asyncio.subprocess.PIPE
        )
        stdout, _ = await proc.communicate()
        self._original_rules = stdout.decode().splitlines()

        # Clear existing rules
        await self._run_iptables(["-F"])
        await self._run_iptables(["-X"])
        await self._run_iptables(["-P", "INPUT", "DROP"])
        await self._run_iptables(["-P", "FORWARD", "DROP"])
        await self._run_iptables(["-P", "OUTPUT", "DROP"])

        # Allow VPN interface
        await self._run_iptables(["-A", "INPUT", "-i", vpn_interface, "-j", "ACCEPT"])
        await self._run_iptables(["-A", "OUTPUT", "-o", vpn_interface, "-j", "ACCEPT"])

        # Allow loopback
        await self._run_iptables(["-A", "INPUT", "-i", "lo", "-j", "ACCEPT"])
        await self._run_iptables(["-A", "OUTPUT", "-o", "lo", "-j", "ACCEPT"])

        # Allow specific IPs
        if allowed_ips:
            for ip in allowed_ips:
                await self._run_iptables(["-A", "OUTPUT", "-d", ip, "-j", "ACCEPT"])

    async def _disable_linux(self):
        """Disable kill switch on Linux."""
        if self._original_rules:
            # Restore original rules
            with tempfile.NamedTemporaryFile(mode='w') as f:
                f.write("\n".join(self._original_rules))
                f.flush()

                proc = await asyncio.create_subprocess_exec(
                    "sudo", "iptables-restore",
                    stdin=open(f.name),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await proc.communicate()

    async def _run_iptables(self, args: List[str]):
        """Run iptables command."""
        proc = await asyncio.create_subprocess_exec(
            "sudo", "iptables", *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await proc.communicate() 