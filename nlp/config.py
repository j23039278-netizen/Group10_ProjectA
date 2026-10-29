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
SKILL_TEXT_MODE = "name_aliases"

# Version of the Strong / Developing / Gap rules (docs/NLP_CLASSIFICATION_RULES.md).
# Change it whenever nlp/matcher.py would classify a stored assessment differently:
# start_backend.bat (data/run_assessments.py --auto) then re-assesses every
# synthetic student once, so the advisor dashboard shows the new rules.
# 2026-10-28: rules A and C adopted.
# 2026-10-29: "Monitoring", "Initiative" and "Experimentation" became ambiguous aliases, so they left
# the embedded skill texts; Log Analysis vs Monitoring & Observability fell from
# 0.508 to 0.487 (below RELATED), which turns Developing into Gap for 16 synthetic students.
MATCH_RULES_VERSION = "2026-10-29"

# Cosine similarity thresholds.
#   MATCH:   a JD phrase at or above this counts as the skill; a different
#            student skill at or above this is "very close" (still Developing).
#   RELATED: at or above this (but below MATCH) it is a similar, not the same,
#            skill; match_skills() uses it for "developing".
# Chosen from 60 hand-labelled pairs; see nlp/experiments/THRESHOLDS.md.
MATCH_THRESHOLD = 0.60
RELATED_THRESHOLD = 0.50

# Candidate phrases longer than this (in tokens) are not embedded.
MAX_PHRASE_TOKENS = 8

# Hybrid extraction only: coordinated skill lists such as "good analytical,
# communication and problem-solving skills". Items that keyword extraction did
# not resolve are read with the shared head noun ("analytical skills") and
# matched against the catalogue with LIST_ITEM_TEXT_MODE. The list context
# already says these items are skills, so the mode with the best recall in the
# threshold sweep is used (name_aliases_max: recall 0.933 vs 0.867 for
# name_aliases at their best thresholds).
LIST_ITEM_TEXT_MODE = "name_aliases_max"
# One sweep step (0.05) above name_aliases_max's F1-best threshold (0.65). On
# the 65 JDs, 0.70 adds 25 list items in 24 JDs and all are right on reading
# the JD line; 0.65 would also add "organizational skills" -> Interpersonal
# Skills (0.676, wrong) in 3 JDs. Evidence: nlp/experiments/hybrid_list_items.py,
# reasoning: nlp/experiments/THRESHOLDS.md, "List items in hybrid extraction".
LIST_ITEM_THRESHOLD = 0.70
