# Preliminary Comparison of Keyword and Semantic Skill Extraction (draft, S2-02-02)

> Draft for the SEAGAS Sprint 2 report. Author: Ng Yong Hin.
> All figures come from `nlp/experiments/compare_methods.py` (run 2026-10-15); the full
> tables are in `nlp/experiments/results/method_comparison_summary.md`.
> Re-check the numbers if the script is run again.

## Purpose

Before the NLP module is connected to the backend, we ran the Level 1 (keyword) and
Level 2 (semantic) extractors on the same real job descriptions to see where they
disagree, and to check what the hybrid method adds. This is a preliminary comparison,
not an accuracy evaluation. No gold labels exist yet, so no precision or recall is
reported; that evaluation is planned for Sprint 4.

## Data and method

The input is the Sprint 2 JD dataset: **65 job descriptions** for the six target roles
(10 to 13 per role), copied by hand from JobStreet and Indeed Malaysia on 12 October 2026
and anonymised (see the Dataset Description). The Sprint 2 target was 60 JDs, and all 65
are used here.

Each JD was processed by three methods of `nlp.extract_skills()`:

- **Keyword:** catalogue names and aliases matched with word boundaries, with context
  rules for ambiguous terms such as R, Go and Excel.
- **Semantic:** candidate phrases embedded with all-MiniLM-L6-v2 [1] and matched to the
  138-skill catalogue at cosine similarity ≥ 0.60.
- **Hybrid:** keyword first, then semantic hits for skills not yet found that do not
  overlap a keyword match.

Skills were compared by canonical name. Agreement between keyword and semantic is the
Jaccard index per JD: skills found by both, divided by skills found by either. Run time
is the median of five runs per JD on a laptop CPU, after the model was loaded. The 350
cases where exactly one of the two methods found a skill were saved with their context;
15 representative cases were classified by reading the JD text.

## Results

**Table 1. Mean skills found per JD and keyword–semantic agreement**

| Role | JDs | Keyword | Semantic | Hybrid | Jaccard |
|---|---:|---:|---:|---:|---:|
| Data Analyst | 11 | 9.8 | 8.0 | 12.1 | 0.49 |
| Data Scientist | 10 | 11.0 | 8.2 | 13.4 | 0.48 |
| Software Developer | 13 | 7.6 | 6.1 | 9.6 | 0.48 |
| Cybersecurity Analyst | 10 | 7.2 | 6.6 | 9.3 | 0.47 |
| Cloud Engineer | 10 | 10.2 | 7.7 | 12.3 | 0.56 |
| Web Developer | 11 | 9.9 | 7.6 | 11.2 | 0.58 |
| **All** | **65** | **9.2** | **7.3** | **11.2** | **0.51** |

Median time per JD: keyword 0.7 ms, semantic 164 ms, hybrid 159 ms. Semantic time
grows with JD length (r = 0.90); across repeated runs on the same laptop the semantic
mean varied between 123 and 155 ms. Loading the model takes 18–24 s, once per process.

![Figure 1](../../nlp/experiments/results/method_skills_per_jd.png)

*Figure 1. Mean number of skills found per JD by each method, for all JDs and per role.*

![Figure 2](../../nlp/experiments/results/method_agreement.png)

*Figure 2. Skills per JD found only by keyword, by both methods, or only by semantic
(mean per JD).*

![Figure 3](../../nlp/experiments/results/method_runtime.png)

*Figure 3. Time per JD by method: median (dot) and range over the 65 JDs (line), log
scale.*

**Table 2. Fifteen disagreements, classified by reading the JD text**

