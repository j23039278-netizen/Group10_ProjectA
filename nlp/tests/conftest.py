"""pytest setup for nlp/tests.

Tests marked @pytest.mark.model load the Sentence Transformers model and the
spaCy pipeline (needs nlp/requirements.txt; the first run downloads the model).
Skip them with:

    python -m pytest nlp/tests -m "not model"

They are also skipped automatically when the packages are not installed.
"""

import importlib.util

import pytest

_MODEL_DEPS = ("sentence_transformers", "spacy", "en_core_web_sm")


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "model: needs the Sentence Transformers model and spaCy (slow first run)")


def pytest_collection_modifyitems(config, items):
    missing = [m for m in _MODEL_DEPS if importlib.util.find_spec(m) is None]
    if not missing:
        return
    skip = pytest.mark.skip(reason=f"not installed: {', '.join(missing)} (see nlp/requirements.txt)")
    for item in items:
        if "model" in item.keywords:
            item.add_marker(skip)
