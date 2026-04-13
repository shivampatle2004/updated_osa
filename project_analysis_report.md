# 📊 OneStopAnalysis (OSA) — Comprehensive Project Analysis Report

> **Project Location:** `d:\onestopanalysis_sth`
> **Analysis Date:** April 12, 2026
> **Analyst:** Antigravity AI

---

## 🧭 Executive Summary

**OneStopAnalysis (OSA)** is a full-stack, self-hosted Business Intelligence and Data Engineering platform. It is a **Power BI-inspired analytics suite** that bundles five major capabilities into one unified application:

| Pillar | Description |
|---|---|
| 📥 **Data Ingestion** | Upload files (CSV, Excel, JSON, Parquet) or connect to 35+ data sources via DLT connectors |
| 🔄 **ETL Pipelines** | Visual pipeline builder with DAG execution, transforms, scheduling, and quality checks |
| 📊 **BI Workspace** | Power BI-like canvas with drag-and-drop charts, pivot tables, maps, slicers |
| 🤖 **AI/Smart Analytics** | AI-suggested visualizations, Smart Narrative, Q&A visual, Influencers |
| 🏗️ **Data Vault** | Central dataset registry, SQL datasets library, and model relationships |

---

## 🏗️ High-Level System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER BROWSER                                 │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────┐ │
│  │  Landing &  │  │  BI Workspace│  │ETL Dashboard │  │Dashboard │ │
│  │  Auth Pages │  │ (Power BI UI)│  │ (7 Tabs)     │  │(Reports) │ │
│  └──────┬──────┘  └──────┬───────┘  └──────┬───────┘  └────┬─────┘ │
│         │                │                  │               │        │
│         └────────────────┴──────────────────┴───────────────┘        │
│                          React + Vite SPA (Port 5173 dev)            │
└─────────────────────────────────────┬───────────────────────────────┘
                                      │ HTTP / REST API
                                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    FastAPI Backend  (Port 8010)                       │
│                                                                       │
│  Auth   Files   Graphs   SQL   ETL   Connectors   Data Vault  Smart  │
│  ────   ─────   ──────   ───   ───   ──────────   ─────────   ─────  │
│  /signup /api/files  /api/graphs  /api/etl  /api/connectors  /api/.. │
│                                                                       │
│  ┌───────────────┐  ┌──────────────┐  ┌──────────────────────────┐  │
│  │   Services    │  │  Connectors  │  │  ETL Engine              │  │
│  │ - Graph Engine│  │ (35+ Sources)│  │ - ETLExecutor            │  │
│  │ - Model Engine│  │ - DLT-based  │  │ - ETLScheduler (APSched) │  │
│  │ - SQL Engine  │  │ - CSV/Excel  │  │ - ETLTransformer         │  │
│  │ - SmartAnalyz │  │ - MongoDB    │  │ - ETLQuality             │  │
│  │ - DataProcessor│  │ - Salesforce│  │ - ETLDelta               │  │
│  └───────────────┘  │ - Postgres   │  └──────────────────────────┘  │
│                     │ - S3, Snowfl.│                                  │
│                     └──────────────┘                                  │
│                                                                       │
│  ┌────────────────────────────────────────────────┐                  │
│  │             Database Layer                      │                  │
│  │  Primary: PostgreSQL  |  Fallback: SQLite       │                  │
│  │  ORM: SQLAlchemy  |  Migrations: Alembic        │                  │
│  └────────────────────────────────────────────────┘                  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 📁 Project Directory Structure

