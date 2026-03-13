# Invoice Collector

A Python CLI that collects, renames, and files tech invoices. Two modes:

- **Gmail mode** — scans email for invoice PDFs from known vendors, downloads and files them
- **Inbox mode** — picks up manually downloaded PDFs from a local `inbox/` folder and renames them

## Setup

### 1. Install dependencies

Using [uv](https://docs.astral.sh/uv/):

```bash
# From the gmail-gdrive-cledara-automation/ directory:
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

Or as a one-liner without activating the venv:

```bash
uv run main.py inbox
```

`uv run` automatically creates a venv and installs dependencies on first use.

### 2. Configure vendors

Edit `config.py` to add your vendors:

```python
VENDORS = [
    Vendor("receipts@stripe.com", "Stripe"),
    Vendor("no-reply-aws@amazon.com", "AWS"),
    Vendor("noreply@github.com", "GitHub", subject_filter="receipt"),
    Vendor("billing@vercel.com", "Vercel"),
]
```

- `subject_filter` is optional — narrows the Gmail search for senders that send non-invoice emails too
- `OUTPUT_DIR` is used by Gmail mode only — set it to wherever you want downloaded PDFs saved

### 3. Set up Gmail API credentials (Gmail mode only)

> Skip this step if you only plan to use inbox mode.

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select an existing one)
3. Navigate to **APIs & Services > Library**, search for **Gmail API**, and enable it
4. Go to **APIs & Services > Credentials**
5. Click **Create Credentials > OAuth client ID**
6. Select **Desktop application** as the application type
7. Download the JSON file and save it as `.credentials/client_secret.json` inside this project folder

On first run, a browser window opens asking you to grant Gmail access. The resulting token is stored in `.credentials/token.json` and reused for future runs.

## Usage

### Inbox mode (start here)

Inbox mode is the simplest way to get started — no Gmail API setup required. Use it for invoices you download manually from billing portals (AWS console, GitHub billing page, Vercel dashboard, etc.).

**Step 1: Drop PDFs into the `inbox/` folder**

Create an `inbox/` folder in the project directory (it's created automatically on first run) and drop your PDFs in. Name them however you like — the tool figures out the vendor and date from the filename:

```
inbox/
  stripe march.pdf          # vendor "stripe" matched, month "march" parsed
  aws-2026-03.pdf            # vendor "aws" matched, date "2026-03" parsed
  github receipt.pdf         # vendor "github" matched, no date -> you'll be prompted
  random-invoice.pdf         # no vendor match -> you'll be prompted to pick one
```

**Step 2: Run it**

```bash
# Preview what would happen (no files renamed):
uv run main.py inbox --dry-run

# Actually rename the files:
uv run main.py inbox
```

**Step 3: Interactive prompts**

If the tool can't determine the vendor or date, it asks you:

```
Processing: random-invoice.pdf
  Could not match vendor from filename: random-invoice.pdf
  Known vendors:
    1. Stripe
    2. AWS
    3. GitHub
    4. Vercel
    5. Enter custom name
  Choose vendor number: 1
  Could not parse date from filename: random-invoice.pdf
  Enter date (YYYY-MM-DD): 2026-03-01
  Renamed to: 2026-03-01-Stripe-Invoice.pdf
```

**Step 4: Check the output**

Files are renamed in place within `inbox/` to `YYYY-MM-DD-Vendor-Invoice.pdf`:

```
inbox/
  2026-03-15-Stripe-Invoice.pdf
  2026-03-01-AWS-Invoice.pdf
  2026-03-10-GitHub-Invoice.pdf
```

Already-renamed files are automatically skipped on subsequent runs. If a name would collide, it's suffixed with `-2`, `-3`, etc.

Google Drive upload is handled separately — the tool just gets your files consistently named and ready.

### Gmail mode

Gmail mode automatically searches your email for invoice PDFs from the vendors in your config, downloads them, renames them, and labels the emails as processed.

**Prerequisites:** Complete step 3 in Setup (Gmail API credentials).

```bash
# Preview what would be downloaded:
uv run main.py --dry-run

# Run for real:
uv run main.py
```

What happens:

1. Authenticates with Gmail (opens browser on first run)
2. Searches for emails from your vendor list that have PDF attachments and haven't been processed yet
3. Downloads each PDF, renames it to `YYYY-MM-DD-Vendor-Invoice.pdf` (date from email header)
4. Saves into `OUTPUT_DIR/VendorName/`
5. Labels the email `invoice-processed` so it's skipped next time
6. Reports any unknown senders with invoice-like emails you might want to add to your vendor list

**Automatic lookback:** The tool tracks when it last ran in `.credentials/last_run`. On the first run it processes the last 90 days. After that, it only looks at emails since the last successful run.

**Multiple attachments:** If an email has multiple PDFs, they're saved as `2026-03-01-Stripe-Invoice-1.pdf`, `2026-03-01-Stripe-Invoice-2.pdf`, etc.

## Summary report

After each run (either mode), a summary is printed:

```
Invoice Collector — 2026-03-12
========================================

Processed: 3
Skipped:   1
Errors:    1

+ 2026-03-01-Stripe-Invoice.pdf         -> Stripe/
+ 2026-02-28-GitHub-Invoice.pdf          -> GitHub/

= 2026-03-01-Stripe-Invoice.pdf         -> Already renamed

x noreply@somevendor.com                -> No PDF attachment found

New senders (not in vendor list):
  - billing@newservice.io — "Your March Invoice"
```

## Project structure

```
main.py            # CLI entry point
gmail.py           # Gmail API: auth, search, download, label
config.py          # Vendor list, output dir, settings
inbox.py           # Inbox mode: match, rename in place
.credentials/      # OAuth tokens (gitignored)
inbox/             # Drop zone for manual downloads (gitignored)
```
