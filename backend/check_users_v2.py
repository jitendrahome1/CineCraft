"""
Check existing users - v2 with correct schema.
"""
import sqlite3

conn = sqlite3.connect('cinecraft.db')
cursor = conn.cursor()

print("=" * 60)
print("CineCraft Users")
print("=" * 60)

try:
    # Get table schema first
    cursor.execute("PRAGMA table_info(users)")
    columns = cursor.fetchall()

    print("\nUsers table columns:")
    for col in columns:
        print(f"  - {col[1]} ({col[2]})")

    # Query users
    cursor.execute("SELECT id, email, created_at FROM users")
    users = cursor.fetchall()

    if users:
        print(f"\n✅ Found {len(users)} user(s):\n")
        for user_id, email, created_at in users:
            print(f"ID: {user_id}")
            print(f"Email: {email}")
            print(f"Created: {created_at}")
            print("-" * 40)
    else:
        print("\n⚠️  No users found in database")

except sqlite3.Error as e:
    print(f"❌ Error: {e}")

finally:
    conn.close()

print("\n" + "=" * 60)
print("🔑 Login Instructions")
print("=" * 60)
print("\n1. Open: http://localhost:3000")
print("2. Go to: Register page (/auth/register)")
print("3. Create a new account")
print("\nOR if you have existing test users:")
print("  Email: test@example.com")
print("  Password: password123")
