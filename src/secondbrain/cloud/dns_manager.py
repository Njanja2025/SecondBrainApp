"""
DNS management module for Samantha's domain configuration.
"""

import logging
import asyncio
from typing import Dict, List, Optional
import json
from pathlib import Path
import requests
from datetime import datetime
import socket
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)


class DNSManager:
    """Manages DNS configuration and updates."""

    def __init__(
        self, config_path: str = "config/dns_config.json", cache_dir: str = "cache/dns"
    ):
        self.config_path = Path(config_path)
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Load configuration
        self.config = self._load_config()

        # DNS cache
        self.dns_cache = {}
        self.last_check = {}
        self.check_interval = 300  # 5 minutes

    def _load_config(self) -> Dict:
        """Load DNS configuration."""
        try:
            if self.config_path.exists():
                with open(self.config_path) as f:
                    return json.load(f)
            return {
                "namecheap": {
                    "enabled": False,
                    "check_frequency": 3600,  # 1 hour
                    "auto_update": True,
                },
                "domains": [],
            }
        except Exception as e:
            logger.error(f"Failed to load DNS config: {e}")
            return {}

    async def update_namecheap_dns(
        self,
        api_user: str,
        api_key: str,
        domain: str,
        subdomain: str,
        ip_address: str,
        record_type: str = "A",
        ttl: int = 1800,
    ) -> bool:
        """
        Update Namecheap DNS records with enhanced error handling.

        Args:
            api_user: Namecheap API username
            api_key: Namecheap API key
            domain: Domain name
            subdomain: Subdomain to update
            ip_address: IP address to point to
            record_type: DNS record type
            ttl: Time to live in seconds

        Returns:
            bool: True if update successful
        """
        try:
            # Validate inputs
            if not all([api_user, api_key, domain, subdomain, ip_address]):
                raise ValueError("Missing required parameters")

            # Validate domain format
            domain_parts = domain.split(".")
            if len(domain_parts) != 2:
                raise ValueError("Domain must be in format: example.com")

            sld, tld = domain_parts

            # Validate IP address
            try:
                socket.inet_aton(ip_address)
            except socket.error:
                raise ValueError("Invalid IP address")

            # Prepare API request
            url = "https://api.namecheap.com/xml.response"
            params = {
                "ApiUser": api_user,
                "ApiKey": api_key,
                "UserName": api_user,
                "Command": "namecheap.domains.dns.setHosts",
                "ClientIp": ip_address,
                "SLD": sld,
                "TLD": tld,
                "HostName1": subdomain,
                "RecordType1": record_type,
                "Address1": ip_address,
                "TTL1": str(ttl),
            }

            # Make API request with retry
            max_retries = 3
            retry_delay = 1

            for attempt in range(max_retries):
                try:
                    response = requests.get(url, params=params, timeout=10)
                    break
                except requests.exceptions.RequestException as e:
                    if attempt == max_retries - 1:
                        raise
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2

            # Parse XML response
            if response.status_code != 200:
                raise Exception(f"API request failed: {response.status_code}")

            root = ET.fromstring(response.text)
            status = root.find(".//Status")

            if status is None or status.text != "OK":
                errors = root.findall(".//Error")
                error_msgs = [e.text for e in errors if e.text]
                raise Exception(f"API errors: {', '.join(error_msgs)}")

            # Update cache
            self._update_dns_cache(domain, subdomain, ip_address)

            logger.info(f"Successfully updated DNS for {subdomain}.{domain}")
            return True

        except Exception as e:
            logger.error(f"Failed to update Namecheap DNS: {e}")
            return False

    async def verify_dns(self, domain: str, subdomain: str, expected_ip: str) -> bool:
        """
        Verify DNS resolution matches expected IP.

        Args:
            domain: Domain name
            subdomain: Subdomain to check
            expected_ip: Expected IP address

        Returns:
            bool: True if DNS matches expected IP
        """
        try:
            fqdn = f"{subdomain}.{domain}"

            # Check cache first
            if self._check_dns_cache(domain, subdomain, expected_ip):
                return True

            # Resolve DNS
            resolved_ips = await self._resolve_dns(fqdn)

            # Update cache
            self._update_dns_cache(domain, subdomain, resolved_ips[0])

            return expected_ip in resolved_ips

        except Exception as e:
            logger.error(f"Failed to verify DNS: {e}")
            return False

    async def _resolve_dns(self, hostname: str) -> List[str]:
        """Resolve DNS with timeout and retries."""
        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, socket.gethostbyname_ex, hostname)[
                2
            ]
        except socket.gaierror as e:
            logger.error(f"DNS resolution failed: {e}")
            return []

    def _check_dns_cache(self, domain: str, subdomain: str, ip: str) -> bool:
        """Check if DNS cache is valid."""
        cache_key = f"{subdomain}.{domain}"

        if (
            cache_key in self.dns_cache
            and cache_key in self.last_check
            and (datetime.now().timestamp() - self.last_check[cache_key])
            < self.check_interval
        ):
            return self.dns_cache[cache_key] == ip

        return False

    def _update_dns_cache(self, domain: str, subdomain: str, ip: str):
        """Update DNS cache."""
        cache_key = f"{subdomain}.{domain}"
        self.dns_cache[cache_key] = ip
        self.last_check[cache_key] = datetime.now().timestamp()

        # Save cache to file
        try:
            cache_file = self.cache_dir / "dns_cache.json"
            cache_data = {
                "cache": self.dns_cache,
                "last_check": self.last_check,
                "updated": datetime.now().isoformat(),
            }
            with open(cache_file, "w") as f:
                json.dump(cache_data, f, indent=4)
        except Exception as e:
            logger.error(f"Failed to save DNS cache: {e}")

    def save_config(self):
        """Save current configuration."""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, "w") as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            logger.error(f"Failed to save DNS config: {e}")

    def add_domain(self, domain: str, subdomains: List[str], auto_update: bool = True):
        """Add domain to configuration."""
        if "domains" not in self.config:
            self.config["domains"] = []

        self.config["domains"].append(
            {
                "domain": domain,
                "subdomains": subdomains,
                "auto_update": auto_update,
                "added": datetime.now().isoformat(),
            }
        )

        self.save_config()

    def remove_domain(self, domain: str):
        """Remove domain from configuration."""
        if "domains" in self.config:
            self.config["domains"] = [
                d for d in self.config["domains"] if d["domain"] != domain
            ]
            self.save_config()
