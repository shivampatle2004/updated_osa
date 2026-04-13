# ETL Pipeline Architecture Overview

## Quick Summary
The **One-Stop Analytics ETL system** is a **metadata-driven, visually-configured data pipeline orchestrator** that eliminates manual ETL coding. Instead of writing Python scripts, users define pipelines through the UI, and the system executes them with built-in data quality checks, transformations, and monitoring.

## Architecture Components

### 1. **Frontend (React/Vite)**
- **ETLDashboard.jsx**: Main UI with 7 tabs:
  - **Connections**: Configure database credentials (PostgreSQL, MySQL, Oracle, SQLite, etc.)
  - **Pipelines**: Define workflows with Extract→Transform→Load nodes
  - **Transforms**: Add column/table-level transformations (cast, filter, regex, etc.)
  - **Quality**: Data quality checks (null checks, type validation, ranges, regex patterns)
  - **Schedule**: Cron-based or interval scheduling with retry logic
  - **Monitor**: Real-time job execution tracking with logs
  - **Audit**: User action history

### 2. **Backend (FastAPI + SQLAlchemy)**

```
┌─ ETL Router (/api/etl)
│  └─ REST endpoints for connections, pipelines, jobs, schedules, quality, transforms, audit
│
├─ ETL Executor (Orchestrator)
│  ├─ Loads pipeline definition from database
│  ├─ Creates job and step records
│  └─ Invokes DAG Runner
│
├─ DAG Engine (DAG Runner)
│  ├─ Builds execution layers using topological sort (Kahn's algorithm)
│  ├─ Executes nodes in parallel within each layer (ThreadPoolExecutor)
│  ├─ Handles retries, fail-fast, conditional branching
│  └─ Returns execution results per node
│
├─ ETL Connector
│  ├─ read_source(): Extract from any database
│  ├─ write_target(): Load to any database
│  └─ Supports batch processing
│
├─ Transformer
│  ├─ apply_transforms(): Column & table-level operations
│  └─ Supports 20+ operations (cast, filter, regex, etc.)
│
├─ Quality Checker
│  ├─ Pre-load & post-load validation
│  └─ Configurable failure handling (reject/stop/warn)
│
└─ Scheduler + Database
   ├─ Stores pipeline definitions, connections, jobs, logs, audit trail
   └─ Uses PostgreSQL + SQLAlchemy ORM
```

### 3. **Execution Flow**

```
1. User clicks "Run" pipeline (REST API called)
   ↓
2. Job created with status="pending"
   ↓
3. Background thread spawned (separate session to avoid DB conflicts)
   ↓
4. Executor loads pipeline definition (nodes, edges, rules, quality checks)
   ↓
5. DAG Runner executes layers sequentially:
   - Layer 1: All Extract nodes in parallel
   - Layer 2: All Transform nodes in parallel
   - Layer 3: All Load nodes in parallel
   ↓
6. Each node execution:
   - Reads from upstream data
   - Applies transformations
   - Writes to target database
   - Logs recorded
   - Step status updated
   ↓
7. All logs flushed, job marked complete
```

### 4. **Key Files**

| File | Purpose |
|------|---------|
| `frontend/src/pages/ETLDashboard.jsx` | Complete UI with all tabs |
| `backend/routers/etl.py` | REST API (787 lines) |
| `backend/services/etl_executor.py` | Job orchestration |
| `backend/services/etl_dag_engine.py` | DAG execution with parallelization |
| `backend/services/etl_connector.py` | Database connectivity |
| `backend/services/etl_transformer.py` | Transformation rules |
| `backend/services/etl_quality.py` | Data quality validation |
| `backend/models.py` | SQLAlchemy ORM schemas |

---

## The Bug & The Fix

### Problem: SQLAlchemy Session State Error
```
[ETL ERROR] DAG execution error: Method 'commit()' can't be called here;
method '_prepare_impl()' is already in progress...
```

**Root Cause:**
- DAG nodes execute in **parallel threads** (ThreadPoolExecutor)
- Each thread called `db.commit()` immediately after logging
- Multiple threads trying to commit the **same SQLAlchemy session** caused state corruption
- SQLAlchemy sessions are NOT thread-safe for writes

### Solution: Thread-Safe Transaction Management
```python
# BEFORE (problematic)
def _log(self, job_id, step_id, level, message):
    entry = models.ETLJobLog(...)
    self.db.add(entry)
    self.db.commit()  # ❌ Immediate commit from threads

# AFTER (fixed)
def _log(self, job_id, step_id, level, message):
    entry = models.ETLJobLog(...)
    with self.log_lock:
        self.log_buffer.append(entry)  # ✅ Buffer logs thread-safely

def _flush_logs(self):
    with self.log_lock:
        for entry in self.log_buffer:
            self.db.add(entry)
        self.log_buffer.clear()
    self.db.flush()  # ✅ Single flush after all execution
    
def _update_step(self, step, **kwargs):
    for k, v in kwargs.items():
        setattr(step, k, v)
    self.db.flush()  # ✅ Use flush instead of commit during execution
```

**Key Changes:**
1. **Buffer logs** with thread lock instead of committing immediately
2. **Use `flush()` instead of `commit()`** during DAG execution
3. **Flush all logs once** after DAG completes (single transaction)
4. **Final commit** only at safe points when session state is consistent

---

## Testing the Fix

Run a test pipeline:
1. Go to **Connections** tab → Add a database connection
2. Go to **Pipelines** tab → Create a pipeline with:
   - Source: Your database
   - Target: Local SQLite
3. Click **Run**
4. Go to **Monitor** tab → Check job status and logs
5. Look for job status = "success" and no error messages

The pipeline should now complete successfully without the `commit()` SQLAlchemy error!
