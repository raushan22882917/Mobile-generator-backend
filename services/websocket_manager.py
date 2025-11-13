"""
WebSocket Manager
Handles real-time communication with frontend clients
"""
import asyncio
import logging
import json
from typing import Dict, Set
from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections for real-time updates"""
    
    def __init__(self):
        # Map project_id -> set of WebSocket connections
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.lock = asyncio.Lock()
    
    async def connect(self, websocket: WebSocket, project_id: str):
        """Accept and register a new WebSocket connection"""
        await websocket.accept()
        
        async with self.lock:
            if project_id not in self.active_connections:
                self.active_connections[project_id] = set()
            self.active_connections[project_id].add(websocket)
        
        logger.info(f"Client connected to project {project_id}")
    
    async def disconnect(self, websocket: WebSocket, project_id: str):
        """Remove a WebSocket connection"""
        async with self.lock:
            if project_id in self.active_connections:
                self.active_connections[project_id].discard(websocket)
                if not self.active_connections[project_id]:
                    del self.active_connections[project_id]
        
        logger.info(f"Client disconnected from project {project_id}")
    
    async def send_to_project(self, project_id: str, message: dict):
        """Send message to all clients watching a project"""
        if project_id not in self.active_connections:
            return
        
        # Get copy of connections to avoid modification during iteration
        async with self.lock:
            connections = list(self.active_connections.get(project_id, []))
        
        # Send to all connections
        disconnected = []
        for connection in connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.warning(f"Failed to send to client: {e}")
                disconnected.append(connection)
        
        # Clean up disconnected clients
        if disconnected:
            async with self.lock:
                if project_id in self.active_connections:
                    for conn in disconnected:
                        self.active_connections[project_id].discard(conn)
    
    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients"""
        async with self.lock:
            all_connections = [
                conn 
                for connections in self.active_connections.values() 
                for conn in connections
            ]
        
        for connection in all_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.warning(f"Failed to broadcast to client: {e}")
    
    def get_connection_count(self, project_id: str = None) -> int:
        """Get number of active connections"""
        if project_id:
            return len(self.active_connections.get(project_id, set()))
        return sum(len(conns) for conns in self.active_connections.values())


# Global connection manager instance
connection_manager = ConnectionManager()
