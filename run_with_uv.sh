#!/bin/sh
# Install dependencies and run the FastAPI app using uv
uv pip install -r requirements.txt
uv run -- uvicorn main:app --reload 