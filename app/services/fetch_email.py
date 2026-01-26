from __future__ import annotations
import email
import os
from datetime import date, datetime
from email.header import decode_header
from typing import List, Optional
import html2text
from imapclient import IMAPClient
from app.models.models import MailProviderConfig, MailItem


def load_login_config() -> MailProviderConfig:
    host = os.getenv("IMAP_HOST")
    user = os.getenv("IMAP_USER")
    password = os.getenv("IMAP_PASS")

    missing = []
    if not host:
        missing.append("IMAP_HOST")
    if not user:
        missing.append("IMAP_USER")
    if not password:
        missing.append("IMAP_PASS")
    if missing:
        raise RuntimeError("Missing env vars: " + ", ".join(missing))

    return MailProviderConfig(host=host, user=user, password=password)

def decode_header_value(raw: Optional[str]) -> str:
    """
    Decodes an email header value into a readable string.

    Why:
    Email headers can be encoded in parts (RFC 2047), e.g. UTF-8 base64.

    Behavior:
    -If raw is None/empty -> ""
    -Uses email.header.decode_header()
    -Decodes bytes parts using specified encoding, fallback "utf-8"
    -Joins parts into one final string
    -Uses errors="replace" so it never crashes on broken encodings

    Example:
    raw: "=?UTF-8?B?U3RlbGxlbmFuZ2ViaW90?="
    -> "Stellenangebot"
    """
    if not raw:
        return ""

    out: list[str] = []
    for part, enc in decode_header(raw):
        if isinstance(part, bytes):
            encoding = enc or "utf-8"
            out.append(part.decode(encoding, errors="replace"))
        else:
            out.append(part)

    return "".join(out)

def decode_part_bytes(part: email.message.Message) -> str:
    """
    Decodes a MIME part payload (bytes) into text.

    Behavior:
    -Reads the payload as bytes with get_payload(decode=True)
    -Tries the part's declared charset first
    -If that fails or is missing, tries common fallbacks:
    utf-8, windows-1252, iso-8859-1
    -Always returns a string

    Example flow:
    1)MIME part charset is "utf-8" -> decode succeeds
    2)MIME part charset missing -> tries fallbacks
    3)Broken encoding -> returns best-effort text with replacements
    """
    raw = part.get_payload(decode=True) or b""

    charset = part.get_content_charset() or part.get_charset()

    if charset:
        try:
            return raw.decode(str(charset), errors="replace")
        except (LookupError, UnicodeDecodeError):
            pass

    for cs in ("utf-8", "windows-1252", "iso-8859-1"):
        try:
            return raw.decode(cs, errors="replace")
        except UnicodeDecodeError:
            continue

    return raw.decode("utf-8", errors="replace")

def html_to_clean_text(html: str) -> str:
    """
    Converts HTML email content to clean plain text.

    Behavior:
    -Removes links and images
    -Keeps emphasis
    -Keeps original line width (no forced wrapping)
    -Strips empty lines

    Example:
    "<p>Hello</p><p>World</p>"
    -> "Hello\\nWorld"
    """
    converter = html2text.HTML2Text()
    converter.ignore_links = True
    converter.ignore_images = True
    converter.ignore_emphasis = False
    converter.body_width = 0

    text = converter.handle(html)
    raw_lines = text.splitlines()

    lines = []

    for line in raw_lines:
        cleaned = line.strip()
        if cleaned:
            lines.append(cleaned)

    return "\n".join(lines)

