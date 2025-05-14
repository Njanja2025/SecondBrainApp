import os
import json
import logging
from pathlib import Path
from typing import Optional, Dict, List
from dataclasses import dataclass, asdict
import keyring
import yaml
from .vpn_location import ServerLocation, LocationManager, ConnectionQualityMonitor
from .vpn_dns import DNSManager
from .vpn_split_tunnel import SplitTunnel

logger = logging.getLogger(__name__)


@dataclass
class VPNCredentials:
    """VPN authentication credentials."""

    username: str
    password: str


@dataclass
class VPNProfile:
    """VPN connection profile configuration."""

    name: str
    config_path: Path
    server: str
    port: int
    protocol: str  # udp/tcp
    credentials_id: Optional[str] = None
    location: Optional[ServerLocation] = None
    backup_servers: List[str] = None
    kill_switch_enabled: bool = False
    allowed_ips: List[str] = None
    dns_servers: List[str] = None  # VPN provider's DNS servers
    split_tunnel_subnets: List[str] = None  # Subnets for split tunneling

    @property
    def credentials(self) -> Optional[VPNCredentials]:
        """Retrieve credentials from secure storage."""
        if not self.credentials_id:
            return None

        try:
            creds_json = keyring.get_password("vpn_manager", self.credentials_id)
            if creds_json:
                creds_dict = json.loads(creds_json)
                return VPNCredentials(**creds_dict)
        except Exception as e:
            logger.error(f"Failed to retrieve credentials: {e}")
        return None


class VPNConfigManager:
    """Manages VPN configurations and credentials."""

    def __init__(self, config_dir: str = "~/.secondbrain/vpn"):
        self.config_dir = Path(config_dir).expanduser()
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.profiles_file = self.config_dir / "profiles.yaml"
        self.profiles: Dict[str, VPNProfile] = {}
        self.location_manager = LocationManager()
        self.quality_monitor = ConnectionQualityMonitor()
        self.dns_manager = DNSManager()
        self.split_tunnel = SplitTunnel()
        self._load_profiles()

    def _load_profiles(self):
        """Load VPN profiles from config file."""
        if not self.profiles_file.exists():
            return

        try:
            with open(self.profiles_file) as f:
                data = yaml.safe_load(f)
                if not data:
                    return

                for name, profile_data in data.items():
                    location_data = profile_data.get("location")
                    location = None
                    if location_data:
                        location = ServerLocation(**location_data)

                    self.profiles[name] = VPNProfile(
                        name=name,
                        config_path=Path(profile_data["config_path"]),
                        server=profile_data["server"],
                        port=profile_data["port"],
                        protocol=profile_data["protocol"],
                        credentials_id=profile_data.get("credentials_id"),
                        location=location,
                        backup_servers=profile_data.get("backup_servers", []),
                        kill_switch_enabled=profile_data.get(
                            "kill_switch_enabled", False
                        ),
                        allowed_ips=profile_data.get("allowed_ips", []),
                        dns_servers=profile_data.get("dns_servers", []),
                        split_tunnel_subnets=profile_data.get(
                            "split_tunnel_subnets", []
                        ),
                    )
        except Exception as e:
            logger.error(f"Failed to load VPN profiles: {e}")

    def save_profile(
        self,
        name: str,
        config_path: str,
        server: str,
        port: int,
        protocol: str = "udp",
        username: Optional[str] = None,
        password: Optional[str] = None,
        backup_servers: Optional[List[str]] = None,
        kill_switch_enabled: bool = False,
        allowed_ips: Optional[List[str]] = None,
        dns_servers: Optional[List[str]] = None,
        split_tunnel_subnets: Optional[List[str]] = None,
    ) -> VPNProfile:
        """
        Save a new VPN profile with optional credentials.

        Args:
            name: Profile name
            config_path: Path to .ovpn config file
            server: VPN server hostname/IP
            port: VPN server port
            protocol: Connection protocol (udp/tcp)
            username: Optional VPN username
            password: Optional VPN password
            backup_servers: List of backup VPN servers
            kill_switch_enabled: Whether to enable kill switch
            allowed_ips: IPs to allow when kill switch is active
            dns_servers: List of VPN provider's DNS servers
            split_tunnel_subnets: List of subnets for split tunneling
        """
        # Create profile
        profile = VPNProfile(
            name=name,
            config_path=Path(config_path),
            server=server,
            port=port,
            protocol=protocol,
            backup_servers=backup_servers or [],
            kill_switch_enabled=kill_switch_enabled,
            allowed_ips=allowed_ips or [],
            dns_servers=dns_servers or [],
            split_tunnel_subnets=split_tunnel_subnets or [],
        )

        # Store credentials if provided
        if username and password:
            creds_id = f"vpn_profile_{name}"
            creds = VPNCredentials(username=username, password=password)
            keyring.set_password(
                "vpn_manager",
                creds_id,
                json.dumps({"username": username, "password": password}),
            )
            profile.credentials_id = creds_id

        # Save profile
        self.profiles[name] = profile
        self._save_profiles()
        return profile

    def _save_profiles(self):
        """Save profiles to config file."""
        data = {}
        for name, profile in self.profiles.items():
            profile_data = {
                "config_path": str(profile.config_path),
                "server": profile.server,
                "port": profile.port,
                "protocol": profile.protocol,
                "backup_servers": profile.backup_servers,
                "kill_switch_enabled": profile.kill_switch_enabled,
                "allowed_ips": profile.allowed_ips,
                "dns_servers": profile.dns_servers,
                "split_tunnel_subnets": profile.split_tunnel_subnets,
            }

            if profile.credentials_id:
                profile_data["credentials_id"] = profile.credentials_id

            if profile.location:
                profile_data["location"] = asdict(profile.location)

            data[name] = profile_data

        with open(self.profiles_file, "w") as f:
            yaml.safe_dump(data, f)

    async def update_server_locations(self):
        """Update location information for all servers."""
        from .vpn_location import GeoIPResolver

        resolver = GeoIPResolver()

        for profile in self.profiles.values():
            # Update main server
            if not profile.location:
                location_data = await resolver.get_server_location(profile.server)
                if location_data:
                    profile.location = ServerLocation(**location_data)
                    await self.location_manager.add_server(
                        profile.server, **location_data
                    )

            # Update backup servers
            for server in profile.backup_servers:
                if server not in self.location_manager.locations:
                    location_data = await resolver.get_server_location(server)
                    if location_data:
                        await self.location_manager.add_server(server, **location_data)

        self._save_profiles()

    async def find_best_server(self, profile: VPNProfile) -> Optional[str]:
        """Find the best server for a profile."""
        # Test all servers
        await self.location_manager.test_server(profile.server, profile.port)
        for server in profile.backup_servers:
            await self.location_manager.test_server(server, profile.port)

        return await self.location_manager.find_best_server()

    def get_profile(self, name: str) -> Optional[VPNProfile]:
        """Get VPN profile by name."""
        return self.profiles.get(name)

    def list_profiles(self) -> Dict[str, VPNProfile]:
        """List all available VPN profiles."""
        return self.profiles.copy()

    def remove_profile(self, name: str):
        """Remove a VPN profile and its credentials."""
        if name in self.profiles:
            profile = self.profiles[name]
            if profile.credentials_id:
                try:
                    keyring.delete_password("vpn_manager", profile.credentials_id)
                except Exception as e:
                    logger.warning(f"Failed to delete credentials: {e}")

            del self.profiles[name]
            self._save_profiles()

    def create_auth_file(self, profile: VPNProfile) -> Optional[Path]:
        """Create temporary auth file for OpenVPN."""
        if not profile.credentials:
            return None

        auth_file = self.config_dir / f"{profile.name}_auth.txt"
        try:
            with open(auth_file, "w") as f:
                f.write(
                    f"{profile.credentials.username}\n{profile.credentials.password}\n"
                )
            return auth_file
        except Exception as e:
            logger.error(f"Failed to create auth file: {e}")
            return None

    def cleanup_auth_file(self, profile: VPNProfile):
        """Remove temporary auth file."""
        auth_file = self.config_dir / f"{profile.name}_auth.txt"
        try:
            if auth_file.exists():
                os.remove(auth_file)
        except Exception as e:
            logger.warning(f"Failed to remove auth file: {e}")