```
onestopanalysis_sth/
├── 📄 ETL_ARCHITECTURE.md          # ETL system design docs
├── 📄 PHASE1_IMPLEMENTATION.md     # Phase 1 feature notes
├── 📄 QUICK_START.md               # Setup guide
├── 📄 SINGLE_PORT_SETUP.md         # Single-port deployment guide
├── 🗄️ analytics.db                 # SQLite fallback database
├── 🔧 setup.bat                    # Windows setup script
│
├── 📂 backend/                     # FastAPI Python backend
│   ├── main.py                     # App entry point, router registration
│   ├── database.py                 # DB engine, sessions, init
│   ├── models.py                   # SQLAlchemy ORM models (20+ tables)
│   ├── schemas.py                  # Pydantic request/response schemas
│   ├── auth_utils.py               # bcrypt password hashing
│   ├── tasks.py                    # Background task helpers
│   │
│   ├── routers/                    # API route handlers
│   │   ├── files.py                # File upload, download, schema
│   │   ├── graphs.py               # Chart data generation
│   │   ├── sql.py                  # SQL query execution
│   │   ├── etl.py                  # Full ETL CRUD + run + audit
│   │   ├── db.py                   # Remote DB connections (saved)
│   │   ├── connections.py          # BI Saved Connections
│   │   ├── smart.py                # AI chart suggestions
│   │   ├── visuals.py              # Custom visual renderer
│   │   ├── automate.py             # Power Automate trigger
│   │   ├── modular_connectors.py   # DLT connector wizard API
│   │   └── data_vault.py           # Data Vault registry
│   │
│   ├── services/                   # Core business logic
│   │   ├── graph_engine.py         # Chart data computation (29KB)
│   │   ├── model_engine.py         # BI data model + join graph
│   │   ├── sql_engine.py           # SQL execution + profiling
│   │   ├── etl_executor.py         # ETL DAG runner (17KB)
│   │   ├── etl_transformer.py      # Transform rule engine
│   │   ├── etl_scheduler.py        # APScheduler integration
│   │   ├── etl_quality.py          # Data quality validation
│   │   ├── etl_connector.py        # Connection test + encrypt
│   │   ├── etl_delta.py            # Delta detection (incremental loads)
│   │   ├── smart_analyzer.py       # AI chart recommendation
│   │   ├── data_processor.py       # Pandas data processing
│   │   ├── remote_db_manager.py    # Remote DB query runner
│   │   ├── sql_dataset_library.py  # Saved SQL dataset library
│   │   ├── model_data_loader.py    # data loader for model
│   │   └── credentials_crypto.py   # Fernet encryption for passwords
│   │
│   └── connectors/                 # 35+ data source adapters
│       ├── registry.py             # Connector catalog seeder
│       ├── dlt_connector.py        # DLT universal connector (36KB)
│       ├── csv_connector.py        # CSV file connector
│       ├── excel_connector.py      # Excel file connector
│       ├── postgres_connector.py   # PostgreSQL connector
│       ├── mysql_connector.py      # MySQL connector
│       ├── mongodb_connector.py    # MongoDB connector
│       ├── salesforce_connector.py # Salesforce connector
│       ├── snowflake_connector.py  # Snowflake connector
│       ├── s3_connector.py         # Amazon S3 connector
│       ├── zoho_connector.py       # Zoho CRM connector
│       ├── tally_connector.py      # Tally ERP connector (11KB)
│       ├── rest_api_connector.py   # Generic REST API connector
│       ├── d365_connector.py       # Dynamics 365 connector
│       ├── sqlite_connector.py     # SQLite connector
│       └── [airtable, hubspot, shopify, github, slack, ...] # DLT-sourced
│
└── 📂 frontend/                    # React/Vite frontend
    ├── vite.config.js              # Vite + proxy config
    ├── package.json                # npm dependencies
    ├── tailwind.config.ts          # Tailwind configuration
    │
    └── src/
        ├── App.jsx                 # Root router + auth state
        ├── main.jsx                # React DOM entry
        │
        ├── pages/
        │   ├── LandingPage.jsx     # Marketing/home page
        │   ├── AnalyticsDashboard.jsx  # Routes to BIWorkspace
        │   ├── Dashboard.jsx       # File list + chart workspace
        │   ├── ETLDashboard.jsx    # 7-tab ETL management UI
        │   ├── AuthPage.jsx        # Auth gateway
        │   ├── SignIn.jsx          # Login form
        │   └── CreateAccount.jsx   # Registration form
        │
        └── components/
            ├── BIWorkspace.jsx         # 🌟 Main BI canvas (158KB!)
            ├── BIRibbon.jsx            # Top ribbon toolbar (55KB)
            ├── BIModelView.jsx         # Data model view (92KB)
            ├── BISavedConnectionsPanel.jsx # Connections panel (43KB)
            ├── DynamicChart.jsx        # 30+ chart types (134KB)
            ├── BIDashboardCanvas.jsx   # Canvas drag-n-drop (30KB)
            ├── BIConnectorsModal.jsx   # Data source picker
            ├── BIConnectionConfigModal.jsx # Connector config form
            ├── BIVisualizationsPane.jsx    # Visual type picker
            ├── BIInsightsPanel.jsx     # AI chart insights
            ├── BIQuickMeasurePanel.jsx # DAX-like quick measures
            ├── BISqlDatasetModal.jsx   # SQL dataset editor
            ├── SmartNarrativeVisual.jsx # AI text summary
            ├── InfluencersVisual.jsx   # Key influencer analysis
            ├── QnaVisual.jsx           # Q&A natural language
            ├── PowerAutomateVisual.jsx # Power Automate trigger
            ├── PowerAppsVisual.jsx     # Power Apps canvas
            ├── InstallVisualModal.jsx  # Custom visual installer
            └── CustomVisualRenderer.jsx # Custom visual sandbox
```

