import re
from datetime import datetime
from pathlib import Path

from config import VENDORS, Vendor


def _fuzzy_match_vendor(filename: str) -> Vendor | None:
    """Try to match a filename to a vendor by name (case-insensitive substring)."""
    name_lower = filename.lower()
    for v in VENDORS:
        if v.name.lower() in name_lower:
            return v
    return None


def _parse_date_from_filename(filename: str) -> str | None:
    """Try to extract a date from the filename."""
    # Try YYYY-MM-DD or YYYY-MM
    match = re.search(r"(\d{4})-(\d{1,2})(?:-(\d{1,2}))?", filename)
    if match:
        year, month = match.group(1), match.group(2)
        day = match.group(3) or "01"
        try:
            dt = datetime(int(year), int(month), int(day))
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            pass

    # Try month names: "march", "mar", etc.
    months = {
        "january": 1, "jan": 1, "february": 2, "feb": 2, "march": 3, "mar": 3,
        "april": 4, "apr": 4, "may": 5, "june": 6, "jun": 6,
        "july": 7, "jul": 7, "august": 8, "aug": 8, "september": 9, "sep": 9,
        "october": 10, "oct": 10, "november": 11, "nov": 11, "december": 12, "dec": 12,
    }
    name_lower = filename.lower()
    for month_name, month_num in months.items():
        if month_name in name_lower:
            # Look for a year nearby
            year_match = re.search(r"(20\d{2})", filename)
            year = int(year_match.group(1)) if year_match else datetime.now().year
            return f"{year}-{month_num:02d}-01"

    return None


def _prompt_date() -> str:
    """Prompt user for a date."""
    while True:
        raw = input("  Enter date (YYYY-MM-DD): ").strip()
        try:
            dt = datetime.strptime(raw, "%Y-%m-%d")
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            print("  Invalid format. Use YYYY-MM-DD.")


def _prompt_vendor() -> str:
    """Prompt user for a vendor name."""
    print("  Known vendors:")
    for i, v in enumerate(VENDORS, 1):
        print(f"    {i}. {v.name}")
    print(f"    {len(VENDORS) + 1}. Enter custom name")

    while True:
        choice = input("  Choose vendor number: ").strip()
        try:
            idx = int(choice)
            if 1 <= idx <= len(VENDORS):
                return VENDORS[idx - 1].name
            if idx == len(VENDORS) + 1:
                name = input("  Enter vendor name: ").strip()
                if name:
                    return name
        except ValueError:
            pass
        print("  Invalid choice.")


def _resolve_path(inbox_dir: Path, vendor_name: str, date_str: str) -> Path:
    """Build renamed path within inbox/ with collision handling."""
    base_name = f"{date_str}-{vendor_name}-Invoice.pdf"
    path = inbox_dir / base_name
    if not path.exists():
        return path
    counter = 2
    while True:
        base_name = f"{date_str}-{vendor_name}-Invoice-{counter}.pdf"
        path = inbox_dir / base_name
        if not path.exists():
            return path
        counter += 1


def process_inbox(dry_run: bool = False) -> dict:
    """Process PDFs from the inbox/ folder. Renames in place. Returns summary dict."""
    inbox = Path("inbox")
    results = {"processed": [], "skipped": [], "errors": []}

    if not inbox.exists():
        inbox.mkdir()
        print("Created inbox/ folder. Drop PDFs there and re-run.")
        return results

    # Collect PDFs from inbox root and any subfolders
    pdfs = sorted(inbox.rglob("*.pdf"))
    if not pdfs:
        print("No PDFs found in inbox/.")
        return results

    for pdf_path in pdfs:
        filename = pdf_path.stem
        # Use parent folder name as extra context for matching (e.g. inbox/stripe/*.pdf)
        parent_name = pdf_path.parent.name if pdf_path.parent != inbox else ""

        # Skip files already renamed by a previous run
        if re.match(r"\d{4}-\d{2}-\d{2}-.+-Invoice", filename):
            results["skipped"].append((pdf_path.name, "Already renamed"))
            continue

        rel_path = pdf_path.relative_to(inbox)
        print(f"\nProcessing: {rel_path}")

        # Check if it's a valid PDF (basic size check)
        if pdf_path.stat().st_size < 100:
            results["errors"].append((str(rel_path), "File too small / corrupt"))
            continue

        # Match vendor — try filename first, then parent folder name
        vendor = _fuzzy_match_vendor(filename)
        if not vendor and parent_name:
            vendor = _fuzzy_match_vendor(parent_name)
        if vendor:
            vendor_name = vendor.name
            print(f"  Matched vendor: {vendor_name}")
        else:
            print(f"  Could not match vendor from filename: {rel_path}")
            vendor_name = _prompt_vendor()

        # Parse date — try filename first, then parent folder name
        date_str = _parse_date_from_filename(filename)
        if not date_str and parent_name:
            date_str = _parse_date_from_filename(parent_name)
        if date_str:
            print(f"  Parsed date: {date_str}")
        else:
            print(f"  Could not parse date from filename: {rel_path}")
            date_str = _prompt_date()

        # Resolve output path (renamed in inbox/ root)
        out_path = _resolve_path(inbox, vendor_name, date_str)

        if dry_run:
            print(f"  Would rename to: {out_path.name}")
            results["processed"].append((out_path.name, vendor_name))
            continue

        pdf_path.rename(out_path)
        results["processed"].append((out_path.name, vendor_name))
        print(f"  Renamed to: {out_path.name}")

    return results
