"""Checks for data/generate_synthetic_data.py (run: python -m pytest tests/test_synthetic_data.py -q)."""

import sys
from pathlib import Path

import pytest

pytest.importorskip("faker")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "data"))
from generate_synthetic_data import BLOCKED_NAMES, generate, name_key  # noqa: E402


@pytest.fixture(scope="module")
def dataset():
    return generate(5000, 42)


def test_names_unique_5000_seed_42(dataset):
    users = dataset[0]
    assert len(users) == 5000
    keys = {name_key(u["full_name"]) for u in users}
    assert len(keys) == 5000
    assert not keys & {name_key(n) for n in BLOCKED_NAMES}


def test_same_seed_same_output(dataset):
    assert generate(5000, 42) == dataset
