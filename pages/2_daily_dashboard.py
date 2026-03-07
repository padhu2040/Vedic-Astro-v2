import streamlit as st
import swisseph as swe
from datetime import datetime, timezone, time, date
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

# --- SIDEBAR: Profile Selection ---
with st.sidebar:
    st.markdown("### 👤 Personal Strategy")
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

# --- TOP CONTROL BAR (Date, Location, Language) ---
st.title("Daily Cosmos")

col1, col2, col3 = st.columns([1.2, 1.5, 1])
with col1:
    target_date = st.date_input("📅 Date", date.today())
with col2:
    target_city = st.text_input("📍 Location", value=def_loc if def_loc else "Chennai")
with col3:
    LANG = st.selectbox("🌐 Language", ["English", "Tamil"])

st.divider()

# --- INSTANT ENGINE EXECUTION ---
with st.spinner("Calculating orbital mechanics..."):
    # 1. Resolve Location
    try:
        lat_val, lon_val, tz_val = get_location_coordinates(target_city)
    except:
        lat_val, lon_val, tz_val = 13.0827, 80.2707, "Asia/Kolkata" # Fallback

    # 2. Resolve Profile Elements (If present)
    natal_lagna_rasi, natal_moon_rasi, natal_moon_lon = None, None, None
    if def_n:
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        birth_dt = datetime.combine(def_dob, def_tob)
        offset = get_utc_offset(tz_val, birth_dt)
        ut_hour = (def_tob.hour + (def_tob.minute/60.0)) - offset
        jd_ut_natal = swe.julday(def_dob.year, def_dob.month, def_dob.day, ut_hour)
        
        ascmc = swe.houses_ex(jd_ut_natal, lat_val, lon_val, b'P', swe.FLG_SIDEREAL)[1]
        natal_lagna_rasi = int(ascmc[0]/30)+1
        natal_moon_lon = swe.calc_ut(jd_ut_natal, swe.MOON, swe.FLG_SIDEREAL)[0][0]
        natal_moon_rasi = int(natal_moon_lon/30)+1

    # 3. Call The Engines
    pan = get_daily_panchangam_metrics(target_date, lat_val, lon_val, tz_val, LANG, natal_lagna_rasi, natal_moon_rasi)
    
    if def_n:
        daily_weather = get_daily_executive_weather(pan['current_jd_ut'], natal_moon_rasi, natal_lagna_rasi, LANG)

# --- SETUP TABS (No flashy icons) ---
t1_name = "Overview" if LANG=="English" else "பஞ்சாங்கம்"
t2_name = "Horai" if LANG=="English" else "ஓரை"
t3_name = "Strategy" if LANG=="English" else "வியூகம்"
tab1, tab2, tab3 = st.tabs([t1_name, t2_name, t3_name])

