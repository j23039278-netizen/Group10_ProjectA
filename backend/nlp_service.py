"""
SEAGAS — Backend access to the NLP module (nlp/, owner: Ng Yong Hin)

Every backend call into nlp/ goes through this file, so the routers do not
deal with import paths or missing packages.

- Level 1 ("keyword") uses only the Python standard library and always works.
- Level 2 ("semantic", "hybrid") needs nlp/requirements.txt (spaCy, Sentence
  Transformers, torch). When those packages are not installed, or the model
  cannot load, the call falls back to "keyword" and says so, instead of
  failing the student's request. The method that actually ran is returned so
  it can be stored (assessments.matching_method) and shown.

Contract: docs/NLP_INTERFACE.md. Rules: docs/NLP_CLASSIFICATION_RULES.md.
"""

import importlib.util
import logging
import sys
import threading
from pathlib import Path

# nlp/ lives in the repo root; it must be importable as a package (not nlp/ itself
# on the path, or nlp/types.py would shadow Python's built-in types module).
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import nlp  # noqa: E402  (needs the path above)

# uvicorn configures this logger, so messages show in the backend window
log = logging.getLogger("uvicorn.error")

METHODS = nlp.VALID_METHODS            # ("keyword", "semantic", "hybrid")
DEFAULT_METHOD = "hybrid"              # the NLP module's default (NLP_INTERFACE.md 6h)
LEVEL2_PACKAGES = ("spacy", "en_core_web_sm", "sentence_transformers", "numpy")


def level2_installed() -> bool:
    """True when the Level 2 packages are installed (checked without importing them)"""
    return all(importlib.util.find_spec(p) is not None for p in LEVEL2_PACKAGES)


def check_method(method: str) -> str:
    if method not in METHODS:
        raise ValueError(f"matching method must be one of {', '.join(METHODS)}; got {method!r}")
    return method


def _run(fn, method, *args, **kwargs):
    """Run fn with method; fall back to keyword if Level 2 is unavailable.

    Returns (result, method_used, note). note is None unless a fallback happened.
    ValueError (bad input) is not caught: callers turn it into HTTP 400.
    """
    check_method(method)
    if method != "keyword":
        # Shown to the student, so no technical detail; that goes to the server log
        note = (f"{method.capitalize()} matching is not available right now, so keyword "
                "matching (exact skill names) was used instead.")
        if not level2_installed():
            log.warning("NLP %s requested but nlp/requirements.txt is not installed; using keyword", method)
            return fn(*args, method="keyword", **kwargs), "keyword", note
        try:
            return fn(*args, method=method, **kwargs), method, None
        except (ImportError, OSError) as e:
            log.warning("NLP %s failed to load (%s: %s); using keyword", method, type(e).__name__, e)
            return fn(*args, method="keyword", **kwargs), "keyword", note
    return fn(*args, method="keyword", **kwargs), "keyword", None


def extract_skills(text, method, skills):
    """nlp.extract_skills with fallback. skills = skills_library rows (dicts)."""
    return _run(nlp.extract_skills, method, text, skills=skills)


def match_skills(student_skills, required_skills, method):
    """nlp.match_skills with fallback."""
    return _run(nlp.match_skills, method, student_skills, required_skills)


def warm_up_in_background():
    """Load the Level 2 model at start-up so the first student does not wait 20-30 s.

    Runs in a thread so FastAPI starts immediately (NLP_INTERFACE.md section 8).
    Does nothing when the Level 2 packages are not installed.
    """
    if not level2_installed():
        log.warning("NLP Level 2 packages not installed: semantic/hybrid requests will use "
                    "keyword matching. Install with: pip install -r nlp/requirements.txt")
        return

    def _warm():
        try:
            nlp.extract_skills("Good analytical and communication skills in SQL.", method="hybrid")
            log.info("NLP model loaded (hybrid ready)")
        except Exception as e:  # never stop the API because warm-up failed
            log.warning("NLP warm-up failed (%s); requests will fall back to keyword", e)

    threading.Thread(target=_warm, name="nlp-warm-up", daemon=True).start()
