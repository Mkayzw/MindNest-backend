import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get database URL from environment variable
database_url = os.getenv("DATABASE_URL")

def test_db_connection():
    print(f"Connecting to database: {database_url}")
    try:
        # Create engine
        engine = create_engine(database_url)
        
        # Test connection
        with engine.connect() as conn:
            print("Database connection successful!")
            
            # Check if users table exists and has data
            result = conn.execute(text("SELECT * FROM users"))
            users = result.fetchall()
            
            if users:
                print(f"Found {len(users)} users in database:")
                for user in users:
                    print(f"  User ID: {user.id}, Email: {user.email}")
            else:
                print("No users found in database!")
                
            # Check tables in database
            result = conn.execute(text(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'public'"
            ))
            tables = result.fetchall()
            print("\nTables in database:")
            for table in tables:
                print(f"  {table[0]}")
    
    except Exception as e:
        print(f"Error connecting to database: {str(e)}")

if __name__ == "__main__":
    test_db_connection() 