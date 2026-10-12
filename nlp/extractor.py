"""
Level 1 (keyword) skill extraction for the SEAGAS NLP module.
Author: Ng Yong Hin (AI / NLP Engineer)

Pure Python + regex, standard library only. Use it through
`nlp.extract_skills(text, method="keyword")`.

How it works:
  1. The JD is split into tokens: runs of letters / digits, plus the symbols
     "+", "#", "/" and "&" that belong to skill names (C++, C#, CI/CD, A/B).
     Every token keeps its character offsets in the original text.
  2. Runs of up to N tokens that are joined only by a space, "-", "_" or "."
     are turned into a key with the steps of normalise.skill_key() (lower case,
     UK spelling, singular, separators removed) and looked up in an index of
     every catalogue name and alias. Whole tokens are compared, so "Java" never
     matches inside "JavaScript" and "SQL" never matches inside "MySQL".
  3. When candidate spans overlap, the longest one wins ("Power BI" over "BI",
     "Kali Linux" over "Linux").
  4. Ambiguous aliases (R, Go, Excel, CV, REST, Shell, ...) are kept only when
     the context supports them: see _CONTEXT_RULES, or a list of other skills
     ("Python, R and SQL").
  5. One ExtractedSkill per canonical skill, ordered by start_char.
"""

import re
import weakref
from functools import lru_cache
from typing import NamedTuple

from nlp.normalise import normalise_text, singularise, uk_spelling
from nlp.types import ExtractedSkill

# Confidence for a canonical name or safe alias, and for an ambiguous alias
# that passed the context check.
KEYWORD_CONFIDENCE = 1.0
AMBIGUOUS_CONFIDENCE = 0.8

# Ambiguous aliases up to this length must keep the catalogue's casing
# ("R", "Go", "CV", "REST"), so "go to" or "the rest" never match.
CASE_SENSITIVE_MAX_LEN = 4

# Characters of text on each side of an ambiguous alias that the rules see.
CONTEXT_WINDOW = 60

# ── Tokens ────────────────────────────────────────────────────
# Letters / digits, or one of the symbols kept by skill_key().
_TOKEN_RE = re.compile(r"[^\W_]+|[+#/&]")
# Text allowed between two tokens of one skill term: "Power BI", "Power-BI",
# "Node.js", "C++" (nothing). A comma, a full stop + space or a line break ends
# the term.
_JOIN_RE = re.compile(r"[ \t]*[-_][ \t]*|[ \t]{1,3}|\.?")


@lru_cache(maxsize=20000)
def _token_key(token):
    """Comparison key of one token: same steps as normalise.skill_key()."""
    return singularise(uk_spelling(normalise_text(token)))


def _term_key(term):
    """Comparison key of a catalogue name or alias ("Power-BI" -> "powerbi")."""
    return "".join(_token_key(m.group()) for m in _TOKEN_RE.finditer(term))


# ── Context rules for ambiguous aliases ───────────────────────
# Keyed by the alias's term key ("excel"; "Excels" uses the same row). Patterns
# are case-insensitive regexes run on the text around the hit (whitespace
# collapsed); "<>" stands for the alias.
#   veto:    the alias never counts here (checked first).
#   support: the alias counts as the skill.
# An ambiguous alias with no veto can also count when it sits in a list next to
# another skill that was found ("Python, R and SQL", bullet lists). Aliases not
# in this table only count in such a list.
_END = r"(?=$|[,.;:)/]| (?:and|or)\b)"   # "<>" ends a phrase: "in R.", "in Go and ..."

