import asyncio
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import aiohttp
import socket
import time
import statistics

logger = logging.getLogger(__name__)


@dataclass
class ServerLocation:
    """VPN server location information."""

    country: str
    city: str
    latitude: float
    longitude: float
    ping: Optional[float] = None
    packet_loss: Optional[float] = None
    last_tested: Optional[float] = None


class LocationManager:
    """Manages VPN server locations and performance metrics."""

    def __init__(self):
        self.locations: Dict[str, ServerLocation] = {}
        self._lock = asyncio.Lock()

    async def add_server(
        self, server: str, country: str, city: str, latitude: float, longitude: float
    ):
        """Add a server location."""
        async with self._lock:
            self.locations[server] = ServerLocation(
                country=country, city=city, latitude=latitude, longitude=longitude
            )

    async def test_server(
        self, server: str, port: int
    ) -> Tuple[Optional[float], Optional[float]]:
        """Test server connection quality."""
        if server not in self.locations:
            return None, None

        total_time = 0
        successful_pings = 0
        num_attempts = 5

        for _ in range(num_attempts):
            try:
                start_time = time.time()
                # Try TCP connection instead of ICMP ping (more reliable through firewalls)
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2.0)
                sock.connect((server, port))
                sock.close()

                ping_time = (time.time() - start_time) * 1000  # Convert to ms
                total_time += ping_time
                successful_pings += 1

                await asyncio.sleep(0.2)  # Don't flood the server

            except Exception:
                pass

        if successful_pings > 0:
            avg_ping = total_time / successful_pings
            packet_loss = (num_attempts - successful_pings) / num_attempts * 100
        else:
            avg_ping = None
            packet_loss = 100.0

        async with self._lock:
            location = self.locations[server]
            location.ping = avg_ping
            location.packet_loss = packet_loss
            location.last_tested = time.time()

        return avg_ping, packet_loss

    async def find_best_server(
        self, max_ping: float = 300.0, max_packet_loss: float = 10.0
    ) -> Optional[str]:
        """Find the best available server based on performance metrics."""
        candidates = []

        async with self._lock:
            for server, location in self.locations.items():
                if (
                    location.ping is not None
                    and location.packet_loss is not None
                    and location.ping <= max_ping
                    and location.packet_loss <= max_packet_loss
                ):
                    # Score based on ping and packet loss
                    score = location.ping * (1 + location.packet_loss / 100)
                    candidates.append((server, score))

        if not candidates:
            return None

        # Return server with lowest score
        return min(candidates, key=lambda x: x[1])[0]

    async def update_all_servers(self, port: int):
        """Update metrics for all servers."""
        tasks = []
        for server in self.locations:
            tasks.append(self.test_server(server, port))
        await asyncio.gather(*tasks)


class GeoIPResolver:
    """Resolves server locations using GeoIP services."""

    async def get_server_location(self, server: str) -> Optional[Dict]:
        """Get server location information."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"https://ipapi.co/{server}/json/") as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "country": data.get("country_name"),
                            "city": data.get("city"),
                            "latitude": float(data.get("latitude", 0)),
                            "longitude": float(data.get("longitude", 0)),
                        }
        except Exception as e:
            logger.error(f"Failed to resolve server location: {e}")
        return None


class ConnectionQualityMonitor:
    """Monitors VPN connection quality."""

    def __init__(
        self, threshold_ping: float = 300.0, threshold_packet_loss: float = 10.0
    ):
        self.threshold_ping = threshold_ping
        self.threshold_packet_loss = threshold_packet_loss
        self.ping_history: List[float] = []
        self.packet_loss_history: List[float] = []
        self._lock = asyncio.Lock()

    async def add_measurement(
        self, ping: Optional[float], packet_loss: Optional[float]
    ):
        """Add a new quality measurement."""
        async with self._lock:
            if ping is not None:
                self.ping_history.append(ping)
                # Keep last 10 measurements
                self.ping_history = self.ping_history[-10:]

            if packet_loss is not None:
                self.packet_loss_history.append(packet_loss)
                self.packet_loss_history = self.packet_loss_history[-10:]

    @property
    def connection_quality(self) -> str:
        """Get current connection quality assessment."""
        if not self.ping_history or not self.packet_loss_history:
            return "unknown"

        avg_ping = statistics.mean(self.ping_history)
        avg_packet_loss = statistics.mean(self.packet_loss_history)

        if avg_ping <= 100 and avg_packet_loss <= 1:
            return "excellent"
        elif avg_ping <= 200 and avg_packet_loss <= 5:
            return "good"
        elif (
            avg_ping <= self.threshold_ping
            and avg_packet_loss <= self.threshold_packet_loss
        ):
            return "fair"
        else:
            return "poor"

    @property
    def should_switch_server(self) -> bool:
        """Determine if server switch is recommended."""
        if not self.ping_history or not self.packet_loss_history:
            return False

        # Check last 3 measurements for consistent poor quality
        recent_ping = self.ping_history[-3:]
        recent_packet_loss = self.packet_loss_history[-3:]

        return (
            len(recent_ping) == 3
            and len(recent_packet_loss) == 3
            and all(p > self.threshold_ping for p in recent_ping)
            or all(pl > self.threshold_packet_loss for pl in recent_packet_loss)
        )
