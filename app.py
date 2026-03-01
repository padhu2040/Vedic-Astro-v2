import streamlit as st

# Configure the main window
st.set_page_config(page_title="Vedic Astro Engine", layout="wide")

# Define the pages using native Material Icons
horoscope_page = st.Page(
    page="pages/1_horoscope.py",
    title="Deep Horoscope",
    icon=":material/account_circle:", # Minimalist user icon
    default=True
)

porutham_page = st.Page(
    page="pages/2_porutham.py",
    title="Matchmaking (Porutham)",
    icon=":material/favorite_border:" # Minimalist heart outline
)

daily_page = st.Page(
    page="pages/2_porutham.py", # Temporarily pointing to placeholder
    title="Daily Transits",
    icon=":material/calendar_today:" # Minimalist calendar
)

# Build the custom navigation menu
pg = st.navigation(
    {
        "Core Engines": [horoscope_page, porutham_page],
        "Daily Insights": [daily_page]
    }
)

# Run the selected page
pg.run()
