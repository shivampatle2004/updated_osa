from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
import traceback
import os
from pathlib import Path

from database import SessionLocal, init_db
import models, schemas
from auth_utils import get_password_hash, verify_password
<<<<<<< HEAD
from routers import files, graphs, smart, sql, etl, db as remote_db, connections as saved_connections, visuals, automate, modular_connectors, data_vault, reports, modeling
import asyncio
from services.modeling_service import change_detection_poller
=======
from routers import files, graphs, smart, sql, etl, db as remote_db, connections as saved_connections, visuals, automate, modular_connectors, data_vault, reports, rls
>>>>>>> 1bfa371dd0fd1e1c13c2870a300651cdbd78dec0

app = FastAPI(title="OneStopAnalytics API")

# CORS is not needed anymore since frontend and backend are on the same port
# but keeping it for API access from other origins if needed
origins = [
    "https://onestopanalytics.ariths.com",
    "http://127.0.0.1:8010",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handler to catch 500 errors and print them to console
@app.exception_handler(Exception)
async def debug_exception_handler(request: Request, exc: Exception):
    print("="*50)
    print(f"CRITICAL ERROR: {type(exc).__name__}: {str(exc)}")
    traceback.print_exc()
    print("="*50)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error", "error_type": type(exc).__name__, "message": str(exc)}
    )

app.include_router(files.router)
app.include_router(graphs.router)
app.include_router(graphs.top_router)
app.include_router(smart.router)
app.include_router(sql.router)
app.include_router(etl.router)
app.include_router(remote_db.router)
app.include_router(saved_connections.router)
app.include_router(visuals.router)
app.include_router(automate.router)
app.include_router(modular_connectors.router)
app.include_router(data_vault.router)
app.include_router(reports.router)
<<<<<<< HEAD
app.include_router(modeling.router)
=======
app.include_router(rls.router)
>>>>>>> 1bfa371dd0fd1e1c13c2870a300651cdbd78dec0

# Initialize DB on startup
@app.on_event("startup")
def startup_event():
    print("DEBUG: Application starting up and initializing DB...")
    try:
        init_db()
        # Create demo user
        db = SessionLocal()
        try:
            demo_email = "demo@example.com"
            db_user = db.query(models.User).filter(models.User.email == demo_email).first()
            if not db_user:
                hashed_password = get_password_hash("demo123")
                demo_user = models.User(
                    email=demo_email,
                    hashed_password=hashed_password,
                    full_name="Demo User"
                )
                db.add(demo_user)
                db.commit()
                print(f"DEBUG: Demo user {demo_email} created successfully!")
            else:
                print(f"DEBUG: Demo user {demo_email} already exists.")
        finally:
            db.close()
    except Exception as e:
        print(f"ERROR during startup: {e}")
        traceback.print_exc()

    # Start ETL scheduler
    try:
        from services.etl_scheduler import load_all_schedules
        load_all_schedules()
    except Exception as e:
        print(f"WARNING: ETL scheduler startup failed: {e}")

    # Start Change Detection Poller
    try:
        asyncio.create_task(change_detection_poller())
        print("DEBUG: Started Change Detection Poller task.")
    except Exception as e:
        print(f"WARNING: Change detection poller startup failed: {e}")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/signup", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        email=user.email,
        hashed_password=hashed_password,
        full_name=user.full_name
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.post("/register", response_model=schemas.User)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """Register endpoint (alias for /signup)"""
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        email=user.email,
        hashed_password=hashed_password,
        full_name=user.full_name
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.post("/api/signup", response_model=schemas.User)
def api_signup(user: schemas.UserCreate, db: Session = Depends(get_db)):
    return create_user(user, db)

@app.post("/api/register", response_model=schemas.User)
def api_register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    return register_user(user, db)

@app.post("/login")
def login(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    
    return {
        "message": "Login successful",
        "user": {
            "email": db_user.email,
            "full_name": db_user.full_name,
            "id": db_user.id
        }
    }

@app.post("/api/login")
def api_login(user: schemas.UserCreate, db: Session = Depends(get_db)):
    return login(user, db)

# Serve static files from the frontend build
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    # Mount static files (assets, images, etc.)
    app.mount("/assets", StaticFiles(directory=str(static_dir / "assets")), name="assets")
    
    @app.get("/{full_path:path}", response_class=HTMLResponse)
    async def serve_spa(full_path: str):
        """Serve index.html for SPA routing, fallback for non-API routes"""
        # Don't serve index.html for API routes
        if full_path.startswith(("api/", "static/", "assets/")):
            raise HTTPException(status_code=404, detail="Not found")
        
        # Try to serve actual files first
        file_path = static_dir / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        
        # Serve index.html for SPA routes
        index_path = static_dir / "index.html"
        if index_path.exists():
            return FileResponse(index_path)
        
        raise HTTPException(status_code=404, detail="Not found")
else:
    print("WARNING: Static directory not found. Please build the frontend first using: cd frontend && npm run build")
