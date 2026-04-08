#!/usr/bin/env bash
set -euo pipefail

streamlit run streamlit_app.py --server.address=0.0.0.0 --server.port=8501
