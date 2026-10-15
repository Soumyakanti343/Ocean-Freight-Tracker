# 🚢 Ocean Freight Rate & Shipment Tracker

**DIGITIZE · OPTIMIZE · DEMOCRATIZE**

An interactive web application built with Python and Streamlit to simplify ocean freight rate comparison, shipment tracking, invoice verification, and email-based logistics updates.

##  Overview

Ocean Freight Rate & Shipment Tracker is designed to make freight management easier by bringing essential logistics operations into a single dashboard.

The application helps users compare carrier rates, monitor shipment progress, identify potential invoice overcharges, and process email updates to keep shipment information organized.

##  Features

###  1. Overview Dashboard
- View key shipment and freight statistics.
- Monitor shipment statuses.
- Explore freight rate information.
- Access important information through a centralized dashboard.

###  2. Freight Rate Search
- Search and compare freight rates from different carriers.
- Filter available rates based on shipment requirements.
- Identify the lowest available freight rate.

###  3. Shipment Tracker
- Search and view shipment information.
- Add new shipment records.
- Monitor shipment statuses, including:
  - In Transit
  - Delivered
  - Delayed
- Allow administrators to update shipment status.

###  4. Invoice Checker
- Compare invoice charges against stored carrier rates.
- Identify potential overcharges.
- Upload CSV files for bulk invoice comparison.

###  5. Email Updates
- Process sample or uploaded email messages.
- Extract relevant freight rate and shipment information.
- Avoid processing duplicate emails using message hashes.
- Update relevant rate and shipment records.
- Maintain an email processing log.

###  6. Authentication
- Login system with user roles.
- Separate administrator and regular-user access.
- Role-based access to selected application features.

###  7. Interactive User Interface
- Modern ocean-blue and teal theme.
- Custom styling using Streamlit and CSS.
- Interactive buttons, forms, metrics, and tables.
- Responsive layout for different screen sizes.

##  Tech Stack

| Technology | Purpose |
|---|---|
| Python | Core application logic |
| Streamlit | Interactive web application |
| Pandas | Data processing and analysis |
| SQLite | Database and persistent local data storage |
| HTML & CSS | Custom user interface styling |
| CSV | Freight rates, shipment data, and bulk invoice input |

##  Project Structure

```text
ocean-freight-tracker/
│
├── app.py
├── style.py
├── requirements.txt
├── README.md
├── .gitignore
│
├── database/
│   ├── __init__.py
│   └── db.py
│
├── modules/
│   ├── __init__.py
│   ├── authentication.py
│   ├── dashboard.py
│   ├── rate_search.py
│   ├── shipment_tracker.py
│   ├── invoice_checker.py
│   └── email_updates.py
│
├── utils/
│   ├── __init__.py
│   └── helpers.py
│
└── data/
    ├── carrier_rates.csv
    ├── sample_shipments.csv
    └── sample_emails.txt
