#!/usr/bin/env bash
set -euo pipefail
export PYTHONUNBUFFERED=1

if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi

source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt

streamlit run ui/streamlit_app.py --server.port 8501
