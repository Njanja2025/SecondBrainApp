"""
Secure communications module for encrypted data transfer.
"""

import asyncio
import json
import logging
import uuid
from typing import Dict, Optional, Any, Callable, Awaitable
from .data_encryption import DataEncryption

logger = logging.getLogger(__name__)


class SecureComms:
    def __init__(self, encryption: DataEncryption):
        """Initialize secure communications with encryption system."""
        self.encryption = encryption
        self.channels: Dict[str, asyncio.Queue] = {}
        self.handlers: Dict[str, Callable[[Dict[str, Any]], Awaitable[None]]] = {}
        self._running = False
        self._tasks: Dict[str, asyncio.Task] = {}

    async def create_channel(
        self,
        name: str,
        handler: Optional[Callable[[Dict[str, Any]], Awaitable[None]]] = None,
    ) -> str:
        """Create a new secure communication channel."""
        channel_id = str(uuid.uuid4())
        self.channels[channel_id] = asyncio.Queue()

        if handler:
            self.handlers[channel_id] = handler
            self._tasks[channel_id] = asyncio.create_task(
                self._handle_messages(channel_id)
            )

        logger.info(f"Created secure channel: {name} ({channel_id})")
        return channel_id

    async def close_channel(self, channel_id: str):
        """Close a secure communication channel."""
        if channel_id in self._tasks:
            self._tasks[channel_id].cancel()
            try:
                await self._tasks[channel_id]
            except asyncio.CancelledError:
                pass
            del self._tasks[channel_id]

        if channel_id in self.handlers:
            del self.handlers[channel_id]

        if channel_id in self.channels:
            del self.channels[channel_id]

        logger.info(f"Closed secure channel: {channel_id}")

    async def send_message(
        self, channel_id: str, message: Dict[str, Any], encrypt: bool = True
    ) -> bool:
        """Send an encrypted message on a channel."""
        try:
            if channel_id not in self.channels:
                raise ValueError(f"Channel {channel_id} not found")

            # Prepare message
            message_data = {
                "id": str(uuid.uuid4()),
                "timestamp": asyncio.get_event_loop().time(),
                "data": message,
            }

            # Encrypt if requested
            if encrypt:
                message_bytes = json.dumps(message_data).encode()
                encrypted_data = self.encryption.encrypt_symmetric(message_bytes)
                message_data = {"encrypted": True, "data": encrypted_data}

            # Send message
            await self.channels[channel_id].put(message_data)
            return True

        except Exception as e:
            logger.error(f"Failed to send message: {str(e)}")
            return False

    async def receive_message(
        self, channel_id: str, timeout: Optional[float] = None
    ) -> Optional[Dict[str, Any]]:
        """Receive and decrypt a message from a channel."""
        try:
            if channel_id not in self.channels:
                raise ValueError(f"Channel {channel_id} not found")

            # Wait for message
            try:
                if timeout:
                    message_data = await asyncio.wait_for(
                        self.channels[channel_id].get(), timeout=timeout
                    )
                else:
                    message_data = await self.channels[channel_id].get()
            except asyncio.TimeoutError:
                return None

            # Decrypt if necessary
            if isinstance(message_data, dict) and message_data.get("encrypted"):
                decrypted_bytes = self.encryption.decrypt_symmetric(
                    message_data["data"]
                )
                message_data = json.loads(decrypted_bytes.decode())

            return message_data

        except Exception as e:
            logger.error(f"Failed to receive message: {str(e)}")
            return None

    async def broadcast_message(
        self, message: Dict[str, Any], encrypt: bool = True
    ) -> bool:
        """Broadcast a message to all channels."""
        success = True
        for channel_id in self.channels:
            if not await self.send_message(channel_id, message, encrypt):
                success = False
        return success

    async def _handle_messages(self, channel_id: str):
        """Handle incoming messages on a channel."""
        try:
            while True:
                message = await self.receive_message(channel_id)
                if message and channel_id in self.handlers:
                    try:
                        await self.handlers[channel_id](message)
                    except Exception as e:
                        logger.error(f"Error in message handler: {str(e)}")

        except asyncio.CancelledError:
            logger.info(f"Message handler cancelled for channel: {channel_id}")
            raise
        except Exception as e:
            logger.error(f"Error in message handling loop: {str(e)}")
            raise

    async def start(self):
        """Start secure communications system."""
        if self._running:
            return

        self._running = True
        logger.info("Secure communications system started")

    async def stop(self):
        """Stop secure communications system."""
        if not self._running:
            return

        self._running = False

        # Close all channels
        channel_ids = list(self.channels.keys())
        for channel_id in channel_ids:
            await self.close_channel(channel_id)

        logger.info("Secure communications system stopped")
