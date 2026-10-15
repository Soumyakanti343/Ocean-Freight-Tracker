import sqlite3
import streamlit as st

from database.db import execute, status_for, TODAY


def render_shipment_tracker(shipments, rates, user):
    # ---------- All Shipments ----------
    st.subheader('All shipments')

    search = st.text_input(
        'Search by shipment ID, carrier, or port'
    )

    view = shipments.copy()

    if search:
        mask = view.astype(str).apply(
            lambda col: col.str.contains(
                search,
                case=False,
                na=False
            )
        ).any(axis=1)

        view = view[mask]

    st.dataframe(
        view[
            [
                'shipment_id',
                'carrier',
                'origin_port',
                'destination_port',
                'container_type',
                'departure_date',
                'expected_arrival',
                'delivered_date',
                'status'
            ]
        ],
        use_container_width=True,
        hide_index=True
    )

    # ---------- Add Shipment ----------
    with st.expander('＋ Add shipment'):
        with st.form('add_shipment'):
            x1, x2, x3 = st.columns(3)

            sid = x1.text_input(
                'Shipment ID'
            ).strip().upper()

            carrier = x2.selectbox(
                'Carrier',
                sorted(rates.carrier.unique())
            )

            container = x3.selectbox(
                'Container type',
                ['20ft', '40ft']
            )

            x4, x5 = st.columns(2)

            origin = x4.selectbox(
                'Origin port',
                sorted(rates.origin_port.unique())
            )

            destination = x5.selectbox(
                'Destination port',
                sorted(rates.destination_port.unique())
            )

            x6, x7 = st.columns(2)

            departure = x6.date_input(
                'Departure date',
                value=TODAY
            )

            arrival = x7.date_input(
                'Expected arrival',
                value=TODAY
            )

            inv = st.number_input(
                'Invoice amount (USD)',
                min_value=0.0,
                step=50.0
            )

            save = st.form_submit_button(
                'Save shipment'
            )

        if save:
            if not sid:
                st.error('Shipment ID is required.')

            elif arrival < departure:
                st.error(
                    'Expected arrival cannot be before departure.'
                )

            else:
                try:
                    execute(
                        '''
                        INSERT INTO shipments(
                            shipment_id,
                            carrier,
                            origin_port,
                            destination_port,
                            container_type,
                            departure_date,
                            expected_arrival,
                            invoice_amount_usd
                        )
                        VALUES(?,?,?,?,?,?,?,?)
                        ''',
                        (
                            sid,
                            carrier,
                            origin,
                            destination,
                            container,
                            departure.isoformat(),
                            arrival.isoformat(),
                            inv
                        )
                    )

                    st.success(
                        f'Shipment {sid} added.'
                    )

                    st.rerun()

                except sqlite3.IntegrityError:
                    st.error(
                        'That shipment ID already exists.'
                    )

    # ---------- Admin: Update Shipment Status ----------
    if user['role'] == 'Admin':
        with st.expander('Update shipment status'):
            ids = shipments.shipment_id.tolist()

            if ids:
                sid = st.selectbox(
                    'Shipment',
                    ids,
                    key='status_sid'
                )

                new_status = st.selectbox(
                    'Status',
                    ['In Transit', 'Delayed', 'Delivered']
                )

                delivered = st.date_input(
                    'Delivery date (used only for Delivered)',
                    value=TODAY,
                    key='delivery_date'
                )

                if st.button('Apply status update'):
                    if new_status == 'Delivered':
                        execute(
                            '''
                            UPDATE shipments
                            SET delivered_date=?,
                                status_override=?,
                                updated_at=CURRENT_TIMESTAMP
                            WHERE shipment_id=?
                            ''',
                            (
                                delivered.isoformat(),
                                'Delivered',
                                sid
                            )
                        )

                    else:
                        execute(
                            '''
                            UPDATE shipments
                            SET delivered_date="",
                                status_override=?,
                                updated_at=CURRENT_TIMESTAMP
                            WHERE shipment_id=?
                            ''',
                            (
                                new_status,
                                sid
                            )
                        )

                    st.success('Shipment status updated.')

                    st.rerun()





                    