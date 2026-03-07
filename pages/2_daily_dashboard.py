import streamlit as st
import swisseph as swe
from datetime import datetime, timezone, time
from supabase import create_client

from astro_engine import (
    get_location_coordinates, get_utc_offset, get_daily_executive_weather,
    get_daily_panchangam_metrics, ZODIAC_TA, ZODIAC
)

st.set_page_config(page_title="Daily Calendar", layout="centered")

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
    LANG = st.radio("Language / மொழி", ["English", "Tamil"], horizontal=True)
    st.divider()
    st.markdown("### 👤 Personal Strategy")
    saved_profiles = load_profiles_from_db()
    profile_options = ["(Select Profile...)"] + list(saved_profiles.keys())
    selected_profile = st.selectbox("Load Saved Profile", profile_options)
    
    if selected_profile != "(Select Profile...)":
        def_n = selected_profile
        def_dob = saved_profiles[selected_profile]["dob"]
        def_tob = saved_profiles[selected_profile]["tob"]
        def_loc = saved_profiles[selected_profile]["city"]
    else:
        def_n, def_dob, def_tob, def_loc = "", datetime(2000, 1, 1).date(), time(12, 0), ""

# --- 1. INSTANT GENERIC LOAD (Page for all visitors) ---
st.title("Daily Cosmos" if LANG=="English" else "தினசரி நாள்காட்டி")
st.markdown("<br>", unsafe_allow_html=True)

# Default to Chennai if no profile is selected
lat_val, lon_val, tz_val = 13.0827, 80.2707, "Asia/Kolkata" 
if def_n:
    lat_val, lon_val, tz_val = get_location_coordinates(def_loc)

# Calculate generic data instantly
pan = get_daily_panchangam_metrics(lat_val, lon_val, tz_val, LANG)
moon_icon = "🌔" if pan['is_waxing'] else "🌘"

lbl = {
    "ast": "Astronomical" if LANG=="English" else "வானியல்",
    "ausp": "Auspicious Timings" if LANG=="English" else "நல்ல நேரங்கள்",
    "inausp": "Obstacle Windows" if LANG=="English" else "தடை நேரங்கள்",
    "horai": "Upcoming Horai" if LANG=="English" else "வரவிருக்கும் ஓரை"
}

# --- THE 6-CARD MINIMALIST GRID ---
grid_html = f"""
<style>
.grid-container {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; margin-bottom: 30px; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; }}
.m-card {{ background: #ffffff; border: 1px solid #eaeaea; border-radius: 4px; padding: 16px; display: flex; flex-direction: column; box-shadow: 0 1px 2px rgba(0,0,0,0.02); }}
.c-head {{ font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; color: #888; font-weight: 500; margin-bottom: 12px; border-bottom: 1px solid #f9f9f9; padding-bottom: 4px; }}
.row-item {{ display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 6px; }}
.row-lbl {{ font-size: 12.5px; color: #7f8c8d; font-weight: 400; }}
.row-val {{ font-size: 13.5px; color: #222; font-weight: 500; text-align: right; }}
</style>

<div class="grid-container">

<div class="m-card" style="flex-direction: row; align-items: center; padding: 12px;">
    <div style="flex: 1; border-right: 1px solid #eee; padding-right: 12px; text-align: center;">
        <div style="font-size: 28px; font-weight: 300; color: #111; line-height: 1;">{pan['date_en'].split(' ')[0]}</div>
        <div style="font-size: 12px; color: #7f8c8d; font-weight: 400; margin-top: 4px;">{pan['day_en']}<br>{pan['date_en'].split(' ')[1]}</div>
    </div>
    <div style="flex: 1; padding-left: 12px; text-align: center;">
        <div style="font-size: 28px; font-weight: 300; color: #2c3e50; line-height: 1;">{pan['date_ta']}</div>
        <div style="font-size: 12px; color: #7f8c8d; font-weight: 400; margin-top: 4px;">{pan['month_ta']}<br>Month</div>
    </div>
</div>

<div class="m-card" style="justify-content: center;">
    <div style="font-size: 20px; font-weight: 400; color: #111; margin-bottom: 6px;">{moon_icon} {pan['tithi']}</div>
    <div style="font-size: 13px; color: #555; margin-bottom: 2px;">{pan['paksha']}</div>
    <div style="font-size: 12px; color: #888;">{pan['countdown']}</div>
</div>

<div class="m-card">
    <div class="c-head">{lbl['ast']}</div>
    <div class="row-item"><span class="row-lbl">Sunrise / Set</span><span class="row-val">{pan['sunrise']} - {pan['sunset']}</span></div>
    <div class="row-item"><span class="row-lbl">Rasi & Star</span><span class="row-val">{pan['rasi']} / {pan['nakshatra']}</span></div>
    <div class="row-item"><span class="row-lbl">Nithya Yoga</span><span class="row-val">{pan['yoga']}</span></div>
</div>

<div class="m-card" style="border-top: 2px solid #27ae60;">
    <div class="c-head" style="color: #27ae60;">{lbl['ausp']}</div>
    <div class="row-item"><span class="row-lbl">Nalla Neram</span><span class="row-val">{pan['nn']}</span></div>
    <div class="row-item"><span class="row-lbl">Gowri</span><span class="row-val">{pan['gnn']}</span></div>
</div>

<div class="m-card" style="border-top: 2px solid #c0392b;">
    <div class="c-head" style="color: #c0392b;">{lbl['inausp']}</div>
    <div class="row-item"><span class="row-lbl">Rahu Kalam</span><span class="row-val">{pan['rk']}</span></div>
    <div class="row-item"><span class="row-lbl">Yemagandam</span><span class="row-val">{pan['yg']}</span></div>
    <div class="row-item" style="margin-top: 8px; border-top: 1px dashed #eee; padding-top: 8px;">
        <span class="row-lbl" style="color:#c0392b;">Chandrashtama</span>
        <span class="row-val" style="font-size: 11px; max-width: 110px;">{pan['ch_naks']}</span>
    </div>
</div>

<div class="m-card" style="padding: 0;">
    <div class="c-head" style="margin: 16px 16px 8px 16px;">{lbl['horai']}</div>
    <div style="max-height: 125px; overflow-y: auto; padding: 0 16px 16px 16px;">
"""
for h in pan["schedule"]:
    bg_col = "#fdfdfd"
    border = "none"
    if h['is_current']:
        bg_col = "#f0f8ff" # Very subtle highlight
        border = f"border-left: 3px solid {h['color']};"
        
    grid_html += f"""
        <div style="display: flex; justify-content: space-between; align-items: center; padding: 8px 6px; background: {bg_col}; {border} border-bottom: 1px solid #f9f9f9;">
            <div>
                <div style="font-size: 13.5px; font-weight: 500; color: {h['color']};">{h['lord']}</div>
                <div style="font-size: 11px; color: #888;">{h['activity']}</div>
            </div>
            <div style="font-size: 11.5px; color: #444; font-weight: 500;">{h['time']}</div>
        </div>
    """
