"""
WebSocket connection manager for CineCraft.
Handles WebSocket connections and broadcasting updates.
"""
from typing import Dict, List, Set
from fastapi import WebSocket, WebSocketDisconnect
import json
from datetime import datetime
import asyncio

from app.core.logging import get_logger

logger = get_logger(__name__)


class ConnectionManager:
    """Manages WebSocket connections and message broadcasting."""

    def __init__(self):
        # Maps job_id to list of active WebSocket connections
        self.active_connections: Dict[int, List[WebSocket]] = {}
        # Maps WebSocket to user_id for authentication
        self.connection_users: Dict[WebSocket, int] = {}
        # Lock for thread-safe operations
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, job_id: int, user_id: int):
        """
        Accept and register a new WebSocket connection.

        Args:
            websocket: WebSocket connection
            job_id: Job ID to subscribe to
            user_id: User ID for authentication
        """
        await websocket.accept()

        async with self._lock:
            # Add to job-specific connections
            if job_id not in self.active_connections:
                self.active_connections[job_id] = []
            self.active_connections[job_id].append(websocket)

            # Map connection to user
            self.connection_users[websocket] = user_id

            logger.info(f"WebSocket connected: user={user_id}, job={job_id}")

        # Send initial connection confirmation
        await self.send_personal_message(
            {
                "type": "connection",
                "status": "connected",
                "job_id": job_id,
                "timestamp": datetime.utcnow().isoformat()
            },
            websocket
        )

    async def disconnect(self, websocket: WebSocket, job_id: int):
        """
        Remove a WebSocket connection.

        Args:
            websocket: WebSocket connection to remove
            job_id: Job ID the connection was subscribed to
        """
        async with self._lock:
            # Remove from job-specific connections
            if job_id in self.active_connections:
                if websocket in self.active_connections[job_id]:
                    self.active_connections[job_id].remove(websocket)

                # Clean up empty job entries
                if len(self.active_connections[job_id]) == 0:
                    del self.active_connections[job_id]

            # Remove user mapping
            user_id = self.connection_users.pop(websocket, None)

            logger.info(f"WebSocket disconnected: user={user_id}, job={job_id}")

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """
        Send message to a specific WebSocket connection.

        Args:
            message: Message dictionary to send
            websocket: Target WebSocket connection
        """
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Failed to send personal message: {e}")

    async def broadcast_to_job(self, job_id: int, message: dict):
        """
        Broadcast message to all connections subscribed to a job.

        Args:
            job_id: Job ID to broadcast to
            message: Message dictionary to broadcast
        """
        async with self._lock:
            if job_id not in self.active_connections:
                logger.debug(f"No active connections for job {job_id}")
                return

            connections = self.active_connections[job_id].copy()

        # Add timestamp if not present
        if "timestamp" not in message:
            message["timestamp"] = datetime.utcnow().isoformat()

        # Send to all connections
        disconnected = []
        for connection in connections:
            try:
                await connection.send_json(message)
            except WebSocketDisconnect:
                disconnected.append(connection)
            except Exception as e:
                logger.error(f"Failed to send message to connection: {e}")
                disconnected.append(connection)

        # Clean up disconnected connections
        if disconnected:
            async with self._lock:
                for connection in disconnected:
                    if job_id in self.active_connections:
                        if connection in self.active_connections[job_id]:
                            self.active_connections[job_id].remove(connection)
                    self.connection_users.pop(connection, None)

        logger.debug(f"Broadcasted to {len(connections) - len(disconnected)} connections for job {job_id}")

    async def broadcast_progress(
        self,
        job_id: int,
        progress: float,
        stage: str,
        status: str = "processing"
    ):
        """
        Broadcast progress update.

        Args:
            job_id: Job ID
            progress: Progress percentage (0-100)
            stage: Current stage description
            status: Job status
        """
        message = {
            "type": "progress",
            "job_id": job_id,
            "progress": progress,
            "stage": stage,
            "status": status
        }
        await self.broadcast_to_job(job_id, message)

    async def broadcast_completion(
        self,
        job_id: int,
        result_data: dict
    ):
        """
        Broadcast job completion.

        Args:
            job_id: Job ID
            result_data: Result data dictionary
        """
        message = {
            "type": "completion",
            "job_id": job_id,
            "status": "completed",
            "result": result_data
        }
        await self.broadcast_to_job(job_id, message)

    async def broadcast_error(
        self,
        job_id: int,
        error_message: str
    ):
        """
        Broadcast job error.

        Args:
            job_id: Job ID
            error_message: Error message
        """
        message = {
            "type": "error",
            "job_id": job_id,
            "status": "failed",
            "error": error_message
        }
        await self.broadcast_to_job(job_id, message)

    async def broadcast_stage_complete(
        self,
        job_id: int,
        stage: str,
        progress: float
    ):
        """
        Broadcast stage completion.

        Args:
            job_id: Job ID
            stage: Completed stage name
            progress: Current progress percentage
        """
        message = {
            "type": "stage_complete",
            "job_id": job_id,
            "stage": stage,
            "progress": progress
        }
        await self.broadcast_to_job(job_id, message)

    async def broadcast_status_change(
        self,
        job_id: int,
        old_status: str,
        new_status: str
    ):
        """
        Broadcast job status change.

        Args:
            job_id: Job ID
            old_status: Previous status
            new_status: New status
        """
        message = {
            "type": "status_change",
            "job_id": job_id,
            "old_status": old_status,
            "new_status": new_status
        }
        await self.broadcast_to_job(job_id, message)

    def get_connection_count(self, job_id: int) -> int:
        """
        Get number of active connections for a job.

        Args:
            job_id: Job ID

        Returns:
            Number of active connections
        """
        return len(self.active_connections.get(job_id, []))

    def get_total_connections(self) -> int:
        """
        Get total number of active connections.

        Returns:
            Total connection count
        """
        return sum(len(conns) for conns in self.active_connections.values())

    def get_active_jobs(self) -> Set[int]:
        """
        Get set of job IDs with active connections.

        Returns:
            Set of job IDs
        """
        return set(self.active_connections.keys())


# Global connection manager instance
manager = ConnectionManager()
