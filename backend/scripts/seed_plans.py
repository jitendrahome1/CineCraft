"""
Seed script for subscription plans.
Creates default Free, Pro, and Enterprise plans in the database.
"""
import sys
import os
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.db.session import SessionLocal
from app.models.plan import Plan
from app.core.logging import get_logger

logger = get_logger(__name__)


def seed_plans():
    """
    Create default subscription plans.
    """
    db = SessionLocal()

    try:
        # Check if plans already exist
        existing_plans = db.query(Plan).count()
        if existing_plans > 0:
            logger.info(f"Plans already exist ({existing_plans} found). Skipping seed.")
            return

        # Define default plans
        plans = [
            {
                "name": "Free",
                "stripe_price_id_monthly": None,
                "stripe_price_id_yearly": None,
                "price_monthly": 0.00,
                "price_yearly": 0.00,
                "max_videos_per_month": 3,
                "max_video_duration": 60,  # 60 seconds
                "max_scenes_per_video": 5,
                "features": {
                    "hd_export": False,
                    "4k_export": False,
                    "watermark": True,
                    "advanced_effects": False,
                    "custom_music": False,
                    "priority_rendering": False,
                    "api_access": False,
                    "team_collaboration": False,
                    "custom_branding": False,
                },
                "is_active": True,
            },
            {
                "name": "Pro",
                "stripe_price_id_monthly": os.getenv("STRIPE_PRICE_PRO_MONTHLY", "price_pro_monthly"),
                "stripe_price_id_yearly": os.getenv("STRIPE_PRICE_PRO_YEARLY", "price_pro_yearly"),
                "price_monthly": 29.99,
                "price_yearly": 299.00,  # ~$25/month
                "max_videos_per_month": 50,
                "max_video_duration": 300,  # 5 minutes
                "max_scenes_per_video": 20,
                "features": {
                    "hd_export": True,
                    "4k_export": False,
                    "watermark": False,
                    "advanced_effects": True,
                    "custom_music": True,
                    "priority_rendering": True,
                    "api_access": False,
                    "team_collaboration": False,
                    "custom_branding": False,
                },
                "is_active": True,
            },
            {
                "name": "Enterprise",
                "stripe_price_id_monthly": os.getenv("STRIPE_PRICE_ENTERPRISE_MONTHLY", "price_enterprise_monthly"),
                "stripe_price_id_yearly": os.getenv("STRIPE_PRICE_ENTERPRISE_YEARLY", "price_enterprise_yearly"),
                "price_monthly": 99.99,
                "price_yearly": 999.00,  # ~$83/month
                "max_videos_per_month": None,  # Unlimited
                "max_video_duration": 600,  # 10 minutes
                "max_scenes_per_video": None,  # Unlimited
                "features": {
                    "hd_export": True,
                    "4k_export": True,
                    "watermark": False,
                    "advanced_effects": True,
                    "custom_music": True,
                    "priority_rendering": True,
                    "api_access": True,
                    "team_collaboration": True,
                    "custom_branding": True,
                },
                "is_active": True,
            },
        ]

        # Create plans
        for plan_data in plans:
            plan = Plan(**plan_data)
            db.add(plan)
            logger.info(f"Creating plan: {plan_data['name']}")

        db.commit()
        logger.info(f"Successfully created {len(plans)} subscription plans")

        # Display created plans
        print("\n" + "=" * 70)
        print("SUBSCRIPTION PLANS CREATED")
        print("=" * 70)

        for plan in db.query(Plan).all():
            print(f"\n{plan.name} Plan (ID: {plan.id})")
            print(f"  Price: ${plan.price_monthly}/month")
            if plan.price_yearly:
                print(f"  Annual: ${plan.price_yearly}/year")
            print(f"  Videos: {plan.max_videos_per_month or 'Unlimited'}/month")
            print(f"  Duration: {plan.max_video_duration} seconds max")
            print(f"  Scenes: {plan.max_scenes_per_video or 'Unlimited'} per video")
            print(f"  Stripe Monthly: {plan.stripe_price_id_monthly or 'N/A'}")
            print(f"  Stripe Yearly: {plan.stripe_price_id_yearly or 'N/A'}")

        print("\n" + "=" * 70)
        print("\nNOTE: Update Stripe Price IDs in .env file:")
        print("  STRIPE_PRICE_PRO_MONTHLY=price_...")
        print("  STRIPE_PRICE_PRO_YEARLY=price_...")
        print("  STRIPE_PRICE_ENTERPRISE_MONTHLY=price_...")
        print("  STRIPE_PRICE_ENTERPRISE_YEARLY=price_...")
        print("=" * 70 + "\n")

    except Exception as e:
        logger.exception(f"Error seeding plans: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("Seeding subscription plans...")
    seed_plans()
    print("Done!")
