"""
Skill catalogue loader for the SEAGAS NLP module.

Two sources:
  * default: nlp/resources/skills_taxonomy.json (generated from
    data/skills/skills_library.csv; no skill_id). Loaded once and cached.
  * rows from the skills_library table, passed in by the backend so results
    carry real UUIDs. The DB has no subcategory / ambiguous_aliases columns,
    so those are filled in from the taxonomy by skill_name.

Lookups are case-insensitive. lookup() also tries the normalised skill_key(),
so "Power-BI" and "nodejs" resolve to "Power BI" and "Node.js".
"""

import json
from functools import lru_cache
from pathlib import Path

from nlp.normalise import skill_key

NLP_DIR = Path(__file__).resolve().parent
TAXONOMY_PATH = NLP_DIR / "resources" / "skills_taxonomy.json"


def _as_list(value):
    """Aliases may arrive as a list, a "|"-separated string or None (NULL TEXT[])."""
    if value is None:
        return []
    if isinstance(value, str):
        value = value.split("|")
    return [str(v).strip() for v in value if v is not None and str(v).strip()]


def _entry(row, extra=None):
    """Build a SkillEntry from a taxonomy item or a DB row (dict)."""
    name = str(row.get("skill_name") or "").strip()
    if not name:
        raise ValueError(f"skill row without skill_name: {row!r}")
    extra = extra or {}

    def pick(key, default):
        # DB value first, then taxonomy metadata, then default
        value = row.get(key)
        return value if value not in (None, "") else extra.get(key, default)

    skill_id = row.get("skill_id")
    return {
        "skill_id": str(skill_id) if skill_id else None,
        "skill_name": name,
        "category": pick("category", ""),
        "subcategory": pick("subcategory", ""),
        "aliases": _as_list(pick("aliases", [])),
        "ambiguous_aliases": _as_list(pick("ambiguous_aliases", [])),
        "description": pick("description", ""),
    }


class SkillCatalogue:
    """Read-only skill catalogue with name / alias lookups."""

    def __init__(self, entries):
        self.entries = tuple(entries)
        self._by_name = {}          # lower-case canonical name -> entry
        self._alias_to_name = {}    # lower-case name or alias  -> canonical name
        self._key_to_name = {}      # skill_key(name or alias)  -> canonical name

        for e in self.entries:
            low = e["skill_name"].lower()
            if low in self._by_name:
                raise ValueError(f"duplicate skill_name: {e['skill_name']!r}")
            self._by_name[low] = e

        # Canonical names always win; an alias claimed by two different skills
        # is dropped (no guessing).
        claims = {}
        key_claims = {}
        for e in self.entries:
            name = e["skill_name"]
            for term in [name] + e["aliases"] + e["ambiguous_aliases"]:
                claims.setdefault(term.lower(), set()).add(name)
                key_claims.setdefault(skill_key(term), set()).add(name)
        for low, names in claims.items():
            if low in self._by_name:
                self._alias_to_name[low] = self._by_name[low]["skill_name"]
            elif len(names) == 1:
                self._alias_to_name[low] = next(iter(names))
        for key, names in key_claims.items():
            if key and len(names) == 1:
                self._key_to_name[key] = next(iter(names))

        # lower-case terms that need context before they count as a skill
        self.ambiguous_aliases = frozenset(
            a.lower() for e in self.entries for a in e["ambiguous_aliases"]
        )

    def __len__(self):
        return len(self.entries)

    def __iter__(self):
        return iter(self.entries)

    def get(self, skill_name):
        """Entry for a canonical skill name (case-insensitive), or None."""
        return self._by_name.get((skill_name or "").strip().lower())

    def canonical_name(self, term):
        """Canonical skill name for a name or alias (case-insensitive), or None.

        Ambiguous aliases resolve too ("Go" -> "Go"); check is_ambiguous()
        before trusting a match found in free text.
        """
        return self._alias_to_name.get((term or "").strip().lower())

    def lookup(self, term):
        """Like canonical_name(), with a fallback on the normalised skill_key()
        ("Power-BI" -> "Power BI", "Data Visualization" -> "Data Visualisation")."""
        name = self.canonical_name(term)
        if name is None:
            name = self._key_to_name.get(skill_key(term or ""))
        return name

    def is_ambiguous(self, term):
        """True if the term is an ambiguous alias (e.g. "R", "Go", "Excel", "CV")."""
        return (term or "").strip().lower() in self.ambiguous_aliases

    def skill_id(self, term):
        """skills_library UUID for a name or alias, or None (unknown or no IDs)."""
        name = self.lookup(term)
        return self._by_name[name.lower()]["skill_id"] if name else None


# ── Loading ───────────────────────────────────────────────────
def _read_taxonomy(path=TAXONOMY_PATH):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return data["skills"]


@lru_cache(maxsize=1)
def _default_catalogue():
    return SkillCatalogue(_entry(item) for item in _read_taxonomy())


def load_catalogue(skills=None):
    """Return the skill catalogue.

    skills=None  -> the default taxonomy (cached, loaded once).
    skills=[...] -> build from these rows (e.g. SELECT skill_id, skill_name,
                    category, aliases, description, is_active FROM skills_library).
                    Rows with is_active == False are skipped. Not cached.
    """
    if skills is None:
        return _default_catalogue()
    taxonomy = {e["skill_name"].lower(): e for e in _default_catalogue()}
    entries = []
    for row in skills:
        if not isinstance(row, dict):
            row = dict(getattr(row, "_mapping", row))  # SQLAlchemy Row is accepted too
        if row.get("is_active") is False:
            continue
        name = str(row.get("skill_name") or "").strip().lower()
        entries.append(_entry(row, taxonomy.get(name)))
    return SkillCatalogue(entries)
