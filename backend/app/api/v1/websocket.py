"""
WebSocket API endpoints.
Handles real-time updates for render jobs and other operations.
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query, status
from sqlalchemy.orm import Session
from typing import Optional

from app.api.deps import get_db
from app.core.websocket import manager
from app.repositories.render_job import RenderJobRepository
from app.core.logging import get_logger
from app.core.security import decode_access_token

logger = get_logger(__name__)

router = APIRouter()


async def get_current_user_ws(
    token: str = Query(..., description="JWT access token"),
    db: Session = Depends(get_db)
) -> int:
    """
    Get current user from WebSocket query parameter token.

    Args:
        token: JWT access token
        db: Database session

    Returns:
        User ID

    Raises:
        WebSocketException: If token is invalid
    """
    try:
        payload = decode_access_token(token)
        user_id = payload.get("sub")
        if user_id is None:
            raise ValueError("Invalid token payload")
        return int(user_id)
    except Exception as e:
        logger.error(f"WebSocket authentication failed: {e}")
        raise


@router.websocket("/jobs/{job_id}")
async def websocket_job_updates(
    websocket: WebSocket,
    job_id: int,
    token: str = Query(..., description="JWT access token"),
    db: Session = Depends(get_db)
):
    """
    WebSocket endpoint for real-time job updates.

    Clients connect to this endpoint to receive live updates about a specific job.

    Args:
        websocket: WebSocket connection
        job_id: Job ID to subscribe to
        token: JWT access token for authentication
        db: Database session

    Example:
        ws://localhost:8000/api/v1/ws/jobs/123?token=your_jwt_token

    Messages sent to client:
        - connection: Initial connection confirmation
        - progress: Progress updates (0-100%)
        - stage_complete: Stage completion notifications
        - status_change: Status change notifications
        - completion: Job completion with result
        - error: Error notifications
        - heartbeat: Keep-alive pings
    """
    try:
        # Authenticate user
        user_id = await get_current_user_ws(token, db)

        # Verify job exists and belongs to user
        job_repo = RenderJobRepository(db)
        job = job_repo.get(job_id)

        if not job:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Job not found")
            return

        if job.user_id != user_id:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Unauthorized")
            return

        # Connect to WebSocket manager
        await manager.connect(websocket, job_id, user_id)

        # Send current job status immediately
        await manager.send_personal_message(
            {
                "type": "status",
                "job_id": job_id,
                "status": job.status.value,
                "progress": job.progress,
                "stage": job.current_stage,
                "stages_completed": job.stages_completed
            },
            websocket
        )

        # Keep connection alive and handle incoming messages
        try:
            while True:
                # Receive messages (for ping/pong or commands)
                data = await websocket.receive_text()

                # Handle ping
                if data == "ping":
                    await manager.send_personal_message(
                        {"type": "pong"},
                        websocket
                    )
                # Handle status request
                elif data == "status":
                    job = job_repo.get(job_id)
                    if job:
                        await manager.send_personal_message(
                            {
                                "type": "status",
                                "job_id": job_id,
                                "status": job.status.value,
                                "progress": job.progress,
                                "stage": job.current_stage,
                                "stages_completed": job.stages_completed,
                                "error_message": job.error_message
                            },
                            websocket
                        )

        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected for job {job_id}")
        finally:
            await manager.disconnect(websocket, job_id)

    except Exception as e:
        logger.exception(f"WebSocket error for job {job_id}")
        try:
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR, reason=str(e))
        except:
            pass


@router.websocket("/notifications")
async def websocket_notifications(
    websocket: WebSocket,
    token: str = Query(..., description="JWT access token"),
    db: Session = Depends(get_db)
):
    """
    WebSocket endpoint for general user notifications.

    Clients connect to receive notifications about all their jobs and activities.

    Args:
        websocket: WebSocket connection
        token: JWT access token for authentication
        db: Database session

    Example:
        ws://localhost:8000/api/v1/ws/notifications?token=your_jwt_token
    """
    try:
        # Authenticate user
        user_id = await get_current_user_ws(token, db)

        await websocket.accept()

        logger.info(f"User {user_id} connected to notifications")

        # Send connection confirmation
        await websocket.send_json({
            "type": "connection",
            "status": "connected",
            "message": "Connected to notification stream"
        })

        # Keep connection alive
        try:
            while True:
                data = await websocket.receive_text()

                if data == "ping":
                    await websocket.send_json({"type": "pong"})

        except WebSocketDisconnect:
            logger.info(f"User {user_id} disconnected from notifications")

    except Exception as e:
        logger.exception("WebSocket error in notifications")
        try:
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR, reason=str(e))
        except:
            pass


@router.get("/stats")
async def get_websocket_stats():
    """
    Get WebSocket connection statistics.

    Returns:
        Dictionary with connection stats
    """
    return {
        "total_connections": manager.get_total_connections(),
        "active_jobs": len(manager.get_active_jobs()),
        "job_ids": list(manager.get_active_jobs())
    }
