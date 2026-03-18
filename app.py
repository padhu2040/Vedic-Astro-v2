import streamlit as st
from supabase import create_client

st.set_page_config(page_title="Vedic Astro Engine", layout="wide")

# --- DATABASE CONNECTION ---
@st.cache_resource
def init_connection():
    try: return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    except: return None

supabase = init_connection()

# --- INITIALIZE GLOBAL SESSION STATE ---
if "user" not in st.session_state:
    st.session_state.user = None
if "global_active_profile" not in st.session_state:
    st.session_state.global_active_profile = None
if "is_premium" not in st.session_state:
    st.session_state.is_premium = False

# --- 💎 CHECK PREMIUM STATUS ---
if st.session_state.user and supabase:
    try:
        # Check the database to see if this specific user has paid
        sub_check = supabase.table("user_subscriptions").select("is_premium").eq("user_id", st.session_state.user.id).execute()
        if sub_check.data and len(sub_check.data) > 0:
            st.session_state.is_premium = sub_check.data[0]["is_premium"]
        else:
            st.session_state.is_premium = False
    except Exception:
        pass

# --- DEFINE ALL PAGES ---
login_page = st.Page(page="pages/0_login.py", title="Account / Login", icon=":material/login:")
daily_page = st.Page(page="pages/2_daily_dashboard.py", title="Daily Cosmos (Free)", icon=":material/calendar_today:")
horoscope_page = st.Page(page="pages/1_horoscope.py", title="Deep Horoscope", icon=":material/account_circle:")
blueprint_page = st.Page(page="pages/5_executive_blueprint.py", title="Executive Blueprint", icon=":material/insights:")
porutham_page = st.Page(page="pages/3_porutham.py", title="Strategic Synergy", icon=":material/favorite_border:")
profile_page = st.Page(page="pages/4_saved_profiles.py", title="CRM / Saved Profiles", icon=":material/group:")
circos_page = st.Page(page="pages/6_circular_chart.py", title="Circos Sandbox", icon=":material/data_exploration:")

# --- DYNAMIC FREEMIUM ROUTING ---
if st.session_state.user is None:
    pg = st.navigation({"Public Tools": [daily_page], "Access": [login_page]})
else:
    pg = st.navigation({
        "Daily Routine": [daily_page],
        "Premium Analytics": [horoscope_page, blueprint_page, porutham_page],
        "Account & Settings": [profile_page, circos_page] 
    })

pg.run()
