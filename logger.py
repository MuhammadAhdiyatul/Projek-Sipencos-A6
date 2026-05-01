import os
import json
from datetime import datetime

# Storage configuration
LOG_DIR = os.path.join(os.path.dirname(__file__), "logs")
LOG_FILE = os.path.join(LOG_DIR, "scrape_log.json")
_TS_FORMAT = "%Y-%m-%d %H:%M:%S"

# Safe default returned when no valid log exists
_DEFAULT_LOG = {
    "last_scraped": "-",
    "status": "never",
    "total_data": 0,
    "message": "No scraping activity yet",
}


def _ensure_log_dir():
    try:
        os.makedirs(LOG_DIR, exist_ok=True)
    except Exception:
        # Fail silently — module must never crash the app
        pass


def _safe_write_json(path: str, data: dict) -> bool:
    """
    Atomically write JSON to `path`. Returns True on success, False on failure.
    """
    tmp_path = path + ".tmp"
    try:
        _ensure_log_dir()
        with open(tmp_path, "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=2)
        os.replace(tmp_path, path)
        return True
    except Exception:
        try:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        except Exception:
            pass
        return False


def log_scrape(status: str, total_data: int = 0, message: str = "") -> dict:
    """
    Save latest scrape metadata.

    - `status`: expected values 'success' or 'failed' (case-insensitive)
    - `total_data`: integer count of scraped kos
    - `message`: optional note or error message

    Always returns the entry that was attempted to be written (or defaults on failure).
    Never raises.
    """
    try:
        s = str(status).lower() if status is not None else "failed"
        s = "success" if s == "success" else "failed"

        entry = {
            "last_scraped": datetime.now().strftime(_TS_FORMAT),
            "status": s,
            "total_data": int(total_data or 0),
            "message": str(message) if message else ("Scraping completed successfully" if s == "success" else ""),
        }

        _safe_write_json(LOG_FILE, entry)
        return entry
    except Exception:
        return _DEFAULT_LOG.copy()


def get_last_scrape_log() -> dict:
    """
    Load the latest scrape metadata from disk.

    Returns a dict with keys: last_scraped, status, total_data, message.
    Falls back to a safe default if file is missing or invalid.
    """
    try:
        if not os.path.exists(LOG_FILE):
            return _DEFAULT_LOG.copy()

        with open(LOG_FILE, "r", encoding="utf-8") as fh:
            data = json.load(fh)

        if not isinstance(data, dict):
            return _DEFAULT_LOG.copy()

        # Ensure required fields exist and have sensible types
        result = {
            "last_scraped": str(data.get("last_scraped", _DEFAULT_LOG["last_scraped"])),
            "status": str(data.get("status", _DEFAULT_LOG["status"])),
            "total_data": int(data.get("total_data", _DEFAULT_LOG["total_data"]) or 0),
            "message": str(data.get("message", _DEFAULT_LOG["message"]) or ""),
        }
        return result
    except Exception:
        return _DEFAULT_LOG.copy()


def get_scrape_status_text() -> dict:
    """
    Return a small UI-friendly dict for display:

    {
        "title": "Last Scraped",
        "timestamp": "21 Sep 2025, 14:32",
        "summary": "Success • 32 kos"
    }

    Always returns a dict and never raises.
    """
    log = get_last_scrape_log()

    # Format timestamp to human-readable form if possible
    ts = log.get("last_scraped", "-")
    human_ts = "-"
    if ts and ts != "-":
        try:
            dt = datetime.strptime(ts, _TS_FORMAT)
            human_ts = dt.strftime("%d %b %Y, %H:%M")
        except Exception:
            # If parsing fails, fall back to the raw value
            human_ts = ts

    status = (log.get("status") or "never").lower()
    status_cap = status.capitalize() if status != "never" else "Never"
    total = int(log.get("total_data", 0) or 0)
    message = (log.get("message") or "").strip()

    if status == "never":
        summary = "No scraping activity yet"
    else:
        # Basic compact summary; include message only if failed and message present
        summary = f"{status_cap} • {total} kos"
        if status == "failed" and message:
            summary = f"{summary} • {message}"

    return {"title": "Last Scraped", "timestamp": human_ts, "summary": summary}
