"""
S2-02 performance check: time per JD for semantic extraction on CPU.

    python nlp/experiments/timing.py [path/to/jds.csv ...]

Default input: data/jd_dataset/jd_dataset.csv and the fictional sample
data/jd_dataset/samples/jd_dataset_sample.csv (column raw_text).
Reports the cold start (model + spaCy load, skill embeddings) separately from
the warm per-JD time.
"""

import csv
import statistics
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

DEFAULT_INPUTS = [REPO / "data" / "jd_dataset" / "jd_dataset.csv",
                  REPO / "data" / "jd_dataset" / "samples" / "jd_dataset_sample.csv"]


def main(paths):
    t0 = time.perf_counter()
    from nlp import extract_skills, load_catalogue
    from nlp.model import get_model, get_spacy, skill_embeddings
    get_model()
    t1 = time.perf_counter()
    get_spacy()
    t2 = time.perf_counter()
    skill_embeddings(load_catalogue())
    t3 = time.perf_counter()
    print(f"cold start: model {t1 - t0:.1f}s, spaCy {t2 - t1:.1f}s, skill embeddings {t3 - t2:.2f}s")

    for path in paths:
        with open(path, encoding="utf-8", newline="") as f:
            texts = [r["raw_text"] for r in csv.DictReader(f) if (r.get("raw_text") or "").strip()]
        extract_skills(texts[0], method="semantic")          # warm-up
        times, counts = [], []
        for text in texts:
            start = time.perf_counter()
            found = extract_skills(text, method="semantic")
            times.append(time.perf_counter() - start)
            counts.append(len(found))
        lengths = [len(t) for t in texts]
        print(f"{Path(path).relative_to(REPO)}: {len(texts)} JDs, "
              f"mean {statistics.mean(lengths):.0f} chars | "
              f"mean {statistics.mean(times):.3f}s, median {statistics.median(times):.3f}s, "
              f"max {max(times):.3f}s per JD | {statistics.mean(counts):.1f} skills per JD")


if __name__ == "__main__":
    main([Path(p) for p in sys.argv[1:]] or DEFAULT_INPUTS)
