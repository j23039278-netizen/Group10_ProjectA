"""
Sentence Transformers model and catalogue skill embeddings (Level 2).
Author: Ng Yong Hin (AI / NLP Engineer)

  * get_model()        loads config.MODEL_NAME once per process (lazy, locked,
                       so concurrent FastAPI requests share one instance).
  * get_spacy()        the same for the spaCy pipeline (config.SPACY_MODEL).
  * encode(texts)      L2-normalised float32 embeddings, so a dot product is
                       the cosine similarity.
  * skill_embeddings() SkillVectors for the catalogue (one row per skill, or
                       one per name / alias in "name_aliases_max"). Cached in memory by a hash
                       of the model, the text mode and the skill texts, and on
                       disk in nlp/resources/skill_embeddings.npy (+ .json with
                       the hash). A changed catalogue gives a new hash, so the
                       embeddings are rebuilt and the file is overwritten.

Needs the packages in nlp/requirements.txt. The first get_model() call
downloads the model (~90 MB) into the Hugging Face cache.
"""

import hashlib
import json
import threading
from pathlib import Path
from typing import NamedTuple

import numpy as np

from nlp import config

NLP_DIR = Path(__file__).resolve().parent
EMBEDDINGS_PATH = NLP_DIR / "resources" / "skill_embeddings.npy"
EMBEDDINGS_META_PATH = NLP_DIR / "resources" / "skill_embeddings.json"

SKILL_TEXT_MODES = ("name_aliases", "name_aliases_max", "name_description")

_model_lock = threading.Lock()
_embedding_lock = threading.Lock()   # separate: building embeddings loads the model
_model = None
_spacy = None
_embedding_cache = {}   # hash -> (skill names tuple, matrix)


# ── Model ─────────────────────────────────────────────────────
def get_model():
    """The shared SentenceTransformer, loaded on first use."""
    global _model
    if _model is None:
        with _model_lock:
            if _model is None:
                from sentence_transformers import SentenceTransformer  # slow import, keep lazy
                _model = SentenceTransformer(config.MODEL_NAME, device="cpu")
    return _model


def get_spacy():
    """The shared spaCy pipeline (en_core_web_sm without NER), loaded on first use."""
    global _spacy
    if _spacy is None:
        with _model_lock:
            if _spacy is None:
                import spacy
                _spacy = spacy.load(config.SPACY_MODEL, exclude=["ner"])
    return _spacy


def encode(texts, batch_size=64):
    """Normalised embeddings (len(texts) x dim) for a list of strings."""
    if not texts:
        return np.zeros((0, get_model().get_sentence_embedding_dimension()), dtype=np.float32)
    vectors = get_model().encode(list(texts), batch_size=batch_size,
                                 normalize_embeddings=True, show_progress_bar=False,
                                 convert_to_numpy=True)
    return vectors.astype(np.float32, copy=False)


# ── Skill texts ───────────────────────────────────────────────
def skill_texts(entry, mode=None):
    """Texts embedded for one catalogue entry (see config.SKILL_TEXT_MODE).

    name_aliases      one text:  "Power BI: PowerBI, Microsoft Power BI"
    name_aliases_max  one text per term: "Power BI", "PowerBI", ...; the skill
                      scores the best of them (ambiguous aliases are left out)
    name_description  one text:  "Power BI: Business intelligence and ..."
    """
    mode = mode or config.SKILL_TEXT_MODE
    name = entry["skill_name"]
    aliases = []
    for a in entry["aliases"]:
        if a.lower() != name.lower() and a.lower() not in {x.lower() for x in aliases}:
            aliases.append(a)
    if mode == "name_aliases":
        return [f"{name}: {', '.join(aliases)}" if aliases else name]
    if mode == "name_aliases_max":
        return [name] + aliases
    if mode == "name_description":
        desc = (entry.get("description") or "").strip()
        return [f"{name}: {desc}" if desc else name]
    raise ValueError(f"unknown skill text mode {mode!r}; use one of {SKILL_TEXT_MODES}")


def catalogue_hash(texts_per_skill, mode):
    """Hash of everything the embeddings depend on (model, mode, every text)."""
    h = hashlib.sha256()
    h.update(config.MODEL_NAME.encode("utf-8"))
    h.update(b"\0" + mode.encode("utf-8"))
    for texts in texts_per_skill:
        h.update(b"\0" + "\x1f".join(texts).encode("utf-8"))
    return h.hexdigest()


# ── Skill embeddings ──────────────────────────────────────────
class SkillVectors(NamedTuple):
    """Embeddings of the catalogue. Rows are grouped by skill: the rows of
    names[k] start at starts[k] (one row per skill except in name_aliases_max)."""
    names: tuple
    matrix: np.ndarray
    starts: np.ndarray

    def similarity(self, vectors):
        """Cosine similarity (len(vectors) x len(names)): best row per skill."""
        sims = vectors @ self.matrix.T
        if len(self.starts) == self.matrix.shape[0]:
            return sims
        return np.maximum.reduceat(sims, self.starts, axis=1)


def _read_disk(digest, names):
    try:
        meta = json.loads(EMBEDDINGS_META_PATH.read_text(encoding="utf-8"))
        if meta.get("hash") != digest or meta.get("skill_names") != list(names):
            return None
        matrix = np.load(EMBEDDINGS_PATH, allow_pickle=False)
        counts = meta["rows_per_skill"]
        return (matrix, counts) if matrix.shape[0] == sum(counts) else None
    except (OSError, ValueError, KeyError, TypeError):
        return None


def _write_disk(digest, names, mode, matrix, counts):
    try:
        EMBEDDINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
        np.save(EMBEDDINGS_PATH, matrix, allow_pickle=False)
        EMBEDDINGS_META_PATH.write_text(json.dumps(
            {"hash": digest, "model": config.MODEL_NAME, "mode": mode,
             "skill_names": list(names), "rows_per_skill": counts}, indent=1),
            encoding="utf-8")
    except OSError:
        pass   # read-only checkout: the in-memory cache still works


def skill_embeddings(catalogue, mode=None, use_disk=True):
    """SkillVectors for every skill in the catalogue.

    Built once per (model, mode, catalogue texts); use_disk=False skips the
    .npy file (experiments use it so they do not overwrite the live cache).
    """
    mode = mode or config.SKILL_TEXT_MODE
    names = tuple(e["skill_name"] for e in catalogue)
    texts_per_skill = [skill_texts(e, mode) for e in catalogue]
    digest = catalogue_hash(texts_per_skill, mode)

    cached = _embedding_cache.get(digest)
    if cached is not None:
        return cached
    with _embedding_lock:
        cached = _embedding_cache.get(digest)
        if cached is not None:
            return cached
        found = _read_disk(digest, names) if use_disk else None
        if found is None:
            counts = [len(t) for t in texts_per_skill]
            matrix = encode([t for texts in texts_per_skill for t in texts])
            if use_disk:
                _write_disk(digest, names, mode, matrix, counts)
        else:
            matrix, counts = found
        starts = np.concatenate(([0], np.cumsum(counts)[:-1])).astype(np.intp)
        vectors = _embedding_cache[digest] = SkillVectors(names, matrix, starts)
        return vectors
