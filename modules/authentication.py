import streamlit as st
from database.db import query, verify_password


def render_login() :
    """Display the login page and authenticate the user."""

    if 'auth_user' not in st.session_state:
        st.session_state.auth_user = None

    if st.session_state.auth_user:
        return

    st.markdown("# 🚢 Ocean Freight Tracker")

    st.caption(
        'A practical workspace for carrier rates, shipments, '
        'invoices, and email updates.'
    )

    left, right = st.columns([1, 1.3])

    with left:
        st.subheader('Sign in')

        with st.form('login_form'):
            username = st.text_input('Username')
            password = st.text_input(
                'Password',
                type='password'
            )

            submitted = st.form_submit_button(
                'Login',
                use_container_width=True
            )

        if submitted:
            users = query(
                'SELECT * FROM users WHERE username=?',
                (username.strip(),)
            )

            if (
                not users.empty
                and verify_password(
                    password,
                    users.iloc[0]['password_hash']
                )
            ):
                st.session_state.auth_user = {
                    'username': username.strip(),
                    'role': users.iloc[0]['role']
                }

                st.rerun()

            else:
                st.error('Invalid username or password.')

    with right:
        st.info(
            '**Demo credentials**\n\n'
            'Admin: `admin` / `Admin@123`\n\n'
            'User: `user` / `User@123`\n\n'
            'Passwords are stored as salted PBKDF2-HMAC-SHA256 '
            'hashes. Change demo credentials before using this '
            'beyond a local prototype.'
        )

    st.stop()




