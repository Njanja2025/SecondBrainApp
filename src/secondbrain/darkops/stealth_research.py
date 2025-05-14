"""
Stealth research module for secure information gathering.
"""

import asyncio
import logging
import json
import os
from typing import Dict, List, Optional, Any
from pathlib import Path
import aiohttp
import aiofiles
from fake_useragent import UserAgent
from src.secondbrain.darkops.data_encryption import DataEncryption

logger = logging.getLogger(__name__)


class StealthResearch:
    def __init__(self, encryption: DataEncryption, storage_path: Optional[str] = None):
        """Initialize stealth research system."""
        self.encryption = encryption
        self.storage_path = Path(
            storage_path or Path.home() / ".secondbrain" / "research"
        )
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self.user_agent = UserAgent()
        self._session: Optional[aiohttp.ClientSession] = None
        self._running = False

    async def start(self):
        """Start stealth research system."""
        if self._running:
            return

        self._session = aiohttp.ClientSession(
            headers={"User-Agent": self.user_agent.random}
        )
        self._running = True
        os.system('say -v "Samantha" "Stealth research system is now active"')
        logger.info("Stealth research system started")

    async def stop(self):
        """Stop stealth research system."""
        if not self._running:
            return

        if self._session:
            await self._session.close()
            self._session = None

        self._running = False
        logger.info("Stealth research system stopped")

    async def gather_information(
        self,
        urls: List[str],
        headers: Optional[Dict[str, str]] = None,
        delay: float = 1.0,
    ) -> List[Dict[str, Any]]:
        """Gather information from multiple sources."""
        if not self._running or not self._session:
            raise RuntimeError("Stealth research system not started")

        results = []
        for url in urls:
            # Add random delay between requests
            await asyncio.sleep(delay)

            try:
                # Rotate user agent
                current_headers = {"User-Agent": self.user_agent.random}
                if headers:
                    current_headers.update(headers)

                async with self._session.get(url, headers=current_headers) as response:
                    if response.status == 200:
                        content = await response.text()
                        result = {
                            "url": url,
                            "status": response.status,
                            "content": content,
                            "headers": dict(response.headers),
                        }
                        results.append(result)

                        # Store encrypted result
                        await self._store_result(url, result)
                    else:
                        logger.warning(f"Failed to fetch {url}: {response.status}")

            except Exception as e:
                logger.error(f"Error gathering information from {url}: {str(e)}")

        return results

    async def _store_result(self, url: str, data: Dict[str, Any]):
        """Store encrypted research results."""
        try:
            # Generate unique filename
            filename = self.storage_path / f"{hash(url)}.enc"

            # Encrypt data
            json_data = json.dumps(data)
            encrypted_data = self.encryption.encrypt_symmetric(json_data)

            # Store encrypted data
            async with aiofiles.open(filename, "wb") as f:
                await f.write(encrypted_data)

        except Exception as e:
            logger.error(f"Failed to store research result: {str(e)}")

    async def load_result(self, url: str) -> Optional[Dict[str, Any]]:
        """Load encrypted research result."""
        try:
            filename = self.storage_path / f"{hash(url)}.enc"

            if not filename.exists():
                return None

            # Load and decrypt data
            async with aiofiles.open(filename, "rb") as f:
                encrypted_data = await f.read()

            decrypted_data = self.encryption.decrypt_symmetric(encrypted_data)
            return json.loads(decrypted_data)

        except Exception as e:
            logger.error(f"Failed to load research result: {str(e)}")
            return None

    async def clear_results(self):
        """Clear all stored research results."""
        try:
            for file in self.storage_path.glob("*.enc"):
                file.unlink()
        except Exception as e:
            logger.error(f"Failed to clear research results: {str(e)}")

    def rotate_identity(self):
        """Rotate research identity (user agent, etc)."""
        if self._session:
            self._session.headers.update({"User-Agent": self.user_agent.random})


if __name__ == "__main__":
    # Initialize and start the system
    from src.secondbrain.darkops.data_encryption import DataEncryption

    encryption = DataEncryption()
    research = StealthResearch(encryption)

    # Run the system
    os.system('say -v "Samantha" "Stealth research system is now active"')
    print("DarkOpsAgent is now running")