_CONTEXT_RULES = {
    "r": {
        "veto": (r"<> ?&", r"& ?<>"),                                    # R&D, Q&R
        "support": (r"\b(?:in|using|with) <>" + _END,
                    r"<> (?:programming|language|studio|shiny|markdown|packages?|scripts?|code)\b",
                    r"\b(?:rstudio|tidyverse|ggplot2?|dplyr|cran)\b"),
    },
    "go": {
        "veto": (r"<>[ -]to\b", r"\b(?:let's|on the) <>",
                 r"<> (?:ahead|beyond|above|live|further|through|back|out)\b"),
        "support": (r"<> ?\((?:golang|go ?lang)\)",
                    r"<> (?:programming|language|lang|developers?|engineers?|modules?|routines?|services?)\b",
                    r"\b(?:in|using|with) <>" + _END,
                    r"\b(?:golang|goroutines?)\b"),
    },
    "excel": {
        "veto": (r"<>s? (?:in|at)\b", r"\b(?:to|will|can|who|you'll|must) <>"),   # "excel in", "to excel"
        "support": (r"<> (?:spreadsheets?|workbooks?|sheets?|formulas?|functions?|macros?|vba|pivot"
                    r"|vlookups?|skills?|reports?|reporting|models?|dashboards?|templates?)\b",
                    r"\b(?:advanced|proficient|proficiency|intermediate|basic|strong|in|using|with|of) <>",
                    r"\b(?:vlookup|xlookup|pivot ?tables?|vba|power query)\b"),
    },
    "cv": {
        "veto": (r"\b(?:send|submit|attach|upload|email|forward|include) (?:us )?(?:a |an |your )?"
                 r"(?:updated |detailed |latest |full )?<>",
                 r"\b(?:your|my|updated|detailed|latest) <>",
                 r"<> (?:and|&|,|or) ?(?:a )?(?:cover letter|resume|résumé|portfolio|transcripts?|references)",
                 r"<> to\b",
                 r"\b(?:resume|résumé|cover letter|curriculum vitae)\b"),
        "support": (r"<> (?:models?|pipelines?|tasks?|algorithms?|engineers?|research|libraries|systems?"
                    r"|projects?|applications?|techniques?)\b",
                    r"\b(?:opencv|yolo|image processing|image classification|object detection|segmentation)\b"),
    },
    "rest": {
        "veto": (r"<> (?:of|assured|day|days|period)\b",),
        "support": (r"<> ?(?:apis?|services?|endpoints?|ful|principles|architecture|interfaces?|calls?|clients?)\b",
                    r"\b(?:soap|grpc|graphql|openapi|swagger|json|http)\b"),
    },
    "shell": {
        "veto": (r"<> (?:malaysia|plc|oil|petroleum|company|group|refinery|station)\b",
                 r"\b(?:at|join|joining) <>"),
        "support": (r"<> (?:scripts?|scripting|commands?|programming)\b",
                    r"\b(?:unix|linux|bash|zsh|posix|command[- ]line|terminal) <>"),
    },
    "node": {
        "veto": (r"<> (?:in|of)\b",),
        "support": (r"<> ?(?:backend|back-end|server|packages?|modules?|apis?)\b",
                    r"\b(?:npm|express(?:\.?js)?|javascript|typescript)\b"),
    },
    "spring": {
        "veto": (r"<> (?:semester|intake|internship|term|break|season|20\d\d)\b",),
        "support": (r"<> (?:mvc|security|data|cloud|batch)\b",
                    r"\b(?:java|kotlin|hibernate|jpa|maven|gradle)\b"),
    },
    "express": {
        "veto": (r"\bto <>", r"<> (?:your|their|ideas?|interest|thoughts|opinions|concerns|yourself|themselves)\b"),
        "support": (r"<> ?(?:framework|server|routes?|routing|middleware|apis?)\b",
                    r"\b(?:node(?:\.?js)?|mongodb|mern|mean stack)\b"),
    },
    "swift": {
        "veto": (r"<> (?:response|action|turnaround|resolution|delivery|learner)\b",),
        "support": (r"<> ?(?:ui|programming|language|developers?)\b",
                    r"\b(?:ios|xcode|swiftui|objective-?c|cocoa)\b"),
    },
}

# Stands for the alias inside the context string. It is not a word character,
# so write "in <>", not "in <>\b".
_MARK = "\ue000"
_SPACES_RE = re.compile(r"\s+")


def _compile_rules(rules):
    def comp(patterns):
        return tuple(re.compile(p.replace("<>", _MARK), re.I) for p in patterns)
    return {alias: (comp(r.get("veto", ())), comp(r.get("support", ())))
            for alias, r in rules.items()}


_COMPILED_RULES = _compile_rules(_CONTEXT_RULES)

# Text between two skills that makes them items of one list:
# "Python, R", "SQL and Excel", "NLP/CV", or one bullet line after another.
_LIST_GAP_RE = re.compile(
    r"\s*(?:,|;|/|\||&|,?\s*\b(?:and|or)\b)\s*"
    r"|[ \t]*\n[\s\-*•·]*"
)


# ── Catalogue index ───────────────────────────────────────────
class _Term(NamedTuple):
    skill_name: str
    ambiguous: bool
    spellings: frozenset   # catalogue spellings of an ambiguous alias ("R", "Go")


class _Index(NamedTuple):
    terms: dict            # term key -> _Term
    prefixes: frozenset    # every prefix of every key (stops a window early)
    max_tokens: int        # longest name / alias, in tokens


def _build_index(catalogue):
    claims = {}            # term key -> {skill_name: set of ambiguous spellings}
    name_owner = {}        # key of a canonical name -> skill_name (None if two names share it)
    max_tokens = 1
    for e in catalogue:
        name = e["skill_name"]
        key = _term_key(name)
        name_owner[key] = None if key in name_owner else name
        for term in [name] + e["aliases"] + e["ambiguous_aliases"]:
            key = _term_key(term)
            if not key:
                continue
            spellings = claims.setdefault(key, {}).setdefault(name, set())
            if term in e["ambiguous_aliases"]:
                spellings.add(term)
            max_tokens = max(max_tokens, len(_TOKEN_RE.findall(term)))

    terms = {}
    for key, owners in claims.items():
        # Canonical names win; an alias claimed by two skills is dropped.
        if key in name_owner:
            owner = name_owner[key]
        else:
            owner = next(iter(owners)) if len(owners) == 1 else None
        if owner is None:
            continue
        spellings = frozenset(owners.get(owner, ()))
        terms[key] = _Term(owner, bool(spellings), spellings)

    prefixes = frozenset(k[:i] for k in terms for i in range(1, len(k) + 1))
    return _Index(terms, prefixes, max_tokens)


