#!/bin/bash
cd "$(dirname "$0")"
source ../../venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8090 --reload

