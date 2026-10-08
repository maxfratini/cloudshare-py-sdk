"""
Delete expired CloudShare classes.

Finds classes whose end_date is in the past and deletes them.

Usage
-----
    python examples/deleteExpiredClasses.py --creds-file credentials.json
    python examples/deleteExpiredClasses.py --api-id ID --api-key KEY
    python examples/deleteExpiredClasses.py --creds-file credentials.json --dry-run

Credentials file format (JSON):
    {"API_ID": "your-api-id", "API_KEY": "your-api-key"}

The script uses the mxcloudshare SDK (no external dependencies beyond what the
project already requires).
"""

from __future__ import annotations

import argparse
import datetime
import json
import sys

from mxcloudshare import mxcloudshare as cs


def is_expired(end_date: str) -> bool:
    """Return True if *end_date* (ISO 8601, e.g. ``2025-10-01T00:00:00Z``) is in the past."""
    try:
        parsed = datetime.datetime.strptime(end_date, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        # Try without trailing Z / with microseconds
        parsed = datetime.datetime.fromisoformat(end_date.replace("Z", "+00:00"))
    now = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
    return now > parsed


def main() -> None:
    parser = argparse.ArgumentParser(description="Delete expired CloudShare classes.")
    parser.add_argument(
        "--creds-file",
        "-c",
        default=None,
        help="Path to JSON file containing API_ID and API_KEY.",
    )
    parser.add_argument("--api-id", default=None, help="CloudShare API ID (overrides creds file).")
    parser.add_argument("--api-key", default=None, help="CloudShare API key (overrides creds file).")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List expired classes without deleting them.",
    )
    args = parser.parse_args()

    # ── Resolve credentials ──────────────────────────────────────────────
    api_id: str | None = args.api_id
    api_key: str | None = args.api_key

    if args.creds_file:
        try:
            with open(args.creds_file) as f:
                creds = json.load(f)
        except FileNotFoundError:
            print(f"Error: credentials file not found: {args.creds_file}", file=sys.stderr)
            sys.exit(1)
        except json.JSONDecodeError as exc:
            print(f"Error: invalid JSON in {args.creds_file}: {exc}", file=sys.stderr)
            sys.exit(1)
        api_id = api_id or creds.get("API_ID")
        api_key = api_key or creds.get("API_KEY")

    if not api_id or not api_key:
        print(
            "Error: API credentials are required. Provide --api-id/--api-key or a --creds-file.",
            file=sys.stderr,
        )
        sys.exit(1)

    # ── Authenticate and fetch classes ───────────────────────────────────
    cs.cs_set_auth_keys(api_id, api_key)

    try:
        classes = cs.cs_class_get_all()
    except Exception as exc:
        print(f"Error fetching classes: {exc}", file=sys.stderr)
        sys.exit(1)

    expired = [cls for cls in classes if is_expired(cls["end_date"])]

    if not expired:
        print("No expired classes found.")
        sys.exit(0)

    print(f"Found {len(expired)} expired class(es):")
    for cls in expired:
        print(f"  ID: {cls['id']}  Name: {cls['name']}  End: {cls['end_date']}")

    if args.dry_run:
        print("[dry-run] No classes were deleted.")
        sys.exit(0)

    # ── Delete each expired class ────────────────────────────────────────
    failures = 0
    for cls in expired:
        try:
            cs.cs_class_delete(cls["id"])
            print(f"  Deleted: {cls['name']} ({cls['id']})")
        except Exception as exc:
            print(f"  Failed to delete {cls['id']}: {exc}", file=sys.stderr)
            failures += 1

    if failures:
        print(f"Deleted {len(expired) - failures} of {len(expired)} classes; {failures} failed.")
        sys.exit(1)
    else:
        print(f"Successfully deleted all {len(expired)} expired classes.")


if __name__ == "__main__":
    main()