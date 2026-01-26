from __future__ import annotations
from datetime import datetime
from typing import Any, Dict, Optional
import app.constants.result_fields as R
import app.services.manage_process_results as pr
from app.services.manage_process_results import dedupe_and_merge_results


def make_entry(employer_name: Optional[str], result: Optional[str], applied_position: Optional[str], contact_person: Optional[str], received_datetime: Optional[datetime]) -> Dict[str, Any]:
    e: Dict[str, Any] = {
        R.EMPLOYER_NAME: employer_name,
        R.RESULT: result,
        R.APPLIED_POSITION: applied_position,
        R.CONTACT_PERSON: contact_person,
        R.POSTAL_ADDRESS: None,
    }
    if received_datetime is not None:
        e[R.RECEIVED_DATETIME] = received_datetime
    return e


def no_prompt(_: Optional[str]) -> None:
    return None


def test_case1_same_company_early_job_title_late_rejection_without_job_title(monkeypatch) -> None:
    monkeypatch.setattr(pr, "prompt_job_title", no_prompt)

    early = make_entry(
        "ABC GmbH",
        "Zwischenstand",
        "Backend Developer",
        None,
        datetime(2026, 1, 6, 9, 0, 0),
    )
    late = make_entry(
        "ABC GmbH",
        "Absage",
        None,
        None,
        datetime(2026, 1, 10, 12, 0, 0),
    )

    out = dedupe_and_merge_results([early, late])

    assert len(out) == 1
    row = out[0]
    assert row[R.RESULT] == "Absage"
    assert row[R.APPLIED_POSITION] == "Backend Developer"
    assert row[R.FIRST_CONTACT_DATE] == "06.01.2026"


def test_case2_same_company_both_have_job_titles_older_wins(monkeypatch) -> None:
    monkeypatch.setattr(pr, "prompt_job_title", no_prompt)

    early = make_entry(
        "ABC GmbH",
        "Zwischenstand",
        "Backend Developer",
        None,
        datetime(2026, 1, 6, 9, 0, 0),
    )
    late = make_entry(
        "ABC GmbH",
        "Absage",
        "Software Engineer",
        None,
        datetime(2026, 1, 10, 12, 0, 0),
    )

    out = dedupe_and_merge_results([early, late])

    assert len(out) == 1
    assert out[0][R.APPLIED_POSITION] == "Backend Developer"


def test_case3_contact_person_preserved(monkeypatch) -> None:
    monkeypatch.setattr(pr, "prompt_job_title", no_prompt)

    early = make_entry(
        "ABC GmbH",
        "Zwischenstand",
        "Backend Developer",
        "Max Mustermann",
        datetime(2026, 1, 6, 9, 0, 0),
    )
    late = make_entry(
        "ABC GmbH",
        "Absage",
        None,
        None,
        datetime(2026, 1, 10, 12, 0, 0),
    )

    out = dedupe_and_merge_results([early, late])

    assert len(out) == 1
    assert out[0][R.CONTACT_PERSON] == "Max Mustermann"


def test_case4_one_missing_datetime_other_present(monkeypatch) -> None:
    monkeypatch.setattr(pr, "prompt_job_title", no_prompt)

    a = make_entry(
        "ABC GmbH",
        "Zwischenstand",
        "Backend Developer",
        None,
        None,
    )
    b = make_entry(
        "ABC GmbH",
        "Absage",
        None,
        None,
        datetime(2026, 1, 10, 12, 0, 0),
    )

    out = dedupe_and_merge_results([a, b])

    assert len(out) == 1
    assert out[0][R.FIRST_CONTACT_DATE] == "10.01.2026"


def test_case5_empty_list() -> None:
    assert dedupe_and_merge_results([]) == []