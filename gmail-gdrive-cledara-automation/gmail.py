import base64
import os
import email.utils
from datetime import datetime, timedelta, timezone
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from config import VENDORS, GMAIL_LABEL, Vendor

SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]
CREDENTIALS_DIR = Path(".credentials")
CLIENT_SECRET = CREDENTIALS_DIR / "client_secret.json"
TOKEN_FILE = CREDENTIALS_DIR / "token.json"
LAST_RUN_FILE = CREDENTIALS_DIR / "last_run"


def authenticate():
    """Authenticate with Gmail API using OAuth2."""
    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CLIENT_SECRET.exists():
                raise FileNotFoundError(
                    f"Missing {CLIENT_SECRET}. Download it from Google Cloud Console."
                )
            flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRET), SCOPES)
            creds = flow.run_local_server(port=0)
        CREDENTIALS_DIR.mkdir(exist_ok=True)
        TOKEN_FILE.write_text(creds.to_json())
    return build("gmail", "v1", credentials=creds)


def _get_after_date() -> str:
    """Get the 'after:' date for Gmail query based on last run or 90-day default."""
    if LAST_RUN_FILE.exists():
        ts = LAST_RUN_FILE.read_text().strip()
        dt = datetime.fromisoformat(ts)
    else:
        dt = datetime.now(timezone.utc) - timedelta(days=90)
    return dt.strftime("%Y/%m/%d")


def _save_last_run():
    CREDENTIALS_DIR.mkdir(exist_ok=True)
    LAST_RUN_FILE.write_text(datetime.now(timezone.utc).isoformat())


def _build_vendor_query() -> str:
    """Build Gmail search query for all vendors."""
    from_clauses = []
    for v in VENDORS:
        clause = f"from:{v.email}"
        if v.subject_filter:
            clause = f"(from:{v.email} subject:{v.subject_filter})"
        from_clauses.append(clause)

    after = _get_after_date()
    vendors_part = " OR ".join(from_clauses)
    return f"({vendors_part}) has:attachment filename:pdf -label:{GMAIL_LABEL} after:{after}"


def _match_vendor(sender: str) -> Vendor | None:
    """Match an email sender to a known vendor."""
    sender_lower = sender.lower()
    for v in VENDORS:
        if v.email.lower() in sender_lower:
            return v
    return None


def _get_or_create_label(service) -> str:
    """Get or create the invoice-processed label, return its ID."""
    results = service.users().labels().list(userId="me").execute()
    for label in results.get("labels", []):
        if label["name"] == GMAIL_LABEL:
            return label["id"]
    label = service.users().labels().create(
        userId="me", body={"name": GMAIL_LABEL, "labelListVisibility": "labelShow", "messageListVisibility": "show"}
    ).execute()
    return label["id"]


def _extract_pdfs(payload) -> list[tuple[str, bytes]]:
    """Recursively walk MIME parts to find PDF attachments. Returns list of (filename, data_placeholder)."""
    pdfs = []
    parts = payload.get("parts", [])
    if not parts:
        parts = [payload]
    for part in parts:
        if part.get("parts"):
            pdfs.extend(_extract_pdfs(part))
        filename = part.get("filename", "")
        if filename.lower().endswith(".pdf") and part.get("body", {}).get("attachmentId"):
            pdfs.append((filename, part["body"]["attachmentId"]))
    return pdfs


def _parse_email_date(headers: list[dict]) -> str:
    """Extract and format date from email headers."""
    for h in headers:
        if h["name"].lower() == "date":
            parsed = email.utils.parsedate_to_datetime(h["value"])
            return parsed.strftime("%Y-%m-%d")
    return datetime.now().strftime("%Y-%m-%d")


def _save_pdf(service, msg_id: str, attachment_id: str, output_path: Path) -> bool:
    """Download and save a PDF attachment."""
    att = service.users().messages().attachments().get(
        userId="me", messageId=msg_id, id=attachment_id
    ).execute()
    data = base64.urlsafe_b64decode(att["data"])
    if len(data) < 100:  # Corrupt/empty check
        return False
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(data)
    return True