# --- TAB 1: 6-CARD GRID (Minimalist & Flat) ---
with tab1:
    moon_icon = "🌔" if pan['is_waxing'] else "🌘"
    
    lbl = {
        "m_phase": "Moon Phase" if LANG=="English" else "சந்திர நிலை",
        "sun_yoga": "Sun & Astronomical Yoga" if LANG=="English" else "சூரியன் & யோகம்",
        "sun_r": "Sunrise" if LANG=="English" else "உதயம்",
        "sun_s": "Sunset" if LANG=="English" else "அஸ்தமனம்",
        "yoga": "Nithya Yoga" if LANG=="English" else "நித்திய யோகம்",
        "tara": "Personal Tarabalam" if LANG=="English" else "தாராபலம்",
        "nak": "Nakshatra" if LANG=="English" else "நட்சத்திரம்",
        "ausp": "Auspicious Timings" if LANG=="English" else "நல்ல நேரங்கள்",
        "nn": "Nalla Neram" if LANG=="English" else "நல்ல நேரம்",
        "gnn": "Gowri Neram" if LANG=="English" else "கௌரி நேரம்",
        "inausp": "Obstacle Windows" if LANG=="English" else "தடை நேரங்கள்",
        "rk": "Rahu Kalam" if LANG=="English" else "ராகு காலம்",
        "yg": "Yemagandam" if LANG=="English" else "எமகண்டம்"
    }

    # Tarabalam Row (Only shows if profile is loaded)
    tara_row = f"""<div class="card-row"><span class="row-lbl">{lbl['tara']}</span><span class="row-val" style="color:{pan['tara_color']};">{pan['tara_name']}</span></div>""" if def_n else ""

    grid_html = f"""
<style>
.grid-container {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; margin-bottom: 20px; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; }}
.m-card {{ background: #ffffff; border: 1px solid #eaeaea; border-radius: 4px; padding: 16px; display: flex; flex-direction: column; box-shadow: 0 1px 2px rgba(0,0,0,0.02); min-height: 120px; }}
.c-head {{ font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; color: #888; font-weight: 500; margin-bottom: 12px; border-bottom: 1px solid #f9f9f9; padding-bottom: 4px; }}
.card-row {{ display: flex; justify-content: space-between; align-items: baseline; border-bottom: 1px solid #f7f7f7; padding: 6px 0; }}
.card-row:last-child {{ border-bottom: none; }}
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
<div style="flex-grow: 1; display: flex; flex-direction: column; justify-content: flex-end;">
<div class="card-row"><span class="row-lbl">{lbl['sun_r']} / {lbl['sun_s']}</span><span class="row-val">{pan['sunrise']} - {pan['sunset']}</span></div>
<div class="card-row"><span class="row-lbl">Rasi & Star</span><span class="row-val">{pan['rasi']} / {pan['nakshatra']}</span></div>
<div class="card-row"><span class="row-lbl">{lbl['yoga']}</span><span class="row-val">{pan['yoga']}</span></div>
{tara_row}
</div>
</div>

<div class="m-card" style="border-top: 2px solid #27ae60;">
<div class="c-head" style="color: #27ae60;">{lbl['ausp']}</div>
<div style="flex-grow: 1; display: flex; flex-direction: column; justify-content: flex-end;">
<div class="card-row"><span class="row-lbl">{lbl['nn']}</span><span class="row-val">{pan['nn']}</span></div>
<div class="card-row"><span class="row-lbl">{lbl['gnn']}</span><span class="row-val">{pan['gnn']}</span></div>
</div>
</div>

<div class="m-card" style="border-top: 2px solid #c0392b; grid-column: span 2;">
<div class="c-head" style="color: #c0392b;">{lbl['inausp']}</div>
<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
<div>
<div class="card-row"><span class="row-lbl">{lbl['rk']}</span><span class="row-val">{pan['rk']}</span></div>
<div class="card-row"><span class="row-lbl">{lbl['yg']}</span><span class="row-val">{pan['yg']}</span></div>
</div>
<div style="border-left: 1px dashed #eee; padding-left: 15px;">
<div class="card-row" style="flex-direction: column; align-items: flex-start; border: none;">
<span class="row-lbl" style="color:#c0392b; margin-bottom: 4px;">Chandrashtama for:</span>
<span class="row-val" style="font-size: 12px; text-align: left;">{pan['ch_naks']}</span>
</div>
</div>
</div>
</div>

</div>
"""
    st.markdown(grid_html, unsafe_allow_html=True)


