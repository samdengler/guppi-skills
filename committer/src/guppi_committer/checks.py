"""Commit message checks.

Format rules come from Tim Pope's commit message note and cbea.ms/git-commit.
Prose rules approximate ASD-STE100 (Simplified Technical English) and the
Google developer documentation style guide.
"""

import re
from dataclasses import dataclass, field

SUBJECT_SOFT_LIMIT = 50
BODY_LINE_LIMIT = 72
SENTENCE_WORD_LIMIT = 25

COMMENT_CHAR = "#"
SCISSORS = "------------------------ >8 ------------------------"

# Auto-generated subject prefixes that are exempt from subject rules.
EXEMPT_SUBJECT_PREFIXES = ("fixup!", "squash!", "amend!", "Merge ", "Revert ")

# Common non-imperative first words mapped to their imperative form.
# An explicit list keeps false positives low (no guessing from -ed/-ing/-s
# suffixes, which would flag words like "Speed", "Bring", or "Focus").
NON_IMPERATIVE = {
    "added": "add", "adds": "add", "adding": "add",
    "allowed": "allow", "allows": "allow", "allowing": "allow",
    "bumped": "bump", "bumps": "bump", "bumping": "bump",
    "changed": "change", "changes": "change", "changing": "change",
    "cleaned": "clean", "cleans": "clean", "cleaning": "clean",
    "corrected": "correct", "corrects": "correct", "correcting": "correct",
    "created": "create", "creates": "create", "creating": "create",
    "deleted": "delete", "deletes": "delete", "deleting": "delete",
    "documented": "document", "documents": "document", "documenting": "document",
    "fixed": "fix", "fixes": "fix", "fixing": "fix",
    "implemented": "implement", "implements": "implement", "implementing": "implement",
    "improved": "improve", "improves": "improve", "improving": "improve",
    "made": "make", "makes": "make", "making": "make",
    "merged": "merge", "merges": "merge", "merging": "merge",
    "moved": "move", "moves": "move", "moving": "move",
    "refactored": "refactor", "refactors": "refactor", "refactoring": "refactor",
    "released": "release", "releases": "release", "releasing": "release",
    "removed": "remove", "removes": "remove", "removing": "remove",
    "renamed": "rename", "renames": "rename", "renaming": "rename",
    "replaced": "replace", "replaces": "replace", "replacing": "replace",
    "reverted": "revert", "reverts": "revert", "reverting": "revert",
    "updated": "update", "updates": "update", "updating": "update",
    "upgraded": "upgrade", "upgrades": "upgrade", "upgrading": "upgrade",
    "used": "use", "uses": "use", "using": "use",
}

# Filler words and phrases that add no information (Google style).
FILLER_PHRASES = (
    "simply", "just", "basically", "actually", "really", "very", "quite",
    "obviously", "clearly", "easily", "of course", "note that", "please note",
    "it should be noted",
)

# Wordy or unapproved terms mapped to plain alternatives (STE approximation).
SUBSTITUTIONS = {
    "utilize": "use", "utilizes": "use", "utilized": "use",
    "leverage": "use", "leverages": "use", "leveraged": "use",
    "facilitate": "help", "facilitates": "help",
    "commence": "start", "commences": "start",
    "terminate": "stop", "terminates": "stop",
    "demonstrate": "show", "demonstrates": "show",
    "approximately": "about",
    "additionally": "also",
    "numerous": "many",
    "sufficient": "enough",
    "modification": "change", "modifications": "changes",
    "in order to": "to",
    "prior to": "before",
    "subsequent to": "after",
    "is able to": "can",
    "attempt to": "try to",
}

_URL_RE = re.compile(r"https?://\S+")
_TRAILER_RE = re.compile(r"^[A-Za-z][A-Za-z-]*:\s+\S")


@dataclass
class Violation:
    line: int  # 1-based line number
    rule: str
    severity: str  # "error" or "warning"
    message: str

    def as_dict(self) -> dict:
        return {
            "line": self.line,
            "rule": self.rule,
            "severity": self.severity,
            "message": self.message,
        }


@dataclass
class CheckResult:
    violations: list[Violation] = field(default_factory=list)

    @property
    def errors(self) -> list[Violation]:
        return [v for v in self.violations if v.severity == "error"]

    @property
    def warnings(self) -> list[Violation]:
        return [v for v in self.violations if v.severity == "warning"]

    def ok(self, strict: bool = False) -> bool:
        if strict:
            return not self.violations
        return not self.errors


def _strip_scissors(lines: list[str]) -> list[str]:
    """Drop everything from the scissors line onward (git verbose diffs)."""
    for i, line in enumerate(lines):
        if SCISSORS in line:
            return lines[:i]
    return lines


