"""
Webhook API endpoints for Stripe events.
"""
from fastapi import APIRouter, Request, Header, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.services.webhook import WebhookService
from app.schemas.webhook import WebhookEventResponse
from app.core.errors import StripeWebhookError
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.post("/stripe", response_model=WebhookEventResponse)
async def handle_stripe_webhook(
    request: Request,
    stripe_signature: str = Header(..., alias="Stripe-Signature"),
    db: Session = Depends(get_db)
):
    """
    Handle Stripe webhook events.

    Args:
        request: FastAPI request
        stripe_signature: Stripe signature header
        db: Database session

    Returns:
        Event processing result

    Raises:
        HTTPException: If webhook verification or processing fails
    """
    try:
        # Get raw body
        payload = await request.body()

        # Verify and process webhook
        webhook_service = WebhookService(db)

        # Verify signature
        event = webhook_service.verify_webhook_signature(payload, stripe_signature)

        # Handle event
        result = webhook_service.handle_webhook_event(event)

        logger.info(f"Webhook processed successfully: {event['type']}")

        return WebhookEventResponse(
            status=result.get("status", "success"),
            event_type=event["type"],
            message="Webhook processed successfully"
        )

    except StripeWebhookError as e:
        logger.error(f"Webhook error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.exception(f"Unexpected webhook error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error processing webhook"
        )
