import MySQLdb
import bcrypt

db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'root123',
    'database': 'educare',
    'charset': 'utf8mb4'
}

def get_db_connection():
    return MySQLdb.connect(**db_config)

def migrate_passwords():
    """Migrate plain text passwords to bcrypt hashes."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get all users with plain text passwords (not starting with $2)
    cursor.execute("SELECT user_id, password FROM users WHERE password IS NOT NULL AND password != ''")
    users = cursor.fetchall()
    
    migrated = 0
    errors = 0
    
    for user_id, password in users:
        try:
            # Skip if already bcrypt hash
            if password and password.startswith('$2'):
                print(f"User {user_id}: Already hashed, skipping")
                continue
            
            # Hash the plain text password
            new_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            cursor.execute("UPDATE users SET password = %s WHERE user_id = %s", (new_hash, user_id))
            conn.commit()
            migrated += 1
            print(f"User {user_id}: Migrated password to bcrypt")
        except Exception as e:
            errors += 1
            print(f"User {user_id}: Error - {e}")
    
    cursor.close()
    conn.close()
    
    print(f"\nMigration complete!")
    print(f"Migrated: {migrated}")
    print(f"Errors: {errors}")

if __name__ == '__main__':
    migrate_passwords()