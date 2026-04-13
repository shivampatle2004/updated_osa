import asyncio
import sys
import os

# Add the current directory to sys.path to allow importing from connectors
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_mongodb():
    print("--- Testing MongoDB Connector Loading ---")
    try:
        from connectors.mongodb_connector import MongoDBConnector
        print("✅ Successfully imported MongoDBConnector")
    except Exception as e:
        print(f"❌ Failed to import MongoDBConnector: {e}")
        return

    # 1. Check metadata
    print(f"Connector Name: {MongoDBConnector.get_display_name()}")
    print(f"Config Schema Keys: {list(MongoDBConnector.get_config_schema()['properties'].keys())}")

    # 2. Test Connection (expect failure if no DB, but testing logic flow)
    config = {
        "host": "localhost",
        "port": 27017,
        "database": "test_db",
        "collection": "test_col"
    }
    connector = MongoDBConnector(config)
    
    print("\n--- Testing Connection (localhost:27017) ---")
    success = await connector.test_connection()
    if success:
        print("✅ Connection Successful!")
    else:
        print("❌ Connection Failed (Expected if MongoDB is not running locally)")

if __name__ == "__main__":
    asyncio.run(test_mongodb())
