from database import SessionLocal
from models import GraphDefinition, UploadedFile

def check_data():
    db = SessionLocal()
    try:
        files = db.query(UploadedFile).order_by(UploadedFile.created_at.desc()).limit(5).all()
        for f in files:
            print(f"File: {f.file_name} (ID: {f.id}) - Rows: {f.row_count}")
            graphs = db.query(GraphDefinition).filter(GraphDefinition.file_id == f.id).all()
            for g in graphs:
                cached_len = 0
                if g.cached_data and isinstance(g.cached_data, dict):
                    cached_len = len(g.cached_data.get("labels", []))
                print(f"  Graph: {g.graph_type} ({g.x_axis} count={cached_len})")
    finally:
        db.close()

if __name__ == "__main__":
    check_data()
