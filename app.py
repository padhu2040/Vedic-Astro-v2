import streamlit as st

st.set_page_config(page_title="Vedic Astro Engine", layout="wide")

# --- INITIALIZE GLOBAL SESSION STATE ---
if "user" not in st.session_state:
    st.session_state.user = None
if "global_active_profile" not in st.session_state:
    st.session_state.global_active_profile = None

# --- DEFINE ALL PAGES ---
# Free / Public Pages
login_page = st.Page(page="pages/0_login.py", title="Account / Login", icon=":material/login:")
daily_page = st.Page(page="pages/2_daily_dashboard.py", title="Daily Cosmos (Free)", icon=":material/calendar_today:")

# Premium / Locked Pages
horoscope_page = st.Page(page="pages/1_horoscope.py", title="Deep Horoscope", icon=":material/account_circle:")
blueprint_page = st.Page(page="pages/5_executive_blueprint.py", title="Executive Blueprint", icon=":material/insights:")
porutham_page = st.Page(page="pages/3_porutham.py", title="Strategic Synergy", icon=":material/favorite_border:")
profile_page = st.Page(page="pages/4_saved_profiles.py", title="CRM / Saved Profiles", icon=":material/group:")
circos_page = st.Page(page="pages/6_circular_chart.py", title="Circos Sandbox", icon=":material/data_exploration:")

# --- DYNAMIC FREEMIUM ROUTING ---
if st.session_state.user is None:
    # GUEST VIEW: They can see the Daily Dashboard, but must log in for the rest
    pg = st.navigation(
        {
            "Public Tools": [daily_page],
            "Access": [login_page]
        }
    )
else:
    # LOGGED IN VIEW: Full Access
    pg = st.navigation(
        {
            "Daily Routine": [daily_page],
            "Premium Analytics": [horoscope_page, blueprint_page, porutham_page],
            "Account & Settings": [profile_page, circos_page] # Put login at the bottom or remove if you add a logout button
        }
    )

pg.run()
