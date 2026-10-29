# Extraction fixes, October 2026: before / after

Known misjudgments from 16 October (docs/SEAGAS_NLP_RemainingWork_16October.pdf, section 3.2),
fixed on 2026-10-29. Regression tests: `nlp/tests/test_known_errors.py`.

**Before** is the code and library on `dev` at e5df370, run over the 65 JDs in
`data/jd_dataset/jd_dataset.csv` on 2026-10-29. The committed `method_comparison.csv` from
before this change predated the v3 Business skills, so it was not used as the baseline.
**After** is `method_comparison.csv` from `nlp/experiments/compare_methods.py` with the fixes.
Thresholds are unchanged (MATCH 0.60, RELATED 0.50, LIST_ITEM 0.70).

## Skills per JD

| Method | Mean before | Mean after | Median before | Median after | Total before | Total after |
|---|---:|---:|---:|---:|---:|---:|
| keyword | 9.51 | 9.40 | 9 | 9 | 618 | 611 |
| semantic | 7.66 | 7.00 | 8 | 7 | 498 | 455 |
| hybrid | 11.63 | 10.83 | 11 | 11 | 756 | 704 |

## What each fix changed

| Case | Step that caused it | Fix |
|---|---|---|
| "testing" → A/B Testing, "analytics" → Google Analytics, "database" → MySQL, "programming languages" → R | semantic (one generic word; the list-item step was not involved) | Field words ("testing", "analytics", "database", "programming", "language", "log", "script", "administration", ...) added to `_GENERIC_LEMMAS` in `nlp/extractor.py`. A phrase made only of such words is not embedded. Phrases with a real term are still embedded ("unit testing", "analyse logs"). The generic check now also uses the plain singular, because spaCy kept "Requirements" (a heading) as plural. |
| "UI/UX", "firewall(s)" not found | keyword (missing alias) | Aliases `UI/UX`, `UX/UI` (UI/UX Design) and `Firewall` (Firewall Management; the plural is handled by `singularise`). |
| "initiatives" → Self-Motivation | keyword (broad alias) | `Initiative` moved to ambiguous aliases, with a context rule: counts after "take / show / demonstrate / with / own ..." ("take initiative"), not as a project ("Digital Transformation initiatives"). |
| "monitoring" → Monitoring & Observability | keyword (broad alias) | `Monitoring` moved to ambiguous aliases, with a context rule: counts with infrastructure / system / cloud / performance context or tools (Prometheus, Grafana, ...). Vetoed for security-event monitoring (SIEM / SOC work), business dashboards and machine control. |
| "meet deadlines" not found | keyword (word form) | Catalogue terms of the form "-ing word ... plural object" are also indexed in the base form (`normalise.verb_base_forms`), so "Meeting deadlines" matches "meet deadlines" and "meets deadlines". This is a general rule, not a new alias. |
| "meeting tight deadlines" not found | semantic (phrase extraction) | spaCy reads "meeting" as a conjunct of "work". The verb-phrase step joined the two verbs into "work under pressure and meeting tight deadlines" (0.525). Two verbs are now joined only when the first verb has no complement of its own, so the phrase is "meeting tight deadlines" (0.631 → Time Management). |
| "change logs" → Log Analysis | semantic (spaCy reads "change" as a verb and leaves the bare noun "logs", 0.682) | Covered by the generic-word fix ("log"). |
| "experimentation" → A/B Testing (found by the scan) | keyword (broad alias) | `Experimentation` moved to ambiguous aliases. It counts only with A/B context ("online experimentation", "conversion rates", ...). |

## Hits per skill (JD count; keyword, semantic and hybrid run separately)

| Skill | Keyword | Semantic | Hybrid |
|---|---|---|---|
| A/B Testing | 1 → 0 | 15 → 0 | 15 → 0 |
| Self-Motivation | 21 → 14 | 0 → 0 | 21 → 14 |
| Log Analysis | 1 → 1 | 5 → 4 | 6 → 4 |
| Monitoring & Observability | 14 → 7 | 2 → 1 | 14 → 7 |
| R | 5 → 5 | 8 → 0 | 12 → 5 |
| MySQL | 6 → 6 | 10 → 6 | 10 → 6 |
| Google Analytics | 0 → 0 | 6 → 2 | 5 → 1 |
| Windows Server | 2 → 2 | 5 → 2 | 5 → 2 |
| Bash | 4 → 4 | 7 → 4 | 7 → 4 |
| Brand Management | 0 → 0 | 1 → 0 | 1 → 0 |
| Market Research | 1 → 1 | 2 → 1 | 2 → 1 |
| Requirements Analysis | 1 → 1 | 6 → 5 | 6 → 5 |
| UI/UX Design | 5 → 7 | 3 → 2 | 6 → 7 |
| Firewall Management | 0 → 5 | 5 → 5 | 5 → 5 |
| Time Management | 6 → 7 | 5 → 5 | 8 → 8 |
| Teamwork | 15 → 15 | 20 → 20 | 26 → 27 |
| SIEM | 6 → 6 | 4 → 4 | 6 → 7 |

Disappeared from hybrid: 15 A/B Testing, 7 Self-Motivation and 2 Log Analysis hits.

**Skills that lost more than 3 hybrid hits:** A/B Testing (15), R (7), Monitoring & Observability (7),
Self-Motivation (7), MySQL (4) and Google Analytics (4). Each lost hit was checked against its
JD line. All were the wrong hits described above. The 7 Monitoring hits that remain are all
infrastructure monitoring (JD-CE-0001, CE-0003, CE-0007, CE-0008, CE-0010, DS-0009, SD-0013).
The 14 Self-Motivation hits that remain are "take / demonstrates initiative", "proactive" and
"self-driven".

**Gained in hybrid (3):** JD-SD-0002 UI/UX Design ("mobile UI/UX principles"), JD-CE-0001
Teamwork ("work collaboratively", which was hidden inside the joined phrase) and JD-CY-0010
SIEM ("Assist in Security Event Monitoring", which overlapped the old Monitoring keyword span).
Firewall Management (5 JDs) and Time Management in JD-DA-0005 moved from semantic to keyword.

## Possible true hits lost, and what is left

- JD-CY-0005 "Monitor security alerts and **logs** from ... SIEM": Log Analysis (0.682) is
  gone with the generic "log". It is a plausible hit; the JD still has SIEM and SOC.
- JD-SD-0008 "provide analytics" → Google Analytics (0.618) remains. The verb makes it a
  two-word phrase, so the generic-word filter does not apply.
- Same kind, but a different fix (canonical names or degree subjects, not one generic word),
  left for later: "React to security alerts" → React (JD-CY-0002), "Degree in Statistics" →
  Statistical Analysis (8 JDs), "performance, accuracy, and user experience" → Attention to
  Detail (list rule).

## Assessments

Moving "Monitoring", "Initiative" and "Experimentation" to ambiguous aliases removes them from
the embedded skill texts (`SKILL_TEXT_MODE = name_aliases` uses plain aliases only). A
hybrid re-match of all synthetic students against their role templates found 16 rows that
change, one per student. Log Analysis vs Monitoring & Observability falls from 0.508 to 0.487,
below RELATED, so 14 rows go from Developing to Gap for required Monitoring & Observability and
2 rows for required Log Analysis. No other row changes. `MATCH_RULES_VERSION` is now `2026-10-29`.
