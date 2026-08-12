"""Tests for commit message checks."""

from guppi_committer.checks import check_message


def _rules(result):
    return {v.rule for v in result.violations}


# --- Subject rules ---


def test_good_message_passes():
    msg = (
        "Add retry logic to the artifact fetcher\n"
        "\n"
        "Transient network failures caused nightly builds to fail. The\n"
        "fetcher now retries three times before it reports an error.\n"
        "\n"
        "Fixes: #142\n"
    )
    result = check_message(msg)
    assert result.violations == []
    assert result.ok(strict=True)


def test_subject_only_passes():
    result = check_message("Add retry logic to fetcher\n")
    assert result.violations == []


def test_empty_message():
    result = check_message("\n\n")
    assert _rules(result) == {"empty-message"}


def test_subject_too_long():
    result = check_message("Add " + "x" * 60 + "\n")
    assert "subject-length" in _rules(result)


def test_subject_lowercase():
    result = check_message("add retry logic\n")
    assert "subject-capitalization" in _rules(result)


def test_subject_trailing_period():
    result = check_message("Add retry logic.\n")
    assert "subject-period" in _rules(result)


def test_subject_past_tense():
    result = check_message("Added retry logic\n")
    violations = [v for v in result.violations if v.rule == "subject-imperative"]
    assert len(violations) == 1
    assert '"Add"' in violations[0].message


def test_subject_third_person():
    result = check_message("Fixes race condition in scheduler\n")
    assert "subject-imperative" in _rules(result)


def test_imperative_words_not_flagged_by_suffix():
    for subject in ("Speed up the test suite\n", "Bring back the old API\n", "Focus search on titles\n"):
        assert "subject-imperative" not in _rules(check_message(subject))


def test_exempt_subjects():
    for subject in (
        "Merge branch 'main' into feature/very-long-branch-name-here\n",
        'Revert "Add retry logic to the artifact fetcher module"\n',
        "fixup! added stuff.\n",
    ):
        result = check_message(subject)
        assert result.violations == [], subject


# --- Structure and body rules ---


def test_missing_blank_line():
    result = check_message("Add retry logic\nBody starts immediately.\n")
    assert "blank-line-after-subject" in _rules(result)


def test_body_line_too_long():
    result = check_message("Add retry logic\n\n" + "word " * 20 + "\n")
    assert "body-line-length" in _rules(result)


def test_long_url_line_exempt():
    msg = "Add retry logic\n\nSee https://example.com/" + "a" * 80 + "\n"
    assert "body-line-length" not in _rules(check_message(msg))


def test_long_trailer_exempt():
    msg = "Add retry logic\n\nCo-authored-by: Someone With A Very Long Name <someone.long@example-company-domain.com>\n"
    assert "body-line-length" not in _rules(check_message(msg))


def test_long_code_line_exempt():
    msg = "Add retry logic\n\nExample:\n\n    " + "x = 1; " * 20 + "\n"
    assert "body-line-length" not in _rules(check_message(msg))


def test_comments_ignored():
    msg = "# this comment line is very long " + "x" * 60 + "\nAdd retry logic\n"
    assert check_message(msg).violations == []


def test_scissors_content_ignored():
    msg = (
        "Add retry logic\n"
        "# ------------------------ >8 ------------------------\n"
        "diff --git a/f b/f\n"
        "+" + "x" * 100 + "\n"
    )
    assert check_message(msg).violations == []


# --- Prose rules ---


def test_filler_word_warning():
    result = check_message("Add retry logic\n\nThis simply retries the fetch.\n")
    violations = [v for v in result.violations if v.rule == "filler-word"]
    assert len(violations) == 1
    assert violations[0].severity == "warning"
    assert result.ok()
    assert not result.ok(strict=True)


def test_word_substitution_warning():
    result = check_message("Add retry logic\n\nUtilize the backoff helper prior to failing.\n")
    messages = [v.message for v in result.violations if v.rule == "word-substitution"]
    assert any("utilize" in m for m in messages)
    assert any("prior to" in m for m in messages)


def test_long_sentence_warning():
    sentence = "This sentence " + "goes on and on " * 8 + "without a break"
    result = check_message(f"Add retry logic\n\n{sentence}.\n")
    assert "sentence-length" in _rules(result)


def test_trailers_skip_prose_checks():
    msg = "Add retry logic\n\nSimply-Named-Trailer: utilize whatever prior to anything\n"
    result = check_message(msg)
    assert {"filler-word", "word-substitution"}.isdisjoint(_rules(result))
