import asyncio
import logging
import os
import subprocess
import time
from typing import Optional, Dict
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class ConnectionStats:
    """VPN connection statistics."""
    bytes_received: int = 0
    bytes_sent: int = 0
    connected_since: Optional[datetime] = None
    current_server: Optional[str] = None
    last_error: Optional[str] = None

class OpenVPNConnection:
    """Handles OpenVPN connection management."""
    
    def __init__(
        self,
        config_path: str,
        auth_file: Optional[str] = None,
        management_port: int = 7505
    ):
        """
        Initialize OpenVPN connection handler.
        
        Args:
            config_path: Path to OpenVPN config file (.ovpn)
            auth_file: Path to authentication file (optional)
            management_port: Port for OpenVPN management interface
        """
        self.config_path = Path(config_path)
        self.auth_file = Path(auth_file) if auth_file else None
        self.management_port = management_port
        self.process: Optional[subprocess.Popen] = None
        self.stats = ConnectionStats()
        self._monitor_task: Optional[asyncio.Task] = None
        self._reader: Optional[asyncio.StreamReader] = None
        self._writer: Optional[asyncio.StreamWriter] = None
        self._lock = asyncio.Lock()
        
    async def connect(self):
        """Establish VPN connection using OpenVPN."""
        if self.process and self.process.poll() is None:
            logger.warning("OpenVPN process already running")
            return

        cmd = [
            "sudo", "openvpn",
            "--config", str(self.config_path),
            "--management", "127.0.0.1", str(self.management_port),
            "--daemon"  # Run in background
        ]

        if self.auth_file:
            cmd.extend(["--auth-user-pass", str(self.auth_file)])

        try:
            # Start OpenVPN process
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Wait briefly to check if process started successfully
            await asyncio.sleep(2)
            if process.returncode is not None:
                _, stderr = await process.communicate()
                raise RuntimeError(f"Failed to start OpenVPN: {stderr.decode()}")
            
            self.process = process
            logger.info("OpenVPN process started successfully")
            
            # Connect to management interface
            await self._connect_management()
            
            # Start monitoring
            self._monitor_task = asyncio.create_task(self._monitor_connection())
            
            # Wait for connection to be established
            await self._wait_for_connection()
            
        except Exception as e:
            self.stats.last_error = str(e)
            logger.error(f"Failed to establish VPN connection: {e}")
            await self.disconnect()  # Cleanup on failure
            raise

    async def disconnect(self):
        """Terminate VPN connection."""
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
            self._monitor_task = None

        if self._writer:
            self._writer.close()
            await self._writer.wait_closed()
            self._writer = None
            self._reader = None

        if self.process:
            try:
                # Send SIGTERM to OpenVPN process
                self.process.terminate()
                try:
                    await asyncio.wait_for(self.process.wait(), timeout=5.0)
                except asyncio.TimeoutError:
                    logger.warning("OpenVPN process didn't terminate, forcing...")
                    self.process.kill()
                    await self.process.wait()
                
                # Cleanup management interface
                await self._cleanup_management()
                
                # Reset stats
                self.stats = ConnectionStats()
                
                logger.info("VPN connection terminated successfully")
            except Exception as e:
                self.stats.last_error = str(e)
                logger.error(f"Error during VPN disconnection: {e}")
                raise
            finally:
                self.process = None

    async def _connect_management(self):
        """Connect to OpenVPN management interface."""
        try:
            self._reader, self._writer = await asyncio.open_connection(
                '127.0.0.1',
                self.management_port
            )
            # Read welcome message
            await self._reader.readline()
        except Exception as e:
            logger.error(f"Failed to connect to management interface: {e}")
            raise

    async def _monitor_connection(self):
        """Monitor connection status and update statistics."""
        while True:
            try:
                if not self._writer or self._writer.is_closing():
                    return

                # Request status update
                self._writer.write(b"status\n")
                await self._writer.drain()

                # Read status response
                while True:
                    line = await self._reader.readline()
                    if not line:
                        break
                    
                    line = line.decode().strip()
                    if line == "END":
                        break
                        
                    # Parse status information
                    if line.startswith("TCP/UDP read bytes"):
                        self.stats.bytes_received = int(line.split(",")[1])
                    elif line.startswith("TCP/UDP write bytes"):
                        self.stats.bytes_sent = int(line.split(",")[1])
                    elif line.startswith("Connected since"):
                        self.stats.connected_since = datetime.fromtimestamp(
                            int(line.split(",")[1])
                        )

                await asyncio.sleep(5)  # Update every 5 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error monitoring connection: {e}")
                await asyncio.sleep(5)  # Retry after error

    async def _wait_for_connection(self, timeout: int = 30):
        """Wait for VPN connection to be established."""
        start_time = asyncio.get_event_loop().time()
        while (asyncio.get_event_loop().time() - start_time) < timeout:
            # Check if tun/tap interface is up
            if await self._check_vpn_interface():
                logger.info("VPN interface detected, connection established")
                return
            await asyncio.sleep(1)
        raise TimeoutError("VPN connection timed out")

    async def _check_vpn_interface(self) -> bool:
        """Check if VPN interface is up."""
        try:
            proc = await asyncio.create_subprocess_exec(
                "ifconfig",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await proc.communicate()
            return b"tun0" in stdout or b"tap0" in stdout
        except Exception:
            return False

    async def _cleanup_management(self):
        """Cleanup OpenVPN management interface."""
        try:
            # Kill any remaining management interface processes
            cmd = f"sudo lsof -ti tcp:{self.management_port} | xargs -r sudo kill"
            proc = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await proc.communicate()
        except Exception as e:
            logger.warning(f"Error cleaning up management interface: {e}")

    @property
    def is_connected(self) -> bool:
        """Check if VPN is currently connected."""
        return (
            self.process is not None
            and self.process.poll() is None
            and self.stats.connected_since is not None
        )

    @property
    def connection_time(self) -> Optional[float]:
        """Get current connection duration in seconds."""
        if not self.stats.connected_since:
            return None
        return (datetime.now() - self.stats.connected_since).total_seconds()

def create_vpn_manager(config_path: str, auth_file: Optional[str] = None) -> 'VPNManager':
    """
    Create a VPNManager instance configured with OpenVPN.
    
    Args:
        config_path: Path to OpenVPN config file (.ovpn)
        auth_file: Path to authentication file (optional)
    
    Returns:
        VPNManager instance configured with OpenVPN
    """
    from .vpn_manager import VPNManager
    
    vpn = OpenVPNConnection(config_path, auth_file)
    return VPNManager(
        connect_vpn_func=vpn.connect,
        disconnect_vpn_func=vpn.disconnect
    ) 