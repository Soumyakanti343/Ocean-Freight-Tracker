import pandas as pd
import streamlit as st

from database.db import execute


def render_invoice_checker(shipments, rates):
    st.write(
        'Compare an invoice with the matching carrier, route, '
        'and container contract rate.'
    )

    if shipments.empty:
        st.info('Add a shipment first.')

    else:
        ids = shipments.shipment_id.tolist()
        sid = st.selectbox('Shipment ID', ids)

        row = shipments[
            shipments.shipment_id == sid
        ].iloc[0]

        matching = rates[
            (rates.carrier == row.carrier)
            & (rates.origin_port == row.origin_port)
            & (rates.destination_port == row.destination_port)
            & (rates.container_type == row.container_type)
        ]

        amount = st.number_input(
            'Invoice amount (USD)',
            min_value=0.0,
            value=float(row.invoice_amount_usd or 0),
            step=10.0
        )

        if matching.empty:
            st.warning(
                'No matching contracted rate exists for this shipment. '
                'Add/confirm the carrier route rate before checking '
                'the invoice.'
            )

        else:
            contracted = float(matching.iloc[0].rate_usd)
            delta = amount - contracted

            x, y, z = st.columns(3)

            x.metric(
                'Contracted rate',
                f'${contracted:,.2f}'
            )

            y.metric(
                'Invoice amount',
                f'${amount:,.2f}'
            )

            z.metric(
                'Difference',
                f'${delta:,.2f}'
            )

            if delta > 0.005:
                st.error(
                    f'OVERCHARGED by ${delta:,.2f} USD.'
                )

            elif delta < -0.005:
                st.success(
                    f'Below contracted rate by '
                    f'${abs(delta):,.2f} USD.'
                )

            else:
                st.success(
                    'CORRECT — invoice matches the contracted rate.'
                )

            if st.button('Save invoice amount to shipment'):
                execute(
                    '''
                    UPDATE shipments
                    SET invoice_amount_usd=?
                    WHERE shipment_id=?
                    ''',
                    (amount, sid)
                )

                st.success('Invoice amount saved.')

    # ---------- Invoice CSV Upload ----------
    uploaded = st.file_uploader(
        'Or upload a CSV with shipment_id and invoice_amount_usd columns',
        type=['csv']
    )

    if uploaded:
        try:
            invdf = pd.read_csv(uploaded)

            if not {
                'shipment_id',
                'invoice_amount_usd'
            }.issubset(invdf.columns):

                st.error(
                    'CSV must contain shipment_id and '
                    'invoice_amount_usd columns.'
                )

            else:
                results = []

                for _, inv in invdf.iterrows():
                    sr = shipments[
                        shipments.shipment_id == str(inv.shipment_id)
                    ]

                    if sr.empty:
                        results.append({
                            'shipment_id': inv.shipment_id,
                            'result': 'Unknown shipment',
                            'difference_usd': None
                        })

                        continue

                    s = sr.iloc[0]

                    rr = rates[
                        (rates.carrier == s.carrier)
                        & (rates.origin_port == s.origin_port)
                        & (rates.destination_port == s.destination_port)
                        & (rates.container_type == s.container_type)
                    ]

                    if rr.empty:
                        results.append({
                            'shipment_id': inv.shipment_id,
                            'result': 'No contracted rate',
                            'difference_usd': None
                        })

                        continue

                    diff = (
                        float(inv.invoice_amount_usd)
                        - float(rr.iloc[0].rate_usd)
                    )

                    results.append({
                        'shipment_id': inv.shipment_id,
                        'contracted_usd': float(
                            rr.iloc[0].rate_usd
                        ),
                        'invoice_usd': float(
                            inv.invoice_amount_usd
                        ),
                        'result': (
                            'Overcharged'
                            if diff > 0.005
                            else (
                                'Correct'
                                if abs(diff) <= 0.005
                                else 'Below rate'
                            )
                        ),
                        'difference_usd': round(diff, 2)
                    })

                st.dataframe(
                    pd.DataFrame(results),
                    use_container_width=True,
                    hide_index=True
                )

        except Exception as e:
            st.error(
                f'Could not read invoice CSV: {e}'
            )




            