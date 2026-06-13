"""Simple local RAG indexer and retriever for weekly reviews.

Builds a TF-IDF index over `weekly_reviews/*.md` and returns top-k relevant
chunks for a user query. Uses scikit-learn (TF-IDF) and stores a small
index file under `.cache/weekly_reviews_index.pkl` for reuse.
"""
from pathlib import Path
from typing import List, Tuple
import pickle
import re

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel

BASE = Path(__file__).resolve().parent.parent
REVIEWS_DIR = BASE / "weekly_reviews"
CACHE_DIR = BASE / ".cache"
CACHE_DIR.mkdir(exist_ok=True)
INDEX_PATH = CACHE_DIR / "weekly_reviews_index.pkl"


def _read_reviews() -> List[Tuple[str, str]]:
    """Return list of (path, text) for each markdown file in weekly_reviews."""
    items = []
    if not REVIEWS_DIR.exists():
        return items
    for p in sorted(REVIEWS_DIR.glob("*.md")):
        try:
            text = p.read_text(encoding="utf-8")
            items.append((str(p), text))
        except Exception:
            continue
    return items


def _chunk_text(text: str, max_len: int = 800) -> List[str]:
    """Chunk text by paragraphs (or by size) into smaller passages."""
    paras = [p.strip() for p in re.split(r"\n\n+", text) if p.strip()]
    chunks = []
    cur = ""
    for p in paras:
        if len(cur) + len(p) + 2 <= max_len:
            cur = (cur + "\n\n" + p).strip() if cur else p
        else:
            if cur:
                chunks.append(cur)
            cur = p
    if cur:
        chunks.append(cur)
    return chunks


def build_index(force: bool = False):
    """Build and persist TF-IDF index. Returns (vectorizer, matrix, metadata).
    metadata is a list of (source_path, chunk_text).
    """
    if INDEX_PATH.exists() and not force:
        try:
            with open(INDEX_PATH, "rb") as f:
                return pickle.load(f)
        except Exception:
            pass

    items = _read_reviews()
    docs = []
    meta = []
    for path, text in items:
        for chunk in _chunk_text(text):
            docs.append(chunk)
            meta.append((path, chunk))

    if not docs:
        vec = TfidfVectorizer(stop_words="english")
        X = vec.fit_transform([""])
    else:
        vec = TfidfVectorizer(stop_words="english")
        X = vec.fit_transform(docs)

    data = (vec, X, meta)
    try:
        with open(INDEX_PATH, "wb") as f:
            pickle.dump(data, f)
    except Exception:
        pass
    return data


def search_reviews(query: str, top_k: int = 5) -> List[Tuple[str, str, float]]:
    """Return top_k (path, chunk, score) for query."""
    vec, X, meta = build_index()
    if not meta:
        return []
    qv = vec.transform([query])
    sims = linear_kernel(qv, X).flatten()
    top_idx = sims.argsort()[::-1][:top_k]
    results = []
    for idx in top_idx:
        score = float(sims[idx])
        path, chunk = meta[idx]
        results.append((path, chunk, score))
    return results


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser(description="Build/search weekly reviews TF-IDF index")
    p.add_argument("query", nargs="?", help="Query to search reviews")
    p.add_argument("--build", action="store_true", help="Force rebuild index")
    args = p.parse_args()
    if args.build:
        build_index(force=True)
        print("Index built.")
    elif args.query:
        for path, chunk, score in search_reviews(args.query):
            print(f"{score:.3f} - {path}\n{chunk}\n---\n")
    else:
        print("Usage: rag.py [--build] <query>")
