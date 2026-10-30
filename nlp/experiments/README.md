# Threshold experiment (S2-02-01)

**Status (2026-10-15):** done. `threshold_pairs.csv` labelled by hand (60 pairs),
sweep run, values chosen and set in `nlp/config.py`
(`name_aliases`, MATCH 0.60, RELATED 0.50). Reasoning: `THRESHOLDS.md`.

Chooses the cosine similarity thresholds for semantic matching
(`MATCH_THRESHOLD`, `RELATED_THRESHOLD` and `SKILL_TEXT_MODE` in `nlp/config.py`).

```bash
python nlp/experiments/threshold_sweep.py
```

1. First run (no `threshold_pairs.csv`): writes `threshold_pairs_candidates.csv`,
   about 60 phrase / skill pairs from `data/jd_dataset/jd_dataset.csv`, and stops.
   The model only picks the pairs (spread over similarity bins, best and
   second-best skill per phrase, shuffled); it does not label them.
2. A person labels every row and saves the file as `threshold_pairs.csv`.
3. Second run: sweeps 0.40–0.90 for all three skill text modes and writes
   `results/threshold_sweep.csv`, `results/pair_scores.csv` and
   `results/threshold_sweep.png`. The decision goes in `THRESHOLDS.md`.

`python nlp/experiments/threshold_sweep.py --method tfidf` runs the same pairs
through TF-IDF (word 1-2-grams and char_wb 3-5-grams, thresholds 0.05–0.90) and
writes `results/threshold_sweep_tfidf.csv`, `results/pair_scores_tfidf.csv` and
`results/threshold_sweep_tfidf.png` (`TFIDF_ANALYZER`, `TFIDF_MATCH_THRESHOLD`).

`timing.py` measures time per JD for keyword, semantic and hybrid extraction.

## Other scripts

| Script | What it shows | Output |
|---|---|---|
| `hybrid_list_items.py` | Evidence for `LIST_ITEM_TEXT_MODE` / `LIST_ITEM_THRESHOLD`: every coordinated-list item ("good **analytical** and problem-solving skills") in the 65 JDs and the brief example, with its nearest skills | `results/hybrid_list_items.csv` (reasoning in `THRESHOLDS.md`) |
| `compare_with_current.py` | Before / after for S2-12-01 and S2-11-02: today's substring matching in `backend/routers/assessments.py` (reimplemented) against `match_skills(method="hybrid")`, 200 synthetic students (seed 42) × 6 roles | `results/compare_with_current.md`, `results/compare_with_current_scores.csv`, `results/compare_with_current_changes.csv` |
| `evidence_effect.py` | Evidence derived from projects and certifications (`nlp/evidence.py`): every synthetic student against their own target role, with and without it, with stored evidence emptied (as for real users) and as generated; Developing → Strong rows and mean readiness per archetype, role and number of records; derived evidence against the generator's | `results/evidence_effect.md`, `results/evidence_effect.csv`, `results/evidence_effect_students.csv` |
| `compare_methods.py` | S2-02-02: keyword vs semantic vs hybrid vs TF-IDF extraction on the 65 real JDs: skills per JD, Jaccard overlap (keyword vs semantic, and every pair of methods), runtime, every disagreement with context, 15 classified by hand; precision / recall / F1 only once `gold_labels.csv` has hand-made rows | `results/method_*.csv`, `results/method_comparison_summary.md`, `results/method_*.png`; write-up in `docs/report_drafts/method_comparison.md` |

Both run from the repo root, e.g. `python nlp/experiments/compare_with_current.py`.

## Labelling rules (`label` column)

Write `1` if a recruiter who wrote the phrase would accept a student who has
`skill_name` as having **that** skill; otherwise `0`. Decide from the phrase
(and the JD in `jd_ref` if needed), never from what the model would say.

| Phrase → skill | Label | Why |
|---|---|---|
| "interactive dashboards" → Data Visualisation | 1 | Same skill in other words |
| "statistical modelling" → Statistical Analysis | 1 | Listed as a variant of the skill |
| "Tableau dashboards" → Power BI | 0 | Related tool, not the same skill (a "related" case) |
| "cloud platforms" → AWS | 0 | Umbrella term; AWS is one option |
| "AWS services" → Cloud Computing | 1 | AWS work is cloud computing work |
| "network troubleshooting" → Networking | 1 | Networking skill applied |
| "the infrastructure team" → Teamwork | 0 | Names a team, asks for no skill |

Keep the `phrase` and `skill_name` text unchanged; only fill in `label`
(`jd_ref` may stay). Do not delete rows because they are hard: borderline
pairs are what decide the threshold. If you really cannot decide, use `0`.