async def setup_vpn_connection(profile_name: str) -> Optional["VPNManager"]:
    """
    Set up VPN connection from a profile.

    Args:
        profile_name: Name of the VPN profile to use

    Returns:
        Configured VPNManager instance or None if setup fails
    """
    from .vpn_connection import create_vpn_manager

    config_manager = VPNConfigManager()
    profile = config_manager.get_profile(profile_name)

    if not profile:
        logger.error(f"VPN profile '{profile_name}' not found")
        return None

    # Update server locations if needed
    if not profile.location:
        await config_manager.update_server_locations()

    # Find best server if there are backups
    if profile.backup_servers:
        best_server = await config_manager.find_best_server(profile)
        if best_server and best_server != profile.server:
            logger.info(f"Switching to better server: {best_server}")
            profile.server = best_server

    # Create auth file if credentials exist
    auth_file = config_manager.create_auth_file(profile)

    try:
        vpn_manager = create_vpn_manager(
            config_path=str(profile.config_path),
            auth_file=str(auth_file) if auth_file else None,
        )

        # Configure kill switch if enabled
        if profile.kill_switch_enabled:
            from .vpn_killswitch import KillSwitch

            kill_switch = KillSwitch()
            await kill_switch.enable("tun0", profile.allowed_ips)

        # Configure DNS protection
        if profile.dns_servers:
            await config_manager.dns_manager.configure_dns(profile.dns_servers, "tun0")

        # Configure split tunneling
        if profile.split_tunnel_subnets:
            for subnet in profile.split_tunnel_subnets:
                await config_manager.split_tunnel.add_route(subnet, interface="tun0")

        return vpn_manager
    except Exception as e:
        logger.error(f"Failed to create VPN manager: {e}")
        if auth_file:
            config_manager.cleanup_auth_file(profile)
        return None