---

## 🔄 Complete Application Flow

### 1. 🚀 Application Startup

```
Browser → / (root URL)
  │
  ├── App.jsx checks localStorage for:
  │     isAuthenticated, userId, userName, theme
  │
  ├── Route "/" → AnalyticsDashboard → BIWorkspace (blank)
  ├── Route "/dashboard" → Dashboard (file list)
  ├── Route "/etl" → ETLDashboard
  └── Route "/analytics/:fileId" → AnalyticsDashboard (with file)

Backend Startup (main.py):
  1. init_db() — creates all 20+ tables if not exist
  2. Demo user created (demo@example.com / demo123)
  3. seed_connectors() — populates connector_catalog table
  4. load_all_schedules() — restores APScheduler jobs from DB
```

---

### 2. 🔐 Authentication Flow

```
User → SignIn / CreateAccount Page
  │
  ├── POST /api/login   → { email, password }
  │     Backend: bcrypt verify → returns { user.id, user.email, full_name }
  │     Frontend: stores in localStorage (userId, userName, isAuthenticated)
  │
  └── POST /api/signup  → { email, password, full_name }
        Backend: bcrypt hash → User model → DB insert
```

> **No JWT tokens** — Authentication is localStorage-based with user ID. Simple session-like approach.

---

### 3. 📥 Data Ingestion Flow (Files)

```
User clicks "Get Data" → BIConnectorsModal opens
  │
  ├── Option A: Upload File (CSV / Excel / JSON / Parquet)
  │     │
  │     ├── POST /api/files/upload
  │     │     Backend (files.py + data_processor.py):
  │     │       1. Save file to /uploads directory
  │     │       2. Parse with pandas
  │     │       3. Compute column stats (min/max/mean/top_values)
  │     │       4. Store UploadedFile + FileColumn + ColumnStatistic in DB
  │     │       5. Return file_id
  │     │
  │     └── GET /api/files/{file_id}/schema → column list + types
  │
  ├── Option B: Remote Database (Saved Connections)
  │     │
  │     ├── BISavedConnectionsPanel → GET /api/connections
  │     ├── User picks table → GET /api/db/{conn_id}/tables
  │     └── Data loaded into BI model via model_engine.py
  │
  └── Option C: DLT Connector (Shopify, HubSpot, Salesforce, etc.)
        │
        ├── GET /api/connectors → connector catalog list
        ├── User fills DynamicForm (schema-driven)
        └── POST /api/connectors/{engine}/fetch → dlt_connector.py runs pipeline
```

---

### 4. 📊 BI Analytics Workspace Flow

