"""
Text normalisation helpers for skill matching.

Pure functions, standard library only. The keyword matcher compares skill
terms through skill_key(), so "Power-BI", "PowerBI" and "Power BI" (or
"Node.js" and "NodeJS") end up as the same key.

normalise_text() and skill_key() change the length of the text, so they are
for comparing terms, not for computing character offsets in a JD.
"""

import re
import unicodedata

# ── Basic clean-up ────────────────────────────────────────────
# Unicode hyphens / dashes that should all count as "-"
_DASHES_RE = re.compile(r"[‐‑‒–—―−﹘﹣－]")
_SPACES_RE = re.compile(r"\s+")


def normalise_text(text):
    """Lower-case, unify dashes to "-", collapse whitespace and strip.

    >>> normalise_text("  Power–BI   Developer ")
    'power-bi developer'
    """
    t = unicodedata.normalize("NFKC", text or "")
    t = _DASHES_RE.sub("-", t)
    t = _SPACES_RE.sub(" ", t)
    return t.strip().lower()


# ── UK / US spelling ──────────────────────────────────────────
# The skills library uses UK spelling, so US forms are mapped to UK.
# Stems spelt with "z" in US English and "s" in UK English:
_IZE_STEMS = (
    "analy", "visuali", "organi", "optimi", "prioriti", "containeri",
    "normali", "standardi", "customi", "virtuali", "summari", "categori",
    "authori", "recogni", "utili", "speciali", "tokeni", "lemmati",
)
_IZE_RE = re.compile(
    r"\b(" + "|".join(_IZE_STEMS) + r")z(e|es|ed|ing|er|ers|ation|ations|ational)\b"
)
_US_TO_UK = {
    "modeling": "modelling",
    "modeled": "modelled",
    "modeler": "modeller",
    "modelers": "modellers",
    "labeling": "labelling",
    "labeled": "labelled",
    "behavior": "behaviour",
    "behaviors": "behaviours",
    "behavioral": "behavioural",
    "center": "centre",
    "centers": "centres",
    "color": "colour",
    "colors": "colours",
    "defense": "defence",
    "catalog": "catalogue",
}
_US_WORD_RE = re.compile(r"\b(" + "|".join(_US_TO_UK) + r")\b")


def uk_spelling(text):
    """Map common US spellings in lower-case text to UK spelling.

    >>> uk_spelling("data visualization and modeling")
    'data visualisation and modelling'
    """
    t = _IZE_RE.sub(lambda m: m.group(1) + "s" + m.group(2), text)
    return _US_WORD_RE.sub(lambda m: _US_TO_UK[m.group(1)], t)


# ── Plurals ───────────────────────────────────────────────────
# Words that end in "s" but are not plurals (or whose singular is not a skill).
_KEEP_WORDS = {
    "pandas", "kubernetes", "jenkins", "redis", "windows", "aws", "gcs",
    "sas", "saas", "paas", "iaas", "series", "sales", "news", "teams",
}
# Endings that are almost never a plain plural "-s".
_KEEP_ENDINGS = ("ss", "us", "is", "ics", "js", "os", "ops")


def singularise(word):
    """Strip a simple English plural from one lower-case word.

    Only the common cases ("skills" -> "skill", "libraries" -> "library",
    "processes" -> "process"). Short words, known product names and endings
    such as "-ics" / "-js" / "-ops" are left alone.

    >>> [singularise(w) for w in ["skills", "libraries", "analytics", "nodejs"]]
    ['skill', 'library', 'analytics', 'nodejs']
    """
    if len(word) <= 3 or word in _KEEP_WORDS or not word.endswith("s"):
        return word
    if word.endswith("ies") and len(word) > 4:
        return word[:-3] + "y"
    if word.endswith(("sses", "shes", "ches", "xes")):
        return word[:-2]
    if word.endswith(_KEEP_ENDINGS):
        return word
    return word[:-1]


# ── Matching key ──────────────────────────────────────────────
# Separators that do not change the meaning of a skill term.
# "+", "#", "/" and "&" are kept: C++, C#, CI/CD, A/B, R&D.
_SEPARATORS_RE = re.compile(r"[\s\-_.]+")


def skill_key(term):
    """Comparison key for a skill term: normalised, UK spelling, singular,
    separators removed.

    >>> {skill_key(t) for t in ["Power-BI", "PowerBI", "Power BI"]}
    {'powerbi'}
    >>> {skill_key(t) for t in ["Node.js", "NodeJS", "node js"]}
    {'nodejs'}
    >>> skill_key("Data Visualization") == skill_key("data visualisation")
    True
    """
    t = uk_spelling(normalise_text(term))
    tokens = [singularise(tok) for tok in _SEPARATORS_RE.split(t) if tok]
    return "".join(tokens)
