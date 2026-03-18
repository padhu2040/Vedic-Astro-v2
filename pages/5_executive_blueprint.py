import streamlit as st
import swisseph as swe
from datetime import datetime, time, date
from supabase import create_client

from astro_engine import get_location_coordinates, get_utc_offset, get_executive_blueprint

st.set_page_config(page_title="Executive Blueprint", layout="wide")

# --- SECURITY GATEKEEPER & GLOBAL SYNC INIT ---
if "user" not in st.session_state or st.session_state.user is None:
    st.warning("🔒 Please log in to access the Executive Blueprint.")
    st.stop()

user_id = st.session_state.user.id

if "global_active_profile" not in st.session_state:
    st.session_state.global_active_profile = None

@st.cache_resource
def init_connection():
    try: return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    except: return None

supabase = init_connection()

# --- SECURE PROFILE LOADER ---
def load_profiles_from_db():
    profiles = {}
    if supabase:
        try:
            # ONLY fetch profiles belonging to this user
            response = supabase.table("profiles").select("*").eq("user_id", user_id).execute()
            for row in response.data:
                try:
                    name, dob_str, tob_str, city = row["name"], row["dob"], row["tob"], row["city"]
                    parsed_dob = datetime.strptime(dob_str, "%Y-%m-%d").date()
                    try: parsed_tob = datetime.strptime(tob_str, "%H:%M:%S").time()
                    except ValueError: parsed_tob = datetime.strptime(tob_str, "%H:%M").time()
                    profiles[name] = {"dob": parsed_dob, "tob": parsed_tob, "city": city}
                except: pass
        except: pass
    return profiles

# --- SIDEBAR WITH GLOBAL SYNC ---
with st.sidebar:
    st.markdown("### Profile Selection")
    saved_profiles = load_profiles_from_db()
    profile_options = ["(No Profile Selected)"] + list(saved_profiles.keys())
    
    # GLOBAL SYNC 1: Find the Global Index
    try:
        default_idx = profile_options.index(st.session_state.global_active_profile)
    except ValueError:
        default_idx = 0

    # GLOBAL SYNC 2: Update Global Memory on Change
    def sync_profile_blueprint():
        selection = st.session_state._blueprint_profile_selector
        if selection != "(No Profile Selected)":
            st.session_state.global_active_profile = selection
        else:
            st.session_state.global_active_profile = None

    selected_profile = st.selectbox(
        "Load Saved Profile", 
        options=profile_options,
        index=default_idx,
        key="_blueprint_profile_selector",
        on_change=sync_profile_blueprint
    )
    
    if selected_profile != "(No Profile Selected)":
        def_n = selected_profile
        def_dob = saved_profiles[selected_profile]["dob"]
        def_tob = saved_profiles[selected_profile]["tob"]
        def_loc = saved_profiles[selected_profile]["city"]
    else:
        def_n, def_dob, def_tob, def_loc = "", date(2000, 1, 1), time(12, 0), ""

# --- MAIN CONTENT ---
st.title("Executive Blueprint")
st.markdown(f"<div style='color:#7f8c8d; margin-top:-15px; margin-bottom: 20px;'>Subject Identity: <b>{def_n if def_n else 'Pending Selection'}</b></div>", unsafe_allow_html=True)
st.divider()

if not def_n:
    st.info("Select a profile from the sidebar to generate the lifetime Executive Blueprint.")
else:
    with st.spinner("Analyzing natal architecture and processing timelines..."):
        try:
            lat_val, lon_val, tz_val = get_location_coordinates(def_loc)
        except:
            lat_val, lon_val, tz_val = 13.0827, 80.2707, "Asia/Kolkata"

        swe.set_sid_mode(swe.SIDM_LAHIRI)
        birth_dt = datetime.combine(def_dob, def_tob)
        offset = get_utc_offset(tz_val, birth_dt)
        ut_hour = (def_tob.hour + (def_tob.minute/60.0)) - offset
        jd_ut_natal = swe.julday(def_dob.year, def_dob.month, def_dob.day, ut_hour)

        bp = get_executive_blueprint(jd_ut_natal, lat_val, lon_val, "English")

        blueprint_html = f"""<style>
.bp-grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px; margin-bottom: 20px; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; }}
.bp-card {{ background: #ffffff; border: 1px solid #eaeaea; border-radius: 4px; padding: 20px; display: flex; flex-direction: column; box-shadow: 0 1px 2px rgba(0,0,0,0.01); }}
.bp-head {{ font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; color: #888; font-weight: 500; margin-bottom: 12px; border-bottom: 1px solid #f9f9f9; padding-bottom: 6px; display: flex; justify-content: space-between; }}
.bp-title {{ font-size: 17px; font-weight: 500; color: #2c3e50; margin-bottom: 8px; }}
.bp-desc {{ font-size: 13.5px; color: #444; line-height: 1.6; font-weight: 300; }}
.bp-metric {{ font-size: 11px; color: #27ae60; background: #f0fdf4; border: 1px solid #c6f6d5; padding: 3px 8px; border-radius: 2px; font-weight: 600; letter-spacing: 0.5px; }}
</style>
<div class="bp-grid">
<div class="bp-card" style="border-top: 3px solid #f39c12;">
<div class="bp-head"><span>01. The Leverage Score</span> <span>Free Will vs Destiny</span></div>
<div style="display:flex; align-items:center; margin-bottom:12px;">
<div style="font-size:38px; font-weight:300; color:#111; margin-right:15px; line-height:1;">{bp['leverage']['score']}<span style="font-size:16px; color:#888;">/100</span></div>
<div class="bp-metric" style="background:#fff3e0; color:#d35400; border-color:#ffe0b2;">{bp['leverage']['tag']}</div>
</div>
<div class="bp-desc">{bp['leverage']['desc']}</div>
</div>
<div class="bp-card" style="border-top: 3px solid #8e44ad;">
<div class="bp-head"><span>02. {bp['timeline']['title']}</span> <span>Vimshottari Dasha</span></div>
<div class="bp-desc" style="margin-top: 5px;">{bp['timeline']['desc']}</div>
</div>
<div class="bp-card" style="border-top: 3px solid #27ae60;">
<div class="bp-head"><span>03. Capital Generation</span> <span>2nd Lord: {bp['l2']}</span></div>
<div class="bp-title">{bp['wealth']['title']}</div>
<div class="bp-desc">{bp['wealth']['desc']}</div>
</div>
<div class="bp-card" style="border-top: 3px solid #27ae60;">
<div class="bp-head"><span>04. Real Estate & Assets</span> <span>4th Lord: {bp['l4']}</span></div>
<div class="bp-title">{bp['assets']['title']}</div>
<div class="bp-desc">{bp['assets']['desc']}</div>
</div>
<div class="bp-card" style="border-top: 3px solid #2980b9;">
<div class="bp-head"><span>05. Professional Trajectory</span> <span>10th Lord: {bp['l10']}</span></div>
<div class="bp-title">{bp['career']['title']}</div>
<div class="bp-desc">{bp['career']['desc']}</div>
</div>
<div class="bp-card" style="border-top: 3px solid #c0392b;">
<div class="bp-head"><span>06. Partnership Dynamics</span> <span>7th Lord: {bp['l7']}</span></div>
<div class="bp-title">{bp['partner']['title']}</div>
<div class="bp-desc">{bp['partner']['desc']}</div>
</div>
</div>
"""
        st.markdown(blueprint_html, unsafe_allow_html=True)
