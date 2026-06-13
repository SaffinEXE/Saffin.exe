#!/usr/bin/env bash
# Run a full embedding demo on Unix-like systems
# Usage: ./scripts/run_embedding_demo.sh

set -euo pipefail

ROOT_DIR="$(dirname "${BASH_SOURCE[0]}")/.."
cd "$ROOT_DIR"

VENV_DIR=".venv"
if [ ! -d "$VENV_DIR" ]; then
  python3 -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"

python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install sentence-transformers

echo "Building embedding index (this may download a model)..."
python scripts/rag.py --build --embeddings

echo "Running a semantic search demo..."
python scripts/rag.py "auth refactor" --embeddings

echo "Running assistant search (embeddings)..."
PYTHONPATH=. python scripts/assistant.py search_reviews "refactor or auth" --embeddings

echo "Done."
