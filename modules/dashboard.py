import streamlit as st


def render_dashboard(shipments, rates):
    # ---------- Shipment Metrics ----------
    total = len(shipments)

    delivered = int(
        (shipments.status == 'Delivered').sum()
    )

    delayed = int(
        (shipments.status == 'Delayed').sum()
    )

    transit = int(
        (shipments.status == 'In Transit').sum()
    )

    a, b, c, d = st.columns(4)

    a.metric('Total shipments', total)
    b.metric('Delivered', delivered)
    c.metric('In transit', transit)
    d.metric('Delayed', delayed)

    # ---------- Shipment Status Overview ----------
    st.subheader('Shipment status overview')

    if total:
        st.bar_chart(
            shipments['status']
            .value_counts()
            .reindex(
                ['In Transit', 'Delivered', 'Delayed'],
                fill_value=0
            )
        )

    # ---------- Upcoming and Delayed Shipments ----------
    st.subheader('Upcoming and delayed shipments')

    st.dataframe(
        shipments[
            [
                'shipment_id',
                'carrier',
                'origin_port',
                'destination_port',
                'container_type',
                'expected_arrival',
                'status'
            ]
        ],
        use_container_width=True,
        hide_index=True
    )

    st.caption(
        f"{len(rates)} carrier rate combinations "
        "loaded from the supplied CSV."
    )



    