def _resolve_path(output_dir: Path, vendor_name: str, date_str: str, suffix: str = "") -> Path:
    """Build output path with collision handling."""
    vendor_dir = output_dir / vendor_name
    base_name = f"{date_str}-{vendor_name}-Invoice{suffix}.pdf"
    path = vendor_dir / base_name
    if not path.exists():
        return path
    counter = 2
    while True:
        base_name = f"{date_str}-{vendor_name}-Invoice{suffix}-{counter}.pdf"
        path = vendor_dir / base_name
        if not path.exists():
            return path
        counter += 1


def process_gmail(output_dir: Path, dry_run: bool = False) -> dict:
    """Main Gmail processing. Returns summary dict."""
    service = authenticate()
    label_id = _get_or_create_label(service)
    query = _build_vendor_query()

    results = {"processed": [], "skipped": [], "errors": [], "new_senders": []}

    # Search for matching emails
    response = service.users().messages().list(userId="me", q=query).execute()
    messages = response.get("messages", [])

    # Handle pagination
    while "nextPageToken" in response:
        response = service.users().messages().list(
            userId="me", q=query, pageToken=response["nextPageToken"]
        ).execute()
        messages.extend(response.get("messages", []))

    for msg_ref in messages:
        try:
            msg = service.users().messages().get(userId="me", id=msg_ref["id"], format="full").execute()
            headers = msg["payload"].get("headers", [])

            # Get sender
            sender = ""
            for h in headers:
                if h["name"].lower() == "from":
                    sender = h["value"]
                    break

            vendor = _match_vendor(sender)
            if not vendor:
                subject = ""
                for h in headers:
                    if h["name"].lower() == "subject":
                        subject = h["value"]
                        break
                results["errors"].append((sender, "Sender not in vendor list"))
                continue

            # Extract PDFs
            pdfs = _extract_pdfs(msg["payload"])
            if not pdfs:
                results["errors"].append((sender, "No PDF attachment found"))
                continue

            date_str = _parse_email_date(headers)

            for i, (filename, att_id) in enumerate(pdfs):
                suffix = f"-{i + 1}" if len(pdfs) > 1 else ""
                out_path = _resolve_path(output_dir, vendor.name, date_str, suffix)

                if dry_run:
                    results["processed"].append((out_path.name, vendor.name))
                    continue

                if _save_pdf(service, msg_ref["id"], att_id, out_path):
                    results["processed"].append((out_path.name, vendor.name))
                else:
                    results["errors"].append((sender, f"Corrupt/empty PDF: {filename}"))

            # Label the message as processed
            if not dry_run:
                service.users().messages().modify(
                    userId="me", id=msg_ref["id"],
                    body={"addLabelIds": [label_id]}
                ).execute()

        except Exception as e:
            results["errors"].append((msg_ref["id"], str(e)))

    # Detect new senders
    results["new_senders"] = _find_new_senders(service)

    if not dry_run:
        _save_last_run()

    return results


def _find_new_senders(service) -> list[tuple[str, str]]:
    """Find invoice-like emails from unknown senders."""
    known_emails = {v.email.lower() for v in VENDORS}
    exclude = " ".join(f"-from:{e}" for e in known_emails)
    query = f"has:attachment filename:pdf subject:(invoice OR receipt) -label:{GMAIL_LABEL} {exclude}"

    response = service.users().messages().list(userId="me", q=query, maxResults=20).execute()
    new_senders = []

    for msg_ref in response.get("messages", []):
        try:
            msg = service.users().messages().get(userId="me", id=msg_ref["id"], format="metadata",
                                                  metadataHeaders=["From", "Subject"]).execute()
            headers = msg.get("payload", {}).get("headers", [])
            sender = subject = ""
            for h in headers:
                if h["name"].lower() == "from":
                    sender = h["value"]
                elif h["name"].lower() == "subject":
                    subject = h["value"]
            if sender:
                new_senders.append((sender, subject))
        except Exception:
            continue

    return new_senders
