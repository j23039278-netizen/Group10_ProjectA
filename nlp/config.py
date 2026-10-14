"""
Settings for Level 2 (semantic) skill extraction and matching.

Every similarity threshold lives here so nothing else hard-codes them.
How the values were chosen: nlp/experiments/THRESHOLDS.md (S2-02-01).
"""

# Sentence Transformers model (384-dim, ~90 MB, CPU friendly).
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

# spaCy pipeline for sentences, noun chunks and verb phrases (NER is not loaded).
SPACY_MODEL = "en_core_web_sm"

# Text embedded for each catalogue skill (see nlp/model.py, skill_texts()):
#   "name_aliases"     -> "Power BI: PowerBI, Microsoft Power BI"
#   "name_aliases_max" -> "Power BI", "PowerBI", "Microsoft Power BI" (best one counts)
#   "name_description" -> "Power BI: Business intelligence and data visualisation tool by Microsoft."
# PROVISIONAL until the labelled sweep has compared them.
SKILL_TEXT_MODE = "name_aliases_max"

# Cosine similarity thresholds.
#   MATCH:   a JD phrase / student skill at or above this counts as the skill.
#   RELATED: at or above this (but below MATCH) it is a similar, not the same,
#            skill; match_skills() will use it for "developing".
# PROVISIONAL: set by hand before the labelled threshold sweep was run.
# Replace with the values from nlp/experiments/THRESHOLDS.md.
MATCH_THRESHOLD = 0.65
RELATED_THRESHOLD = 0.55

# Candidate phrases longer than this (in tokens) are not embedded.
MAX_PHRASE_TOKENS = 8