```
AnalyticsDashboard → BIWorkspace (Central Hub)
  │
  BIWorkspace state:
    - pages: [{ visuals: [{ type, fields, filters, ... }] }]
    - dataModel: { tables, relationships, measures }
    - activeVisual: currently selected visual
  │
  ├── BIRibbon (top toolbar)
  │     └── Home | Insert | Modeling | View | File tabs
  │         each tab has sub-actions (new visual, import data, theme, etc.)
  │
  ├── BIDashboardCanvas (main canvas)
  │     └── drag-to-position, resize visuals
  │         each visual = DynamicChart / BISpecial / CustomVisual
  │
  ├── BIFieldsPane (left or right)
  │     └── list of tables + columns from data model
  │         drag fields into visual buckets (X-axis, Y-axis, Legend, etc.)
  │
  ├── BIVisualizationsPane (visual type picker)
  │     └── 30+ chart types: bar, line, pie, card, table, matrix, map,
  │         scatter, gauge, treemap, waterfall, funnel, heatmap, etc.
  │
  ├── BIFiltersPane (right)
  │     └── page-level and visual-level filters
  │
  └── BIModelView (data modeling)
        └── drag tables, create relationships, edit columns
            communicate with GET/POST /api/files/model
```

---

### 5. 📈 Chart Rendering Flow

```
User drags field onto visual on canvas
  │
  BIWorkspace updates visual config (fields, aggregation, filters)
  │
  DynamicChart receives props:
    { type, data, xField, yField, legend, filters, options }
  │
  ├── Local data path (file-based):
  │     GET /api/graphs/data/{file_id}
  │       params: x_axis, y_axis, aggregation, chart_type
  │       Backend: graph_engine.py → pandas groupby/agg → return {labels, values}
  │
  ├── Remote DB path:
  │     GET /api/db/{conn_id}/query
  │       Backend: remote_db_manager.py → SQL query → return rows
  │
  └── DynamicChart renders using:
        Recharts (bar, line, pie, scatter, area, radar, treemap, etc.)
        react-simple-maps (choropleth maps)
        Custom SVG (gauge, KPI card, matrix)
```

---

### 6. 🔄 ETL Pipeline Flow

```
User opens /etl → ETLDashboard (7 tabs)
  │
  Tabs: Connections | Pipelines | Transforms | Quality | Schedule | Monitor | Audit
  │
  ── Step 1: Create Connection ──────────────────────────────────────
  │   POST /api/etl/connections → saves ETLConnection (password encrypted via Fernet)
  │   POST /api/etl/connections/test → etl_connector.py tests live connection
  │
  ── Step 2: Create Pipeline ────────────────────────────────────────
  │   POST /api/etl/pipelines → creates ETLPipeline + 3 auto nodes (extract/transform/load)
  │   Saves version snapshot (ETLPipelineVersion)
  │
  ── Step 3: Add Transforms ─────────────────────────────────────────
  │   POST /api/etl/transforms → ETLTransformRule
  │   Operations: cast | formula | arithmetic | to_upper | to_lower | trim |
  │               replace | replace_null | rename | date_format | filter |
  │               drop_duplicates | sort | limit | add_column | sql_rule
  │
  ── Step 4: Add Quality Checks ─────────────────────────────────────
  │   POST /api/etl/quality-checks → ETLDataQualityCheck
  │   Rules: not_null | type_check | range | regex | unique | min_rows | custom_sql
  │   On failure: reject_row | stop | warn
  │
  ── Step 5: Schedule ───────────────────────────────────────────────
  │   POST /api/etl/schedules → ETLSchedule
  │   Types: cron | daily | hourly | interval
  │   APScheduler registers the job → auto-triggers on schedule
  │
  ── Step 6: Run Pipeline ───────────────────────────────────────────
  │   POST /api/etl/pipelines/{id}/run
  │   Backend creates ETLJob (pending) → starts background thread
  │   ETLExecutor.run_job():
  │     For each node (extract → transform → load):
  │       1. Create ETLJobStep record
  │       2. Execute node logic (pull data, apply transforms, push data)
  │       3. Log each step to ETLJobLog
  │       4. Handle retries if fail_fast=false
  │     Update ETLJob.status (success/failed/partial)
  │
  ── Step 7: Monitor ────────────────────────────────────────────────
  │   GET /api/etl/jobs/{job_id} → status, rows_extracted, rows_loaded
  │   GET /api/etl/jobs/{job_id}/steps → per-node step status
  │   GET /api/etl/jobs/{job_id}/logs → detailed log messages
  │
  └── Audit Tab: GET /api/etl/audit/{user_id} → all actions logged
```

