import streamlit as st


def render_rate_search(rates):
    st.write(
        'Compare available carrier rates by route and container size.'
    )

    c1, c2, c3 = st.columns(3)

    origins = sorted(
        rates.origin_port.dropna().unique().tolist()
    )

    destinations = sorted(
        rates.destination_port.dropna().unique().tolist()
    )

    origin = c1.selectbox('Origin port', origins)

    destination = c2.selectbox(
        'Destination port',
        destinations
    )

    container = c3.selectbox(
        'Container type',
        ['20ft', '40ft']
    )

    found = rates[
        (rates.origin_port == origin)
        & (rates.destination_port == destination)
        & (rates.container_type == container)
    ].sort_values('rate_usd')

    if found.empty:
        st.warning(
            'No carrier rates found for this route and container type.'
        )

    else:
        cheapest = found.iloc[0]

        st.success(
            f"Cheapest option: {cheapest.carrier} · "
            f"${cheapest.rate_usd:,.2f} USD · "
            f"{int(cheapest.transit_days)} transit days"
        )

        display = found.copy()

        display.insert(
            0,
            'Recommendation',
            [
                '⭐ Cheapest' if i == 0 else ''
                for i in range(len(display))
            ]
        )

        display = display.rename(
            columns={
                'carrier': 'Carrier',
                'rate_usd': 'Rate (USD)',
                'transit_days': 'Transit (days)'
            }
        )

        st.dataframe(
            display[
                [
                    'Recommendation',
                    'Carrier',
                    'Rate (USD)',
                    'Transit (days)'
                ]
            ],
            use_container_width=True,
            hide_index=True
        )




        