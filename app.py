import streamlit as st

# Configure the main window
st.set_page_config(page_title="Vedic Astro Engine", layout="wide")

# Define the pages using native Material Icons
horoscope_page = st.Page(
    page="pages/1_horoscope.py",
    title="Deep Horoscope",
    icon=":material/account_circle:", 
    default=True
)

porutham_page = st.Page(
    page="pages/2_porutham.py",
    title="Matchmaking (Porutham)",
    icon=":material/favorite_border:" 
)

# NEW: Link the Daily Insights page
daily_page = st.Page(
    page="pages/3_daily_insights.py",
    title="Daily Insights",
    icon=":material/calendar_today:" 
)

# Build the custom navigation menu
pg = st.navigation(
    {
        "Core Engines": [horoscope_page, porutham_page],
        "Daily Routine": [daily_page]  # This adds the new section to the sidebar!
    }
)

# Run the selected page
pg.run()
