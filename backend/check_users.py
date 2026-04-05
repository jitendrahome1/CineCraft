"""
Check existing users in the database.
"""
import sqlite3

# Connect to database
conn = sqlite3.connect('cinecraft.db')
cursor = conn.cursor()

print("=" * 60)
print("Existing Users in CineCraft Database")
print("=" * 60)

try:
    # Check if users table exists and has data
    cursor.execute("SELECT email, is_admin, created_at FROM users")
    users = cursor.fetchall()

    if users:
        print(f"\nFound {len(users)} user(s):\n")
        for i, (email, is_admin, created_at) in enumerate(users, 1):
            role = "Admin" if is_admin else "User"
            print(f"{i}. Email: {email}")
            print(f"   Role: {role}")
            print(f"   Created: {created_at}")
            print()
    else:
        print("\n❌ No users found in database")
        print("\nYou need to create a test user!")

except sqlite3.Error as e:
    print(f"❌ Database error: {e}")

finally:
    conn.close()

print("=" * 60)
print("Login Information:")
print("=" * 60)
print("\nIf users exist, use the email and password:")
print("  - Test User Password: password123")
print("  - Admin Password: admin123")
print("\nIf no users exist, you'll need to register a new account")
print("at: http://localhost:3000/auth/register")
