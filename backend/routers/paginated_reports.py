from fastapi import APIRouter, Depends, HTTPException, Response, Body
from pydantic import BaseModel
from typing import List, Optional, Dict, Any, Union
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from database import SessionLocal
from models import PaginatedReport, PaginatedReportElement, PaginatedReportDataSource, UploadedFile
from services.paginated_report_engine import PaginatedReportEngine
from services.model_engine import ModelEngine
from services.sql_execute import execute_paginated_select

router = APIRouter(prefix="/api/reports", tags=["paginated_reports"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class ElementCreate(BaseModel):
    type: str # 'table', 'text', 'image'
    config_json: Dict[str, Any]

class DataSourceCreate(BaseModel):
    id: Optional[str] = None
    query: Optional[str] = None
    connection_id: Optional[str] = None # file_id or remote DB profile id

class ReportCreate(BaseModel):
    name: str
    page_size: str = "A4"
    orientation: str = "portrait"
    elements: List[ElementCreate]
    data_sources: List[DataSourceCreate]

@router.post("/create")
def create_report(report: ReportCreate, db: Session = Depends(get_db)):
    db_report = PaginatedReport(
        name=report.name,
        page_size=report.page_size,
        orientation=report.orientation
    )
    db.add(db_report)
    db.commit()
    db.refresh(db_report)
    
    for ds in report.data_sources:
        db_ds = PaginatedReportDataSource(
            report_id=db_report.id,
            query=ds.query,
            connection_id=ds.connection_id
        )
        db.add(db_ds)
        
    for idx, el in enumerate(report.elements):
        # assign an ID to the data source so we can map it back during element config
        db_el = PaginatedReportElement(
            report_id=db_report.id,
            type=el.type,
            config_json=el.config_json
        )
        db.add(db_el)
        
    db.commit()
    return {"message": "Report created", "id": db_report.id}

@router.get("/{report_id}")
def get_report(report_id: str, db: Session = Depends(get_db)):
    report = db.query(PaginatedReport).filter(PaginatedReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
        
    return {
        "id": report.id,
        "name": report.name,
        "page_size": report.page_size,
        "orientation": report.orientation,
        "elements": [{"type": e.type, "config_json": e.config_json} for e in report.elements],
        "data_sources": [{"id": d.id, "query": d.query, "connection_id": d.connection_id} for d in report.data_sources]
    }

@router.post("/{report_id}/generate-pdf")
def generate_report_pdf(
    report_id: str, 
    body: Optional[Dict[str, Any]] = Body(default=None),
    db: Session = Depends(get_db)
):
    """
    Generate PDF for a paginated report.
    Optional body: {"include_summary": true, "include_chart": false, "chart_type": "bar"}
    """
    report = db.query(PaginatedReport).filter(PaginatedReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    # Get extended config from request body
    request_config = body or {}

    def data_provider(ds_id_or_connection_id):
        # 1. Try finding it in DB by data_source id
        ds = db.query(PaginatedReportDataSource).filter(PaginatedReportDataSource.id == ds_id_or_connection_id).first()
        connection_id = ds_id_or_connection_id
        query = None
        if ds:
            connection_id = ds.connection_id
            query = ds.query
            
        if not connection_id:
            return []

        # 2. Check if connection_id is a file_id (Dataset)
        file_record = db.query(UploadedFile).filter(UploadedFile.id == connection_id).first()
        if file_record:
            df = ModelEngine.load_report_dataframe(connection_id, db)
            if df is not None:
                # Replace nan with None
                df = df.where(df.notnull(), None)
                return df.to_dict(orient='records')
        
        # 3. If query and remote DB profile (Custom SQL)
        if query:
            try:
                # We use execute_paginated_select with a large limit for paginated report
                data = execute_paginated_select(
                    connection_id="", # typically left empty if profile_id used
                    query=query,
                    limit=10000,
                    offset=0,
                    profile_id=connection_id,
                    db=db
                )
                return data.get("rows", [])
            except Exception as e:
                print(f"SQL execution error for paginated report: {e}")
                return []
                
        return []

    config = {
        "page_size": report.page_size,
        "orientation": report.orientation,
        "header_text": report.name,
        "include_summary": request_config.get("include_summary", True),
        "include_chart": request_config.get("include_chart", False),
        "chart_type": request_config.get("chart_type", "bar")
    }
    
    # Build elements list with proper structure
    elements = []
    for el in report.elements:
        config_json = el.config_json
        if isinstance(config_json, str):
            import json
            config_json = json.loads(config_json)
        
        elements.append({
            "type": el.type,
            "config_json": config_json
        })
    
    # Get all data sources for this report
    data_sources = report.data_sources
    
    # Create a data provider that uses the data source index
    def data_provider(ds_index):
        if ds_index is None:
            return []
        
        # Handle both integer index and string connection_id
        if isinstance(ds_index, int) and ds_index < len(data_sources):
            ds = data_sources[ds_index]
            connection_id = ds.connection_id
            query = ds.query
        else:
            # ds_index might be the actual connection_id
            connection_id = ds_index
            query = None
            # Try to find matching data source
            for ds in data_sources:
                if ds.connection_id == connection_id:
                    query = ds.query
                    break
        
        if not connection_id:
            return []

        # Check if connection_id is a file_id (Dataset)
        file_record = db.query(UploadedFile).filter(UploadedFile.id == connection_id).first()
        if file_record:
            df = ModelEngine.load_report_dataframe(connection_id, db)
            if df is not None:
                df = df.where(df.notnull(), None)
                return df.to_dict(orient='records')
        
        # If query and remote DB profile (Custom SQL)
        if query:
            try:
                data = execute_paginated_select(
                    connection_id="",
                    query=query,
                    limit=10000,
                    offset=0,
                    profile_id=connection_id,
                    db=db
                )
                return data.get("rows", [])
            except Exception as e:
                print(f"SQL execution error for paginated report: {e}")
                return []
                
        return []
    
    pdf_bytes = PaginatedReportEngine.generate_pdf(config, elements, data_provider)
    
    return Response(content=pdf_bytes, media_type="application/pdf", headers={
        "Content-Disposition": f"attachment; filename={report.name}.pdf"
    })
