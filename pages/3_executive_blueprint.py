import streamlit as st
import swisseph as swe
from datetime import datetime, time, date
from supabase import create_client

from astro_engine import get_location_coordinates, get_utc_offset, get_executive_blueprint

st.set_page_config(page_title="Executive Blueprint", layout="centered")

@st.cache_resource
def init_connection():
    try: return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    except: return None

supabase = init_connection()

def load_profiles_from_db():
    profiles = {}
    if supabase:
        try:
            response = supabase.table("profiles").select("*").execute()
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

with st.sidebar:
    st.markdown("### Profile Selection")
    saved_profiles = load_profiles_from_db()
    profile_options = ["(No Profile Selected)"] + list(saved_profiles.keys())
    selected_profile = st.selectbox("Load Saved Profile", profile_options)
    
    if selected_profile != "(No Profile Selected)":
        def_n = selected_profile
        def_dob = saved_profiles[selected_profile]["dob"]
        def_tob = saved_profiles[selected_profile]["tob"]
        def_loc = saved_profiles[selected_profile]["city"]
    else:
        def_n, def_dob, def_tob, def_loc = "", date(2000, 1, 1), time(12, 0), ""

st.title("Executive Blueprint")

col1, col2 = st.columns([1, 1])
with col1:
    LANG = st.selectbox("Language", ["English", "Tamil"])
with col2:
    st.markdown(f"<div style='text-align:right; margin-top:30px; font-size:14px; color:#7f8c8d;'>Subject: <b>{def_n if def_n else 'Select Profile'}</b></div>", unsafe_allow_html=True)

st.divider()

if not def_n:
    st.info("Select a profile from the sidebar to generate the lifetime Executive Blueprint.")
else:
    with st.spinner("Analyzing natal architecture..."):
        try:
            lat_val, lon_val, tz_val = get_location_coordinates(def_loc)
        except:
            lat_val, lon_val, tz_val = 13.0827, 80.2707, "Asia/Kolkata"

        swe.set_sid_mode(swe.SIDM_LAHIRI)
        birth_dt = datetime.combine(def_dob, def_tob)
        offset = get_utc_offset(tz_val, birth_dt)
        ut_hour = (def_tob.hour + (def_tob.minute/60.0)) - offset
        jd_ut_natal = swe.julday(def_dob.year, def_dob.month, def_dob.day, ut_hour)

        bp = get_executive_blueprint(jd_ut_natal, lat_val, lon_val, LANG)

        # Labels setup based on language
        l_cap = "Capital & Asset Generation" if LANG=="English" else "மூலதனம் மற்றும் சொத்து உருவாக்கம்"
        l_car = "Professional Trajectory" if LANG=="English" else "தொழில் பாதை"
        l_par = "Partnership Dynamics" if LANG=="English" else "கூட்டாண்மை"
        l_net = "Networking & Alliances" if LANG=="English" else "நட்பு மற்றும் கூட்டமைப்பு"
        l_lev = "The Leverage Score" if LANG=="English" else "திறன் மதிப்பெண்"

        blueprint_html = f"""<style>
.bp-card {{ background: #ffffff; border: 1px solid #eaeaea; border-radius: 4px; padding: 24px; margin-bottom: 20px; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; box-shadow: 0 1px 2px rgba(0,0,0,0.01); }}
.bp-head {{ font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; color: #888; font-weight: 500; margin-bottom: 8px; border-bottom: 1px solid #f9f9f9; padding-bottom: 6px; display: flex; justify-content: space-between; }}
.bp-title {{ font-size: 18px; font-weight: 500; color: #2c3e50; margin-bottom: 12px; }}
.bp-desc {{ font-size: 14px; color: #444; line-height: 1.6; font-weight: 300; }}
.bp-metric {{ font-size: 11px; color: #27ae60; background: #f0fdf4; border: 1px solid #c6f6d5; padding: 2px 6px; border-radius: 2px; font-weight: 600; }}
</style>

<div class="bp-card" style="border-left: 3px solid #27ae60;">
<div class="bp-head"><span>01. {l_cap}</span> <span>Driver: {bp['l2']} / {bp['l11']}</span></div>
<div class="bp-title">{bp['wealth']['title']}</div>
<div class="bp-desc">{bp['wealth']['desc']}</div>
</div>

<div class="bp-card" style="border-left: 3px solid #2980b9;">
<div class="bp-head"><span>02. {l_car}</span> <span>Driver: {bp['l10']}</span></div>
<div class="bp-title">{bp['career']['title']}</div>
<div class="bp-desc">{bp['career']['desc']}</div>
</div>

<div class="bp-card" style="border-left: 3px solid #8e44ad;">
<div class="bp-head"><span>03. {l_par}</span> <span>Driver: {bp['l7']}</span></div>
<div class="bp-title">{bp['partner']['title']}</div>
<div class="bp-desc">{bp['partner']['desc']}</div>
</div>

<div class="bp-card" style="border-left: 3px solid #f39c12;">
<div class="bp-head"><span>04. {l_lev}</span> <span>Free Will vs Destiny</span></div>
<div style="display:flex; align-items:center; margin-bottom:12px;">
<div style="font-size:32px; font-weight:300; color:#111; margin-right:15px;">{bp['leverage']['score']}<span style="font-size:16px; color:#888;">/100</span></div>
<div class="bp-metric">HIGH AGENCY</div>
</div>
<div class="bp-desc">{bp['leverage']['desc']}</div>
</div>
"""
        st.markdown(blueprint_html, unsafe_allow_html=True)
