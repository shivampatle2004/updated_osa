import os
import shutil
import base64
import math
from fastapi import APIRouter, UploadFile as _FastAPIUploadFile, File, Depends, HTTPException, BackgroundTasks, Body, Query, Form, Header
from typing import Optional
from sqlalchemy.orm import Session
from database import SessionLocal
from models import UploadedFile, FileColumn, ColumnStatistic, User, GraphDefinition
import models
from services.data_processor import DataProcessor
from tasks import run_file_processing
import uuid

router = APIRouter(prefix="/api/files", tags=["files"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_UPLOAD_ABS = os.path.join(_BACKEND_DIR, "uploads")
UPLOAD_DIR = _UPLOAD_ABS
os.makedirs(UPLOAD_DIR, exist_ok=True)

def verify_write_permission(
    x_simulated_role: Optional[str] = Header(None, alias="X-Simulated-Role"),
    db: Session = Depends(get_db)
):
    if not x_simulated_role:
        return
    role_ids = [r.strip() for r in x_simulated_role.split(",") if r.strip()]
    if not role_ids:
        return
        
    from models import RLSRole
    roles = db.query(RLSRole).filter(RLSRole.id.in_(role_ids)).all()
    if not roles:
        return
        
    best = "view"
    hierarchy = ['view', 'edit', 'view_edit']
    for r in roles:
        p = r.permission or "view"
        if hierarchy.index(p) > hierarchy.index(best):
            best = p
            
    if best == "view":
        raise HTTPException(status_code=403, detail="Simulated role has 'view' access only")


def resolve_stored_file_path(file_record: UploadedFile):
    """
    Resolve the on-disk path for an uploaded file.
    Handles relative paths, different working directories, and standard uploads/{id}.{ext} layout.
    """
    if not file_record:
        return None
    raw = (file_record.file_path or "").strip()
    candidates = []
    if raw:
        candidates.append(raw)
        if not os.path.isabs(raw):
            candidates.append(os.path.join(_BACKEND_DIR, raw))
            candidates.append(os.path.join(os.getcwd(), raw))
    fn = (file_record.file_name or "")
    ext = fn.rsplit(".", 1)[-1].lower() if "." in fn else ""
    if ext in ("csv", "xlsx", "xls", "json", "txt"):
        candidates.append(os.path.join(_UPLOAD_ABS, f"{file_record.id}.{ext}"))
    candidates.append(os.path.join(_UPLOAD_ABS, f"{file_record.id}.csv"))
    seen = set()
    for p in candidates:
        if not p or p in seen:
            continue
        seen.add(p)
        try:
            if os.path.isfile(p):
                return os.path.normpath(p)
        except Exception:
            continue
    return None


def dataset_missing_payload(file_record: UploadedFile, limit: int, offset: int, reason: str):
    """Return 200 JSON so the BI client can show a message instead of a hard 404."""
    return {
        "columns": [],
        "rows": [],
        "metadata": {
            "fileId": file_record.id,
            "fileName": file_record.file_name,
            "status": file_record.status,
            "missingSourceFile": True,
            "error": reason,
            "totalRows": 0,
            "returnedRows": 0,
            "offset": offset,
            "limit": limit,
        },
    }



@router.post("/upload")
async def upload_file(
    background_tasks: BackgroundTasks,
    file: _FastAPIUploadFile = File(...),
    user_id: int = Form(None),  # Get from form, None means not authenticated
    db: Session = Depends(get_db)
):
    # Allow anonymous uploads - user_id is optional
    # If user_id provided, verify user exists
    if user_id:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            # If user not found (e.g. stale session after DB reset), fall back to anonymous upload
            # Or we could just ignore it. Setting user_id to None for the rest of the flow.
            user_id = None
            print(f"WARNING: User {user_id} not found. Uploading as anonymous.")
    
    # Validate file type
    allowed_extensions = ["csv", "xlsx", "xls", "json", "txt", "tsv", "parquet"]
    extension = file.filename.split(".")[-1].lower()
    if extension not in allowed_extensions:
        raise HTTPException(status_code=400, detail="Unsupported file format")

    file_id = uuid.uuid4()
    file_path = os.path.join(UPLOAD_DIR, f"{file_id}.{extension}")

    # Save file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Basic content validation for common mismatches (e.g. HTML downloaded as .xlsx)
    try:
        with open(file_path, "rb") as f:
            head = f.read(64)
        if extension == "xlsx":
            # XLSX is a ZIP container and usually starts with "PK"
            if not head.startswith(b"PK"):
                # Common case: error page HTML saved with .xlsx extension
                if head.lstrip().lower().startswith(b"<!doctype html") or head.lstrip().lower().startswith(b"<html"):
                    raise HTTPException(
                        status_code=400,
                        detail="Invalid .xlsx file: it looks like an HTML page. Re-download the Excel file and upload the real .xlsx."
                    )
                raise HTTPException(status_code=400, detail="Invalid .xlsx file: file signature is not a valid Excel workbook.")
        elif extension == "xls":
            # Legacy XLS typically starts with D0 CF 11 E0 (OLE header)
            if not head.startswith(b"\xD0\xCF\x11\xE0"):
                raise HTTPException(status_code=400, detail="Invalid .xls file: file signature is not a valid Excel workbook.")
    except HTTPException:
        # Remove the saved file to avoid keeping invalid uploads.
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception:
            pass
        raise
    except Exception:
        # If validation fails unexpectedly, continue; processing will report the real error.
        pass

    # Create DB record - allow anonymous uploads (user_id can be NULL)
    db_file = UploadedFile(
        id=str(file_id),
        user_id=user_id,  # Will be None for anonymous users
        file_name=file.filename,
        file_path=file_path,
        status="pending"
    )
    db.add(db_file)
    db.commit()
    db.refresh(db_file)

    # Trigger background task
    background_tasks.add_task(run_file_processing, str(file_id))
    print(f"SUCCESS: Triggered processing for {file_id}" + (f" by user {user_id}" if user_id else " (anonymous)"))

    return {
        "file_id": str(file_id),
        "status": "pending",
        "message": "File upload successful, processing started",
        # Basename only — CSV/Excel/JSON connectors resolve under backend/uploads/
        "connector_file_path": f"{file_id}.{extension}",
    }


@router.post("/blank-report")
async def create_blank_report(
    background_tasks: BackgroundTasks,
    user_id: int = Form(None),
    db: Session = Depends(get_db),
):
    """
    Create a new report file with a minimal placeholder CSV and model_config.blank_report=True.
    Used for 'Blank report → Database' so the Model view does not show a competing 'main' dataset
    card until the user imports real tables; avoids client-uploaded New_report.csv polluting the model.
    """
    if user_id:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            user_id = None

    file_id = uuid.uuid4()
    extension = "csv"
    file_path = os.path.join(UPLOAD_DIR, f"{file_id}.{extension}")
    # Header-only CSV: single internal column, zero data rows (processed like any upload).
    with open(file_path, "wb") as buffer:
        buffer.write(b"_osa_placeholder\n")

    display_name = "Untitled report.csv"
    model_cfg = {
        "tables": [],
        "relationships": [],
        "blank_report": True,
    }
    db_file = UploadedFile(
        id=str(file_id),
        user_id=user_id,
        file_name=display_name,
        file_path=file_path,
        status="pending",
        model_config=model_cfg,
    )
    db.add(db_file)
    db.commit()
    db.refresh(db_file)

    background_tasks.add_task(run_file_processing, str(file_id))
    print(f"SUCCESS: Blank report {file_id}" + (f" for user {user_id}" if user_id else " (anonymous)"))

    return {
        "file_id": str(file_id),
        "file_name": display_name,
        "status": "pending",
        "message": "Blank report created, processing started",
    }


@router.get("/{file_id}/dataset")
def get_file_dataset(
    file_id: str,
    limit: int = Query(500, ge=1, le=5000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    Return a preview dataset payload used by the BI workspace Data view.
    Shape matches frontend expectations:
      { columns: [{ name, type? }], rows: [ {col: value, ...} ], metadata: {...} }
    """
    file_record = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")

    from services.sql_profile_helpers import attach_sql_profile_if_missing

    _sd0 = (file_record.model_config or {}).get("sql_dataset")
    if isinstance(_sd0, dict) and _sd0.get("enabled"):
        attach_sql_profile_if_missing(file_record, db)

    mc = file_record.model_config or {}
    rels = mc.get("relationships") or []
    if isinstance(rels, list) and len(rels) > 0:
        try:
            from services.model_engine import ModelEngine

            merged_df = ModelEngine.build_full_model_df(file_id, db)
        except Exception as exc:
            print(f"get_file_dataset: relationship merge failed: {exc}")
            merged_df = None
        if merged_df is not None and not merged_df.empty:
            total_rows = int(len(merged_df))
            preview_df = merged_df.iloc[offset : offset + limit].copy()

            def _clean_value(v):
                try:
                    if v is None:
                        return None
                    if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
                        return None
                    if hasattr(v, "isoformat") and not isinstance(v, (str, bytes)):
                        try:
                            return v.isoformat()
                        except Exception:
                            pass
                    if hasattr(v, "item"):
                        try:
                            return v.item()
                        except Exception:
                            pass
                    return v
                except Exception:
                    return None

            out_rows = []
            for rec in preview_df.to_dict(orient="records"):
                out_rows.append({k: _clean_value(v) for k, v in rec.items()})
            inferred = DataProcessor.infer_column_types(merged_df.head(500).copy())
            columns = [{"name": c, "type": inferred.get(c, "unknown")} for c in list(merged_df.columns)]
            return {
                "columns": columns,
                "rows": out_rows,
                "metadata": {
                    "fileId": file_record.id,
                    "fileName": file_record.file_name,
                    "status": file_record.status,
                    "totalRows": total_rows,
                    "returnedRows": len(out_rows),
                    "offset": offset,
                    "limit": limit,
                    "datasetSource": "model",
                    "relationshipsApplied": True,
                },
            }

    # Virtual dataset from custom SQL when the model has no merged rows from relationships
    sd = mc.get("sql_dataset")
    if isinstance(sd, dict) and sd.get("enabled") and sd.get("query") and (
        sd.get("connection_id") or sd.get("profile_id")
    ):
        from services.sql_execute import execute_paginated_select

        try:
            data = execute_paginated_select(
                sd.get("connection_id") or "",
                sd["query"],
                limit,
                offset,
                profile_id=sd.get("profile_id"),
                db=db,
            )
        except ValueError as exc:
            return {
                "columns": [],
                "rows": [],
                "metadata": {
                    "fileId": file_record.id,
                    "fileName": file_record.file_name,
                    "status": file_record.status,
                    "totalRows": 0,
                    "returnedRows": 0,
                    "offset": offset,
                    "limit": limit,
                    "error": str(exc),
                    "datasetSource": "sql",
                    "missingSourceFile": True,
                },
            }
        except Exception as exc:
            return {
                "columns": [],
                "rows": [],
                "metadata": {
                    "fileId": file_record.id,
                    "fileName": file_record.file_name,
                    "status": file_record.status,
                    "totalRows": 0,
                    "returnedRows": 0,
                    "offset": offset,
                    "limit": limit,
                    "error": str(exc),
                    "datasetSource": "sql",
                    "missingSourceFile": True,
                },
            }

        def _clean_sql_val(v):
            try:
                if v is None:
                    return None
                if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
                    return None
                if hasattr(v, "isoformat") and not isinstance(v, (str, bytes)):
                    try:
                        return v.isoformat()
                    except Exception:
                        pass
                if hasattr(v, "item"):
                    try:
                        return v.item()
                    except Exception:
                        pass
                return v
            except Exception:
                return None

        rows = [{k: _clean_sql_val(v) for k, v in rec.items()} for rec in data["rows"]]
        pg = data.get("pagination") or {}
        total_sql = int(pg.get("total_rows", 0))

        return {
            "columns": data["columns"],
            "rows": rows,
            "metadata": {
                "fileId": file_record.id,
                "fileName": sd.get("name") or file_record.file_name,
                "status": file_record.status,
                "totalRows": total_sql,
                "returnedRows": len(rows),
                "offset": offset,
                "limit": limit,
                "datasetSource": "sql",
            },
        }

    # If processing is still running, still try to provide a usable preview directly
    # from the uploaded file. This prevents the UI from showing "0 records" for
    # valid files that are pending/processing or whose derived metadata isn't saved yet.
    if file_record.status in ("pending", "processing"):
        _pending_path = resolve_stored_file_path(file_record)
        if _pending_path:
            try:
                df = DataProcessor.read_file(_pending_path)
                total_rows = int(len(df))
                preview_df = df.iloc[offset: offset + limit].copy()

                def _clean_value(v):
                    try:
                        if v is None:
                            return None
                        if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
                            return None
                        if hasattr(v, "isoformat") and not isinstance(v, (str, bytes)):
                            try:
                                return v.isoformat()
                            except Exception:
                                pass
                        if hasattr(v, "item"):
                            try:
                                return v.item()
                            except Exception:
                                pass
                        return v
                    except Exception:
                        return None

                rows = [{k: _clean_value(v) for k, v in rec.items()} for rec in preview_df.to_dict(orient="records")]
                inferred = DataProcessor.infer_column_types(df)
                columns = [{"name": c, "type": inferred.get(c, "unknown")} for c in list(df.columns)]

                return {
                    "columns": columns,
                    "rows": rows,
                    "metadata": {
                        "fileId": file_record.id,
                        "fileName": file_record.file_name,
                        "status": file_record.status,
                        "totalRows": total_rows,
                        "returnedRows": len(rows),
                        "offset": offset,
                        "limit": limit,
                    }
                }
            except Exception:
                # If preview fails for any reason, fall back to the previous behavior.
                pass

        return {
            "columns": [],
            "rows": [],
            "metadata": {
                "fileId": file_record.id,
                "fileName": file_record.file_name,
                "status": file_record.status,
                "totalRows": 0,
                "returnedRows": 0,
                "offset": offset,
                "limit": limit,
            }
        }

    if file_record.status == "failed":
        return {
            "columns": [],
            "rows": [],
            "metadata": {
                "fileId": file_record.id,
                "fileName": file_record.file_name,
                "status": "failed",
                "error": file_record.error_message or "Processing failed",
                "totalRows": 0,
                "returnedRows": 0,
                "offset": offset,
                "limit": limit,
            }
        }

    # Same merged frame as charts/graphs: DB-imported tables without relationships, custom SQL, joins, etc.
    try:
        from services.model_engine import ModelEngine

        merged_df = ModelEngine.load_report_dataframe(file_id, db)
    except Exception as exc:
        print(f"get_file_dataset: load_report_dataframe failed: {exc}")
        merged_df = None

    if merged_df is not None and not merged_df.empty:
        total_rows = int(len(merged_df))
        preview_df = merged_df.iloc[offset : offset + limit].copy()

        def _clean_value(v):
            try:
                if v is None:
                    return None
                if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
                    return None
                if hasattr(v, "isoformat") and not isinstance(v, (str, bytes)):
                    try:
                        return v.isoformat()
                    except Exception:
                        pass
                if hasattr(v, "item"):
                    try:
                        return v.item()
                    except Exception:
                        pass
                return v
            except Exception:
                return None

        rows = []
        for rec in preview_df.to_dict(orient="records"):
            rows.append({k: _clean_value(v) for k, v in rec.items()})
        inferred = DataProcessor.infer_column_types(merged_df.head(500).copy())
        columns = [{"name": c, "type": inferred.get(c, "unknown")} for c in list(merged_df.columns)]
        return {
            "columns": columns,
            "rows": rows,
            "metadata": {
                "fileId": file_record.id,
                "fileName": file_record.file_name,
                "status": file_record.status,
                "totalRows": total_rows,
                "returnedRows": len(rows),
                "offset": offset,
                "limit": limit,
                "datasetSource": "model",
            },
        }

    resolved_path = resolve_stored_file_path(file_record)
    if not resolved_path:
        return dataset_missing_payload(
            file_record,
            limit,
            offset,
            "The data file is not on the server anymore (deleted, moved, or DB reset). Re-upload the dataset or open a recent file.",
        )

    try:
        df = DataProcessor.read_file(resolved_path)
    except Exception as e:
        print(f"get_file_dataset: read_file failed for {resolved_path}: {e}")
        return dataset_missing_payload(
            file_record,
            limit,
            offset,
            f"Could not read the data file: {str(e)}",
        )

    total_rows = int(file_record.row_count or len(df))
    # Paged rows for data view
    preview_df = df.iloc[offset: offset + limit].copy()

    # Best-effort JSON-safe conversion: replace NaN/inf with None
    def _clean_value(v):
        try:
            if v is None:
                return None
            # pandas/numpy NaN handling without importing numpy explicitly
            if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
                return None
            # Convert pandas Timestamp to ISO string
            if hasattr(v, "isoformat") and not isinstance(v, (str, bytes)):
                # datetime/date objects
                try:
                    return v.isoformat()
                except Exception:
                    pass
            # Convert numpy scalars to python scalars
            if hasattr(v, "item"):
                try:
                    return v.item()
                except Exception:
                    pass
            return v
        except Exception:
            return None

    rows = []
    for rec in preview_df.to_dict(orient="records"):
        rows.append({k: _clean_value(v) for k, v in rec.items()})

    # Prefer processed schema if available, otherwise infer from dataframe dtypes
    processed_cols = db.query(FileColumn).filter(FileColumn.file_id == file_id).all()
    if processed_cols:
        columns = [{"name": c.column_name, "type": c.data_type} for c in processed_cols]
    else:
        inferred = DataProcessor.infer_column_types(df)
        columns = [{"name": c, "type": inferred.get(c, "unknown")} for c in list(df.columns)]

    return {
        "columns": columns,
        "rows": rows,
        "metadata": {
            "fileId": file_record.id,
            "fileName": file_record.file_name,
            "status": file_record.status,
            "totalRows": total_rows,
            "returnedRows": len(rows),
            "offset": offset,
            "limit": limit,
        }
    }

@router.get("/{file_id}/schema")
def get_file_schema(file_id: str, db: Session = Depends(get_db)):
    from services.model_engine import ModelEngine
    
    file_record = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")

    from services.sql_profile_helpers import attach_sql_profile_if_missing

    _sd0 = (file_record.model_config or {}).get("sql_dataset")
    if isinstance(_sd0, dict) and _sd0.get("enabled"):
        attach_sql_profile_if_missing(file_record, db)

    mc = file_record.model_config or {}
    rels = mc.get("relationships") or []
    # Relationship model: same column names as charts/Data view (merged frame), not raw SQL only.
    if isinstance(rels, list) and len(rels) > 0:
        schema_data = ModelEngine.get_merged_schema(file_id, db) or []
        try:
            df = ModelEngine.load_report_dataframe(file_id, db)
            if df is not None and not df.empty:
                preview_df = df.head(500).copy()
                inferred_types = DataProcessor.infer_column_types(preview_df)
                for col in schema_data:
                    col_name = col.get("column_name")
                    if not col_name or col_name not in inferred_types:
                        continue
                    inferred = inferred_types[col_name]
                    if inferred in ("numeric", "datetime"):
                        col["data_type"] = inferred
        except Exception:
            pass
        return schema_data

    sd = mc.get("sql_dataset")
    if isinstance(sd, dict) and sd.get("enabled") and sd.get("query") and (
        sd.get("connection_id") or sd.get("profile_id")
    ):
        from services.sql_execute import execute_paginated_select

        try:
            data = execute_paginated_select(
                sd.get("connection_id") or "",
                sd["query"],
                1,
                0,
                profile_id=sd.get("profile_id"),
                db=db,
            )
            # Do not send unique_count: 0 — the UI treats 0 as real and hides /statistics (means).
            return [
                {
                    "column_name": c.get("name"),
                    "data_type": c.get("type") or "text",
                    "null_count": None,
                    "unique_count": None,
                }
                for c in data.get("columns") or []
            ]
        except Exception:
            pass
        
    # While processing is pending/running, try to infer schema directly from the file
    # so the UI can still build visuals and field wells.
    if file_record.status in ("pending", "processing"):
        if file_record.file_path and os.path.exists(file_record.file_path):
            try:
                df = DataProcessor.read_file(file_record.file_path)
                inferred = DataProcessor.infer_column_types(df.head(500).copy())
                return [{"column_name": c, "data_type": inferred.get(c, "unknown"), "null_count": 0, "unique_count": 0} for c in list(df.columns)]
            except Exception:
                return []
        return []

    schema_data = ModelEngine.get_merged_schema(file_id, db) or []

    # Repair schema types on-the-fly using improved inference.
    # This fixes cases where numeric-looking columns were stored as "categorical"
    # due to numbers being uploaded as strings (e.g. "1,234", "$99.5").
    try:
        if file_record.file_path and os.path.exists(file_record.file_path) and len(schema_data) > 0:
            df = DataProcessor.read_file(file_record.file_path)
            preview_df = df.head(500).copy()
            inferred_types = DataProcessor.infer_column_types(preview_df)

            for col in schema_data:
                col_name = col.get("column_name")
                if not col_name or col_name not in inferred_types:
                    continue
                inferred = inferred_types[col_name]
                if inferred in ("numeric", "datetime"):
                    col["data_type"] = inferred
    except Exception:
        # Never fail the schema endpoint due to inference.
        pass

    return schema_data

@router.get("/{file_id}/statistics")
def get_file_statistics(file_id: str, db: Session = Depends(get_db)):
    from services.model_engine import ModelEngine
    file_record = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")

    def _stats_from_file_columns():
        columns = db.query(FileColumn).filter(FileColumn.file_id == file_id).all()
        if not columns:
            return {}
        out = {}
        for col in columns:
            if col.statistics:
                s = col.statistics
                out[col.column_name] = {
                    "min_value": s.min_value,
                    "max_value": s.max_value,
                    "mean_value": s.mean_value,
                    "median_value": s.median_value,
                    "std_dev": s.std_dev,
                    "null_count": col.null_count,
                    "unique_count": col.unique_count,
                    "top_values": s.top_values,
                }
        return out

    # While processing, still return stats if the report dataframe is already loadable (e.g. DB model tables).
    if file_record.status in ("pending", "processing"):
        try:
            df = ModelEngine.load_report_dataframe(file_id, db)
            if df is not None and not df.empty:
                sample = df.head(50000)
                return ModelEngine.compute_stats_from_dataframe(sample, list(sample.columns))
        except Exception:
            pass
        return {}

    stats = ModelEngine.get_merged_stats(file_id, db) or {}

    # Virtual db-* tables have no FileColumn rows; merged_stats can also return early with only base columns.
    # Always overlay stats from the same dataframe charts use so KPI strip and Data Summary get real numbers.
    try:
        df = ModelEngine.load_report_dataframe(file_id, db)
        if df is not None and not df.empty:
            sample = df.head(50000)
            computed = ModelEngine.compute_stats_from_dataframe(sample, list(sample.columns))
            for k, v in computed.items():
                stats[k] = v
    except Exception as exc:
        print(f"get_file_statistics: dataframe stats overlay failed: {exc}")

    if stats:
        return stats

    return _stats_from_file_columns()

@router.get("/{file_id}/status")
def get_file_status(file_id: str, db: Session = Depends(get_db)):
    file_record = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")
    # Blank-report CSV row_count is 0 even when SQL/relationships supply real data for charts.
    row_count = file_record.row_count or 0
    mc = file_record.model_config or {}
    if row_count == 0 or mc.get("relationships") or (mc.get("sql_dataset") or {}).get("enabled"):
        try:
            from services.model_engine import ModelEngine

            df = ModelEngine.load_report_dataframe(file_id, db)
            if df is not None and not df.empty:
                row_count = int(len(df))
        except Exception as exc:
            print(f"get_file_status: effective row count failed: {exc}")
    return {
        "status": file_record.status,
        "error": file_record.error_message,
        "row_count": row_count,
        "fileName": file_record.file_name,
        "created_at": file_record.created_at.strftime("%Y-%m-%d %H:%M") if file_record.created_at else None,
    }

@router.post("/{file_id}/retry-processing")
async def retry_file_processing(
    file_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Re-run processing for an existing uploaded file.
    Useful when processing failed due to missing dependencies or transient errors.
    """
    file_record = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")

    if file_record.status == "processing":
        return {"status": "processing", "message": "File is already processing"}

    # Clear previous derived metadata so recomputation is clean.
    db.query(FileColumn).filter(FileColumn.file_id == file_id).delete()
    db.query(GraphDefinition).filter(GraphDefinition.file_id == file_id).delete()
    file_record.status = "pending"
    file_record.error_message = None
    db.commit()

    background_tasks.add_task(run_file_processing, file_id)
    return {"status": "pending", "message": "Retry started"}

@router.get("/user/{user_id}")
def get_user_files(user_id: int, db: Session = Depends(get_db)):
    files = db.query(UploadedFile).filter(UploadedFile.user_id == user_id).order_by(UploadedFile.created_at.desc()).all()
    
    result = []
    for f in files:
        viz_count = db.query(GraphDefinition).filter(GraphDefinition.file_id == f.id).count()
        result.append({
            "id": f.id,
            "fileName": f.file_name,
            "uploadDate": f.created_at.strftime("%Y-%m-%d"),
            "uploadDateTime": f.created_at.strftime("%Y-%m-%d %H:%M") if f.created_at else None,
            "recordCount": f.row_count,
            "visualizations": viz_count,
            "status": f.status
        })
    return result

@router.get("/user/{user_id}/activity")
def get_user_activity(user_id: int, db: Session = Depends(get_db)):
    files = db.query(UploadedFile).filter(UploadedFile.user_id == user_id).order_by(UploadedFile.created_at.desc()).limit(10).all()
    
    activities = []
    for f in files:
        activities.append({
            "id": f.id,
            "fileId": f.id,
            "action": f"Uploaded {f.file_name}",
            "timestamp": f.created_at.strftime("%Y-%m-%d %H:%M")
        })
        
        graphs = db.query(GraphDefinition).filter(GraphDefinition.file_id == f.id).order_by(GraphDefinition.id.desc()).all()
        for g in graphs:
            activities.append({
                "id": f"g-{g.id}",
                "fileId": f.id,
                "action": f"Generated {g.graph_type} for {f.file_name}",
                "timestamp": f.created_at.strftime("%Y-%m-%d %H:%M")
            })
            
    return sorted(activities, key=lambda x: x["timestamp"], reverse=True)[:40]

@router.get("/{file_id}/download")
def download_file(file_id: str, db: Session = Depends(get_db)):
    """Download file content (handles both text and binary files)"""
    file_record = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")
    
    if not os.path.exists(file_record.file_path):
        raise HTTPException(status_code=404, detail="File not found on disk")
    
    try:
        file_ext = file_record.file_name.split('.')[-1].lower()
        
        # Try UTF-8 text reading first (for CSV, JSON)
        if file_ext in ['csv', 'json', 'txt']:
            try:
                with open(file_record.file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                return {"content": content, "fileName": file_record.file_name, "isText": True}
            except UnicodeDecodeError:
                # Fall through to binary handling
                pass
        
        # Handle binary files (xlsx, xls) with base64 encoding
        with open(file_record.file_path, 'rb') as f:
            file_bytes = f.read()
            encoded_content = base64.b64encode(file_bytes).decode('utf-8')
        return {"content": encoded_content, "fileName": file_record.file_name, "isText": False, "isBase64": True}
    except Exception as e:
        print(f"ERROR downloading file {file_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error reading file: {str(e)}")

@router.delete("/{file_id}")
def delete_file(
    file_id: str, 
    db: Session = Depends(get_db),
    _=Depends(verify_write_permission)
):
    file_record = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Optional: Delete physical file if it exists
    if file_record.file_path and os.path.exists(file_record.file_path):
        os.remove(file_record.file_path)
        
    db.query(GraphDefinition).filter(GraphDefinition.file_id == file_id).delete()
    db.delete(file_record)
    db.commit()
    return {"message": "File deleted successfully"}


@router.patch("/{file_id}")
def rename_file(
    file_id: str,
    payload: dict = Body(...),
    user_id: Optional[int] = Query(None, description="When set, must match file owner"),
    db: Session = Depends(get_db),
    _=Depends(verify_write_permission)
):
    """Rename report file display name (does not change on-disk path)."""
    file_record = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")
    if user_id is not None and file_record.user_id != user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    new_name = (payload.get("fileName") or payload.get("file_name") or "").strip()
    if not new_name:
        raise HTTPException(status_code=400, detail="fileName is required")
    file_record.file_name = new_name[:400]
    db.commit()
    return {"success": True, "fileName": file_record.file_name}


@router.post("/{file_id}/save-as")
def save_as_file(
    file_id: str,
    payload: dict = Body(...),
    db: Session = Depends(get_db),
    _=Depends(verify_write_permission)
):
    """
    Create a new file entry duplicating an existing report (data + derived metadata + graphs),
    but with a new name. Returns the new file_id.
    """
    new_name = (payload.get("fileName") or payload.get("file_name") or "").strip()
    if not new_name:
        raise HTTPException(status_code=400, detail="fileName is required")

    src = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
    if not src:
        raise HTTPException(status_code=404, detail="Source file not found")

    if not src.file_path or not os.path.exists(src.file_path):
        raise HTTPException(status_code=404, detail="Source file not found on disk")

    # Preserve extension from the original filename/path
    extension = (src.file_name.split(".")[-1] if "." in src.file_name else "").lower()
    if not extension:
        # Fallback to file_path extension
        extension = os.path.splitext(src.file_path)[1].lstrip(".").lower()

    new_id = str(uuid.uuid4())
    new_path = os.path.join(UPLOAD_DIR, f"{new_id}.{extension}") if extension else os.path.join(UPLOAD_DIR, f"{new_id}")

    try:
        shutil.copy2(src.file_path, new_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to copy file: {str(e)}")

    # Create new UploadedFile record
    dst = UploadedFile(
        id=new_id,
        user_id=src.user_id,
        file_name=new_name,
        file_path=new_path,
        row_count=src.row_count,
        column_count=src.column_count,
        status=src.status if src.status else "completed",
        error_message=None,
        model_config=src.model_config
    )
    db.add(dst)
    db.flush()  # ensure dst is present for FK constraints

    # Duplicate columns + statistics
    src_columns = db.query(FileColumn).filter(FileColumn.file_id == file_id).all()
    for c in src_columns:
        new_col = FileColumn(
            file_id=new_id,
            column_name=c.column_name,
            data_type=c.data_type,
            null_count=c.null_count,
            unique_count=c.unique_count
        )
        db.add(new_col)
        db.flush()

        if c.statistics:
            s = c.statistics
            new_stat = ColumnStatistic(
                column_id=new_col.id,
                min_value=s.min_value,
                max_value=s.max_value,
                mean_value=s.mean_value,
                median_value=s.median_value,
                std_dev=s.std_dev,
                top_values=s.top_values
            )
            db.add(new_stat)

    # Duplicate graphs
    src_graphs = db.query(GraphDefinition).filter(GraphDefinition.file_id == file_id).all()
    for g in src_graphs:
        new_graph = GraphDefinition(
            file_id=new_id,
            graph_type=g.graph_type,
            x_axis=g.x_axis,
            y_axis=g.y_axis,
            aggregation=g.aggregation,
            cached_data=g.cached_data,
            options=g.options
        )
        db.add(new_graph)

    db.commit()
    return {"file_id": new_id, "fileName": new_name}

@router.get("/{file_id}/model")
def get_file_model(file_id: str, db: Session = Depends(get_db)):
    """Retrieve the saved model configuration (tables & relationships, SQL dataset library)."""
    from services.sql_dataset_library import normalize_sql_datasets

    file_record = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")

    base = file_record.model_config or {"tables": [], "relationships": []}
    mc, migrated = normalize_sql_datasets(base)
    if migrated:
        file_record.model_config = mc
        db.commit()
    return mc

@router.put("/{file_id}/model")
def update_file_model(
    file_id: str,
    payload: dict = Body(...),
    db: Session = Depends(get_db),
    _=Depends(verify_write_permission)
):
    """Save model configuration; merges with existing so SQL dataset library is not wiped by partial saves."""
    file_record = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")

    existing = file_record.model_config or {}
    merged = {**existing, **payload}
    file_record.model_config = merged
    db.commit()
    return {"message": "Model configuration saved successfully"}


@router.post("/{file_id}/model/build-query")
def build_model_aggregate_query(
    file_id: str,
    body: dict = Body(...),
    db: Session = Depends(get_db),
):
    """
    Build a single-connection GROUP BY query from saved relationships (star schema).
    Body: fact_table_id, dimension_table_id, dimension_column, measure_column, aggregation (optional).
    """
    from services.model_sql_builder import build_aggregate_by_dimension_sql

    file_record = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")

    model = file_record.model_config or {}
    try:
        sql, connection_id = build_aggregate_by_dimension_sql(
            model,
            body.get("fact_table_id"),
            body.get("dimension_table_id"),
            body.get("dimension_column"),
            body.get("measure_column"),
            body.get("aggregation") or "SUM",
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"sql": sql, "connection_id": connection_id}


@router.put("/{file_id}/sql-dataset")
def save_sql_dataset(
    file_id: str,
    body: dict = Body(...),
    db: Session = Depends(get_db),
):
    """Persist a custom SQL query as the report's primary dataset; adds/updates an entry in sql_datasets library."""
    file_record = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")

    from services.sql_safe import validate_select_only
    from services.sql_dataset_library import normalize_sql_datasets, upsert_library_entry

    q = (body.get("query") or "").strip()
    ok, err = validate_select_only(q)
    if not ok:
        raise HTTPException(status_code=400, detail=err)

    mc, _ = normalize_sql_datasets(file_record.model_config or {})
    name = (body.get("name") or "SQL dataset").strip()[:200]
    dataset_id = (body.get("id") or "").strip() or str(uuid.uuid4())
    cols = body.get("columns")
    if cols is not None and not isinstance(cols, list):
        cols = []

    sql_ds = upsert_library_entry(
        mc,
        dataset_id=dataset_id,
        name=name,
        query=q,
        connection_id=body.get("connection_id"),
        columns=cols if isinstance(cols, list) else [],
        profile_id=(body.get("profile_id") or "").strip() or None,
    )
    sql_ds["enabled"] = bool(body.get("enabled", True))
    mc["sql_dataset"] = sql_ds

    file_record.model_config = mc
    db.commit()
    return {"success": True, "sql_dataset": mc["sql_dataset"], "sql_datasets": mc.get("sql_datasets") or []}


@router.delete("/{file_id}/sql-dataset")
def clear_sql_dataset(file_id: str, db: Session = Depends(get_db)):
    """Stop using SQL as the active report dataset; keeps saved library entries."""
    file_record = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")
    mc = dict(file_record.model_config or {})
    if "sql_dataset" in mc:
        del mc["sql_dataset"]
    mc["active_sql_dataset_id"] = None
    file_record.model_config = mc
    db.commit()
    return {"success": True}


@router.post("/{file_id}/sql-datasets/{dataset_id}/activate")
def activate_sql_dataset_entry(
    file_id: str,
    dataset_id: str,
    db: Session = Depends(get_db),
):
    """Set the given library entry as the active report dataset (re-run query for schema/Data view)."""
    file_record = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")

    from services.sql_dataset_library import activate_library_entry, normalize_sql_datasets

    mc, _ = normalize_sql_datasets(file_record.model_config or {})
    sql_ds = activate_library_entry(mc, dataset_id)
    if not sql_ds:
        raise HTTPException(status_code=404, detail="Dataset not found")
    file_record.model_config = mc
    db.commit()
    return {"success": True, "sql_dataset": sql_ds}


@router.patch("/{file_id}/sql-datasets/{dataset_id}")
def rename_sql_dataset_entry(
    file_id: str,
    dataset_id: str,
    body: dict = Body(...),
    db: Session = Depends(get_db),
):
    from services.sql_dataset_library import normalize_sql_datasets
    from services.sql_dataset_library import now_iso

    file_record = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")

    mc, _ = normalize_sql_datasets(file_record.model_config or {})
    lib = mc.get("sql_datasets") or []
    name = (body.get("name") or "").strip()[:200]
    if not name:
        raise HTTPException(status_code=400, detail="name is required")

    found = False
    for e in lib:
        if e.get("id") == dataset_id:
            e["name"] = name
            e["updated_at"] = now_iso()
            found = True
            break
    if not found:
        raise HTTPException(status_code=404, detail="Dataset not found")

    mc["sql_datasets"] = lib
    if mc.get("active_sql_dataset_id") == dataset_id and isinstance(mc.get("sql_dataset"), dict):
        mc["sql_dataset"]["name"] = name
        mc["sql_dataset"]["updated_at"] = now_iso()

    file_record.model_config = mc
    db.commit()
    return {"success": True, "sql_datasets": lib}


@router.delete("/{file_id}/sql-datasets/{dataset_id}")
def delete_sql_dataset_entry(file_id: str, dataset_id: str, db: Session = Depends(get_db)):
    from services.sql_dataset_library import normalize_sql_datasets, remove_library_entry

    file_record = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")

    mc, _ = normalize_sql_datasets(file_record.model_config or {})
    mc = remove_library_entry(mc, dataset_id)
    file_record.model_config = mc
    db.commit()
    return {"success": True, "sql_datasets": mc.get("sql_datasets") or [], "sql_dataset": mc.get("sql_dataset")}
