<div align="center">

# 📊 One-Stop Analytics (OSA)

**A Modern, Full-Stack Visual ETL & Business Intelligence Platform**

[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-20232A?style=flat-square&logo=react&logoColor=61DAFB)](https://react.dev)
[![Vite](https://img.shields.io/badge/Vite-646CFF?style=flat-square&logo=vite&logoColor=white)](https://vitejs.dev)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-D71F00?style=flat-square&logo=sqlalchemy&logoColor=white)](https://www.sqlalchemy.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=flat-square&logo=postgresql&logoColor=white)](https://www.postgresql.org)

<p align="center">
  <em>An end-to-end data platform bridging code-free ETL data orchestration with Power BI-style dashboard visual analytics.</em>
</p>

</div>

---

## 🚀 Overview

**One-Stop Analytics (OSA)** eliminates fragmented data tooling by combining **ETL pipeline automation** and **interactive business intelligence reporting** into a unified, single-port web interface. Users can extract data from multiple external sources, clean and transform it through a DAG orchestrator, and build interactive analytical dashboards in real time.

---

## 🌟 Key Features

### 1. 🔄 Visual ETL & Pipeline Orchestration
- **Metadata-Driven DAG Engine:** Parallel task execution using topological sorting (Kahn's Algorithm) and `ThreadPoolExecutor`.
- **15+ Data Connectors:** Native support for PostgreSQL, MySQL, Snowflake, MongoDB, SQLite, AWS S3, Parquet, REST APIs, CSV, and Excel.
- **Built-in Quality & Transformation:** Automated null checks, type casting, regex filters, and range validation before warehouse loading.
- **Job Scheduling & Auditing:** Automated interval/cron execution with real-time execution logs and error recovery.

### 2. 📈 Power BI-Style Analytics Workspace
- **Drag-and-Drop Visual Studio:** Build interactive bar, line, scatter, pie, and metric cards with ribbon and fields panes.
- **SQL Dataset Editor:** Run custom analytical queries and turn result sets directly into report visuals.
- **Data Vault & Relationship Views:** Manage data schemas, table joins, and model relationships seamlessly.
- **Paginated Reports:** Generate and export publication-ready reporting layouts.

---

## 🏗️ Architecture

```
┌────────────────────────────────────────────────────────┐
│                   React + Vite UI                      │
│   • BI Workspace & Ribbon      • ETL DAG Designer      │
│   • Visuals & Fields Panes     • SQL Query Editor      │
└───────────────────────────┬────────────────────────────┘
                            │ REST APIs
┌───────────────────────────▼────────────────────────────┐
│                  FastAPI Backend                       │
│   • ETL Orchestrator (DAG Runner, Kahn's Algo)         │
│   • Connector Registry (Postgres, S3, Snowflake, etc.) │
│   • Query Engine & Data Quality Validators             │
│   • SQLAlchemy ORM & Alembic Migrations                │
└────────────────────────────────────────────────────────┘
```

---

## 🛠️ Tech Stack

- **Backend:** Python 3.11+, FastAPI, SQLAlchemy, Alembic, Pydantic, Uvicorn
- **Frontend:** React 18, Vite, Tailwind CSS, Lucide Icons, Chart.js / Recharts
- **Data & Connectors:** Pandas, PyArrow, ConnectorX, Psycopg2, S3Fs, DuckDB / SQLite
- **Orchestration:** Multi-threaded DAG execution, Cron scheduling

---

## ⚡ Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/shivampatle2004/updated_osa.git
cd updated_osa
```

### 2. Backend Setup
```bash
cd backend
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

pip install -r requirements.txt
python main.py
```

### 3. Frontend Setup
```bash
cd ../frontend
npm install
npm run dev
```

Visit **`http://localhost:5173`** (or configured single-port host) to launch the workspace.

---

<div align="center">
  <sub>Developed by <a href="https://github.com/shivampatle2004">Shivam Patle</a></sub>
</div>