---

### 7. 🔌 Connector Ecosystem Flow

```
User clicks "Get Data" → BIConnectorsModal → picks a source
  │
  GET /api/connectors → ConnectorCatalog (seeded at startup)
    Returns: { name, engine, config_schema (JSON Schema), icon_url }
  │
  Frontend: DynamicForm renders fields from config_schema
    (no hardcoded form — fully schema-driven)
  │
  User fills form → POST /api/connectors/{engine}/test → validate config
  │
  User clicks "Fetch" → POST /api/connectors/{engine}/fetch
    Backend:
      ├── dlt_connector.py → runs dlt pipeline for cloud sources:
      │     Shopify, HubSpot, Salesforce, Airtable, GitHub, Slack,
      │     Google Analytics, Google Ads, Facebook Ads, LinkedIn Ads,
      │     Stripe, Pipedrive, Intercom, Notion, Zendesk, Snowflake,
      │     BigQuery, Google Sheets, Google Drive, LinkedIn Ads...
      │
      ├── Or direct connector for DB sources:
      │     csv_connector.py, excel_connector.py, postgres_connector.py,
      │     mysql_connector.py, mongodb_connector.py, sqlite_connector.py,
      │     s3_connector.py, snowflake_connector.py, salesforce_connector.py,
      │     zoho_connector.py, d365_connector.py, rest_api_connector.py,
      │     tally_connector.py, warehouse_connector.py...
      │
      └── Data stored in → DataVaultItem (Data Vault)
                          or directly as UploadedFile
```

---

## 🗄️ Database Schema

### Core Tables

| Table | Purpose | Key Columns |
|---|---|---|
| `users` | User accounts | id, email, hashed_password, full_name |
| `uploaded_files` | Uploaded datasets | id, user_id, file_name, file_path, row_count, model_config |
| `file_columns` | Column metadata | file_id, column_name, data_type, null_count |
| `column_statistics` | Stats per column | column_id, min/max/mean/median/std_dev, top_values |
| `graph_definitions` | Saved charts | file_id, graph_type, x_axis, y_axis, aggregation, cached_data |

### Connection Tables

| Table | Purpose |
|---|---|
| `remote_connection_profiles` | Saved remote DB connections (encrypted password) |
| `user_db_connections` | Legacy user DB connections |
| `connector_catalog` | 35+ connector definitions with JSON schema |

### ETL Tables

| Table | Purpose |
|---|---|
| `etl_connections` | Source/target connection configs (Fernet-encrypted) |
| `etl_pipelines` | Pipeline definitions with versioning |
| `etl_pipeline_versions` | Snapshots for rollback |
| `etl_workflow_nodes` | DAG nodes (extract/transform/load) |
| `etl_workflow_edges` | Directed edges between nodes |
| `etl_transform_rules` | Column/table-level transform rules |
| `etl_schedules` | Cron/interval scheduling configs |
| `etl_jobs` | Job execution records |
| `etl_job_steps` | Per-node step records within a job |
| `etl_job_logs` | Line-level execution logs |
| `etl_data_quality_checks` | Pre/post load validation rules |
| `audit_logs` | Full audit trail of all actions |
| `user_roles` | RBAC (admin/developer/operator/viewer) |
| `data_vault_items` | Central dataset storage registry |

---

## 🧩 Key Component Deep Dive

