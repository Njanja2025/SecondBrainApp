from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List
import asyncio
import json
import logging

logger = logging.getLogger(__name__)

class ConnectionManager:
    """Manage WebSocket connections."""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.connection_ids: Dict[WebSocket, str] = {}
        
    async def connect(self, websocket: WebSocket, client_id: str):
        """Accept and store a new WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)
        self.connection_ids[websocket] = client_id
        logger.info(f"Client {client_id} connected. Total connections: {len(self.active_connections)}")
        
    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            client_id = self.connection_ids.pop(websocket, "unknown")
            logger.info(f"Client {client_id} disconnected. Remaining connections: {len(self.active_connections)}")
            
    async def broadcast(self, message: dict):
        """Send a message to all connected clients."""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except WebSocketDisconnect:
                disconnected.append(connection)
            except Exception as e:
                logger.error(f"Error broadcasting to {self.connection_ids.get(connection)}: {e}")
                disconnected.append(connection)
                
        # Clean up disconnected clients
        for connection in disconnected:
            self.disconnect(connection)
            
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send a message to a specific client."""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending personal message to {self.connection_ids.get(websocket)}: {e}")
            self.disconnect(websocket)

class VoiceStreamManager(ConnectionManager):
    """Manage voice stream WebSocket connections."""
    
    async def handle_audio_stream(self, websocket: WebSocket, client_id: str):
        """Handle incoming audio stream."""
        try:
            await self.connect(websocket, client_id)
            
            while True:
                audio_data = await websocket.receive_bytes()
                # Process audio data here
                # For example, send it to the voice recognition system
                
                # Send back any response
                await self.send_personal_message({
                    "type": "audio_processed",
                    "status": "success"
                }, websocket)
                
        except WebSocketDisconnect:
            self.disconnect(websocket)
        except Exception as e:
            logger.error(f"Error in audio stream handler: {e}")
            self.disconnect(websocket)

class NotificationManager(ConnectionManager):
    """Manage notification WebSocket connections."""
    
    async def send_notification(self, notification_type: str, message: str, data: dict = None):
        """Send a notification to all connected clients."""
        await self.broadcast({
            "type": notification_type,
            "message": message,
            "data": data or {}
        })
        
    async def start_notification_worker(self):
        """Background worker for sending periodic status updates."""
        while True:
            try:
                # Send system status updates
                await self.broadcast({
                    "type": "status_update",
                    "data": {
                        "cpu_usage": "30%",
                        "memory_usage": "45%",
                        "active_tasks": 2
                    }
                })
                await asyncio.sleep(30)  # Update every 30 seconds
            except Exception as e:
                logger.error(f"Error in notification worker: {e}")
                await asyncio.sleep(5)  # Wait before retrying 