grid_html += """
    </div>
</div>
</div>
"""
st.markdown(grid_html, unsafe_allow_html=True)


# --- 2. PERSONALIZED STRATEGY (Only if profile is selected) ---
if def_n:
    st.markdown(f"<h3 style='font-family: sans-serif; font-size: 20px; color: #2c3e50; border-bottom: 1px solid #eee; padding-bottom: 8px; margin-top: 10px;'>🎯 Tactical Strategy: {def_n}</h3>", unsafe_allow_html=True)
    
    with st.spinner("Calculating personal alignment..."):
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        birth_dt = datetime.combine(def_dob, def_tob)
        offset = get_utc_offset(tz_val, birth_dt)
        ut_hour = (def_tob.hour + (def_tob.minute/60.0)) - offset
        jd_ut_natal = swe.julday(def_dob.year, def_dob.month, def_dob.day, ut_hour)
        
        ascmc = swe.houses_ex(jd_ut_natal, lat_val, lon_val, b'P', swe.FLG_SIDEREAL)[1]
        natal_lagna_rasi = int(ascmc[0]/30)+1
        natal_moon_lon = swe.calc_ut(jd_ut_natal, swe.MOON, swe.FLG_SIDEREAL)[0][0]
        natal_moon_rasi = int(natal_moon_lon/30)+1

        daily_weather = get_daily_executive_weather(pan['current_jd_ut'], natal_moon_rasi, natal_lagna_rasi, LANG)

        focus = daily_weather["focus"]
        comm = daily_weather["communication"]
        
        weather_html = f"""
        <style>
        .t-card {{ background: #fff; border: 1px solid #eaeaea; padding: 18px; border-radius: 4px; margin-bottom: 15px; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; box-shadow: 0 1px 2px rgba(0,0,0,0.01); }}
        .t-head {{ font-size: 11px; color: #888; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 6px; font-weight: 500; display: flex; justify-content: space-between; }}
        .t-title {{ font-size: 17px; font-weight: 500; margin-bottom: 8px; }}
        .t-desc {{ font-size: 13.5px; color: #444; line-height: 1.5; margin-bottom: 12px; font-weight: 300; }}
        .t-rem {{ font-size: 12.5px; color: #222; font-style: italic; background: #fafafa; padding: 10px; border-radius: 4px; border: 1px solid #f5f5f5; }}
        </style>

        <div class="t-card" style="border-left: 3px solid {focus['color']};">
            <div class="t-head"><span>Primary Focus</span> <span>Moon in {daily_weather['positions']['Moon']}</span></div>
            <div class="t-title" style="color: {focus['color']};">{focus['title']}</div>
            <div class="t-desc">{focus['desc']}</div>
            <div class="t-rem">{focus['remedy']}</div>
        </div>

        <div class="t-card" style="border-left: 3px solid #27ae60;">
            <div class="t-head"><span>Communication</span> <span>Mercury in {daily_weather['positions']['Mercury']}</span></div>
            <div class="t-title" style="color: #2c3e50;">{comm['title']}</div>
            <div class="t-desc">{comm['desc']}</div>
            <div class="t-rem">{comm['remedy']}</div>
        </div>
        """
        st.markdown(weather_html, unsafe_allow_html=True)