def extract_body(msg: email.message.Message) -> str:
    """
    Extracts the best email body as plain text.

    Rules:
    -If the email is NOT multipart:
      -If content-type is text/html -> convert to clean text
      -Else -> use plain decoded text
    -If multipart:
      -Walk through parts
      -Skip multipart containers
      -Skip attachments
      -Prefer the first "text/plain"
      -Otherwise, use the first "text/html" and convert it
    -If nothing usable: return "(no content)"

    Example flow (multipart):
    1)Email has text/plain part -> return it
    2)No text/plain, but text/html exists -> convert HTML and return it
    3)Only attachments -> "(no content)"
    """
    if not msg.is_multipart():
        content_type = msg.get_content_type()
        content = decode_part_bytes(msg)

        if content_type == "text/html":
            text = html_to_clean_text(content)
        else:
            text = content.strip()

        if text:
            return text
        else:
            return "(no content)"

    html_part: Optional[str] = None

    for part in msg.walk():
        if part.get_content_maintype() == "multipart":
            continue

        disp = (part.get("Content-Disposition") or "").lower()
        if "attachment" in disp:
            continue

        ctype = part.get_content_type()

        if ctype == "text/plain":
            text = decode_part_bytes(part).strip()
            if text:
                return text
            continue

        if ctype == "text/html" and html_part is None:
            html_part = decode_part_bytes(part)

    if html_part:
        cleaned = html_to_clean_text(html_part).strip()
        if cleaned:
            return cleaned
        return "(no content)"

    return "(no content)"

def build_or_subject_query(terms: list[str]) -> list[str]:
    """
    Builds an IMAPClient search expression that ORs multiple SUBJECT terms.

    Why:
    IMAP search syntax is prefix-style. To search multiple subjects you need OR chains.

    Behavior:
    -[] -> []
    -["a"] -> ["SUBJECT", "a"]
    -["a", "b"] -> ["OR", "SUBJECT", "a", "SUBJECT", "b"]

    Example:
    terms = ["bewerbung", "application"]
    -> ["OR", "SUBJECT", "bewerbung", "SUBJECT", "application"]
    """
    if not terms:
        return []

    if len(terms) == 1:
        return ["SUBJECT", terms[0]]

    expr: list[str] = ["SUBJECT", terms[-1]]
    for term in reversed(terms[:-1]):
        expr = ["OR", "SUBJECT", term] + expr

    return expr

def fetch_mails(cfg: MailProviderConfig, search_terms: List[str], since_date: date) -> List[MailItem]:
    """
    Fetches emails from IMAP based on SUBJECT keywords and a SINCE date.

    Inputs:
    -cfg: IMAP connection config
    -search_terms: list of subject keywords (OR logic)
    -since_date: only emails since this date (IMAP SINCE)

    Output:
    -List[MailItem] with decoded headers and extracted body

    Flow:
    1)build_or_subject_query(search_terms) builds the OR filter for subject
    2)search_query = ["SINCE", since_date, ...subject_filter]
    3)Connect to IMAP using IMAPClient(cfg.host, ssl=cfg.ssl)
    4)Login and select folder (default INBOX)
    5)Search message ids with client.search(search_query)
    6)Fetch full RFC822 and INTERNALDATE for each message
    7)Parse each message:
       -decode sender/subject/date headers
       -extract body (plain text or html-cleaned)
       -read INTERNALDATE as received_datetime
    8)Return list of MailItem objects

    Example:
    cfg = load_login_config()
    mails = fetch_mails(cfg, ["bewerbung", "application"], date(2026, 1, 5))

    Result items:
    -mails[0].subject -> "Ihre Bewerbung..."
    -mails[0].body -> extracted plain text
    -mails[0].received_datetime -> datetime(...) or None
    """
    subject_filter = build_or_subject_query(search_terms)
    search_query: list[object] = ["SINCE", since_date, *subject_filter]

    with IMAPClient(cfg.host, ssl=cfg.ssl) as client:
        client.login(cfg.user, cfg.password)
        client.select_folder(cfg.folder)

        msg_ids = client.search(search_query)
        if not msg_ids:
            return []

        messages = client.fetch(msg_ids, ["RFC822", "INTERNALDATE"])

        result: List[MailItem] = []

        for msg_id, data in messages.items():
            raw = data.get(b"RFC822")
            if not raw:
                continue

            msg = email.message_from_bytes(raw)

            sender = decode_header_value(msg.get("From"))
            subject = decode_header_value(msg.get("Subject"))
            msg_date = decode_header_value(msg.get("Date"))
            body = extract_body(msg)

            received_datetime = data.get(b"INTERNALDATE")
            if received_datetime is not None and not isinstance(received_datetime, datetime):
                received_datetime = None

            result.append(
                MailItem(
                    msg_id=int(msg_id),
                    sender=sender,
                    subject=subject,
                    msg_date=msg_date,
                    body=body,
                    received_datetime=received_datetime,
                )
            )

        return result