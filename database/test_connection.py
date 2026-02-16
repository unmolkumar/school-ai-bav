import os
from sqlalchemy import create_engine
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("❌ DATABASE_URL not found in .env file")
    exit()

print("🔎 Trying to connect to Railway MySQL...")

try:
    engine = create_engine(DATABASE_URL)
    with engine.connect() as connection:
        print("✅ Connection successful!")
except Exception as e:
    print("❌ Connection failed:")
    print(e)