# --- TAB 2: HOURLY PLANNER (Scrollable & Highlighted) ---
with tab2:
    msg_h = "Full 12-Hour Horai Planner" if LANG=="English" else "முழு 12 மணிநேர ஓரை நாள்காட்டி"
    st.markdown(f"<div style='font-family: sans-serif; font-size: 14px; color: #7f8c8d; margin-bottom: 10px;'>{msg_h}</div>", unsafe_allow_html=True)
    
    if def_n:
        st.markdown("<div style='font-size: 12px; color: #f39c12; margin-bottom: 15px;'><b>⭐ Note:</b> Starred blocks indicate highly favorable timings based on your specific Lagna and Moon Rasi.</div>", unsafe_allow_html=True)

    schedule_html = "<div style='font-family: \"Helvetica Neue\", Helvetica, Arial, sans-serif; max-height: 400px; overflow-y: auto; padding-right: 5px;'>"
    
    for row in pan["schedule"]:
        bg_col = "#ffffff"
        border = "border-bottom: 1px solid #f2f2f2;"
        indicator = ""
        
        # Highlight current hour
        if row['is_current']:
            bg_col = "#f4f9f4"
            border = f"border-left: 4px solid {row['color']}; border-bottom: 1px solid #e0e0e0;"
            indicator = "<span style='font-size: 10px; color: #27ae60; text-transform: uppercase; font-weight: bold; margin-left: 8px;'>(Now)</span>"
            
        # Highlight personal power hour
        if row['is_power']:
            indicator += " ⭐"

        schedule_html += f"""
<div style="display: flex; justify-content: space-between; align-items: center; padding: 12px 10px; background-color: {bg_col}; {border} margin-bottom: 4px; border-radius: 4px;">
<div>
<div style="font-size: 11px; color: #999; font-weight: 400; margin-bottom: 2px;">{row['time']} {indicator}</div>
<div style="font-size: 15px; font-weight: 500; color: {row['color']};">{row['lord']}</div>
</div>
<div style="text-align: right;">
<div style="font-size: 12.5px; color: #555; font-weight: 400;">{row['activity']}</div>
</div>
</div>
"""
    schedule_html += "</div>"
    st.markdown(schedule_html, unsafe_allow_html=True)


# --- TAB 3: TACTICAL STRATEGY (Requires Profile) ---
with tab3:
    if not def_n:
        st.info("👈 Select your profile from the sidebar to generate your personalized tactical strategy.")
    else:
        focus = daily_weather["focus"]
        comm = daily_weather["communication"]
        
        s_focus = "Strategic Focus" if LANG=="English" else "வியூகம்"
        s_comm = "Communication" if LANG=="English" else "தகவல் தொடர்பு"

        weather_html = f"""
<style>
.t-card {{ background: #fff; border: 1px solid #eaeaea; padding: 18px; border-radius: 4px; margin-bottom: 15px; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; box-shadow: 0 1px 2px rgba(0,0,0,0.01); }}
.t-head {{ font-size: 11px; color: #888; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 6px; font-weight: 500; display: flex; justify-content: space-between; }}
.t-title {{ font-size: 17px; font-weight: 500; margin-bottom: 8px; }}
.t-desc {{ font-size: 13.5px; color: #444; line-height: 1.5; margin-bottom: 12px; font-weight: 300; }}
.t-rem {{ font-size: 12.5px; color: #222; font-style: italic; background: #fafafa; padding: 10px; border-radius: 4px; border: 1px solid #f5f5f5; }}
</style>

<div class="t-card" style="border-left: 3px solid {focus['color']};">
<div class="t-head"><span>{s_focus}</span> <span>Moon in {daily_weather['positions']['Moon']}</span></div>
<div class="t-title" style="color: {focus['color']};">{focus['title']}</div>
<div class="t-desc">{focus['desc']}</div>
<div class="t-rem">{focus['remedy']}</div>
</div>

<div class="t-card" style="border-left: 3px solid #27ae60;">
<div class="t-head"><span>{s_comm}</span> <span>Mercury in {daily_weather['positions']['Mercury']}</span></div>
<div class="t-title" style="color: #2c3e50;">{comm['title']}</div>
<div class="t-desc">{comm['desc']}</div>
<div class="t-rem">{comm['remedy']}</div>
</div>
"""
        st.markdown(weather_html, unsafe_allow_html=True)
