from pathlib import Path
from datetime import date, datetime
import hashlib, hmac, re, sqlite3
import pandas as pd
import streamlit as st

BASE = Path(__file__).resolve().parent
DATA = BASE / "data"
DB = BASE / "ocean_freight.db"
TODAY = date.today()

st.set_page_config(page_title="Ocean Freight Tracker", page_icon="🚢", layout="wide")

# ---------- Database ----------
def connect():
    conn = sqlite3.connect(DB, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password, salt=None):
    salt = salt or __import__('os').urandom(16).hex()
    digest = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 200_000).hex()
    return f"{salt}${digest}"

def verify_password(password, stored):
    try:
        salt, digest = stored.split('$', 1)
        return hmac.compare_digest(hash_password(password, salt).split('$', 1)[1], digest)
    except Exception:
        return False

def init_db():
    with connect() as c:
        c.executescript('''
        CREATE TABLE IF NOT EXISTS users(username TEXT PRIMARY KEY, password_hash TEXT NOT NULL, role TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS rates(
          id INTEGER PRIMARY KEY AUTOINCREMENT, carrier TEXT NOT NULL, origin_port TEXT NOT NULL,
          destination_port TEXT NOT NULL, container_type TEXT NOT NULL, rate_usd REAL NOT NULL,
          transit_days INTEGER NOT NULL, effective_from TEXT DEFAULT '',
          UNIQUE(carrier, origin_port, destination_port, container_type));
        CREATE TABLE IF NOT EXISTS shipments(
          shipment_id TEXT PRIMARY KEY, carrier TEXT NOT NULL, origin_port TEXT NOT NULL,
          destination_port TEXT NOT NULL, container_type TEXT NOT NULL, departure_date TEXT NOT NULL,
          expected_arrival TEXT NOT NULL, delivered_date TEXT DEFAULT '', invoice_amount_usd REAL DEFAULT 0,
          status_override TEXT DEFAULT '', updated_at TEXT DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS email_logs(
          id INTEGER PRIMARY KEY AUTOINCREMENT, email_subject TEXT, action TEXT, details TEXT,
          processed_at TEXT DEFAULT CURRENT_TIMESTAMP, email_hash TEXT UNIQUE);
        ''')
        if c.execute('SELECT COUNT(*) FROM users').fetchone()[0] == 0:
            c.execute('INSERT INTO users VALUES(?,?,?)', ('admin', hash_password('Admin@123'), 'Admin'))
            c.execute('INSERT INTO users VALUES(?,?,?)', ('user', hash_password('User@123'), 'User'))
        if c.execute('SELECT COUNT(*) FROM rates').fetchone()[0] == 0:
            df = pd.read_csv(DATA / 'carrier_rates.csv').fillna('')
            for _, r in df.iterrows():
                c.execute('''INSERT OR IGNORE INTO rates(carrier,origin_port,destination_port,container_type,rate_usd,transit_days)
                  VALUES(?,?,?,?,?,?)''', (r.carrier, r.origin_port, r.destination_port, r.container_type, float(r.rate_usd), int(r.transit_days)))
        if c.execute('SELECT COUNT(*) FROM shipments').fetchone()[0] == 0:
            df = pd.read_csv(DATA / 'sample_shipments.csv').fillna('')
            for _, r in df.iterrows():
                c.execute('''INSERT OR IGNORE INTO shipments(shipment_id,carrier,origin_port,destination_port,container_type,departure_date,expected_arrival,delivered_date,invoice_amount_usd)
                  VALUES(?,?,?,?,?,?,?,?,?)''', (r.shipment_id,r.carrier,r.origin_port,r.destination_port,r.container_type,r.departure_date,r.expected_arrival,r.delivered_date,float(r.invoice_amount_usd or 0)))
init_db()

def query(sql, params=()):
    with connect() as c:
        return pd.read_sql_query(sql, c, params=params)

def execute(sql, params=()):
    with connect() as c:
        c.execute(sql, params)

def status_for(row):
    if row.get('delivered_date') and str(row.get('delivered_date')).strip(): return 'Delivered'
    if row.get('status_override') in ('Delayed', 'In Transit'): return row['status_override']
    try:
        return 'Delayed' if date.fromisoformat(str(row['expected_arrival'])) < TODAY else 'In Transit'
    except Exception:
        return 'In Transit'

