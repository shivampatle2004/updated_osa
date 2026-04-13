#!/bin/bash
cd /Users/tanmayrathi/Downloads/one-stop-analytics-saa-s-frontend\ 2/backend
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8010 --reload
