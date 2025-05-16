import os
import sqlalchemy
from sqlalchemy import create_engine, text
import psycopg2

# Database connection string
DATABASE_URL = "postgresql://neondb_owner:npg_E3By5fYHDgak@ep-silent-fog-a48gwvbn-pooler.us-east-1.aws.neon.tech/neondb?sslmode=require"

# Test SQLAlchemy connection
def test_sqlalchemy_connection():
    try:
        print("Testing SQLAlchemy connection...")
        engine = create_engine(DATABASE_URL)
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            for row in result:
                print(f"Connection successful! Result: {row[0]}")
        print("SQLAlchemy connection test completed successfully.\n")
        return True
    except Exception as e:
        print(f"SQLAlchemy connection error: {e}")
        return False

# Test psycopg2 connection
def test_psycopg2_connection():
    try:
        print("Testing psycopg2 connection...")
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        print(f"Connection successful! Result: {result[0]}")
        cursor.close()
        conn.close()
        print("psycopg2 connection test completed successfully.\n")
        return True
    except Exception as e:
        print(f"psycopg2 connection error: {e}")
        return False

if __name__ == "__main__":
    print("PostgreSQL Connection Test")
    print("==========================")
    sqlalchemy_success = test_sqlalchemy_connection()
    psycopg2_success = test_psycopg2_connection()
    
    if sqlalchemy_success and psycopg2_success:
        print("All connection tests passed successfully!")
    else:
        print("Some connection tests failed. Please check the errors above.") 