import os
import psycopg2
try:
    import redis
except ImportError:
    redis = None
from dotenv import load_dotenv

load_dotenv()

def check_db():
    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_NAME = os.getenv("DB_NAME", "onestopanalytics")
    
    print(f"Checking PostgreSQL at {DB_HOST}:{DB_PORT}...")
    try:
        conn = psycopg2.connect(
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME
        )
        print("Successfully connected to 'postgres' database.")
        conn.close()
    except Exception as e:
        print(f"FAILED to connect to PostgreSQL: {e}")

def check_redis():
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    print(f"Checking Redis at {REDIS_URL}...")
    try:
        r = redis.from_url(REDIS_URL)
        r.ping()
        print("Successfully connected to Redis.")
    except Exception as e:
        print(f"FAILED to connect to Redis: {e}")

if __name__ == "__main__":
    check_db()
    check_redis()
