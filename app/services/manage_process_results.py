from __future__ import annotations
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
import app.constants.result_fields as R

def clean_str(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def company_key(value: Any, entry_id: int) -> str:
    """Normalize employer name for grouping, fall back to a stable unknown key."""
    text = clean_str(value)
    if text is None:
        return R.UNKNOWN_COMPANY_PREFIX + str(entry_id)
    parts = text.split()
    return " ".join(parts).lower()


def role_key(value: Any) -> Optional[str]:
    text = clean_str(value)
    if text is None:
        return None
    parts = text.split()
    return " ".join(parts).lower()


def sort_key_received_datetime(entry: Dict[str, Any]) -> datetime:
    dt = entry.get(R.RECEIVED_DATETIME)
    if not isinstance(dt, datetime):
        dt = datetime.min
    return dt


def first_non_null(entries: List[Dict[str, Any]], field: str) -> Optional[str]:
    for entry in entries:
        value = clean_str(entry.get(field))
        if value is not None:
            return value
    return None


def prompt_job_title(company_name: Optional[str]) -> Optional[str]:
    print()
    print("Job title not found for: " + (company_name or "(unknown)"))
    job_title = input("Job title (leave empty to skip): ").strip()
    if job_title:
        return job_title
    return None


def group_key(entry: Dict[str, Any], include_role: bool, entry_id: int) -> Tuple[str, Optional[str]]:
    """Return the grouping key (company[, role]) for one entry."""
    company = company_key(entry.get(R.EMPLOYER_NAME), entry_id)
    role = role_key(entry.get(R.APPLIED_POSITION))
    if include_role:
        return company, role
    return company, None


def earliest_valid_received_datetime(entries_sorted_newest_first: List[Dict[str, Any]]) -> Optional[datetime]:
    """Return the earliest received_datetime in the group, ignoring datetime.min."""
    for entry in reversed(entries_sorted_newest_first):
        dt = sort_key_received_datetime(entry)
        if dt != datetime.min:
            return dt
    return None


def dedupe_and_merge_results(results: List[Dict[str, Any]], include_role_in_key: bool = False) -> List[Dict[str, Any]]:
    """
    Deduplicate and merge result entries that belong to the same employer.

    Grouping:
    -By normalized employer name
    -If include_role_in_key=True, also by normalized applied position

    Merge strategy per group:
    -employer_name/contact_person/applied_position/postal_address:
      take the first non-empty value from oldest to newest
      (fallback: newest value)
    -result: taken from the newest entry
    -first_contact_date: earliest valid received_datetime formatted as DATE_FORMAT

    Notes:
    -Entries with missing/invalid received_datetime are treated as datetime.min.
    -May prompt the user for a job title if it is missing in all entries.

    Returns a new list of merged dicts sorted by first_contact_date (oldest first).
    """
    if not results:
        return []

    for result in results:
        value = result.get(R.RECEIVED_DATETIME)
        if not isinstance(value, datetime):
            result[R.RECEIVED_DATETIME] = datetime.min

    groups: Dict[Tuple[str, Optional[str]], List[Dict[str, Any]]] = {}
    for entry_id, result in enumerate(results):
        key = group_key(result, include_role_in_key, entry_id)
        groups.setdefault(key, []).append(result)

    merged: List[Dict[str, Any]] = []

    for key, entries in groups.items():
        newest_first = sorted(entries, key=sort_key_received_datetime, reverse=True)
        oldest_first = list(reversed(newest_first))

        latest = newest_first[0]
        earliest_dt = earliest_valid_received_datetime(newest_first)

        output: Dict[str, Any] = {}

        employer_name = first_non_null(oldest_first, R.EMPLOYER_NAME)
        if employer_name is None:
            employer_name = clean_str(latest.get(R.EMPLOYER_NAME))
        output[R.EMPLOYER_NAME] = employer_name

        output[R.RESULT] = latest.get(R.RESULT)

        contact_person = first_non_null(oldest_first, R.CONTACT_PERSON)
        if contact_person is None:
            contact_person = clean_str(latest.get(R.CONTACT_PERSON))
        output[R.CONTACT_PERSON] = contact_person

        job_title = first_non_null(oldest_first, R.APPLIED_POSITION)
        if job_title is None:
            job_title = clean_str(latest.get(R.APPLIED_POSITION))
        if job_title is None:
            job_title = prompt_job_title(clean_str(output.get(R.EMPLOYER_NAME)))
        output[R.APPLIED_POSITION] = job_title

        address = first_non_null(oldest_first, R.POSTAL_ADDRESS)
        if address is None:
            address = clean_str(latest.get(R.POSTAL_ADDRESS))
        output[R.POSTAL_ADDRESS] = address

        if earliest_dt is not None:
            output[R.FIRST_CONTACT_DATE] = earliest_dt.strftime(R.DATE_FORMAT)
        else:
            output[R.FIRST_CONTACT_DATE] = None

        merged.append(output)

    def sort_key(entry: Dict[str, Any]) -> Tuple[int, datetime]:
        value = clean_str(entry.get(R.FIRST_CONTACT_DATE))
        if value is not None:
            try:
                return 0, datetime.strptime(value, R.DATE_FORMAT)
            except ValueError:
                pass
        return (1, datetime.min)

    merged.sort(key=sort_key)
    return merged