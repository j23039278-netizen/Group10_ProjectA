# Threshold experiment (S2-02-01)

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
3. Second run: sweeps 0.40–0.90 for both skill text modes and writes
   `results/threshold_sweep.csv`, `results/pair_scores.csv` and
   `results/threshold_sweep.png`. The decision goes in `THRESHOLDS.md`.

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
