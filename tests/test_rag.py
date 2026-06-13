import tempfile
from pathlib import Path
from scripts import rag


def test_build_index_and_search(tmp_path):
    # create a temporary weekly_reviews directory
    wd = tmp_path / "weekly_reviews"
    wd.mkdir()
    f1 = wd / "2025-01-01.md"
    f1.write_text("Primary focus: refactoring auth module. Several deep sessions.")
    f2 = wd / "2025-01-08.md"
    f2.write_text("Worked on docs and onboarding; small bug fixes.")

    # patch rag.REVIEWS_DIR to point to tmp
    old = rag.REVIEWS_DIR
    try:
        rag.REVIEWS_DIR = wd
        vec, X, meta = rag.build_index(force=True)
        results = rag.search_reviews("refactor auth", top_k=2)
        assert len(results) >= 1
        assert any("auth" in chunk.lower() for _, chunk, _ in results)
    finally:
        rag.REVIEWS_DIR = old
