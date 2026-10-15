# Semantic similarity thresholds (S2-02-01)

**Chosen:** `SKILL_TEXT_MODE = "name_aliases"`, `MATCH_THRESHOLD = 0.60`,
`RELATED_THRESHOLD = 0.50` (set in `nlp/config.py`).

## Data
60 phrase / skill pairs, labelled by hand by Ng Yong Hin (30 same skill, 30 not).
Phrases come from the candidate generator of the semantic extractor run over the
65 JDs in `data/jd_dataset/jd_dataset.csv` (3,252 distinct phrases; phrases that
are exactly a catalogue name or alias were left out, as the keyword extractor
handles them). Each phrase was paired with its most and second-most similar
skill, and 10 pairs were drawn at random from each of six similarity bins
(< 0.40 up to ≥ 0.80) so that clear matches, near misses and non-matches are all
present. The model only chose which pairs to show; it did not label them.

## Method
For each way of embedding a skill (`name_aliases`: name and aliases as one text;
`name_aliases_max`: name and each alias separately, best one counts;
`name_description`: name and description), the cosine similarity of every pair
was computed with `all-MiniLM-L6-v2`, and a pair counted as a match when the
similarity ≥ t, for t = 0.40, 0.45, …, 0.90. Precision, recall and F1 were
measured against the hand labels (`results/threshold_sweep.csv`,
`results/pair_scores.csv`, figure `results/threshold_sweep.png`).

| Mode | Best t | Precision | Recall | F1 |
|---|---|---|---|---|
| **name_aliases** | **0.60** | **1.000** | 0.867 | **0.929** |
| name_aliases_max | 0.65 | 0.875 | 0.933 | 0.903 |
| name_description | 0.50 | 0.848 | 0.933 | 0.889 |

## Choice
`name_aliases` has the best F1 (0.026 above the next mode) and is also the
simplest representation (one vector per skill). Its best threshold, 0.60, gives
no false positives on this set; the next step down, 0.55, has a slightly lower
F1 (0.915) with two false positives, and false skills hurt students more than a
missed synonym. `RELATED_THRESHOLD = 0.50` was read from `pair_scores.csv`: 7 of
the 30 label-0 pairs lie in [0.50, 0.60), and they are mostly the "related tool /
umbrella term" cases it is meant for (Microsoft Power Automate → Power BI 0.59,
security findings → Vulnerability Assessment 0.54, backend, APIs → REST API 0.52,
security platforms → SOC 0.51, logs → Splunk 0.51, private and public cloud
infrastructure → AWS 0.50, plus project leads → Leadership 0.597). Going down to
0.45 would add generic phrases such as "testing" and "work independently".

**Fragility.** With only 60 pairs, one pair moves F1 by about 0.02.
6 pairs lie within ±0.05 of MATCH (4 positive, 2 negative) and 13 within ±0.05 of
RELATED, so both values should be re-checked on the gold set (Sprint 4).

## Limitations
Joining all aliases into one text lowers the similarity of short, natural
phrases. On the POC004 brief example, semantic extraction alone finds 4 of 7
skills (Python, Power BI, Data Visualisation, Problem Solving); "SQL" and
"communication" score 0.59 and Critical Thinking ("good analytical … skills")
is not found (best phrase "analytical skills" 0.53, below Problem Solving
0.58). "statistical modelling" (0.56), "written and verbal communication"
(0.57) and "communicates well" (0.51) also stay below MATCH. Exact names and
aliases are found by the keyword extractor, so semantic extraction is meant to
run inside hybrid extraction, not alone. `name_aliases_max` recovers these
cases but adds false positives at its best threshold; it should be compared
again on the gold set.