# ---------- Authentication ----------
if 'auth_user' not in st.session_state: st.session_state.auth_user = None
if not st.session_state.auth_user:
    st.markdown("# 🚢 Ocean Freight Tracker")
    st.caption('A practical workspace for carrier rates, shipments, invoices, and email updates.')
    left, right = st.columns([1, 1.3])
    with left:
        st.subheader('Sign in')
        with st.form('login_form'):
            username = st.text_input('Username')
            password = st.text_input('Password', type='password')
            submitted = st.form_submit_button('Login', use_container_width=True)
        if submitted:
            users = query('SELECT * FROM users WHERE username=?', (username.strip(),))
            if not users.empty and verify_password(password, users.iloc[0]['password_hash']):
                st.session_state.auth_user = {'username': username.strip(), 'role': users.iloc[0]['role']}
                st.rerun()
            else: st.error('Invalid username or password.')
    with right:
        st.info('**Demo credentials**\n\nAdmin: `admin` / `Admin@123`\n\nUser: `user` / `User@123`\n\nPasswords are stored as salted PBKDF2-HMAC-SHA256 hashes. Change demo credentials before using this beyond a local prototype.')
    st.stop()

user = st.session_state.auth_user
with st.sidebar:
    st.title('🚢 Ocean Freight')
    st.caption(f"Signed in as **{user['username']}** · {user['role']}")
    page = st.radio('Navigation', ['Overview', 'Rate Search', 'Shipment Tracker', 'Invoice Checker', 'Email Updates'])
    if st.button('Log out', use_container_width=True):
        st.session_state.auth_user = None
        st.rerun()
    st.divider()
    st.caption('Ocean Freight Rate & Shipment Tracker')

st.title(page)
st.caption('DIGITIZE  ·  OPTIMIZE  ·  DEMOCRATIZE')

rates = query('SELECT * FROM rates ORDER BY rate_usd')
shipments = query('SELECT * FROM shipments ORDER BY expected_arrival')
if not shipments.empty: shipments['status'] = shipments.apply(lambda r: status_for(r.to_dict()), axis=1)

if page == 'Overview':
    total = len(shipments); delivered = int((shipments.status == 'Delivered').sum()); delayed = int((shipments.status == 'Delayed').sum()); transit = int((shipments.status == 'In Transit').sum())
    a,b,c,d = st.columns(4)
    a.metric('Total shipments', total); b.metric('Delivered', delivered); c.metric('In transit', transit); d.metric('Delayed', delayed)
    st.subheader('Shipment status overview')
    if total:
        st.bar_chart(shipments['status'].value_counts().reindex(['In Transit','Delivered','Delayed'], fill_value=0))
    st.subheader('Upcoming and delayed shipments')
    st.dataframe(shipments[['shipment_id','carrier','origin_port','destination_port','container_type','expected_arrival','status']], use_container_width=True, hide_index=True)
    st.caption(f"{len(rates)} carrier rate combinations loaded from the supplied CSV.")

elif page == 'Rate Search':
    st.write('Compare available carrier rates by route and container size.')
    c1,c2,c3 = st.columns(3)
    origins = sorted(rates.origin_port.dropna().unique().tolist()); destinations = sorted(rates.destination_port.dropna().unique().tolist())
    origin = c1.selectbox('Origin port', origins); destination = c2.selectbox('Destination port', destinations); container = c3.selectbox('Container type', ['20ft','40ft'])
    found = rates[(rates.origin_port == origin) & (rates.destination_port == destination) & (rates.container_type == container)].sort_values('rate_usd')
    if found.empty: st.warning('No carrier rates found for this route and container type.')
    else:
        cheapest = found.iloc[0]
        st.success(f"Cheapest option: {cheapest.carrier} · ${cheapest.rate_usd:,.2f} USD · {int(cheapest.transit_days)} transit days")
        display = found.copy(); display.insert(0, 'Recommendation', ['⭐ Cheapest' if i == 0 else '' for i in range(len(display))])
        display = display.rename(columns={'carrier':'Carrier','rate_usd':'Rate (USD)','transit_days':'Transit (days)'})
        st.dataframe(display[['Recommendation','Carrier','Rate (USD)','Transit (days)']], use_container_width=True, hide_index=True)

