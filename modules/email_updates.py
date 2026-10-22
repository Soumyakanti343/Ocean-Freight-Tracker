import hashlib
import re
from datetime import datetime

import pandas as pd
import streamlit as st

from database.db import query, execute, TODAY


def render_email_updates(rates):
    st.write(
        'Parse plain-text emails and apply valid rate or shipment updates. '
        'Emails without enough structured details are skipped for review.'
    )

    default_path = (
        __import__('pathlib').Path(__file__).resolve().parent.parent
        / 'data'
        / 'sample_emails.txt'
    )

    uploaded = st.file_uploader(
        'Use the provided sample inbox or upload a .txt inbox',
        type=['txt']
    )

    if uploaded:
        inbox_text = uploaded.getvalue().decode(
            'utf-8',
            errors='replace'
        )
    else:
        inbox_text = default_path.read_text(encoding='utf-8')

    st.caption(
        f'{len(re.split(r"-{10,}", inbox_text))} '
        'email sections detected (including possible header text).'
    )

    if st.button('Process inbox', type='primary'):
        emails = [
            e.strip()
            for e in re.split(r'\n-{10,}\s*\n', inbox_text)
            if re.search(r'(?im)^Subject:', e)
        ]

        outcomes = []

        for email in emails:
            subject_match = re.search(
                r'(?im)^Subject:\s*(.+)',
                email
            )

            subject = (
                subject_match.group(1).strip()
                if subject_match
                else '(no subject)'
            )

            email_hash = hashlib.sha256(
                email.encode('utf-8')
            ).hexdigest()

            if not query(
                'SELECT id FROM email_logs WHERE email_hash=?',
                (email_hash,)
            ).empty:

                outcomes.append({
                    'Email': subject,
                    'Action': 'Skipped',
                    'Details': 'Already processed'
                })

                continue

            sender = re.search(
                r'(?im)^From:\s*([^\s]+)',
                email
            )

            sender = (
                sender.group(1).lower()
                if sender
                else ''
            )

            carrier = None

            sender_map = {
                'oceanlinklines.com': 'OceanLink Lines',
                'bluewaveshipping.com': 'BlueWave Shipping',
                'globalmariner.com': 'GlobalMariner',
                'pacificstarline.com': 'PacificStar Line',
                'atlasseacarriers.com': 'AtlasSea Carriers'
            }

            for domain, name in sender_map.items():
                if domain in sender:
                    carrier = name
                    break

            action = 'Skipped'
            details = 'No valid rate or shipment update detected.'

            # ---------- Rate Updates ----------
            rate_signal = (
                re.search(
                    r'(?i)\b(rate|tariff|pricing)\b',
                    subject + '\n' + email
                )
                and re.search(
                    r'(?i)USD\s*([\d,]+(?:\.\d{1,2})?)',
                    email
                )
            )

            if rate_signal and carrier:
                amount_match = re.search(
                    r'(?i)USD\s*([\d,]+(?:\.\d{1,2})?)',
                    email
                )

                amount = float(
                    amount_match.group(1).replace(',', '')
                )

                ct = re.search(
                    r'(?i)\b(20\s*ft|20ft|40\s*ft|40ft)\b',
                    email
                )

                route = re.search(
                    r'(?i)(?:rate\s*(?:for|on)|rate\s+update\s*-?\s*)'
                    r'\s*([A-Za-z ]+?)\s*(?:to|[-–/])\s*'
                    r'([A-Za-z ]+?)'
                    r'(?=,|\s*\(|\s*container|\s*is\s+now|'
                    r'\s+has\s+changed|\s*:\s*USD|'
                    r'\s+new\s+rate|\s*$)',
                    email
                )

                # Alternate common sentence patterns.
                if not route:
                    route = re.search(
                        r'(?i)(Nhava\s+Sheva|Mundra|Chennai|Kolkata)'
                        r'\s*(?:to|[-–/])\s*'
                        r'(Los\s+Angeles|New\s+York|Savannah|'
                        r'Houston|Norfolk|Long\s+Beach)',
                        email
                    )

                if ct and route:
                    origin = re.sub(
                        r'\s+',
                        ' ',
                        route.group(1)
                    ).strip(' ,.-')

                    dest = re.sub(
                        r'\s+',
                        ' ',
                        route.group(2)
                    ).strip(' ,.-')

                    container = (
                        '20ft'
                        if ct.group(1).replace(' ', '').lower() == '20ft'
                        else '40ft'
                    )

                    # Normalize port names against the database rates.
                    canon = {
                        str(v).lower(): str(v)
                        for v in (
                            rates.origin_port.tolist()
                            + rates.destination_port.tolist()
                        )
                    }

                    origin = canon.get(origin.lower())
                    dest = canon.get(dest.lower())

                    if origin and dest:
                        eff = re.search(
                            r'(?i)effective\s+(?:from|on)\s+'
                            r'(\d{1,2}\s+[A-Za-z]{3}\s+\d{4}|'
                            r'\d{1,2}\s+[A-Za-z]+\s+\d{4})',
                            email
                        )

                        eff_date = ''

                        if eff:
                            for fmt in (
                                '%d %b %Y',
                                '%d %B %Y'
                            ):
                                try:
                                    eff_date = datetime.strptime(
                                        eff.group(1),
                                        fmt
                                    ).date().isoformat()

                                    break

                                except ValueError:
                                    pass

                        existing = query(
                            '''
                            SELECT id FROM rates
                            WHERE carrier=?
                              AND origin_port=?
                              AND destination_port=?
                              AND container_type=?
                            ''',
                            (
                                carrier,
                                origin,
                                dest,
                                container
                            )
                        )

                        if not existing.empty:
                            execute(
                                '''
                                UPDATE rates
                                SET rate_usd=?, effective_from=?
                                WHERE carrier=?
                                  AND origin_port=?
                                  AND destination_port=?
                                  AND container_type=?
                                ''',
                                (
                                    amount,
                                    eff_date,
                                    carrier,
                                    origin,
                                    dest,
                                    container
                                )
                            )

                        else:
                            transit = query(
                                '''
                                SELECT AVG(transit_days) AS n
                                FROM rates
                                WHERE origin_port=?
                                  AND destination_port=?
                                  AND container_type=?
                                ''',
                                (
                                    origin,
                                    dest,
                                    container
                                )
                            )

                            days = (
                                int(round(transit.iloc[0]['n']))
                                if not pd.isna(transit.iloc[0]['n'])
                                else 30
                            )

                            execute(
                                '''
                                INSERT INTO rates(
                                    carrier,
                                    origin_port,
                                    destination_port,
                                    container_type,
                                    rate_usd,
                                    transit_days,
                                    effective_from
                                )
                                VALUES(?,?,?,?,?,?,?)
                                ''',
                                (
                                    carrier,
                                    origin,
                                    dest,
                                    container,
                                    amount,
                                    days,
                                    eff_date
                                )
                            )

                        action = 'Rate updated'

                        details = (
                            f'{carrier}: {origin} → {dest}, '
                            f'{container}, ${amount:,.2f} USD'
                            + (
                                f', effective {eff_date}'
                                if eff_date
                                else ''
                            )
                        )

                    else:
                        details = (
                            'Route could not be matched to known ports.'
                        )

                else:
                    details = (
                        'Missing carrier, route, container type, '
                        'or USD amount.'
                    )

            else:
                # ---------- Shipment Updates ----------
                sidm = re.search(
                    r'(?i)\b(SHP\d+)\b',
                    email
                )

                if sidm:
                    sid = sidm.group(1).upper()
                    lower = email.lower()

                    delivered = re.search(
                        r'(?i)\b(delivered|delivery confirmation)\b',
                        lower
                    )

                    delayed = re.search(
                        r'(?i)\b(delayed|delay)\b',
                        lower
                    )

                    transit = re.search(
                        r'(?i)\b(in transit|departed .* currently in transit)\b',
                        lower
                    )

                    if delivered:
                        dm = re.search(
                            r'(?i)\bon\s+'
                            r'(\d{1,2}\s+[A-Za-z]{3}\s+\d{4}|'
                            r'\d{1,2}\s+[A-Za-z]+\s+\d{4})',
                            email
                        )

                        dval = ''

                        if dm:
                            for fmt in (
                                '%d %b %Y',
                                '%d %B %Y'
                            ):
                                try:
                                    dval = datetime.strptime(
                                        dm.group(1),
                                        fmt
                                    ).date().isoformat()

                                    break

                                except ValueError:
                                    pass

                        if not dval:
                            dval = TODAY.isoformat()

                        exists = query(
                            '''
                            SELECT shipment_id
                            FROM shipments
                            WHERE shipment_id=?
                            ''',
                            (sid,)
                        )

                        if not exists.empty:
                            execute(
                                '''
                                UPDATE shipments
                                SET delivered_date=?,
                                    status_override="Delivered",
                                    updated_at=CURRENT_TIMESTAMP
                                WHERE shipment_id=?
                                ''',
                                (dval, sid)
                            )

                            action = 'Shipment updated'
                            details = (
                                f'{sid} marked Delivered ({dval}).'
                            )

                        else:
                            details = f'Shipment {sid} not found.'

                    elif delayed or transit:
                        new_status = (
                            'Delayed'
                            if delayed
                            else 'In Transit'
                        )

                        exists = query(
                            '''
                            SELECT shipment_id
                            FROM shipments
                            WHERE shipment_id=?
                            ''',
                            (sid,)
                        )

                        if not exists.empty:
                            execute(
                                '''
                                UPDATE shipments
                                SET delivered_date="",
                                    status_override=?,
                                    updated_at=CURRENT_TIMESTAMP
                                WHERE shipment_id=?
                                ''',
                                (new_status, sid)
                            )

                            action = 'Shipment updated'
                            details = (
                                f'{sid} marked {new_status}.'
                            )

                        else:
                            details = f'Shipment {sid} not found.'

                    else:
                        details = (
                            f'No clear status found for {sid}.'
                        )

            # ---------- Save Processing Log ----------
            execute(
                '''
                INSERT OR IGNORE INTO email_logs(
                    email_subject,
                    action,
                    details,
                    email_hash
                )
                VALUES(?,?,?,?)
                ''',
                (
                    subject,
                    action,
                    details,
                    email_hash
                )
            )

            outcomes.append({
                'Email': subject,
                'Action': action,
                'Details': details
            })

        st.session_state['email_results'] = pd.DataFrame(
            outcomes
        )

        st.success(
            f'Inbox processing complete: '
            f'{sum(x["Action"] not in ("Skipped",) for x in outcomes)} '
            f'update(s) applied; '
            f'{sum(x["Action"] == "Skipped" for x in outcomes)} skipped.'
        )

    # ---------- Processing Results ----------
    if 'email_results' in st.session_state:
        st.dataframe(
            st.session_state['email_results'],
            width = "stretch",    # use_container_width=True,
            hide_index=True
        )

    # ---------- Processing History ----------
    logs = query(
        '''
        SELECT email_subject, action, details, processed_at
        FROM email_logs
        ORDER BY id DESC
        '''
    )

    if not logs.empty:
        with st.expander('Processing history'):
            st.dataframe(
                logs,
                width = "stretch",    # use_container_width=True,
                hide_index=True
            )




            
