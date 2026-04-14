from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import List, Optional, Any, Dict
from database import SessionLocal
import models
from utils.logger import get_logger
from services.data_engine import DataEngine
from services.report_pdf_service import sync_generate_pdf
from services.paginated_report_engine import PaginatedReportEngine
from fastapi.responses import FileResponse, StreamingResponse, JSONResponse
import os
import io

logger = get_logger("routers.reports")

router = APIRouter(prefix="/api/reports", tags=["reports"])


def _cap_row_list(data_list, cap: int):
    """Limit list length for PDF charts / fallbacks (matches Rows per page setting)."""
    if not isinstance(data_list, list) or not data_list:
        return data_list
    cap = max(1, min(int(cap), 50_000))
    if len(data_list) <= cap:
        return data_list
    return data_list[:cap]

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

@router.post("/generate-pdf-direct")
def generate_pdf_direct(payload: Dict[str, Any] = Body(...)):
    """Generate PDF directly from elements with inline data."""
    try:
        from pydantic import BaseModel
        from services.model_engine import ModelEngine
        from database import SessionLocal
        
        class ElementWithData(BaseModel):
            type: str
            config: Dict[str, Any] = {}
            data: Optional[List[Dict[str, Any]]] = None
        
        title = payload.get("title", "Report")
        page_size = payload.get("page_size", "A4")
        orientation = payload.get("orientation", "portrait")
        elements_data = payload.get("elements", [])
        file_id = payload.get("file_id")
        include_summary = bool(payload.get("include_summary", False))
        rows_per_page_req = max(1, min(int(payload.get("rows_per_page", 30) or 30), 50_000))
        dataset_row_count = payload.get("dataset_row_count")
        selected_columns_count = payload.get("selected_columns_count")
        row_cap = rows_per_page_req

        config = {
            "page_size": page_size,
            "orientation": orientation,
            "header_text": title,
            "include_summary": include_summary,
            "include_chart": False,
            "rows_per_page": rows_per_page_req,
            "dataset_row_count": dataset_row_count,
            "selected_columns_count": selected_columns_count,
        }
        
        db = SessionLocal()
        all_data = []
        
        try:
            if file_id:
                df = ModelEngine.load_report_dataframe(file_id, db)
                if df is not None:
                    df = df.where(df.notnull(), None)
                    all_data = df.to_dict(orient="records")
        finally:
            db.close()
        
        elements = []
        logger.info(
            "Processing %s incoming elements (row_cap=%s), dataframe rows: %s",
            len(elements_data),
            row_cap,
            len(all_data),
        )

        for el in elements_data:
            config_json = dict(el.get("config", {}) or {})
            el_type = el.get("type", "text")
            if isinstance(el_type, str):
                el_type = el_type.strip().lower()
            inline_data = el.get("data")

            logger.info(f"Element type: {el_type}, has inline data: {inline_data is not None}")

            # ── Charts: modal sends type "chart" with chartType inside config ──
            if el_type == "chart":
                ct = (config_json.get("chartType") or config_json.get("chart_type") or "bar").lower()
                if ct == "column":
                    ct = "bar"
                config_json["chart_type"] = ct
                chart_data = inline_data
                if chart_data:
                    config_json["chart_data"] = _cap_row_list(chart_data, row_cap)
                elif all_data:
                    config_json["chart_data"] = _cap_row_list(all_data, row_cap)
            elif el_type in ("bar", "line", "pie", "area", "column"):
                ct = el_type if el_type != "column" else "bar"
                config_json["chart_type"] = config_json.get("chartType") or ct
                chart_data = inline_data
                if chart_data:
                    config_json["chart_data"] = _cap_row_list(chart_data, row_cap)
                elif all_data and (config_json.get("xField") or config_json.get("x_axis") or config_json.get("yField") or config_json.get("y_axis")):
                    config_json["chart_data"] = _cap_row_list(all_data, row_cap)
                elif all_data:
                    config_json["chart_data"] = _cap_row_list(all_data, row_cap)

            if el_type == "table":
                table_rows = inline_data
                if not table_rows and all_data:
                    table_rows = all_data
                col_specs = config_json.get("columns") or []
                col_names = []
                for c in col_specs:
                    if isinstance(c, dict):
                        n = c.get("name") or c.get("header")
                        if n:
                            col_names.append(n)
                    elif isinstance(c, str):
                        col_names.append(c)
                if table_rows and col_names:
                    table_rows = [{k: row.get(k) for k in col_names} for row in table_rows]
                if table_rows:
                    config_json["table_data"] = _cap_row_list(table_rows, row_cap)
                config_json["rows_per_page"] = config_json.get("rows_per_page", rows_per_page_req)
                if not config_json.get("columns") and table_rows:
                    config_json["columns"] = [{"name": c, "header": c} for c in list(table_rows[0].keys())[:20]]

            if el_type == "text":
                config_json["content"] = config_json.get("content", config_json.get("title", ""))

            elements.append({
                "type": el_type,
                "config_json": config_json,
            })

        logger.info("Built %s PDF elements: %s", len(elements), [e.get("type") for e in elements])

        def inline_data_provider(ds_index):
            return all_data if all_data else []

        pdf_bytes = PaginatedReportEngine.generate_pdf(config, elements, inline_data_provider)
        
        if not pdf_bytes or len(pdf_bytes) < 100:
            return JSONResponse(
                status_code=500,
                content={"error": "PDF generation failed"}
            )
        
        pdf_buffer = io.BytesIO(pdf_bytes)
        pdf_buffer.seek(0)
        
        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={title}.pdf"}
        )
    except Exception as e:
        logger.error(f"Direct PDF generation error: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


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
