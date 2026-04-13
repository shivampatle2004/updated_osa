from database import SessionLocal
from models import GraphDefinition

def clear_cache():
    db = SessionLocal()
    try:
        updated = db.query(GraphDefinition).update({GraphDefinition.cached_data: None})
        db.commit()
        print(f"Successfully cleared cache for {updated} graphs.")
    finally:
        db.close()

if __name__ == "__main__":
    clear_cache()
