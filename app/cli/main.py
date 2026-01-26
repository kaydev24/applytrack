import os
from typing import Any, Dict, List
from datetime import date

from dotenv import load_dotenv
load_dotenv()

from app.services.address_resolver import load_address_resolver
from app.services.enrich_addresses import enrich_missing_addresses
from app.services.extract_ai import extract_fields_from_email, format_email
from app.services.fetch_email import fetch_mails, load_login_config
from app.services.export_to_table import write_results_to_excels
from app.services.manage_process_results import dedupe_and_merge_results

search_terms = ["bewerbung", "application"]
since_date = date(2026, 1, 5)
agreed_count = None
include_job_title_in_key = False

customer_number = os.getenv("KUNDENNUMMER")
first_name = os.getenv("VORNAME")
last_name = os.getenv("NACHNAME")

def main() -> None:
    """
    Main CLI entry point.

    Workflow:
    -Load IMAP config and fetch emails
    -Extract structured fields via LLM
    -Deduplicate and merge results
    -Resolve missing postal addresses
    -Export everything into Excel template files
    """
    imap_cfg = load_login_config()
    mails = fetch_mails(imap_cfg, search_terms, since_date)

    results: List[Dict[str, Any]] = []

    for mail in mails:
        email_text = format_email(mail.sender, mail.subject, mail.msg_date, mail.body)
        parsed = extract_fields_from_email(email_text, mail.subject, mail.received_datetime)
        results.append(parsed)

    results = dedupe_and_merge_results(results, include_role_in_key=include_job_title_in_key)

    resolver = None
    try:
        resolver = load_address_resolver()
        results = enrich_missing_addresses(results, resolver, interactive=True)
    finally:
        if resolver is not None:
            resolver.close()

    template_path = os.getenv("TABLE_XLSX", "../../table/table.xlsx")
    write_results_to_excels(
        template_path,
        results,
        since_date,
        agreed_count,
        customer_number,
        first_name,
        last_name,
    )

if __name__ == "__main__":
    main()