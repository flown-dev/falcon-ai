# Invoice Collector

A Python CLI that collects, renames, and files tech invoices. Two modes:

- **Gmail mode** — scans email for invoice PDFs from known vendors, downloads and files them
- **Inbox mode** — picks up manually downloaded PDFs from a local `inbox/` folder, renames and files them

Files are saved to a local directory. If that directory is inside a Google Drive for Desktop sync folder, they sync to Drive automatically.

## Setup

### 1. Install dependencies

```
pip install -r requirements.txt
```

### 2. Configure vendors and output directory

Edit `config.py` to add your vendors and set the output path:

```python
VENDORS = [
    Vendor("receipts@stripe.com", "Stripe"),
    Vendor("no-reply-aws@amazon.com", "AWS"),
    Vendor("noreply@github.com", "GitHub", subject_filter="receipt"),
    Vendor("billing@vercel.com", "Vercel"),
]

OUTPUT_DIR = "~/Drive/Invoices"
```

- `subject_filter` is optional — narrows the Gmail search for senders that send non-invoice emails too
- `OUTPUT_DIR` should point to your Google Drive for Desktop sync folder (or any local directory)

### 3. Set up Gmail API credentials (Gmail mode only)

1. Create a project in the [Google Cloud Console](https://console.cloud.google.com/)
2. Enable the **Gmail API**
3. Create OAuth 2.0 credentials (Desktop application)
4. Download the credentials file and save it as `.credentials/client_secret.json`

On first run, a browser window opens for OAuth consent. The token is stored in `.credentials/token.json` for subsequent runs.

## Usage

```
python main.py              # Gmail mode — scan email and download invoices
python main.py inbox        # Inbox mode — process PDFs from inbox/ folder
python main.py --dry-run    # Preview without making changes (either mode)
python main.py inbox --dry-run
```

### Gmail mode

Searches Gmail for invoice emails from your vendor list, downloads PDF attachments, renames them as `YYYY-MM-DD-Vendor-Invoice.pdf`, and saves them into vendor subfolders. Processed emails are labeled `invoice-processed` so they aren't re-downloaded.

The tool tracks the last successful run in `.credentials/last_run`. First run processes the last 90 days.

### Inbox mode

For invoices downloaded manually from billing portals:

1. Drop PDFs into the `inbox/` folder
2. Name them roughly — `stripe march.pdf`, `aws-2026-03.pdf`, anything recognizable
3. Run `python main.py inbox`

The tool fuzzy-matches filenames to your vendor list and parses dates from the filename. If it can't match a vendor or parse a date, it prompts you interactively.

## Output structure

```
~/Drive/Invoices/
  Stripe/
    2025-03-15-Stripe-Invoice.pdf
  AWS/
    2025-03-01-AWS-Invoice.pdf
  GitHub/
    2025-03-10-GitHub-Invoice.pdf
```

## Summary report

After each run, a summary is printed:

```
Invoice Collector — 2026-03-12
========================================

Processed: 3
Skipped:   1
Errors:    1

+ 2026-03-01-Stripe-Invoice.pdf         -> Stripe/
+ 2026-02-28-GitHub-Invoice.pdf          -> GitHub/

= 2026-03-01-Stripe-Invoice.pdf         -> Already exists

x noreply@somevendor.com                -> No PDF attachment found

New senders (not in vendor list):
  - billing@newservice.io — "Your March Invoice"
```

## Project structure

```
main.py            # CLI entry point
gmail.py           # Gmail API: auth, search, download, label
config.py          # Vendor list, output dir, settings
inbox.py           # Inbox mode: match, rename, move
.credentials/      # OAuth tokens (gitignored)
inbox/             # Drop zone for manual downloads (gitignored)
```
