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
    Vendor("noreply@github.com", "GitHub", subject_filter="receipt"),
    Vendor("billing@vercel.com", "Vercel"),
    # Add new vendors here
]

OUTPUT_DIR = "~/Drive/Invoices"  # Google Drive for Desktop sync folder
GMAIL_LABEL = "invoice-processed"
