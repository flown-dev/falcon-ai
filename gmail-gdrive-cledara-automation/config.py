from dataclasses import dataclass
from typing import Optional


@dataclass
class Vendor:
    email: str
    name: str
    subject_filter: Optional[str] = None


VENDORS = [
    Vendor("receipts@stripe.com", "Stripe"),
    Vendor("no-reply-aws@amazon.com", "AWS"),
    Vendor("aws-receivables-support@email.amazon.com", "AWS"),
    Vendor("billing@datadoghq.com", "Datadog"),
    Vendor("sales@auth0.com", "Auth0"),
    Vendor("noreply@github.com", "GitHub", subject_filter="receipt"),
    Vendor("billing@vercel.com", "Vercel"),
    Vendor("archive@mixpanel.com", "Mixpanel"),
    Vendor("no-reply@typeform.com", "Typeform"),
    Vendor("hi@cursor.com", "Cursor"),
    Vendor("donotreply@godaddy.com", "GoDaddy"),
    Vendor("", "OneSignal"),
    Vendor("accountsreceivable@intercom.io", "Intercom"),
    Vendor("", "Sendgrid"),
    Vendor("", "Medium"),
    Vendor("", "Google")
    # Add new vendors here
]

OUTPUT_DIR = "/Users/kiily/Documents/00 - FLOWN/code/falcon-ai/gmail-gdrive-cledara-automation/inbox/Invoices"  # Google Drive for Desktop sync folder
GMAIL_LABEL = "invoice-processed"
