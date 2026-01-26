import json
import os
from datetime import datetime
from typing import Any, Dict, Optional
from openai import OpenAI
import app.constants.result_fields as R

base_url = os.getenv("OLLAMA_BASE_URL")
api_key = os.getenv("OLLAMA_API_KEY")
model = os.getenv("OLLAMA_MODEL")

if not base_url or not api_key or not model:
    raise RuntimeError("Missing Ollama env vars")

client = OpenAI(base_url=base_url, api_key=api_key)


SYSTEM_PROMPT = """
You extract structured data from job application emails.

Rules:
-Extract only information that is explicitly stated in the text. Do not infer or invent anything.
-If a value is not clearly identifiable, return null.

gespraechspartner (contact person):
-If a specific person is explicitly named in the text (usually after the closing phrase), use exactly that name.
-The “From:” line may ONLY be used if it clearly contains a personal name (first + last name; no roles/teams/emails).
-If “From:” is only a team/department/shared mailbox: return null.
-If multiple persons are mentioned directly after the closing phrase, or if the person is unclear, return null.

beworben_als (applied position):
-Job title without additions such as (m/f/d), etc.

anschrift (address):
-Return ONLY a postal address in ONE LINE: "<street> <house_number>, <postal_code> <city>"
-Do NOT include company name, campus/location names, departments, Postfach/PO box lines, country, or any extra lines.
-If you cannot extract street+postal_code+city clearly: return null.

ergebnis (result):
-Absage = clear rejection
-Einladung = ONLY if explicit invitation to interview/meeting/call
-Zwischenstand = all other cases
""".strip()

SCHEMA: Dict[str, Any] = {
    "name": "bewerbung_extraction",
    "strict": True,
    "schema": {
        "type": "object",
        "properties": {
            "arbeitgeber_name": {"type": ["string", "null"]},
            "gespraechspartner": {"type": ["string", "null"]},
            "beworben_als": {"type": ["string", "null"]},
            "anschrift": {"type": ["string", "null"]},
            "ergebnis": {"type": "string", "enum": ["Absage", "Einladung", "Zwischenstand"]},
        },
        "required": ["arbeitgeber_name", "beworben_als", "ergebnis"],
        "additionalProperties": False,
    },
}

def ask_ollama(email_text: str) -> str:
    """
    Send email text to the Ollama/OpenAI endpoint and return the raw JSON response.
    Raises RuntimeError if env vars are missing or the model returns no content.
    """
    resp = client.chat.completions.create(
        model=model,
        temperature=0.0,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": email_text},
        ],
        response_format={"type": "json_schema", "json_schema": SCHEMA},
    )

    content = resp.choices[0].message.content
    if not isinstance(content, str) or not content.strip():
        raise RuntimeError("Model returned no usable content")

    return content

def parse_llm_json(raw: Optional[str]) -> Dict[str, Any]:
    """
    Parses the raw JSON string from the model into a Python dict and ensures keys exist.

    Inputs:
    -raw: JSON string returned by ask_ollama()

    Output:
    -parsed dict

    Flow:
    1)Validate raw is not empty
    2)json.loads(raw) -> dict
    3)Ensure keys that might be missing exist:
       -"gespraechspartner" -> None if missing
       -"anschrift" -> None if missing

    Example:
    raw = '{"arbeitgeber_name":"ABC GmbH","beworben_als":"Dev","ergebnis":"Zwischenstand"}'
    -> {
         "arbeitgeber_name": "ABC GmbH",
         "beworben_als": "Dev",
         "ergebnis": "Zwischenstand",
         "gespraechspartner": None,
         "anschrift": None
       }
    """
    if raw is None or not raw.strip():
        raise ValueError("Model returned empty output")

    parsed = json.loads(raw.strip())
    if not isinstance(parsed, dict):
        raise ValueError("Parsed JSON is not an object")

    for key in SCHEMA["schema"]["properties"]:
        parsed.setdefault(key, None)

    return parsed

def extract_fields_from_email(email_text: str, subject_for_log: str, received_datetime: Optional[datetime] = None) -> Dict[str, Any]:
    """
    High-level wrapper: calls the LLM, parses the output, maps keys,
    and attaches received_datetime directly.

    Output (success):
    {
      "employer_name": ...,
      "contact_person": ...,
      "applied_position": ...,
      "postal_address": ...,
      "result": ...,
      "received_datetime": ...,
      "status": "ok"
    }

    Output (failure):
    Same keys, all None except status="llm_failed"
    """

    try:
        raw = ask_ollama(email_text)
        parsed = parse_llm_json(raw)

        return {
            R.EMPLOYER_NAME: parsed.get("arbeitgeber_name"),
            R.CONTACT_PERSON: parsed.get("gespraechspartner"),
            R.APPLIED_POSITION: parsed.get("beworben_als"),
            R.POSTAL_ADDRESS: parsed.get("anschrift"),
            R.RESULT: parsed.get("ergebnis"),
            R.RECEIVED_DATETIME: received_datetime,
            "status": "ok",
        }

    except Exception as e:
        print("LLM failed:", subject_for_log, "-", e)

        return {
            R.EMPLOYER_NAME: None,
            R.CONTACT_PERSON: None,
            R.APPLIED_POSITION: None,
            R.POSTAL_ADDRESS: None,
            R.RESULT: None,
            R.RECEIVED_DATETIME: received_datetime,
            "status": "llm_failed",
        }

def format_email(sender: str, subject: str, msg_date: str, body: str) -> str:
    """
    Builds the exact text that is sent to the LLM.

    Inputs:
    -sender: decoded From header
    -subject: decoded Subject header
    -msg_date: decoded Date header
    -body: extracted plain text email body

    Output:
    -One string containing:
      From: ...
      Subject: ...
      Date: ...

      <body>

    Example:
    email_text = format_email(
        sender="ABC HR <hr@abc.com>",
        subject="Your application",
        msg_date="Mon, 6 Jan 2026 09:00:00 +0100",
        body="Hello...\\nRegards..."
    )

    email_text becomes:
    "From: ABC HR <hr@abc.com>\\n"
    "Subject: Your application\\n"
    "Date: Mon, 6 Jan 2026 09:00:00 +0100\\n\\n"
    "Hello...\\nRegards..."
    """
    return (
        "From: " + sender + "\n"
        "Subject: " + subject + "\n"
        "Date: " + msg_date + "\n\n"
        + body
    )