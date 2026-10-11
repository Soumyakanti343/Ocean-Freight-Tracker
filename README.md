# Ocean Freight Rate & Shipment Tracker

A Streamlit + SQLite prototype for carrier rate comparison, shipment status tracking, invoice checking, and plain-text email updates.

## Features
- Login with Admin and User roles; passwords are stored as salted PBKDF2-HMAC-SHA256 hashes.
- Rate Search by origin, destination, and container size; cheapest option highlighted.
- Shipment Tracker with add/search, automatic overdue status, and Admin status updates.
- Invoice Checker for single invoices or CSV uploads.
- Email Updates parser for the supplied sample inbox; updates rates and shipment statuses, logs processed emails, and skips incomplete/irrelevant messages.
- Overview dashboard with shipment status chart.

## Run locally (Windows PowerShell)
```powershell
cd ocean_freight_tracker
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

If `py -3.12` is not available, use an installed supported Python version (3.10–3.12 recommended).

## Demo accounts
- Admin: `admin` / `Admin@123`
- User: `user` / `User@123`

These accounts are for demonstration only. The prototype uses a local SQLite database (`ocean_freight.db`) created automatically on first run. Delete that database to reset the app and reload the original CSV data.

## Data files
- `data/carrier_rates.csv`
- `data/sample_shipments.csv`
- `data/sample_emails.txt`

## Notes / assumptions
- Shipment status is `Delivered` if a delivery date exists, otherwise an explicit email/Admin override is honored; without an override, an overdue expected-arrival date means `Delayed`, otherwise `In Transit`.
- Invoice checks compare the invoice to the current matching rate for the same carrier, route, and container size. A missing matching rate is flagged instead of guessing.
- Email parsing uses deterministic patterns and sender-domain mapping; incomplete messages are skipped for manual review. The parser records email hashes to avoid applying the same email twice.
- This is a demo prototype, not a production shipping or authentication system.
