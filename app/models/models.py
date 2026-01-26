from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class ManualPostalAddress:
    """Represents a manually stored postal address."""
    street: str
    postal_code: str
    city: str

    def to_one_line(self) -> str:
        return self.street + ", " + self.postal_code + " " + self.city


@dataclass
class MailProviderConfig:
    """
    Holds IMAP connection settings.

    Fields:
    -host: IMAP server hostname (e.g. "imap.gmail.com")
    -user: IMAP username/login (often the email address)
    -password: IMAP password or app password
    -folder: mailbox folder to read from (default "INBOX")
    -ssl: use SSL (default True)

    Example:
    cfg = MailProviderConfig(host="imap.example.com", user="me@example.com", password="secret")
    """
    host: str
    user: str
    password: str
    folder: str = "INBOX"
    ssl: bool = True

@dataclass
class MailItem:
    """
    Represents one fetched email in a simplified structure.

    Fields:
    -msg_id: IMAP message id
    -sender: decoded "From" header
    -subject: decoded "Subject" header
    -msg_date: decoded "Date" header
    -body: extracted email body as plain text (HTML cleaned if needed)
    -received_datetime: server/internal receive datetime (if available)

    Example:
    item.sender -> "Max Mustermann <max@example.com>"
    item.subject -> "Application for Backend Developer"
    item.body -> "...email content..."
    """
    msg_id: int
    sender: str
    subject: str
    msg_date: str
    body: str
    received_datetime: Optional[datetime]