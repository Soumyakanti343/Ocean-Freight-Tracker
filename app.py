from pathlib import Path

import streamlit as st

from database.db import init_db, query, status_for
from modules.authentication import render_login
from modules.dashboard import render_dashboard
from modules.rate_search import render_rate_search
from modules.shipment_tracker import render_shipment_tracker
from modules.invoice_checker import render_invoice_checker
from modules.email_updates import render_email_updates

from style import apply_styles


# ---------- Application Configuration ----------

BASE = Path(__file__).resolve().parent

st.set_page_config(
    page_title="Ocean Freight Tracker",
    page_icon="🚢",
    layout="wide"
)

# ---------- Add Style --------------

apply_styles()


# ---------- Database Initialization ----------

init_db()


# ---------- Authentication ----------

render_login()

user = st.session_state.auth_user


# ---------- Sidebar Navigation ----------

with st.sidebar:
    st.title('🚢 Ocean Freight')

    st.caption(
        f"Signed in as **{user['username']}** · {user['role']}"
    )

    page = st.radio(
        'Navigation',
        [
            'Overview',
            'Rate Search',
            'Shipment Tracker',
            'Invoice Checker',
            'Email Updates'
        ]
    )

    if st.button('Log out', width = "stretch"):
        st.session_state.auth_user = None
        st.rerun()

    st.divider()

    st.caption('Ocean Freight Rate & Shipment Tracker')


# ---------- Page Header ----------

st.title(page)

st.caption('DIGITIZE  ·  OPTIMIZE  ·  DEMOCRATIZE')


# ---------- Load Application Data ----------

rates = query(
    'SELECT * FROM rates ORDER BY rate_usd'
)

shipments = query(
    'SELECT * FROM shipments ORDER BY expected_arrival'
)

if not shipments.empty:
    shipments['status'] = shipments.apply(
        lambda r: status_for(r.to_dict()),
        axis=1
    )


# ---------- Page Routing ----------

if page == 'Overview':
    render_dashboard(shipments, rates)

elif page == 'Rate Search':
    render_rate_search(rates)

elif page == 'Shipment Tracker':
    render_shipment_tracker(shipments, rates, user)

elif page == 'Invoice Checker':
    render_invoice_checker(shipments, rates)

elif page == 'Email Updates':
    render_email_updates(rates)


# ---------- Footer ----------

st.divider()





