"""
Subscription API endpoints.
Handles subscription management, checkout, and billing portal.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.services.subscription import SubscriptionService
from app.services.payment import PaymentService
from app.repositories.plan import PlanRepository
from app.schemas.subscription import (
    CheckoutSessionRequest,
    CheckoutSessionResponse,
    SubscriptionWithPlanResponse,
    CancelSubscriptionRequest,
    CustomerPortalResponse
)
from app.schemas.plan import PlanResponse
from app.schemas.payment import PaymentResponse
from app.core.errors import (
    SubscriptionError,
    SubscriptionNotFoundError,
    PaymentError
)
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.get("/plans", response_model=List[PlanResponse])
async def list_plans(db: Session = Depends(get_db)):
    """
    List all available subscription plans.

    Args:
        db: Database session

    Returns:
        List of plans
    """
    plan_repo = PlanRepository(db)
    plans = plan_repo.get_active_plans()
    return plans


@router.get("/me", response_model=SubscriptionWithPlanResponse)
async def get_my_subscription(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current user's subscription with plan details.

    Args:
        current_user: Current user
        db: Database session

    Returns:
        Subscription with plan and usage info

    Raises:
        HTTPException: If subscription not found
    """
    subscription_service = SubscriptionService(db)
    subscription_data = subscription_service.get_subscription_with_plan(current_user.id)

    if not subscription_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active subscription found"
        )

    return subscription_data


@router.post("/checkout", response_model=CheckoutSessionResponse)
async def create_checkout_session(
    request: CheckoutSessionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create Stripe checkout session for subscription.

    Args:
        request: Checkout request data
        current_user: Current user
        db: Database session

    Returns:
        Checkout session URL

    Raises:
        HTTPException: If plan not found or checkout fails
    """
    try:
        # Get plan
        plan_repo = PlanRepository(db)
        plan = plan_repo.get(request.plan_id)

        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Plan not found"
            )

        if not plan.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Plan is not available"
            )

        # Create checkout session
        payment_service = PaymentService(db)
        session_data = payment_service.create_checkout_session(
            user=current_user,
            plan=plan,
            billing_interval=request.billing_interval,
            success_url=request.success_url,
            cancel_url=request.cancel_url
        )

        return CheckoutSessionResponse(**session_data)

    except PaymentError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/portal", response_model=CustomerPortalResponse)
async def create_customer_portal_session(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create Stripe customer portal session.
    Allows users to manage their subscription, payment methods, and billing.

    Args:
        current_user: Current user
        db: Database session

    Returns:
        Customer portal URL

    Raises:
        HTTPException: If subscription not found or portal creation fails
    """
    try:
        # Get user subscription
        subscription_service = SubscriptionService(db)
        subscription = subscription_service.get_user_subscription(current_user.id)

        if not subscription or not subscription.stripe_customer_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active subscription found"
            )

        # Create portal session
        payment_service = PaymentService(db)
        portal_data = payment_service.create_customer_portal_session(
            customer_id=subscription.stripe_customer_id
        )

        return CustomerPortalResponse(**portal_data)

    except PaymentError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/cancel")
async def cancel_subscription(
    request: CancelSubscriptionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Cancel user's subscription.

    Args:
        request: Cancel request
        current_user: Current user
        db: Database session

    Returns:
        Success message

    Raises:
        HTTPException: If subscription not found
    """
    try:
        subscription_service = SubscriptionService(db)
        subscription = subscription_service.cancel_subscription(
            user_id=current_user.id,
            at_period_end=request.at_period_end
        )

        message = (
            "Subscription will be canceled at the end of the billing period"
            if request.at_period_end
            else "Subscription canceled immediately"
        )

        return {
            "message": message,
            "subscription_id": subscription.id,
            "canceled_at": subscription.canceled_at
        }

    except SubscriptionNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/payments", response_model=List[PaymentResponse])
async def get_payment_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = 50
):
    """
    Get payment history for current user.

    Args:
        current_user: Current user
        db: Database session
        limit: Maximum number of payments

    Returns:
        List of payments
    """
    payment_service = PaymentService(db)
    payments = payment_service.get_payment_history(current_user.id, limit=limit)
    return payments
