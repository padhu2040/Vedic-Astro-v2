import streamlit as st

st.set_page_config(page_title="Vedic Astro Engine", layout="wide")

# Make Daily Insights the default landing page
daily_page = st.Page(
    page="pages/3_daily_insights.py",
    title="Daily Insights",
    icon=":material/calendar_today:",
    default=True 
)

horoscope_page = st.Page(
    page="pages/1_horoscope.py",
    title="Deep Horoscope",
    icon=":material/account_circle:"
)

porutham_page = st.Page(
    page="pages/2_porutham.py",
    title="Matchmaking (Porutham)",
    icon=":material/favorite_border:" 
)

pg = st.navigation(
    {
        "Daily Routine (Free)": [daily_page],
        "Deep Analysis (Premium)": [horoscope_page, porutham_page]
    }
)

pg.run()
