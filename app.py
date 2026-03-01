import streamlit as st

st.set_page_config(page_title="Vedic Astro Engine", layout="wide")

daily_page = st.Page(page="pages/3_daily_insights.py", title="Daily Insights", icon=":material/calendar_today:", default=True)
horoscope_page = st.Page(page="pages/1_horoscope.py", title="Deep Horoscope", icon=":material/account_circle:")
porutham_page = st.Page(page="pages/2_porutham.py", title="Matchmaking (Porutham)", icon=":material/favorite_border:")

# NEW: The Profile Vault
profile_page = st.Page(page="pages/4_saved_profiles.py", title="Saved Profiles", icon=":material/group:")

# Updated Navigation Router
pg = st.navigation(
    {
        "Daily Routine (Free)": [daily_page],
        "Deep Analysis (Premium)": [horoscope_page, porutham_page],
        "Settings & CRM": [profile_page] # Added here!
    }
)

pg.run()