_INDEX_CACHE = weakref.WeakKeyDictionary()   # SkillCatalogue -> _Index


def _index_for(catalogue):
    index = _INDEX_CACHE.get(catalogue)
    if index is None:
        index = _INDEX_CACHE[catalogue] = _build_index(catalogue)
    return index


# ── Matching ──────────────────────────────────────────────────
class _Span(NamedTuple):
    start: int
    end: int
    term: _Term


def _candidates(text, index):
    """Every token window whose key is a catalogue name or alias."""
    tokens = [(m.start(), m.end(), _token_key(m.group())) for m in _TOKEN_RE.finditer(text)]
    found = []
    for i, (start, _, _) in enumerate(tokens):
        key = ""
        for j in range(i, min(len(tokens), i + index.max_tokens)):
            if j > i and not _JOIN_RE.fullmatch(text, tokens[j - 1][1], tokens[j][0]):
                break
            key += tokens[j][2]
            if key not in index.prefixes:
                break
            term = index.terms.get(key)
            if term is not None:
                found.append(_Span(start, tokens[j][1], term))
    return found


def _longest_first(spans):
    """Drop spans that overlap a longer one (ties: the earlier span wins)."""
    kept = []
    for s in sorted(spans, key=lambda s: (s.start - s.end, s.start)):
        if all(s.end <= k.start or s.start >= k.end for k in kept):
            kept.append(s)
    return kept


def _context(text, span):
    left = _SPACES_RE.sub(" ", text[max(0, span.start - CONTEXT_WINDOW):span.start])
    right = _SPACES_RE.sub(" ", text[span.end:span.end + CONTEXT_WINDOW])
    return left + _MARK + right


def _in_skill_list(text, span, accepted):
    """True if the nearest accepted skill on either side is a neighbour in a list."""
    before = [s for s in accepted if s.end <= span.start]
    after = [s for s in accepted if s.start >= span.end]
    if before:
        left = max(before, key=lambda s: s.end)
        if _LIST_GAP_RE.fullmatch(text, left.end, span.start):
            return True
    if after:
        right = min(after, key=lambda s: s.start)
        if _LIST_GAP_RE.fullmatch(text, span.end, right.start):
            return True
    return False


def _resolve_ambiguous(text, spans):
    """Split spans into accepted [(span, confidence)] using the context rules."""
    accepted = [s for s in spans if not s.term.ambiguous]
    result = [(s, KEYWORD_CONFIDENCE) for s in accepted]
    undecided = []
    for s in spans:
        if not s.term.ambiguous:
            continue
        raw = text[s.start:s.end]
        if len(raw) <= CASE_SENSITIVE_MAX_LEN and raw not in s.term.spellings:
            continue
        veto, support = _COMPILED_RULES.get(_term_key(raw), ((), ()))
        ctx = _context(text, s)
        if any(p.search(ctx) for p in veto):
            continue
        if any(p.search(ctx) for p in support):
            accepted.append(s)
            result.append((s, AMBIGUOUS_CONFIDENCE))
        else:
            undecided.append(s)

    # List rule; repeat so "Python, R, Go" accepts R first, then Go.
    changed = True
    while changed and undecided:
        changed = False
        for s in list(undecided):
            if _in_skill_list(text, s, accepted):
                undecided.remove(s)
                accepted.append(s)
                result.append((s, AMBIGUOUS_CONFIDENCE))
                changed = True
    return result


def extract_keyword(text, catalogue):
    """Level 1 extraction: catalogue names and aliases found in `text`.

    Returns one ExtractedSkill per canonical skill, ordered by start_char.
    raw_skill_text / offsets come from the skill's first occurrence;
    confidence_score is the best over all occurrences (1.0 for a name or safe
    alias, AMBIGUOUS_CONFIDENCE for an ambiguous alias with context).
    """
    if not text or not text.strip():
        return []
    index = _index_for(catalogue)
    spans = _longest_first(_candidates(text, index))

    best = {}   # skill_name -> [first span, confidence]
    for span, conf in sorted(_resolve_ambiguous(text, spans), key=lambda x: x[0].start):
        name = span.term.skill_name
        if name not in best:
            best[name] = [span, conf]
        else:
            best[name][1] = max(best[name][1], conf)

    results = []
    for name, (span, conf) in best.items():
        entry = catalogue.get(name)
        results.append(ExtractedSkill(
            skill_id=entry["skill_id"],
            skill_name=name,
            raw_skill_text=text[span.start:span.end],
            method="keyword",
            confidence_score=conf,
            start_char=span.start,
            end_char=span.end,
        ))
    return results
