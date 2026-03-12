# Invoice Collector — Design Spec

**Date:** 2026-03-12
**Status:** Approved

## Overview

A Python CLI script that collects, renames, and files tech invoices. Two modes:

1. **Gmail mode** — scans email for invoice PDFs from known vendors, downloads and files them
2. **Inbox mode** — picks up manually downloaded PDFs from a local `inbox/` folder, renames and files them

Files are stored in a local directory. If that directory is inside a Google Drive for Desktop sync folder, they sync to Drive automatically — no Drive API needed.

Output: a summary of what was processed, skipped, and flagged.

## Why Local + Drive Sync (Not Drive API)

Using Google Drive for Desktop eliminates an entire API integration (OAuth scope, folder creation logic, duplicate checking via API). The tool just writes files to disk. Drive handles the rest. This can be revisited if cloud deployment requires direct API access.

## Two Modes

### Gmail Mode

Connects to Gmail via OAuth2. Searches for invoice emails from a vendor list, downloads PDF attachments, renames them, and saves to the output directory.

**Authentication:** OAuth2 with offline refresh token.
- Requires a Google Cloud project with Gmail API enabled
- Download `client_secret.json` to `.credentials/`
- First run opens browser for consent, stores token in `.credentials/token.json`
- Single scope: `gmail.modify` (includes read + ability to label)

**Vendor list** (Python, not JSON — supports comments and IDE autocomplete):

```python
# config.py
VENDORS = [
    Vendor("receipts@stripe.com", "Stripe"),
    Vendor("no-reply-aws@amazon.com", "AWS"),
    Vendor("noreply@github.com", "GitHub", subject_filter="receipt"),
    Vendor("billing@vercel.com", "Vercel"),
    # Add new vendors here
]

OUTPUT_DIR = "~/Drive/Invoices"  # Google Drive for Desktop sync folder
GMAIL_LABEL = "invoice-processed"
```

`subject_filter` is optional — appended as `subject:` to the Gmail query for that vendor. Useful for senders like GitHub where not all emails are invoices.

**Processing:**
1. Build Gmail query: `(from:vendor1 OR from:vendor2 ...) has:attachment filename:pdf -label:invoice-processed`
2. For each matching email: extract date from `Date` header, match sender to vendor name
3. Recursively walk MIME parts to find PDF attachments
4. Save as `YYYY-MM-DD-Vendor-Invoice.pdf` to `OUTPUT_DIR/Vendor/`
5. Apply `invoice-processed` label (created automatically if it doesn't exist)

**Tracking last run:** Stores timestamp of last successful run in `.credentials/last_run`. Gmail query uses `after:` based on this — no manual `lookbackDays` config. First run processes last 90 days.

### Inbox Mode

For portal-downloaded invoices (AWS console, GitHub billing, etc.) that can't be fetched from email:

1. Drop PDFs into `inbox/` folder (in the project directory)
2. Name them roughly: `stripe march.pdf`, `aws-2026-03.pdf`, anything
3. Run `python main.py inbox`
4. Tool matches filename to vendor list (fuzzy match on vendor name), prompts for date if not parseable, renames, and moves to the output directory
5. If vendor can't be matched, prompts interactively

This covers the other half of your invoices with minimal effort.

## Renaming

- **Date** — Gmail mode: from email header. Inbox mode: parsed from filename, or prompted.
- **Vendor** — Gmail mode: matched by sender. Inbox mode: fuzzy matched from filename.
- **Format** — `YYYY-MM-DD-Vendor-Invoice.pdf`
- **Collisions** — if file already exists in output folder, suffix with `-2`, `-3`, etc.
- **Multiple attachments** — suffixed: `-1.pdf`, `-2.pdf`

## Output Directory Structure

```
~/Drive/Invoices/
  Stripe/
    2025-03-15-Stripe-Invoice.pdf
  AWS/
    2025-03-01-AWS-Invoice.pdf
  GitHub/
    2025-03-10-GitHub-Invoice.pdf
```

Vendor folders created automatically. Duplicate check is a simple filesystem `exists()`.

## Error Handling

Skip-and-continue. Errors on individual emails/files don't halt the run:

- **Download fails** — logged, email not labeled (retried next run)
- **Corrupt/empty PDF** — logged, skipped
- **No PDF attachment** — logged in report
- All errors appear in the summary

## Summary Report

Printed to console after each run:

```
Invoice Collector — 2026-03-12
================================

Processed: 5
Skipped:   2 (already exist)
Errors:    1

+ 2026-03-01-Stripe-Invoice.pdf        -> Stripe/
+ 2026-03-01-Stream-Invoice.pdf         -> Stream/
+ 2026-02-28-GitHub-Invoice.pdf         -> GitHub/

= 2026-03-01-Stripe-Invoice.pdf        -> Already exists

x noreply@somevendor.com               -> No PDF attachment found

New senders (not in vendor list):
  - billing@newservice.io — "Your March Invoice"
  - payments@another.app — "Receipt #4521"
```

"New senders" runs a separate Gmail query (`has:attachment filename:pdf subject:(invoice OR receipt) -label:invoice-processed` excluding known vendors) to flag emails you might want to add.

## Project Structure

```
invoice-collector/
  main.py            # CLI entry point, orchestration
  gmail.py           # Gmail API: auth, search, download, label
  config.py          # Vendor list, output dir, settings
  inbox.py           # Inbox mode: match, rename, move
  .credentials/      # OAuth tokens (gitignored)
  inbox/             # Drop zone for manual downloads (gitignored)
  requirements.txt
```

Four source files. No frameworks, no JSON configs, no build step.

**Dependencies:**
- `google-api-python-client`
- `google-auth-oauthlib`

**CLI:**
```
python main.py              # Gmail mode
python main.py inbox        # Inbox mode
python main.py --dry-run    # Preview without changes (either mode)
```

## What Was Removed (and Why)

| Removed | Why |
|---------|-----|
| Google Drive API | Local folder + Drive for Desktop sync is simpler and eliminates an entire API integration |
| `settings.json` + `vendors.json` | Config as Python code — one file, with comments and type checking |
| `types.py`, `rename.py`, `report.py`, `auth.py` | Collapsed into the files that use them — each was <20 lines |
| `pyproject.toml` | Overkill for a personal script |
| `lookbackDays` config | Replaced with automatic last-run tracking |
| `drive.file` / `drive` scope debate | Eliminated entirely — no Drive API |
| `saveReportToDrive` option | Just print to console. Redirect to file if you want it saved |
| Future extensions section | YAGNI — add them when needed |

## Future Path to Cloud

When ready to run this on a schedule without your laptop:
- Wrap `main.py` in a Google Cloud Function
- Replace local filesystem with Drive API (add back `drive.py`)
- Replace interactive OAuth with a service account
- Add Slack/email notification for the summary report

This is a later project, not designed for now.
