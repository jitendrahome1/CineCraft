"""
Script to create an admin user.
Usage: python scripts/create_admin.py
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from app.db.session import SessionLocal
from app.services.auth import AuthService
from app.core.logging import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)


def create_admin():
    """Create an admin user."""
    db = SessionLocal()

    try:
        auth_service = AuthService(db)

        # Admin credentials
        email = input("Enter admin email: ").strip()
        password = input("Enter admin password (min 8 characters): ").strip()
        full_name = input("Enter admin full name (optional): ").strip() or None

        # Validate password
        if len(password) < 8:
            logger.error("Password must be at least 8 characters")
            return

        # Create admin
        admin = auth_service.create_admin_user(
            email=email,
            password=password,
            full_name=full_name
        )

        logger.info(f"Admin user created successfully: {admin.email}")
        print(f"\n✓ Admin user created:")
        print(f"  Email: {admin.email}")
        print(f"  ID: {admin.id}")
        print(f"  Role: {admin.role}")

    except Exception as e:
        logger.error(f"Error creating admin user: {str(e)}")
        print(f"\n✗ Error: {str(e)}")

    finally:
        db.close()


if __name__ == "__main__":
    create_admin()
