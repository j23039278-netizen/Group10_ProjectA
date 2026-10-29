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

## List items in hybrid extraction (S2-02, added 2026-10-15)

**Chosen:** `LIST_ITEM_TEXT_MODE = "name_aliases_max"`,
`LIST_ITEM_THRESHOLD = 0.70` (set in `nlp/config.py`). The three values above
are unchanged.

**Problem.** Requirements are often written as coordinated lists: "good
analytical, communication and problem-solving skills". Keyword extraction finds
Communication and Problem Solving, but "analytical" is not a catalogue term, and
no semantic candidate phrase contains it (the whole list is one 9-token noun
chunk, above `MAX_PHRASE_TOKENS`). So L1 and L2 both miss Critical Thinking
("Analytical thinking" is its alias) on the POC004 brief example, and on the 20
of the 65 JDs that use the same pattern ("analytical skills / skill / abilities
/ mindset").

**Step.** Hybrid extraction reads each list item that keyword extraction did not
resolve together with the shared head noun ("analytical skills"). The phrase is
looked up as a catalogue term first; otherwise its most similar skill is taken
if the similarity is at least `LIST_ITEM_THRESHOLD`. A list only counts when one
of its items is a keyword hit, so these phrases are skills by construction, and
the question is only *which* skill.

**Mode.** With `name_aliases` the nearest skill for "analytical skills" is
Problem Solving (0.576, wrong); Critical Thinking is second (0.529). With
`name_aliases_max` (each alias embedded separately) it is Critical Thinking at
0.770, matching the alias "Analytical thinking". The sweep above showed that
`name_aliases_max` has the best recall (0.933) and that its false positives come
from phrases that are not skills at all. List items do not have that problem.

**Threshold.** `python nlp/experiments/hybrid_list_items.py` lists every
unresolved list item in the 65 JDs and the brief example
(`results/hybrid_list_items.csv`, 40 items). Each added skill was checked by
reading the JD line:

| Threshold | Items added (65 JDs) | Right | Wrong |
|---|---:|---:|---:|
| 0.65 (F1-best for `name_aliases_max`) | 28 in 24 JDs | 25 | 3 × "organizational skills" → Interpersonal Skills (0.676) |
| **0.70** | **25 in 24 JDs** | **25** | **0** |

At 0.70 the additions are: "analytical skills / skill / abilities / mindset" and
"critical thinker skills" → Critical Thinking (21), "interpersonal skills /
abilities" → Interpersonal Skills (3; two of them are exact catalogue names once
the head noun is added), and "work in a team [and good communication] skills" →
Teamwork (1). Items left out at 0.70 include "customer engagement skills" →
Customer Focus (0.615) and "analytical capabilities" → Critical Thinking
(0.589), which are right but below the threshold. "Organizational skills" has
no matching catalogue skill, so its nearest skills (Interpersonal Skills 0.676,
Communication 0.656) are both wrong.

**Caveat.** 0.70 is one sweep step above the pair-based best threshold, and it
was chosen on the same 65 JDs it is reported on. Re-check it on the gold set
(Sprint 4). Setting `LIST_ITEM_THRESHOLD` above 1.0 switches the similarity part
of this step off; catalogue-term lookups such as "interpersonal skills" stay.

## TF-IDF extraction (added 2026-10-29)

**Chosen:** `TFIDF_ANALYZER = "char_wb"` (character 3-5-grams inside word
boundaries), `TFIDF_MATCH_THRESHOLD = 0.25` (set in `nlp/config.py`). The
values above are unchanged.

**What it is.** `extract_skills(method="tfidf")` is the third L2 option named
in the brief (TF-IDF + cosine), kept for the method comparison, not for the
backend. It uses the same candidate phrases as semantic extraction, so only the
representation differs: a scikit-learn `TfidfVectorizer` is fitted on the
catalogue skill texts (`SKILL_TEXT_MODE = "name_aliases"`, one text per skill;
IDF from the 166 skills), and each phrase counts as its most similar skill when
the TF-IDF cosine is at least the threshold. Both sides go through
`normalise_text()` and `uk_spelling()` first, as in keyword extraction.

**Sweep.** `python nlp/experiments/threshold_sweep.py --method tfidf`, the same
60 hand-labelled pairs (labels unchanged), thresholds 0.05-0.90 in 0.05 steps
(`results/threshold_sweep_tfidf.csv`, `results/pair_scores_tfidf.csv`, figure
`results/threshold_sweep_tfidf.png`). Word analyzer: 1-2-grams, English stop
words removed, tokens keep "+" and "#" ("c++", "c#").