### BIWorkspace.jsx (158 KB — the heart of the UI)
- Power BI-like canvas with multi-page support
- Drag-and-drop visual positioning and resizing
- Full BI ribbon with Home/Insert/Modeling/View tabs
- Theme engine (light/dark + 10+ built-in themes)
- Page navigation (add/rename/delete pages)
- Export to PDF via html2canvas + jsPDF
- Publish/share functionality
- Undo/Redo stack for canvas operations

### DynamicChart.jsx (134 KB — the chart engine)
- 30+ chart types rendered via Recharts library:
  - Bar (clustered/stacked/100%), Line, Area, Pie/Donut
  - Scatter, Bubble, Waterfall, Funnel, Treemap
  - Box Plot, Histogram, Radar/Spider, Ribbon
  - Card/KPI metrics, Table, Matrix
  - Choropleth Map (react-simple-maps + d3-geo)
  - Gauge, Heatmap, Candlestick
- Supports conditional formatting (color rules)
- Drill-through navigation
- Cross-filtering between visuals on same page

### BIModelView.jsx (92 KB — data modeling)
- Visual table relationship editor
- Many-to-one / one-to-many relationship definition
- Column type overrides
- Calculated column / quick measure definitions
- Communicates with backend model_engine.py

### graph_engine.py (29 KB — chart data computation)
- Handles all aggregation: sum, mean, count, min, max
- Time-series resampling (daily/weekly/monthly)
- Pivot table generation
- Percentile calculations
- Handles both file-based and SQL-based data sources

### etl_executor.py (17 KB — pipeline runner)
- Runs DAG nodes in topological order
- Per-node retry logic with exponential backoff
- Delta detection (incremental loads via etl_delta.py)
- Quality check enforcement (pre/post load)
- Detailed step-level logging to DB

---

## 🛠️ Technology Stack

### Backend
| Technology | Version / Purpose |
|---|---|
| **FastAPI** | REST API framework |
| **SQLAlchemy** | ORM for DB access |
| **Alembic** | Database migrations |
| **PostgreSQL** | Primary database |
| **SQLite** | Fallback for local dev |
| **Pandas / NumPy** | Data processing |
| **DLT (Data Load Tool)** | Cloud connector pipelines |
| **APScheduler** | ETL job scheduling |
| **Cryptography (Fernet)** | Credential encryption |
| **OpenAI** | AI chart suggestions |
| **Polars** | High-performance data processing |
| **Boto3** | AWS S3 connectivity |
| **Motor** | MongoDB async driver |
| **Snowflake Connector** | Snowflake connectivity |
| **pymssql** | SQL Server connectivity |
| **Passlib + bcrypt** | Password hashing |

### Frontend
| Technology | Version / Purpose |
|---|---|
| **React 18** | UI framework |
| **Vite 5** | Build tool + dev server |
| **React Router v6** | Client-side routing |
| **Recharts** | Chart library |
| **Radix UI** | Accessible primitives (20+ components) |
| **Tailwind CSS v4** | Utility CSS |
| **Lucide React** | Icon library |
| **XLSX (SheetJS)** | Excel file parsing |
| **react-simple-maps** | Map visualizations |
| **d3-geo** | Geographic projections |
| **Zustand** | State management |
| **jsPDF + html2canvas** | PDF export |
| **Zod + React Hook Form** | Form validation |

---

## 🌐 API Surface Summary

| Route Prefix | Module | Key Endpoints |
|---|---|---|
| `/signup`, `/login` | main.py | Auth endpoints |
| `/api/files` | routers/files.py | Upload, download, list, delete, schema |
| `/api/graphs` | routers/graphs.py | Chart data, top charts |
| `/api/sql` | routers/sql.py | SQL execution, datasets |
| `/api/etl` | routers/etl.py | Full ETL CRUD + run + monitor + audit |
| `/api/db` | routers/db.py | Remote DB table list, query, save connection |
| `/api/connections` | routers/connections.py | Saved connection profiles (BI) |
| `/api/smart` | routers/smart.py | AI chart recommendations |
| `/api/visuals` | routers/visuals.py | Custom visual metadata |
| `/api/power-automate` | routers/automate.py | Power Automate trigger |
| `/api/connectors` | routers/modular_connectors.py | DLT connector fetch + test |
| `/api/data-vault` | routers/data_vault.py | DataVault items |