def _is_comment(line: str) -> bool:
    return line.startswith(COMMENT_CHAR)


def _is_code(line: str) -> bool:
    return line.startswith("    ") or line.startswith("\t")


def check_message(text: str) -> CheckResult:
    """Check a full commit message. Returns a CheckResult."""
    result = CheckResult()
    lines = _strip_scissors(text.split("\n"))

    # Content lines: (1-based line number, text), comments removed.
    content = [(i + 1, line) for i, line in enumerate(lines) if not _is_comment(line)]
    nonblank = [(n, line) for n, line in content if line.strip()]

    if not nonblank:
        result.violations.append(Violation(1, "empty-message", "error", "Commit message is empty"))
        return result

    subject_no, subject = nonblank[0]
    _check_subject(subject, subject_no, result)

    # The line right after the subject must be blank if a body follows.
    after = [(n, line) for n, line in content if n > subject_no]
    if after and after[0][1].strip():
        result.violations.append(Violation(
            after[0][0], "blank-line-after-subject", "error",
            "Separate the subject from the body with a blank line",
        ))

    body = [(n, line) for n, line in after]
    _check_body_lines(body, result)
    _check_prose(body, result)

    result.violations.sort(key=lambda v: (v.line, v.rule))
    return result


def _check_subject(subject: str, line_no: int, result: CheckResult) -> None:
    if subject.startswith(EXEMPT_SUBJECT_PREFIXES):
        return

    if len(subject) > SUBJECT_SOFT_LIMIT:
        result.violations.append(Violation(
            line_no, "subject-length", "error",
            f"Subject is {len(subject)} characters (limit {SUBJECT_SOFT_LIMIT})",
        ))

    if subject.rstrip().endswith("."):
        result.violations.append(Violation(
            line_no, "subject-period", "error",
            "Do not end the subject with a period",
        ))

    first_alpha = next((c for c in subject if c.isalpha()), "")
    if first_alpha and first_alpha.islower():
        result.violations.append(Violation(
            line_no, "subject-capitalization", "error",
            "Capitalize the subject line",
        ))

    first_word = re.split(r"[\s:]", subject.strip(), maxsplit=1)[0].lower()
    if first_word in NON_IMPERATIVE:
        result.violations.append(Violation(
            line_no, "subject-imperative", "error",
            f'Use the imperative mood: "{NON_IMPERATIVE[first_word].capitalize()}", '
            f'not "{first_word.capitalize()}"',
        ))


def _check_body_lines(body: list[tuple[int, str]], result: CheckResult) -> None:
    for n, line in body:
        if len(line) <= BODY_LINE_LIMIT:
            continue
        if _URL_RE.search(line) or _is_code(line) or _TRAILER_RE.match(line):
            continue
        result.violations.append(Violation(
            n, "body-line-length", "error",
            f"Body line is {len(line)} characters (limit {BODY_LINE_LIMIT})",
        ))


def _prose_paragraphs(body: list[tuple[int, str]]) -> list[tuple[int, str]]:
    """Group body lines into paragraphs of prose: (start line, joined text).

    Skips code blocks and trailers so prose rules only apply to sentences.
    """
    paragraphs: list[tuple[int, str]] = []
    start, parts = None, []
    for n, line in body:
        if not line.strip() or _is_code(line) or _TRAILER_RE.match(line):
            if parts:
                paragraphs.append((start, " ".join(parts)))
                start, parts = None, []
            continue
        if start is None:
            start = n
        parts.append(line.strip())
    if parts:
        paragraphs.append((start, " ".join(parts)))
    return paragraphs


def _check_prose(body: list[tuple[int, str]], result: CheckResult) -> None:
    for start, text in _prose_paragraphs(body):
        lowered = text.lower()

        for phrase in FILLER_PHRASES:
            if re.search(rf"\b{re.escape(phrase)}\b", lowered):
                result.violations.append(Violation(
                    start, "filler-word", "warning",
                    f'Remove filler: "{phrase}"',
                ))

        for term, replacement in SUBSTITUTIONS.items():
            if re.search(rf"\b{re.escape(term)}\b", lowered):
                result.violations.append(Violation(
                    start, "word-substitution", "warning",
                    f'Replace "{term}" with "{replacement}"',
                ))

        for sentence in re.split(r"[.!?]+\s+", text):
            words = sentence.split()
            if len(words) > SENTENCE_WORD_LIMIT:
                result.violations.append(Violation(
                    start, "sentence-length", "warning",
                    f"Sentence has {len(words)} words (limit {SENTENCE_WORD_LIMIT}); split it",
                ))