| Threshold | word P | word R | word F1 | char_wb P | char_wb R | char_wb F1 |
|---:|---:|---:|---:|---:|---:|---:|
| 0.05 | 0.674 | 0.967 | 0.795 | 0.588 | 1.000 | 0.741 |
| 0.10 | 0.674 | 0.967 | 0.795 | 0.625 | 1.000 | 0.769 |
| 0.15 | 0.700 | 0.933 | 0.800 | 0.682 | 1.000 | 0.811 |
| 0.20 | 0.750 | 0.900 | 0.818 | 0.725 | 0.967 | 0.829 |
| **0.25** | 0.788 | 0.867 | 0.825 | **0.784** | **0.967** | **0.866** |
| 0.30 | **0.833** | **0.833** | **0.833** | 0.758 | 0.833 | 0.794 |
| 0.35 | 0.857 | 0.600 | 0.706 | 0.793 | 0.767 | 0.780 |
| 0.40 | 0.850 | 0.567 | 0.680 | 0.846 | 0.733 | 0.786 |
| 0.45 | 0.833 | 0.500 | 0.625 | 0.870 | 0.667 | 0.755 |
| 0.50 | 0.867 | 0.433 | 0.578 | 0.870 | 0.667 | 0.755 |
| 0.55 | 0.846 | 0.367 | 0.512 | 0.941 | 0.533 | 0.681 |
| 0.60 | 0.900 | 0.300 | 0.450 | 0.938 | 0.500 | 0.652 |
| 0.65 | 0.900 | 0.300 | 0.450 | 1.000 | 0.400 | 0.571 |
| 0.70 | 1.000 | 0.200 | 0.333 | 1.000 | 0.333 | 0.500 |
| 0.75 | 1.000 | 0.100 | 0.182 | 1.000 | 0.267 | 0.421 |
| 0.80 | 0.000 | 0.000 | 0.000 | 1.000 | 0.200 | 0.333 |
| 0.85 | 0.000 | 0.000 | 0.000 | 1.000 | 0.100 | 0.182 |
| 0.90 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |

Best per analyzer (F1, ties to the higher threshold): word 0.30 (P 0.833,
R 0.833, F1 0.833); **char_wb 0.25 (P 0.784, R 0.967, F1 0.866)**. char_wb wins
by 0.033 because sub-word n-grams match word forms that word n-grams miss: of
the positive pairs, char_wb (at 0.25) keeps and word (at 0.30) loses
"Communicate with stakeholders" → Stakeholder Communication (word 0.000, char_wb
0.774), "building RESTful APIs" → REST API (0.257 vs 0.535) and "visualization
software" → Data Visualisation (0.162 vs 0.271). For comparison, embeddings
(`name_aliases`) reach F1 0.929 at 0.60 on the same pairs. TF-IDF cosines run
much lower than embedding cosines, so the two thresholds are not comparable.

**Caveat: the pairs favour TF-IDF less than the JDs punish it.** The 60 pairs
were sampled by embedding similarity and score only the labelled skill, while
extraction keeps a phrase's *best* skill out of 166. On the 65 JDs, TF-IDF at
0.25 finds 25.6 skills per JD (hybrid 10.8, keyword 9.4), and only 34% of its
JD-skill pairs are also hybrid results. Most of the rest are surface look-alikes:
"deployment" → Employment Law (0.54), "restore" → REST API (0.32), "backend
developers" → Training & Development (0.72), "Computer Science" → Computer
Vision (0.29). Raising the threshold does not fix this, it only removes skills:

| TF-IDF threshold | Skills per JD | Share also found by hybrid |
|---:|---:|---:|
| 0.25 | 25.6 | 0.34 |
| 0.40 | 15.9 | 0.50 |
| 0.50 | 11.0 | 0.62 |
| 0.60 | 7.1 | 0.72 |

(Read from `results/method_comparison.csv`: a skill's confidence is its best
phrase score, so the counts at a higher threshold are exact.) The F1-best value
is kept as asked, so the comparison shows TF-IDF at its best on the labelled
pairs. On the POC004 brief example TF-IDF finds 6 of 7 (Critical Thinking
missing; extra Data Analysis from the title "junior data analyst").

### Check on the gold set (2026-10-29)

`gold_labels.csv` (892 hand-made skills in 59 JDs, frozen after the A/B
resolution) gives micro precision / recall / F1 per method
(`results/method_comparison_summary.md`, "Gold labels"):

| Method | Precision | Recall | F1 | Skills per JD |
|---|---:|---:|---:|---:|
| keyword | 0.920 | 0.583 | 0.714 | 9.6 |
| semantic | 0.883 | 0.414 | 0.563 | 7.1 |
| hybrid | 0.867 | 0.631 | **0.731** | 11.0 |
| TF-IDF (char_wb, 0.25) | 0.356 | 0.604 | 0.448 | 25.7 |

The same TF-IDF run at other settings on those 59 JDs (scratch script, not kept;
same loading and scoring as `gold_scores()` in `compare_methods.py`):

| Threshold | char_wb P / R / F1 | word P / R / F1 |
|---:|---|---|
| 0.20 | 0.319 / 0.618 / 0.421 | 0.435 / 0.580 / 0.497 |
| **0.25** | **0.356 / 0.604 / 0.448** | 0.475 / 0.554 / 0.511 |
| 0.30 | 0.398 / 0.595 / 0.477 | 0.540 / 0.538 / **0.539** |
| 0.40 | 0.497 / 0.529 / 0.512 | 0.587 / 0.445 / 0.506 |
| 0.45 | 0.542 / 0.497 / 0.518 | 0.628 / 0.407 / 0.494 |
| 0.50 | 0.609 / 0.453 / **0.520** | 0.651 / 0.348 / 0.453 |
| 0.60 | 0.692 / 0.331 / 0.448 | 0.783 / 0.279 / 0.412 |

**Decision: keep char_wb at 0.25.** The gold set confirms the caveat above:
the labelled pairs overrate TF-IDF, whose F1 on real JDs (0.448) is far below
keyword (0.714) and hybrid (0.731). Retuning on the gold set would raise it to
at most 0.539 (word, 0.30), still well below keyword, so the conclusion of the
comparison does not depend on the threshold. Choosing the value on the set it
is reported on would also overstate it; 0.25 was chosen on independent data.
TF-IDF's recall stays near hybrid's even at 0.15 (0.624), so its problem is
precision: surface look-alikes, not missed skills.