---

## 📦 Deployment Architecture

### Development Mode
```
Terminal 1: cd backend && uvicorn main:app --port 8010 --reload
Terminal 2: cd frontend && npm run dev (port 5173, proxied to 8010)
```

### Production Mode (Single Port)
```
cd frontend && npm run build
→ Output copied to backend/static/
→ FastAPI serves SPA from backend/static/index.html
→ All on single port 8010
```

The `vite.config.js` sets up a proxy so all `/api/*` requests from the frontend dev server are forwarded to the backend at port 8010 during development.

---

## 🔐 Security Architecture

| Area | Implementation |
|---|---|
| Password storage | bcrypt hashing via passlib |
| Credential encryption | Fernet (symmetric encryption, key in `.etl_fernet.key`) |
| Auth | localStorage session (no JWT currently) |
| CORS | Whitelisted origins (localhost:5173, localhost:3000, production domain) |
| RBAC | user_roles table (admin/developer/operator/viewer) |
| Audit | audit_logs table records every action |
| Input validation | Pydantic schemas on all request bodies |

---

## 🤖 AI/Smart Features

| Feature | Implementation |
|---|---|
| **Smart Visualization** | `smart_analyzer.py` → OpenAI API → returns recommended chart type + config |
| **Smart Narrative** | `SmartNarrativeVisual.jsx` → calls backend → AI generates text summary |
| **Q&A Visual** | Natural language → converted to chart query |
| **Key Influencers** | `InfluencersVisual.jsx` → statistical correlation analysis |
| **AI Insights Panel** | `BIInsightsPanel.jsx` → anomaly/trend detection |

---

## ⚠️ Notable Observations & Architecture Notes

> [!NOTE]
> The **BIWorkspace.jsx** at 158KB is the largest and most complex file. It functions as the entire BI application shell — managing pages, visuals, data model, theme, toolbar state, and more. This could benefit from being broken into sub-contexts.

> [!NOTE]
> Authentication uses **localStorage only** — no JWT, no refresh tokens. This is simple for development but would need enhancement for production security.

> [!TIP]
> The database automatically **falls back from PostgreSQL to SQLite** at startup. The `analytics.db` file in the root is this SQLite fallback used in local dev.

> [!IMPORTANT]
> The **Fernet encryption key** is stored in `backend/services/.etl_fernet.key`. This must be kept secret and backed up — losing it means all stored passwords become unreadable.

> [!NOTE]
> The **ETL system is production-grade** with: versioned pipelines, rollback, DAG visualization, delta detection, quality checks, scheduling, retry logic, and full audit trails.

> [!TIP]
> The **connector catalog is auto-seeded** from `connectors/registry.py` on every startup. This makes adding new connectors as simple as adding an entry to the registry.

---

## 📊 Code Size Context

| File | Size | Significance |
|---|---|---|
| `BIWorkspace.jsx` | 158 KB | Main BI canvas — largest file |
| `DynamicChart.jsx` | 134 KB | Chart rendering engine |
| `BIModelView.jsx` | 92 KB | Data model editor |
| `BIRibbon.jsx` | 55 KB | Toolbar implementation |
| `ETLDashboard.jsx` | 57 KB | ETL UI (7 tabs) |
| `dlt_connector.py` | 36 KB | DLT connector hub |
| `routers/etl.py` | 35 KB | ETL API router |
| `routers/files.py` | 47 KB | File handling API |
| `services/graph_engine.py` | 29 KB | Chart data engine |
| `services/model_engine.py` | 25 KB | BI data model engine |

---

*Report generated by Antigravity AI — April 12, 2026*