| # | JD text | Skill | Found by (score) | Class |
|---:|---|---|---|---|
| 1 | "Develop dashboards" | Data Visualisation | semantic (0.69) | Likely keyword miss |
| 2 | "Collaborate with cross-functional teams" | Teamwork | semantic (0.67) | Likely keyword miss |
| 3 | "meet deadlines" (alias is "Meeting deadlines") | Time Management | semantic (0.68) | Likely keyword miss |
| 4 | "security assessments and vulnerability scans" | Vulnerability Assessment | semantic (0.87) | Likely keyword miss |
| 5 | "designing, developing, testing, and maintaining software" | A/B Testing | semantic (0.62) | Likely semantic false positive |
| 6 | "capabilities in AI, ... data, and analytics" | Google Analytics | semantic (0.66) | Likely semantic false positive |
| 7 | "subject to business needs and available headcount" | Business Analysis | semantic (0.62) | Likely semantic false positive |
| 8 | "Meet customer with Project Manager" | Project Management | semantic (0.67) | Likely semantic false positive |
| 9 | "Digital Transformation initiatives" | Self-Motivation | keyword (1.00) | Ambiguous-term issue |
| 10 | "Continuous monitoring of security events" | Monitoring & Observability | keyword (1.00) | Ambiguous-term issue |
| 11 | "knowledge in programming languages such as Java" | R | semantic (0.60) | Ambiguous-term issue |
| 12 | "ensuring prompt resolution" | Prompt Engineering | semantic (0.64) | Ambiguous-term issue |
| 13 | "UI/UX flows" ("UI/UX" is not an alias) | UI/UX Design | semantic (0.69) | Catalogue gap |
| 14 | "firewalls" (not an alias) | Firewall Management | semantic (0.65) | Catalogue gap |
| 15 | "the database" (no general database skill) | MySQL | semantic (0.67) | Catalogue gap |

JD references and the full context are in
`nlp/experiments/results/method_disagreements_reviewed.csv`.

## Findings

1. **Hybrid finds the most skills, in every role.** It averages 11.2 skills per JD,
   against 9.2 for keyword and 7.3 for semantic. It adds 129 skills on top of the keyword
   results, in 58 of the 65 JDs. The largest single gain is Critical Thinking (21 JDs),
   from coordinated lists such as "good analytical and problem-solving skills".
2. **The two methods agree only moderately.** Mean Jaccard is 0.51, and 16 of the 65 JDs
   score below 0.40. Of 713 JD–skill pairs found by either method, 51% were found by
   both, 33% only by keyword and 16% only by semantic.
3. **Semantic misses exact names near its threshold.** 69 of the 237 keyword-only skills
   score 0.55–0.60 as a phrase, just below the 0.60 threshold: SQL (23 JDs),
   Communication (12), CSS (8), PHP (6), CI/CD (5). Another 88 were never produced as
   candidate phrases. Semantic extraction alone is therefore not suitable; keyword
   matching has to lead, as it does in hybrid.
4. **Semantic-only hits sit close to the threshold and mix paraphrases with generic
   words.** The median score is 0.644, and 59 of the 113 hits are below 0.65.
   - Many are paraphrases that keyword misses, such as Teamwork (11 JDs) and Data
     Visualisation (8).
   - Others map generic words to one specific tool: "testing" → A/B Testing (14 JDs),
     "programming languages" → R (7), "analytics" → Google Analytics (6), "database" →
     MySQL (4). Inside hybrid, these four patterns account for 30 of the 129 added
     skills.
5. **Keyword errors come from broad aliases and missing aliases.** "Initiatives" (a
   project) counts as Self-Motivation in 9 JDs, and "monitoring" counts as Monitoring &
   Observability in 12 JDs, including security monitoring. Real mentions such as
   "UI/UX", "firewalls" and "meet deadlines" are missed because no alias covers them.

## Before the Sprint 4 evaluation

- Label the 60-JD gold sample by hand. `compare_methods.py` then adds precision, recall
  and F1 per method on the labelled JDs; until then, the classes in Table 2 are one
  reader's judgement.
- Catalogue:
  - add the missing aliases ("UI/UX", "firewall", "firewalls");
  - decide whether general "Software Testing" and "Database" skills are needed, so that
    generic mentions stop mapping to A/B Testing and MySQL.
- Semantic step: filter one-word generic phrases ("testing", "analytics", "database",
  "administration"), and re-check the 0.60 threshold on the gold set, because many
  semantic-only hits fall between 0.60 and 0.65.
- Keyword step: narrow the "Initiative" and "Monitoring" aliases, and match verb forms
  ("meet" / "meeting" deadlines).
- Repeat this comparison on the larger Sprint 3 JD collection.

## References

[1] N. Reimers and I. Gurevych, "Sentence-BERT: Sentence embeddings using Siamese
BERT-networks," in *Proc. 2019 Conf. Empirical Methods in Natural Language Processing
and 9th Int. Joint Conf. Natural Language Processing (EMNLP-IJCNLP)*, Hong Kong, China,
2019, pp. 3982–3992.
