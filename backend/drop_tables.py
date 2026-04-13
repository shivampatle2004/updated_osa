from database import engine
from sqlalchemy import text
with engine.connect() as conn:
    conn.execute(text('DROP TABLE IF EXISTS change_detection; DROP TABLE IF EXISTS date_tables;'))
    conn.commit()
from database import init_db
init_db()
print("Tables reset and initialized")