elif page == 'Shipment Tracker':
    st.subheader('All shipments')
    search = st.text_input('Search by shipment ID, carrier, or port')
    view = shipments.copy()
    if search:
        mask = view.astype(str).apply(lambda col: col.str.contains(search, case=False, na=False)).any(axis=1); view = view[mask]
    st.dataframe(view[['shipment_id','carrier','origin_port','destination_port','container_type','departure_date','expected_arrival','delivered_date','status']], use_container_width=True, hide_index=True)
    with st.expander('＋ Add shipment'):
        with st.form('add_shipment'):
            x1,x2,x3 = st.columns(3)
            sid = x1.text_input('Shipment ID').strip().upper(); carrier = x2.selectbox('Carrier', sorted(rates.carrier.unique()))
            container = x3.selectbox('Container type', ['20ft','40ft'])
            x4,x5 = st.columns(2); origin = x4.selectbox('Origin port', sorted(rates.origin_port.unique())); destination = x5.selectbox('Destination port', sorted(rates.destination_port.unique()))
            x6,x7 = st.columns(2); departure = x6.date_input('Departure date', value=TODAY); arrival = x7.date_input('Expected arrival', value=TODAY)
            inv = st.number_input('Invoice amount (USD)', min_value=0.0, step=50.0)
            save = st.form_submit_button('Save shipment')
        if save:
            if not sid: st.error('Shipment ID is required.')
            elif arrival < departure: st.error('Expected arrival cannot be before departure.')
            else:
                try:
                    execute('INSERT INTO shipments(shipment_id,carrier,origin_port,destination_port,container_type,departure_date,expected_arrival,invoice_amount_usd) VALUES(?,?,?,?,?,?,?,?)', (sid,carrier,origin,destination,container,departure.isoformat(),arrival.isoformat(),inv))
                    st.success(f'Shipment {sid} added.'); st.rerun()
                except sqlite3.IntegrityError: st.error('That shipment ID already exists.')
    if user['role'] == 'Admin':
        with st.expander('Update shipment status'):
            ids = shipments.shipment_id.tolist()
            if ids:
                sid = st.selectbox('Shipment', ids, key='status_sid'); new_status = st.selectbox('Status', ['In Transit','Delayed','Delivered'])
                delivered = st.date_input('Delivery date (used only for Delivered)', value=TODAY, key='delivery_date')
                if st.button('Apply status update'):
                    if new_status == 'Delivered': execute('UPDATE shipments SET delivered_date=?, status_override=?, updated_at=CURRENT_TIMESTAMP WHERE shipment_id=?', (delivered.isoformat(), 'Delivered', sid))
                    else: execute('UPDATE shipments SET delivered_date="", status_override=?, updated_at=CURRENT_TIMESTAMP WHERE shipment_id=?', (new_status, sid))
                    st.success('Shipment status updated.'); st.rerun()

elif page == 'Invoice Checker':
    st.write('Compare an invoice with the matching carrier, route, and container contract rate.')
    if shipments.empty: st.info('Add a shipment first.')
    else:
        ids = shipments.shipment_id.tolist(); sid = st.selectbox('Shipment ID', ids)
        row = shipments[shipments.shipment_id == sid].iloc[0]
        matching = rates[(rates.carrier == row.carrier) & (rates.origin_port == row.origin_port) & (rates.destination_port == row.destination_port) & (rates.container_type == row.container_type)]
        amount = st.number_input('Invoice amount (USD)', min_value=0.0, value=float(row.invoice_amount_usd or 0), step=10.0)
        if matching.empty:
            st.warning('No matching contracted rate exists for this shipment. Add/confirm the carrier route rate before checking the invoice.')
        else:
            contracted = float(matching.iloc[0].rate_usd); delta = amount - contracted
            x,y,z = st.columns(3); x.metric('Contracted rate', f'${contracted:,.2f}'); y.metric('Invoice amount', f'${amount:,.2f}'); z.metric('Difference', f'${delta:,.2f}')
            if delta > 0.005: st.error(f'OVERCHARGED by ${delta:,.2f} USD.')
            elif delta < -0.005: st.success(f'Below contracted rate by ${abs(delta):,.2f} USD.')
            else: st.success('CORRECT — invoice matches the contracted rate.')
            if st.button('Save invoice amount to shipment'):
                execute('UPDATE shipments SET invoice_amount_usd=? WHERE shipment_id=?', (amount,sid)); st.success('Invoice amount saved.')
        uploaded = st.file_uploader('Or upload a CSV with shipment_id and invoice_amount_usd columns', type=['csv'])
        if uploaded:
            try:
                invdf = pd.read_csv(uploaded)
                if not {'shipment_id','invoice_amount_usd'}.issubset(invdf.columns): st.error('CSV must contain shipment_id and invoice_amount_usd columns.')
                else:
                    results=[]
                    for _, inv in invdf.iterrows():
                        sr = shipments[shipments.shipment_id == str(inv.shipment_id)]
                        if sr.empty: results.append({'shipment_id':inv.shipment_id,'result':'Unknown shipment','difference_usd':None}); continue
                        s=sr.iloc[0]; rr=rates[(rates.carrier==s.carrier)&(rates.origin_port==s.origin_port)&(rates.destination_port==s.destination_port)&(rates.container_type==s.container_type)]
                        if rr.empty: results.append({'shipment_id':inv.shipment_id,'result':'No contracted rate','difference_usd':None}); continue
                        diff=float(inv.invoice_amount_usd)-float(rr.iloc[0].rate_usd)
                        results.append({'shipment_id':inv.shipment_id,'contracted_usd':float(rr.iloc[0].rate_usd),'invoice_usd':float(inv.invoice_amount_usd),'result':'Overcharged' if diff>0.005 else ('Correct' if abs(diff)<=0.005 else 'Below rate'),'difference_usd':round(diff,2)})
                    st.dataframe(pd.DataFrame(results), use_container_width=True, hide_index=True)
            except Exception as e: st.error(f'Could not read invoice CSV: {e}')

