import streamlit as st
import swisseph as swe
from datetime import datetime, timezone, time
from supabase import create_client

# --- IMPORTS FROM OUR CUSTOM ENGINE ---
from astro_engine import (
    get_location_coordinates, get_utc_offset, get_daily_executive_weather,
    ZODIAC_TA, ZODIAC
)

st.set_page_config(page_title="Daily Executive Weather", layout="centered")

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

# --- SIDEBAR: FAST PROFILE LOADER ---
with st.sidebar:
    st.markdown("### ⚡ Daily Dashboard")
    LANG = st.radio("Language / மொழி", ["English", "Tamil"], horizontal=True)
    st.divider()
    
    st.markdown("### 👤 Select Profile")
    saved_profiles = load_profiles_from_db()
    profile_options = ["✨ Select Profile..."] + list(saved_profiles.keys())
    selected_profile = st.selectbox("Load Saved Profile", profile_options)
    
    if selected_profile != "✨ Select Profile...":
        def_n = selected_profile
        def_dob = saved_profiles[selected_profile]["dob"]
        def_tob = saved_profiles[selected_profile]["tob"]
        def_loc = saved_profiles[selected_profile]["city"]
    else:
        def_n, def_dob, def_tob, def_loc = "", datetime(2000, 1, 1).date(), time(12, 0), ""

    # Hidden inputs to keep the logic intact without cluttering the daily UI
    name_in = st.text_input("Name", value=def_n, disabled=True) if def_n else None
    
    calc_btn = st.button("Generate Today's Strategy", type="primary", use_container_width=True)

# --- MAIN DASHBOARD UI ---
st.title("⚡ Daily Executive Weather")
st.markdown(f"**Live Tactical Strategy for:** {datetime.now().strftime('%B %d, %Y')}")
st.divider()

if not def_n:
    st.info("👈 Please select a saved profile from the sidebar to load your daily executive weather report.")
else:
    if calc_btn or def_n:
        with st.spinner("Synchronizing real-time planetary coordinates..."):
            # 1. Calculate Natal Baseline
            lat_val, lon_val, tz_val = get_location_coordinates(def_loc)
            swe.set_sid_mode(swe.SIDM_LAHIRI)
            birth_dt = datetime.combine(def_dob, def_tob)
            offset = get_utc_offset(tz_val, birth_dt)
            ut_hour = (def_tob.hour + (def_tob.minute/60.0)) - offset
            jd_ut_natal = swe.julday(def_dob.year, def_dob.month, def_dob.day, ut_hour)
            
            ascmc = swe.houses_ex(jd_ut_natal, lat_val, lon_val, b'P', swe.FLG_SIDEREAL)[1]
            natal_lagna_rasi = int(ascmc[0]/30)+1
            
            moon_res = swe.calc_ut(jd_ut_natal, swe.MOON, swe.FLG_SIDEREAL)[0]
            natal_moon_rasi = int(moon_res[0]/30)+1

            # 2. Calculate Current Live Transits (UTC)
            utcnow = datetime.now(timezone.utc)
            current_ut_hour = utcnow.hour + (utcnow.minute/60.0)
            current_jd_ut = swe.julday(utcnow.year, utcnow.month, utcnow.day, current_ut_hour)

            # 3. Call the Daily Engine
            daily_weather = get_daily_executive_weather(current_jd_ut, natal_moon_rasi, natal_lagna_rasi, LANG)

            # 4. Render the Dashboard
            focus_data = daily_weather["focus"]
            comm_data = daily_weather["communication"]
            energy_data = daily_weather["energy"]
            positions = daily_weather["positions"]

            dashboard_html = f"""
<div style="font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; color: #333;">
                
<h3 style="color: #2c3e50; margin-bottom: 15px; font-size: 20px; border-bottom: 2px solid #eee; padding-bottom: 8px;">1. Primary Strategic Focus (24-48 Hours)</h3>
<div style="background: #fff; border: 1px solid #eaeaea; border-left: 5px solid {focus_data['color']}; padding: 20px; border-radius: 6px; box-shadow: 0 2px 8px rgba(0,0,0,0.04); margin-bottom: 30px;">
<div style="font-size: 12px; color: #888; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px;"><b>Astrological Driver:</b> The Moon currently in {positions['Moon']}</div>
<div style="font-size: 20px; font-weight: bold; color: {focus_data['color']}; margin-bottom: 10px;">{focus_data['title']}</div>
<div style="font-size: 15px; color: #444; line-height: 1.6;">{focus_data['desc']}</div>
</div>

<h3 style="color: #2c3e50; margin-bottom: 15px; font-size: 20px; border-bottom: 2px solid #eee; padding-bottom: 8px;">2. Communication & Data Weather</h3>
<div style="background: #fafafa; border: 1px solid #eaeaea; border-left: 5px solid #27ae60; padding: 20px; border-radius: 6px; margin-bottom: 30px;">
<div style="font-size: 12px; color: #888; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px;"><b>Astrological Driver:</b> Mercury currently in {positions['Mercury']}</div>
<div style="font-size: 18px; font-weight: bold; color: #2c3e50; margin-bottom: 10px;">{comm_data['title']}</div>
<div style="font-size: 15px; color: #444; line-height: 1.6;">{comm_data['desc']}</div>
</div>

<h3 style="color: #2c3e50; margin-bottom: 15px; font-size: 20px; border-bottom: 2px solid #eee; padding-bottom: 8px;">3. Executive Vitality & Authority</h3>
<div style="background: #fafafa; border: 1px solid #eaeaea; border-left: 5px solid #f39c12; padding: 20px; border-radius: 6px; margin-bottom: 30px;">
<div style="font-size: 12px; color: #888; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px;"><b>Astrological Driver:</b> The Sun currently in {positions['Sun']}</div>
<div style="font-size: 18px; font-weight: bold; color: #2c3e50; margin-bottom: 10px;">{energy_data['title']}</div>
<div style="font-size: 15px; color: #444; line-height: 1.6;">{energy_data['desc']}</div>
</div>

</div>
"""
            st.markdown(dashboard_html, unsafe_allow_html=True)
            
            st.caption("Note: This dashboard calculates transits dynamically based on current UTC time mapping against your exact natal coordinates. Micro-transits (like the Moon) shift every 2.5 days.")
