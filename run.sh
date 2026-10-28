#!/bin/sh
exec python -m streamlit run dash.py \
  --server.port="${PORT:-8501}" \
  --server.address=0.0.0.0 \
  --server.headless=true
