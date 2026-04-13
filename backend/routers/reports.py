from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import List, Optional, Any, Dict
from database import SessionLocal
import models
from utils.logger import get_logger
from services.data_engine import DataEngine
from services.report_pdf_service import sync_generate_pdf
from fastapi.responses import FileResponse
import os

logger = get_logger("routers.reports")

router = APIRouter(prefix="/api/reports", tags=["reports"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("")
def list_reports(user_id: Optional[int] = None, db: Session = Depends(get_db)):
    """List all paginated reports."""
    try:
        query = db.query(models.PaginatedReport)
        if user_id:
            query = query.filter(models.PaginatedReport.user_id == user_id)
        reports = query.order_by(models.PaginatedReport.created_at.desc()).all()
        return {"reports": reports, "total": len(reports)}
    except Exception as e:
        logger.error(f"Error listing reports: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("", status_code=201)
@router.post("/create", status_code=201)
def create_report(payload: Dict[str, Any] = Body(...), db: Session = Depends(get_db)):
    """
    Create a new paginated report definition.
    Supports both the new 'layout' format and the legacy 'elements'/'data_sources' format.
    """
    try:
        # Detect legacy format and translate to new layout_json structure
        layout = payload.get("layout", {})
        datasource_mapping = payload.get("datasource_mapping", {})
        
        if not layout and "elements" in payload:
            # Legacy format detected
            layout = {
                "pages": [
                    {
                        "id": "page-1",
                        "elements": payload.get("elements", []),
                        "settings": {
                            "size": payload.get("page_size", "A4"),
                            "orientation": payload.get("orientation", "portrait")
                        }
                    }
                ]
            }
            
            # Map legacy data_sources to datasource_mapping
            # In the legacy format, we usually had a data_source_index in element config
            # We'll try to preserve what we can.
            if "data_sources" in payload:
                for idx, ds in enumerate(payload["data_sources"]):
                    # We don't have a stable element ID mapping here, 
                    # but the elements themselves have IDs in the new system.
                    pass 

        report = models.PaginatedReport(
            name=payload.get("name", "Untitled Report"),
            description=payload.get("description"),
            user_id=payload.get("user_id"),
            layout_json=layout,
            datasource_mapping=datasource_mapping,
            parameters=payload.get("parameters", [])
        )

        db.add(report)
        db.commit()
        db.refresh(report)
        return report
    except Exception as e:
        logger.error(f"Error creating report: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{report_id}")
def get_report(report_id: str, db: Session = Depends(get_db)):
    """Get a single report definition."""
    report = db.query(models.PaginatedReport).filter(models.PaginatedReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report

@router.put("/{report_id}")
def update_report(report_id: str, payload: Dict[str, Any] = Body(...), db: Session = Depends(get_db)):
    """Update an existing report definition."""
    try:
        report = db.query(models.PaginatedReport).filter(models.PaginatedReport.id == report_id).first()
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        
        if "name" in payload: report.name = payload["name"]
        if "description" in payload: report.description = payload["description"]
        if "layout" in payload: report.layout_json = payload["layout"]
        if "datasource_mapping" in payload: report.datasource_mapping = payload["datasource_mapping"]
        if "parameters" in payload: report.parameters = payload["parameters"]
        
        db.commit()
        db.refresh(report)
        return report
    except Exception as e:
        logger.error(f"Error updating report {report_id}: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{report_id}")
def delete_report(report_id: str, db: Session = Depends(get_db)):
    """Delete a report definition."""
    try:
        report = db.query(models.PaginatedReport).filter(models.PaginatedReport.id == report_id).first()
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        db.delete(report)
        db.commit()
        return {"deleted": True, "id": report_id}
    except Exception as e:
        logger.error(f"Error deleting report {report_id}: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# ─── Data Binding Endpoints (Advanced Querying) ──────────────────────────────

@router.post("/{report_id}/render-data")
def get_report_data(
    report_id: str, 
    payload: Dict[str, Any] = Body(default={}), 
    db: Session = Depends(get_db)
):
    """
    Execute all associated queries for the report elements.
    Applies report parameters to the queries dynamically.
    
    Expected payload: {
        "parameters": { "param1": "val1" },
        "element_id": "optional_specific_element",
        "config": { ... } # Optional config for temp report resolution
    }
    """
    datasource_mapping = {}
    
    if report_id == "temp-id":
        element_id = payload.get("element_id")
        config = payload.get("config")
        if element_id and config:
            datasource_mapping = {element_id: config}
    else:
        report = db.query(models.PaginatedReport).filter(models.PaginatedReport.id == report_id).first()
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        datasource_mapping = report.datasource_mapping or {}
        
    results = {}
    
    # Process element mappings
    for element_id, config in datasource_mapping.items():
        if payload.get("element_id") and element_id != payload.get("element_id"):
            continue
            
        vault_id = config.get("vault_id")
        if not vault_id: continue
        
        # Get vault item for table name
        vault_item = db.query(models.DataVaultItem).filter(models.DataVaultItem.id == vault_id).first()
        if not vault_item or not vault_item.table_name: continue
        
        try:
            # Execute query via DataEngine
            element_data = DataEngine.query_vault_item(
                table_name=vault_item.table_name,
                filters=config.get("filters", []),
                group_by=config.get("group_by", []),
                aggregations=config.get("aggregations", []),
                sort_by=config.get("sort_by"),
                ascending=config.get("ascending", True),
                limit=config.get("limit")
            )
            results[element_id] = element_data
        except Exception as e:
            logger.error(f"Failed to fetch data for element {element_id} in report {report_id}: {e}")
            results[element_id] = {"error": str(e)}

    return {
        "report_id": report_id,
        "results": results
    }

@router.post("/{report_id}/export/pdf")
@router.post("/{report_id}/generate-pdf")
def export_report_pdf(report_id: str, db: Session = Depends(get_db)):

    """Trigger server-side PDF generation for a report."""
    report = db.query(models.PaginatedReport).filter(models.PaginatedReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    try:
        # Playwright opens the SPA preview; origin must match where the app is served.
        base_url = os.getenv("REPORT_PDF_BASE_URL", "http://127.0.0.1:8000")
        pdf_path = sync_generate_pdf(report_id, base_url)
        
        if os.path.exists(pdf_path):
            return FileResponse(
                path=pdf_path, 
                filename=f"{report.name.replace(' ', '_')}.pdf",
                media_type="application/pdf"
            )
        else:
            raise HTTPException(status_code=500, detail="PDF generation failed - file not created")
            
    except Exception as e:
        logger.error(f"PDF Export failed for report {report_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
