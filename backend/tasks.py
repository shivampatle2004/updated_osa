import os
import pandas as pd
from database import SessionLocal
from models import UploadedFile, FileColumn, ColumnStatistic, DataVaultItem
from services.data_processor import DataProcessor

import concurrent.futures


def run_file_processing(file_id: str):
    print(f"DEBUG: Processing file: {file_id}")
    db = SessionLocal()
    try:
        file_record = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
        if not file_record:
            return "File record not found"

        file_record.status = "processing"
        db.commit()

        # Load file
        print(f"DEBUG: Reading file from path: {file_record.file_path}")
        df = DataProcessor.read_file(file_record.file_path)
        
        file_record.row_count = len(df)
        file_record.column_count = len(df.columns)
        
        print(f"DEBUG: Inferring types for {len(df.columns)} columns")
        col_types = DataProcessor.infer_column_types(df)
        
        column_configs = []
        
        # Parallelize Column Stats Calculation
        print(f"DEBUG: Calculating column stats in parallel")
        with concurrent.futures.ThreadPoolExecutor() as executor:
            # Map column name to future
            future_to_col = {
                executor.submit(DataProcessor.get_column_stats, df, col, dtype): (col, dtype)
                for col, dtype in col_types.items()
            }
            
            # Process results as they complete (or just iterate)
            results = []
            for future in concurrent.futures.as_completed(future_to_col):
                col_name, col_type = future_to_col[future]
                try:
                    stats = future.result()
                    results.append((col_name, col_type, stats))
                except Exception as exc:
                    print(f"WARNING: Stats calculation failed for {col_name}: {exc}")

        # Write stats to DB (Sequential to avoid locking/session issues)
        for col_name, col_type, stats in results:
            db_column = FileColumn(
                file_id=file_record.id,
                column_name=col_name,
                data_type=col_type,
                null_count=stats["null_count"],
                unique_count=stats["unique_count"]
            )
            db.add(db_column)
            db.flush() # Get ID for stats

            db_stats = ColumnStatistic(
                column_id=db_column.id,
                min_value=stats.get("min_value"),
                max_value=stats.get("max_value"),
                mean_value=stats.get("mean_value"),
                median_value=stats.get("median_value"),
                std_dev=stats.get("std_dev"),
                top_values=stats.get("top_values")
            )
            db.add(db_stats)
            column_configs.append({"name": col_name, "type": col_type})

        # Optional graph recommendations are disabled — users add visuals from the ribbon.
        print(f"DEBUG: Skipping auto-generated charts (recommendations disabled)")

        file_record.status = "completed"
        db.commit()

        # ── Auto-save to DataVault ────────────────────────────────────────────
        try:
            _save_to_data_vault(db, file_record)
        except Exception as vault_err:
            # DataVault save is non-critical — never fail the main task for it
            print(f"WARNING: DataVault auto-save failed for {file_id}: {vault_err}")
        # ─────────────────────────────────────────────────────────────────────

        print(f"DEBUG: Successfully processed {file_id}")
        return f"Processed {file_id} successfully"

    except Exception as e:
        db.rollback()
        print(f"ERROR: Failed to process {file_id}: {str(e)}")
        file_record = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
        if file_record:
            file_record.status = "failed"
            file_record.error_message = str(e)
            db.commit()
        return f"Error processing {file_id}: {str(e)}"
    finally:
        db.close()

