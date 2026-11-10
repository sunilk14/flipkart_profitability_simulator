"""Submission storage. Sheets for hosted deployments; CSV for local demo only."""
import csv
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock

FIELDS = ["timestamp_utc", "section", "group_id", "submission_id", "cuts_json", "metrics_json"]
LOCK = Lock()
CSV_PATH = Path(__file__).parent / "data" / "submissions.csv"


def _sheet(secrets):
    import gspread
    from google.oauth2.service_account import Credentials
    credentials = Credentials.from_service_account_info(
        dict(secrets["gcp_service_account"]),
        scopes=["https://www.googleapis.com/auth/spreadsheets"],
    )
    spreadsheet = gspread.authorize(credentials).open_by_key(secrets["spreadsheet_id"])
    try:
        worksheet = spreadsheet.worksheet("Submissions")
    except gspread.WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(title="Submissions", rows=500, cols=10)
    if not worksheet.row_values(1):
        worksheet.append_row(FIELDS, value_input_option="RAW")
    return worksheet


def backend(secrets):
    has_id = bool(secrets.get("spreadsheet_id", ""))
    has_credentials = "gcp_service_account" in secrets
    if has_id != has_credentials:
        raise RuntimeError("Supply both spreadsheet_id and [gcp_service_account], or neither.")
    return "Google Sheets" if has_id else "Local CSV (temporary)"


def save_submission(secrets, section, group_id, cuts, metrics):
    # Store only aggregate selections; don't collect student names.
    import uuid
    row = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "section": section.strip(), "group_id": group_id.strip(),
        "submission_id": uuid.uuid4().hex,
        "cuts_json": json.dumps(cuts),
        "metrics_json": json.dumps({k: v for k, v in metrics.items()
                                    if k not in ("costs_p1", "costs_p2")}),
    }
    if backend(secrets) == "Google Sheets":
        _sheet(secrets).append_row([row[f] for f in FIELDS], value_input_option="RAW")
    else:
        with LOCK:
            CSV_PATH.parent.mkdir(exist_ok=True)
            exists = CSV_PATH.exists() and CSV_PATH.stat().st_size > 0
            with CSV_PATH.open("a", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=FIELDS)
                if not exists:
                    writer.writeheader()
                writer.writerow(row)
    return row["submission_id"]


def load_submissions(secrets):
    if backend(secrets) == "Google Sheets":
        rows = _sheet(secrets).get_all_records()
    else:
        if not CSV_PATH.exists():
            return []
        with LOCK, CSV_PATH.open(encoding="utf-8", newline="") as f:
            rows = list(csv.DictReader(f))
    result = []
    for row in rows:
        try:
            result.append({**row, "cuts": json.loads(row["cuts_json"]),
                           "metrics": json.loads(row["metrics_json"])})
        except (ValueError, KeyError, TypeError):
            continue
    return result


def latest_per_group(rows):
    # Submissions append for auditability. The dashboard shows the last per group.
    latest = {}
    for row in rows:
        key = (str(row["section"]).strip().casefold(), str(row["group_id"]).strip().casefold())
        if key not in latest or (str(row["timestamp_utc"]), str(row["submission_id"])) > (
                str(latest[key]["timestamp_utc"]), str(latest[key]["submission_id"])):
            latest[key] = row
    return sorted(latest.values(), key=lambda x: (str(x["section"]), str(x["group_id"])))
