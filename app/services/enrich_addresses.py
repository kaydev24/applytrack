from __future__ import annotations
from typing import Any, Dict, List, Optional
import app.constants.result_fields as R


def enrich_missing_addresses(results: List[Dict[str, Any]], resolver: Any, interactive: bool = True) -> List[Dict[str, Any]]:
    """
    Fill missing postal addresses in merged result entries.

    For each entry:
    -Skip if employer_name is missing/empty
    -Skip if postal_address is already set
    -Try resolver.find_manual(company_name)
    -Fallback to resolver.find_openregister(company_name)
    -If still missing and interactive=True, prompt the user and store it

    Updates entries in-place and returns the same list.
    """
    for entry in results:
        company = entry.get(R.EMPLOYER_NAME)
        if not isinstance(company, str) or not company.strip():
            continue

        company_name = company.strip()

        addr = entry.get(R.POSTAL_ADDRESS)
        if isinstance(addr, str) and addr.strip():
            continue

        resolved: Optional[str] = None

        manual = resolver.find_manual(company_name)
        if manual is not None:
            resolved = manual.to_one_line()

        if resolved is None:
            reg = resolver.find_openregister(company_name)
            if isinstance(reg, str) and reg.strip():
                resolved = reg.strip()

        if resolved is None and interactive:
            prompted = resolver.prompt_and_save(company_name)
            if isinstance(prompted, str) and prompted.strip():
                resolved = prompted.strip()

        entry[R.POSTAL_ADDRESS] = resolved

    return results