def run_sql_processing(file_id: str):
    print(f"DEBUG: Processing SQL file: {file_id}")
    from services.sql_engine import SQLEngine
    from database import engine as local_engine
    import sqlalchemy
    from sqlalchemy import inspect
    
    db = SessionLocal()
    try:
        file_record = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
        if not file_record:
            return "File record not found"

        file_record.status = "processing"
        db.commit()

        # 1. Execute SQL Commands
        print(f"DEBUG: Parsing and executing SQL from {file_record.file_path}")
        commands = SQLEngine.parse_sql_file(file_record.file_path)
        SQLEngine.execute_on_local_db(commands, local_engine)

        # 2. Heuristically find the primary table to analyze
        # We look for tables that are NOT internal system tables and have data
        inspector = inspect(local_engine)
        table_names = inspector.get_table_names()
        
        # Exclude app's own tables
        app_tables = ["users", "uploaded_files", "file_columns", "column_statistics", "graph_definitions", "user_db_connections"]
        candidate_tables = [t for t in table_names if t not in app_tables]
        
        if not candidate_tables:
            # If no new tables, maybe it modified existing ones? 
            # For now, let's assume one of the candidate tables is the target.
            raise ValueError("No data tables found after SQL execution.")

        # Find the table with data (preferring the one with most data if multiple)
        primary_table = None
        max_rows = -1
        
        for table in candidate_tables:
            try:
                row_count = db.execute(sqlalchemy.text(f"SELECT COUNT(*) FROM {table}")).scalar()
                if row_count > max_rows:
                    max_rows = row_count
                    primary_table = table
            except:
                continue

        if not primary_table:
            raise ValueError("Could not find any filled tables in the SQL script.")

        file_record.row_count = max_rows
        print(f"DEBUG: Identified primary table '{primary_table}' with {max_rows} rows")

        # 3. Extract metadata from the primary table
        # We can use a SELECT * query with LIMIT 0 to get column names or use inspector
        df = pd.read_sql_table(primary_table, local_engine)
        file_record.column_count = len(df.columns)
        
        col_types = SQLEngine.infer_column_types(df)
        column_configs = []
        
        # Calculate stats and save columns (Similar to run_file_processing)
        for col_name, col_type in col_types.items():
            stats = DataProcessor.get_column_stats(df, col_name, col_type)
            
            db_column = FileColumn(
                file_id=file_record.id,
                column_name=col_name,
                data_type=col_type,
                null_count=stats["null_count"],
                unique_count=stats["unique_count"]
            )
            db.add(db_column)
            db.flush()

            db_stats = ColumnStatistic(
                column_id=db_column.id,
                min_value=stats.get("min_value"),
                max_value=stats.get("max_value"),
                mean_value=stats.get("mean_value"),
                median_value=stats.get("median_value"),
                std_dev=stats.get("std_dev"),
                top_values=stats.get("top_values")
            )
            db.add(db_stats)
            column_configs.append({"name": col_name, "type": col_type})

        # Auto-generated charts disabled for SQL-import flows — users add visuals manually.
        print(f"DEBUG: Skipping auto-generated charts for SQL file")

        file_record.status = "completed"
        db.commit()

        print(f"DEBUG: Successfully processed SQL {file_id}")
        return f"Processed SQL {file_id} successfully"

    except Exception as e:
        db.rollback()
        print(f"ERROR: Failed to process SQL {file_id}: {str(e)}")
        file_record = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
        if file_record:
            file_record.status = "failed"
            file_record.error_message = str(e)
            db.commit()
        return f"Error processing SQL {file_id}: {str(e)}"
    finally:
        db.close()


# ─────────────────────────────────────────────────────────────────────────────
# DataVault auto-save helper
# ─────────────────────────────────────────────────────────────────────────────

_EXT_TO_SOURCE = {
    "csv":     "csv",
    "tsv":     "csv",
    "txt":     "csv",
    "xlsx":    "excel",
    "xls":     "excel",
    "json":    "json",
    "parquet": "parquet",
    "sql":     "sql",
}


def _save_to_data_vault(db, file_record: UploadedFile):
    """
    Upsert a DataVaultItem for the given completed UploadedFile.
    Called by run_file_processing (and optionally run_sql_processing) on success.
    This is a best-effort write — callers must catch any exceptions.
    """
    # Skip placeholder blank-report stubs
    mc = file_record.model_config or {}
    if mc.get("blank_report"):
        return

    fn = (file_record.file_name or "").lower()
    ext = fn.rsplit(".", 1)[-1] if "." in fn else ""
    source_name = _EXT_TO_SOURCE.get(ext, "file")

    # Avoid duplicates — update if already exists
    existing = db.query(DataVaultItem).filter(
        DataVaultItem.file_id == file_record.id
    ).first()

    if existing:
        existing.name = file_record.file_name or existing.name
        existing.row_count = file_record.row_count or existing.row_count
        existing.column_count = file_record.column_count or existing.column_count
        db.commit()
        print(f"DEBUG: DataVault entry updated for {file_record.id}")
        return

    item = DataVaultItem(
        user_id=file_record.user_id,
        name=file_record.file_name or f"Dataset {file_record.id[:8]}",
        source_name=source_name,
        dataset_type="file",
        file_id=file_record.id,
        table_name=None,
        row_count=file_record.row_count or 0,
        column_count=file_record.column_count or 0,
        metadata_json={
            "original_path": file_record.file_path or "",
            "status": file_record.status,
        },
    )
    db.add(item)
    db.commit()
    print(f"DEBUG: DataVault entry created for {file_record.id} ({source_name})")