elif page == 'Email Updates':
    st.write('Parse plain-text emails and apply valid rate or shipment updates. Emails without enough structured details are skipped for review.')
    default_path = DATA / 'sample_emails.txt'
    uploaded = st.file_uploader('Use the provided sample inbox or upload a .txt inbox', type=['txt'])
    if uploaded:
        inbox_text = uploaded.getvalue().decode('utf-8', errors='replace')
    else:
        inbox_text = default_path.read_text(encoding='utf-8')
    st.caption(f'{len(re.split(r"-{10,}", inbox_text))} email sections detected (including possible header text).')
    if st.button('Process inbox', type='primary'):
        emails = [e.strip() for e in re.split(r'\n-{10,}\s*\n', inbox_text) if re.search(r'(?im)^Subject:', e)]
        outcomes=[]
        for email in emails:
            subject_match = re.search(r'(?im)^Subject:\s*(.+)', email)
            subject = subject_match.group(1).strip() if subject_match else '(no subject)'
            email_hash = hashlib.sha256(email.encode('utf-8')).hexdigest()
            if not query('SELECT id FROM email_logs WHERE email_hash=?', (email_hash,)).empty:
                outcomes.append({'Email':subject,'Action':'Skipped','Details':'Already processed'}); continue
            sender = re.search(r'(?im)^From:\s*([^\s]+)', email)
            sender = sender.group(1).lower() if sender else ''
            carrier = None
            sender_map = {'oceanlinklines.com':'OceanLink Lines','bluewaveshipping.com':'BlueWave Shipping','globalmariner.com':'GlobalMariner','pacificstarline.com':'PacificStar Line','atlasseacarriers.com':'AtlasSea Carriers'}
            for domain, name in sender_map.items():
                if domain in sender: carrier=name; break
            action='Skipped'; details='No valid rate or shipment update detected.'
            # Rate updates: require a recognized carrier, route, container size and numeric USD amount.
            rate_signal = re.search(r'(?i)\b(rate|tariff|pricing)\b', subject+'\n'+email) and re.search(r'(?i)USD\s*([\d,]+(?:\.\d{1,2})?)', email)
            if rate_signal and carrier:
                amount_match = re.search(r'(?i)USD\s*([\d,]+(?:\.\d{1,2})?)', email)
                amount = float(amount_match.group(1).replace(',',''))
                ct = re.search(r'(?i)\b(20\s*ft|20ft|40\s*ft|40ft)\b', email)
                route = re.search(r'(?i)(?:rate\s*(?:for|on)|rate\s+update\s*-?\s*)\s*([A-Za-z ]+?)\s*(?:to|[-–/])\s*([A-Za-z ]+?)(?=,|\s*\(|\s*container|\s*is\s+now|\s+has\s+changed|\s*:\s*USD|\s+new\s+rate|\s*$)', email)
                # Alternate common sentence patterns, e.g. "Nhava Sheva to Los Angeles, 20ft container"
                if not route:
                    route = re.search(r'(?i)(Nhava\s+Sheva|Mundra|Chennai|Kolkata)\s*(?:to|[-–/])\s*(Los\s+Angeles|New\s+York|Savannah|Houston|Norfolk|Long\s+Beach)', email)
                if ct and route:
                    origin, dest = re.sub(r'\s+',' ',route.group(1)).strip(' ,.-'), re.sub(r'\s+',' ',route.group(2)).strip(' ,.-')
                    container = '20ft' if ct.group(1).replace(' ','').lower() == '20ft' else '40ft'
                    # Normalize common port spellings/case to names from the CSV.
                    canon = {str(v).lower():str(v) for v in rates.origin_port.tolist()+rates.destination_port.tolist()}
                    origin, dest = canon.get(origin.lower()), canon.get(dest.lower())
                    if origin and dest:
                        eff = re.search(r'(?i)effective\s+(?:from|on)\s+(\d{1,2}\s+[A-Za-z]{3}\s+\d{4}|\d{1,2}\s+[A-Za-z]+\s+\d{4})', email)
                        eff_date=''
                        if eff:
                            for fmt in ('%d %b %Y','%d %B %Y'):
                                try: eff_date=datetime.strptime(eff.group(1),fmt).date().isoformat(); break
                                except ValueError: pass
                        existing = query('SELECT id FROM rates WHERE carrier=? AND origin_port=? AND destination_port=? AND container_type=?',(carrier,origin,dest,container))
                        if not existing.empty:
                            execute('UPDATE rates SET rate_usd=?, effective_from=? WHERE carrier=? AND origin_port=? AND destination_port=? AND container_type=?',(amount,eff_date,carrier,origin,dest,container))
                        else:
                            transit = query('SELECT AVG(transit_days) AS n FROM rates WHERE origin_port=? AND destination_port=? AND container_type=?',(origin,dest,container))
                            days = int(round(transit.iloc[0]['n'])) if not pd.isna(transit.iloc[0]['n']) else 30
                            execute('INSERT INTO rates(carrier,origin_port,destination_port,container_type,rate_usd,transit_days,effective_from) VALUES(?,?,?,?,?,?,?)',(carrier,origin,dest,container,amount,days,eff_date))
                        action='Rate updated'; details=f'{carrier}: {origin} → {dest}, {container}, ${amount:,.2f} USD'+(f', effective {eff_date}' if eff_date else '')
                    else: details='Route could not be matched to known ports.'
                else: details='Missing carrier, route, container type, or USD amount.'
            else:
                # Shipment updates require ID and an explicit recognized status/delivery signal.
                sidm = re.search(r'(?i)\b(SHP\d+)\b', email)
                if sidm:
                    sid=sidm.group(1).upper(); lower=email.lower()
                    delivered = re.search(r'(?i)\b(delivered|delivery confirmation)\b', lower)
                    delayed = re.search(r'(?i)\b(delayed|delay)\b', lower)
                    transit = re.search(r'(?i)\b(in transit|departed .* currently in transit)\b', lower)
                    if delivered:
                        dm = re.search(r'(?i)\bon\s+(\d{1,2}\s+[A-Za-z]{3}\s+\d{4}|\d{1,2}\s+[A-Za-z]+\s+\d{4})', email)
                        dval=''
                        if dm:
                            for fmt in ('%d %b %Y','%d %B %Y'):
                                try: dval=datetime.strptime(dm.group(1),fmt).date().isoformat(); break
                                except ValueError: pass
                        if not dval: dval=TODAY.isoformat()
                        exists=query('SELECT shipment_id FROM shipments WHERE shipment_id=?',(sid,))
                        if not exists.empty:
                            execute('UPDATE shipments SET delivered_date=?,status_override="Delivered",updated_at=CURRENT_TIMESTAMP WHERE shipment_id=?',(dval,sid)); action='Shipment updated'; details=f'{sid} marked Delivered ({dval}).'
                        else: details=f'Shipment {sid} not found.'
                    elif delayed or transit:
                        new_status='Delayed' if delayed else 'In Transit'
                        exists=query('SELECT shipment_id FROM shipments WHERE shipment_id=?',(sid,))
                        if not exists.empty:
                            execute('UPDATE shipments SET delivered_date="",status_override=?,updated_at=CURRENT_TIMESTAMP WHERE shipment_id=?',(new_status,sid)); action='Shipment updated'; details=f'{sid} marked {new_status}.'
                        else: details=f'Shipment {sid} not found.'
                    else: details=f'No clear status found for {sid}.'
            execute('INSERT OR IGNORE INTO email_logs(email_subject,action,details,email_hash) VALUES(?,?,?,?)',(subject,action,details,email_hash))
            outcomes.append({'Email':subject,'Action':action,'Details':details})
        st.session_state['email_results']=pd.DataFrame(outcomes)
        st.success(f'Inbox processing complete: {sum(x["Action"] not in ("Skipped",) for x in outcomes)} update(s) applied; {sum(x["Action"] == "Skipped" for x in outcomes)} skipped.')
    if 'email_results' in st.session_state:
        st.dataframe(st.session_state['email_results'], use_container_width=True, hide_index=True)
    logs=query('SELECT email_subject, action, details, processed_at FROM email_logs ORDER BY id DESC')
    if not logs.empty:
        with st.expander('Processing history'): st.dataframe(logs,use_container_width=True,hide_index=True)

st.divider()
st.caption('Prototype note: rates and shipment changes are saved locally in SQLite. Demo credentials are for evaluation only; change them before any real deployment.')



