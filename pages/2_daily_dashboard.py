import streamlit as st
import swisseph as swe
from datetime import datetime, timezone, time
from supabase import create_client

# --- IMPORTS FROM OUR CUSTOM ENGINE ---
from astro_engine import (
    get_location_coordinates, get_utc_offset, get_daily_executive_weather,
    get_daily_panchangam_metrics, ZODIAC_TA, ZODIAC
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

# --- SIDEBAR ---
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

    name_in = st.text_input("Name", value=def_n, disabled=True) if def_n else None
    calc_btn = st.button("Generate Today's Strategy" if LANG=="English" else "இன்றைய பலன்கள்", type="primary", use_container_width=True)

# --- MAIN DASHBOARD UI ---
st.title("⚡ Daily Executive Weather" if LANG=="English" else "⚡ தினசரி ஜோதிட அறிக்கை")

if not def_n:
    msg = "👈 Please select a saved profile from the sidebar to load your daily executive weather report." if LANG=="English" else "👈 உங்கள் சுயவிவரத்தை தேர்ந்தெடுக்கவும்."
    st.info(msg)
else:
    if calc_btn or def_n:
        with st.spinner("Synchronizing exact local coordinates..."):
            lat_val, lon_val, tz_val = get_location_coordinates(def_loc)
            swe.set_sid_mode(swe.SIDM_LAHIRI)
            birth_dt = datetime.combine(def_dob, def_tob)
            offset = get_utc_offset(tz_val, birth_dt)
            ut_hour = (def_tob.hour + (def_tob.minute/60.0)) - offset
            jd_ut_natal = swe.julday(def_dob.year, def_dob.month, def_dob.day, ut_hour)
            
            ascmc = swe.houses_ex(jd_ut_natal, lat_val, lon_val, b'P', swe.FLG_SIDEREAL)[1]
            natal_lagna_rasi = int(ascmc[0]/30)+1
            natal_moon_lon = swe.calc_ut(jd_ut_natal, swe.MOON, swe.FLG_SIDEREAL)[0][0]
            natal_moon_rasi = int(natal_moon_lon/30)+1

            utcnow = datetime.now(timezone.utc)
            current_ut_hour = utcnow.hour + (utcnow.minute/60.0)
            current_jd_ut = swe.julday(utcnow.year, utcnow.month, utcnow.day, current_ut_hour)

            daily_weather = get_daily_executive_weather(current_jd_ut, natal_moon_rasi, natal_lagna_rasi, LANG)
            pan = get_daily_panchangam_metrics(current_jd_ut, natal_moon_lon, lat_val, lon_val, tz_val, LANG)

            # --- SETUP TABS ---
            t1_name = "📅 Daily Overview" if LANG=="English" else "📅 பஞ்சாங்கம்"
            t2_name = "⏳ Hourly Planner" if LANG=="English" else "⏳ நாள்காட்டி"
            t3_name = "🎯 Strategy" if LANG=="English" else "🎯 வியூகம்"
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
                    "ch_alert": "Chandrashtama for" if LANG=="English" else "சந்திராஷ்டமம்",
                    "ausp": "Auspicious Timings" if LANG=="English" else "நல்ல நேரங்கள்",
                    "nn": "Nalla Neram" if LANG=="English" else "நல்ல நேரம்",
                    "gnn": "Gowri Neram" if LANG=="English" else "கௌரி நேரம்",
                    "inausp": "Obstacle Windows" if LANG=="English" else "தடை நேரங்கள்",
                    "rk": "Rahu Kalam" if LANG=="English" else "ராகு காலம்",
                    "yg": "Yemagandam" if LANG=="English" else "எமகண்டம்"
                }

                grid_html = f"""
<style>
.metric-card {{ background: #ffffff; border: 1px solid #e0e0e0; border-radius: 4px; padding: 16px; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; box-shadow: 0 1px 2px rgba(0,0,0,0.01); display: flex; flex-direction: column; justify-content: space-between; min-height: 120px; }}
.card-header {{ font-size: 10.5px; text-transform: uppercase; letter-spacing: 0.5px; color: #7f8c8d; font-weight: 500; margin-bottom: 8px; }}
.card-title {{ font-size: 26px; font-weight: 300; color: #111; line-height: 1.1; margin-bottom: 4px; }}
.card-sub {{ font-size: 13px; color: #555; font-weight: 400; }}
.card-row {{ display: flex; justify-content: space-between; align-items: baseline; border-bottom: 1px solid #f7f7f7; padding: 6px 0; }}
.card-row:last-child {{ border-bottom: none; }}
.row-lbl {{ font-size: 12px; color: #7f8c8d; font-weight: 400; }}
.row-val {{ font-size: 13px; color: #222; font-weight: 500; text-align: right; }}
</style>

<div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; margin-bottom: 20px;">

<div class="metric-card">
<div class="card-header">{pan['day_str']}</div>
<div>
<div class="card-title">{pan['date_str']}</div>
<div class="card-sub" style="color: #2c3e50;">{pan['tamil_month']}</div>
</div>
</div>

<div class="metric-card">
<div class="card-header">{lbl['m_phase']}</div>
<div>
<div class="card-title" style="font-size: 22px;">{moon_icon} {pan['tithi']}</div>
<div class="card-sub">{pan['paksha']} <span style="color:#95a5a6;">|</span> {pan['countdown']}</div>
</div>
</div>

<div class="metric-card">
<div class="card-header">{lbl['sun_yoga']}</div>
<div style="flex-grow: 1; display: flex; flex-direction: column; justify-content: flex-end;">
<div class="card-row"><span class="row-lbl">{lbl['sun_r']} / {lbl['sun_s']}</span><span class="row-val">{pan['sunrise']} - {pan['sunset']}</span></div>
<div class="card-row"><span class="row-lbl">{lbl['yoga']}</span><span class="row-val">{pan['yoga']}</span></div>
</div>
</div>

<div class="metric-card">
<div class="card-header">{lbl['tara']}</div>
<div style="flex-grow: 1; display: flex; flex-direction: column; justify-content: flex-end;">
<div class="card-row"><span class="row-lbl">{lbl['nak']}</span><span class="row-val">{pan['nakshatra']} <span style="color:#7f8c8d; font-weight:400;">({pan['tara_name']})</span></span></div>
<div class="card-row"><span class="row-lbl" style="color:#c0392b;">{lbl['ch_alert']}</span><span class="row-val" style="color:#c0392b;">{pan['ch_rasi_name']}</span></div>
</div>
</div>

<div class="metric-card" style="border-top: 2px solid #27ae60;">
<div class="card-header" style="color: #27ae60;">{lbl['ausp']}</div>
<div style="flex-grow: 1; display: flex; flex-direction: column; justify-content: flex-end;">
<div class="card-row"><span class="row-lbl">{lbl['nn']}</span><span class="row-val">{pan['nn']}</span></div>
<div class="card-row"><span class="row-lbl">{lbl['gnn']}</span><span class="row-val">{pan['gnn']}</span></div>
</div>
</div>

<div class="metric-card" style="border-top: 2px solid #c0392b;">
<div class="card-header" style="color: #c0392b;">{lbl['inausp']}</div>
<div style="flex-grow: 1; display: flex; flex-direction: column; justify-content: flex-end;">
<div class="card-row"><span class="row-lbl">{lbl['rk']}</span><span class="row-val">{pan['rk']}</span></div>
<div class="card-row"><span class="row-lbl">{lbl['yg']}</span><span class="row-val">{pan['yg']}</span></div>
</div>
</div>

</div>
"""
                st.markdown(grid_html, unsafe_allow_html=True)


            # --- TAB 2: HOURLY PLANNER (Minimalist Line Items) ---
            with tab2:
                schedule_html = "<div style='font-family: \"Helvetica Neue\", Helvetica, Arial, sans-serif;'>"
                for row in pan["schedule"]:
                    badges_html = ""
                    for b in row["badges"]:
                        badges_html += f"<div style='color: {b['color']}; font-size: 11px; font-weight: 500; margin-top: 2px;'>{b['text']} ({b['start'].strftime('%I:%M').lstrip('0')} - {b['end'].strftime('%I:%M').lstrip('0')})</div>"
                    
                    schedule_html += f"""
<div style="display: flex; justify-content: space-between; align-items: flex-start; padding: 12px 2px; border-bottom: 1px solid #f2f2f2;">
<div style="flex: 1;">
<div style="font-size: 11px; color: #999; font-weight: 400; margin-bottom: 2px;">{row['time']}</div>
<div style="font-size: 14.5px; font-weight: 500; color: {row['color']};">{row['lord']}</div>
<div style="font-size: 12px; color: #666; margin-top: 1px; font-weight: 300;">{row['activity']}</div>
</div>
<div style="text-align: right; flex: 1;">
{badges_html}
</div>
</div>
"""
                schedule_html += "</div>"
                st.markdown(schedule_html, unsafe_allow_html=True)


            # --- TAB 3: TACTICAL STRATEGY ---
            with tab3:
                focus = daily_weather["focus"]
                comm = daily_weather["communication"]
                energy = daily_weather["energy"]
                
                s_focus = "Strategic Focus" if LANG=="English" else "வியூகம்"
                s_comm = "Communication" if LANG=="English" else "தகவல் தொடர்பு"
                s_energy = "Executive Vitality" if LANG=="English" else "ஆளுமை நிலை"

                weather_html = f"""
<style>
.t-card {{ background: #fff; border: 1px solid #e0e0e0; padding: 18px; border-radius: 4px; margin-bottom: 20px; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; box-shadow: 0 1px 2px rgba(0,0,0,0.01); }}
.t-head {{ font-size: 11px; color: #888; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px; font-weight: 500; }}
.t-title {{ font-size: 17px; font-weight: 600; margin-bottom: 8px; }}
.t-desc {{ font-size: 13.5px; color: #444; line-height: 1.5; margin-bottom: 12px; font-weight: 300; }}
.t-rem {{ font-size: 12.5px; color: #222; font-style: italic; background: #fafafa; padding: 10px; border-radius: 4px; border: 1px solid #f0f0f0; }}
</style>

<div class="t-card" style="border-left: 3px solid {focus['color']};">
<div class="t-head">1. {s_focus} (Moon in {daily_weather['positions']['Moon']})</div>
<div class="t-title" style="color: {focus['color']};">{focus['title']}</div>
<div class="t-desc">{focus['desc']}</div>
<div class="t-rem">{focus['remedy']}</div>
</div>

<div class="t-card" style="border-left: 3px solid #27ae60;">
<div class="t-head">2. {s_comm} (Mercury in {daily_weather['positions']['Mercury']})</div>
<div class="t-title" style="color: #2c3e50;">{comm['title']}</div>
<div class="t-desc">{comm['desc']}</div>
<div class="t-rem">{comm['remedy']}</div>
</div>

<div class="t-card" style="border-left: 3px solid #f39c12;">
<div class="t-head">3. {s_energy} (Sun in {daily_weather['positions']['Sun']})</div>
<div class="t-title" style="color: #2c3e50;">{energy['title']}</div>
<div class="t-desc">{energy['desc']}</div>
<div class="t-rem">{energy['remedy']}</div>
</div>
"""
                st.markdown(weather_html, unsafe_allow_html=True)
