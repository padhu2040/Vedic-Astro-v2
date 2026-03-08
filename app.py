import streamlit as st

st.set_page_config(page_title="Vedic Astro Engine", layout="wide")

# --- DEFINE PAGES WITH CORRECT FILE PATHS ---
# Setting the daily dashboard as the default landing page is a great SaaS practice
daily_page = st.Page(page="pages/2_daily_dashboard.py", title="Daily Dashboard", icon=":material/calendar_today:", default=True)

# Existing Premium Pages
horoscope_page = st.Page(page="pages/1_horoscope.py", title="Deep Horoscope", icon=":material/account_circle:")
porutham_page = st.Page(page="pages/3_porutham.py", title="Matchmaking (Porutham)", icon=":material/favorite_border:")

# NEW: Executive Blueprint Page
blueprint_page = st.Page(page="pages/5_executive_blueprint.py", title="Executive Blueprint", icon=":material/insights:")

# CRM Page
profile_page = st.Page(page="pages/4_saved_profiles.py", title="Saved Profiles", icon=":material/group:")

# --- UPDATED NAVIGATION ROUTER ---
pg = st.navigation(
    {
        "Daily Routine (Free)": [daily_page],
        "Deep Analysis (Premium)": [horoscope_page, blueprint_page, porutham_page],
        "Settings & CRM": [profile_page]
    }
)

pg.run()
