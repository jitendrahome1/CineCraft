"""
Script to create test users for development/testing.
Usage: python scripts/create_test_users.py
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


def create_test_users():
    """Create test users with predefined credentials."""
    db = SessionLocal()

    test_users = [
        {
            "email": "admin@cinecraft.com",
            "password": "admin123",
            "full_name": "Admin User",
            "is_admin": True
        },
        {
            "email": "user@cinecraft.com",
            "password": "user123",
            "full_name": "Test User",
            "is_admin": False
        },
        {
            "email": "john@example.com",
            "password": "john123",
            "full_name": "John Doe",
            "is_admin": False
        },
    ]

    try:
        auth_service = AuthService(db)

        print("\n🔧 Creating test users...\n")

        for user_data in test_users:
            try:
                if user_data["is_admin"]:
                    user = auth_service.create_admin_user(
                        email=user_data["email"],
                        password=user_data["password"],
                        full_name=user_data["full_name"]
                    )
                else:
                    user = auth_service.register_user(
                        email=user_data["email"],
                        password=user_data["password"],
                        full_name=user_data["full_name"]
                    )

                role_label = "Admin" if user_data["is_admin"] else "User"
                print(f"✓ Created {role_label}: {user.email}")
                print(f"  Password: {user_data['password']}")
                print(f"  Full Name: {user.full_name}")
                print()

            except Exception as e:
                if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
                    print(f"⚠ User already exists: {user_data['email']}")
                    print()
                else:
                    print(f"✗ Error creating {user_data['email']}: {str(e)}")
                    print()

        print("\n" + "="*50)
        print("TEST CREDENTIALS")
        print("="*50)
        print("\nAdmin Account:")
        print("  Email: admin@cinecraft.com")
        print("  Password: admin123")
        print("\nRegular User Account:")
        print("  Email: user@cinecraft.com")
        print("  Password: user123")
        print("\nAlternate User Account:")
        print("  Email: john@example.com")
        print("  Password: john123")
        print("\n" + "="*50)

    except Exception as e:
        logger.error(f"Error creating test users: {str(e)}")
        print(f"\n✗ Fatal Error: {str(e)}")

    finally:
        db.close()


if __name__ == "__main__":
    create_test_users()
