import streamlit as st

st.set_page_config(page_title="Vedic Astro Engine", layout="wide")

# Initialize session state for authentication
if "user" not in st.session_state:
    st.session_state.user = None

# --- DEFINE ALL PAGES ---
# Public Page
login_page = st.Page(page="pages/0_login.py", title="Secure Login", icon=":material/login:", default=True)

# Protected Pages
daily_page = st.Page(page="pages/2_daily_dashboard.py", title="Daily Dashboard", icon=":material/calendar_today:")
horoscope_page = st.Page(page="pages/1_horoscope.py", title="Deep Horoscope", icon=":material/account_circle:")
blueprint_page = st.Page(page="pages/5_executive_blueprint.py", title="Executive Blueprint", icon=":material/insights:")
porutham_page = st.Page(page="pages/3_porutham.py", title="Strategic Synergy", icon=":material/favorite_border:")
profile_page = st.Page(page="pages/4_saved_profiles.py", title="Saved Profiles", icon=":material/group:")
circos_page = st.Page(page="pages/6_circular_chart.py", title="Circos Sandbox", icon=":material/data_exploration:")

# --- DYNAMIC NAVIGATION ROUTING ---
if st.session_state.user is None:
    # IF NOT LOGGED IN: Only show the login page
    pg = st.navigation({"Authentication": [login_page]})
else:
    # IF LOGGED IN: Unlock the full application
    pg = st.navigation(
        {
            "Daily Routine": [daily_page],
            "Deep Analysis (Premium)": [horoscope_page, blueprint_page, porutham_page],
            "Settings & CRM": [profile_page],
            "Developer Sandbox": [circos_page]
        }
    )

pg.run()
