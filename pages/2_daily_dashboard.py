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
st.markdown(f"**{'Live Tactical Strategy for' if LANG=='English' else 'இன்றைய நாள்'}:** {datetime.now().strftime('%B %d, %Y')}")

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
            t3_name = "🎯 Tactical Strategy" if LANG=="English" else "🎯 வியூகம்"
            tab1, tab2, tab3 = st.tabs([t1_name, t2_name, t3_name])

            # --- TAB 1: DAILY OVERVIEW (The Tearaway Calendar Summary) ---
            with tab1:
                # Chandrashtama Alert
                if pan['is_chandrashtama']:
                    alert_title = "🚨 CHANDRASHTAMA ALERT" if LANG=="English" else "🚨 சந்திராஷ்டமம் எச்சரிக்கை"
                    alert_desc = "The Moon is in your 8th house today. Maintain a low profile, avoid arguments, and delay major executive decisions." if LANG=="English" else "இன்று சந்திராஷ்டமம். முக்கிய முடிவுகளைத் தவிர்க்கவும், கவனமாக இருக்கவும்."
                    st.markdown(f"<div style='background-color:#ffebee; border-left:5px solid #c0392b; padding:15px; border-radius:4px; margin-bottom:20px;'><h4 style='color:#c0392b; margin:0 0 5px 0;'>{alert_title}</h4><p style='color:#333; margin:0; font-size:14px;'>{alert_desc}</p></div>", unsafe_allow_html=True)

                t_tara = "Personalized Tarabalam" if LANG=="English" else "தாராபலம்"
                t_horai = "Current Active Horai" if LANG=="English" else "நடப்பு ஓரை"
                t_moon = "Daily Moon Phase" if LANG=="English" else "சந்திர நிலை"

                metric_html = f"""
<div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin-bottom: 25px; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;">
<div style="background: #fff; border: 1px solid #eaeaea; border-top: 3px solid {pan['tara_color']}; border-radius: 6px; padding: 15px; text-align: center;">
<div style="font-size: 11px; color: #888; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px;">{t_tara}</div>
<div style="font-size: 14px; font-weight: bold; color: {pan['tara_color']};">{pan['tara_name']}</div>
<div style="font-size: 12px; color: #666; margin-top: 4px;">{pan['tara_desc']}</div>
</div>
<div style="background: #fff; border: 1px solid #eaeaea; border-top: 3px solid #8e44ad; border-radius: 6px; padding: 15px; text-align: center;">
<div style="font-size: 11px; color: #888; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px;">{t_horai}</div>
<div style="font-size: 16px; font-weight: bold; color: #8e44ad;">{pan['horai']}</div>
</div>
<div style="background: #fff; border: 1px solid #eaeaea; border-top: 3px solid #2980b9; border-radius: 6px; padding: 15px; text-align: center;">
<div style="font-size: 11px; color: #888; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px;">{t_moon} ({pan['nakshatra']})</div>
<div style="font-size: 14px; font-weight: bold; color: #2980b9;">{pan['moon_phase']}</div>
</div>
</div>
                """
                st.markdown(metric_html, unsafe_allow_html=True)

                # Core Timing Summary Grid
                t_title = "Important Timings Today" if LANG=="English" else "இன்றைய முக்கிய நேரங்கள்"
                sun_str = "Sunrise / Sunset" if LANG=="English" else "சூரிய உதயம் / அஸ்தமனம்"
                soolam_str = "Soolam (Avoid Travel)" if LANG=="English" else "சூலம் (பயணத் தடை)"
                rem_str = "Remedy" if LANG=="English" else "பரிகாரம்"

                timing_html = f"""
<div style="font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; background: #fff; border: 1px solid #eaeaea; border-radius: 6px; padding: 20px;">
<h3 style="margin-top:0; color:#2c3e50; font-size: 18px; border-bottom: 1px solid #eee; padding-bottom: 10px;">{t_title}</h3>

<div style="display: flex; border-bottom: 1px solid #f9f9f9; padding: 8px 0;">
    <div style="flex: 1; color: #7f8c8d; font-size: 14px;">{sun_str}</div>
    <div style="flex: 1; text-align: right; color: #333; font-weight: bold; font-size: 14px;">{pan['sunrise']} / {pan['sunset']}</div>
</div>
"""
                for key, val in pan["summary_times"].items():
                    color = "#27ae60" if "Nalla" in key or "நல்ல" in key or "கௌரி" in key else "#c0392b" if "Rahu" in key or "ராகு" in key else "#d35400" if "Yem" in key or "எம" in key else "#8e44ad"
                    timing_html += f"""
<div style="display: flex; border-bottom: 1px solid #f9f9f9; padding: 8px 0;">
    <div style="flex: 1; color: {color}; font-size: 14px; font-weight: bold;">{key}</div>
    <div style="flex: 1; text-align: right; color: #333; font-size: 14px;">{val}</div>
</div>
"""
                timing_html += f"""
<div style="display: flex; padding: 8px 0;">
    <div style="flex: 1; color: #7f8c8d; font-size: 14px;">{soolam_str}</div>
    <div style="flex: 1; text-align: right; color: #333; font-size: 14px;"><b>{pan['soolam_dir']}</b> ({rem_str}: {pan['soolam_rem']})</div>
</div>
</div>
"""
                st.markdown(timing_html, unsafe_allow_html=True)


            # --- TAB 2: HOURLY PLANNER (The Minimalist List) ---
            with tab2:
                cal_title = "The Cosmic Calendar" if LANG=="English" else "நாள்காட்டி"
                st.markdown(f"<h3 style='color: #2c3e50; font-family: sans-serif; font-size: 18px; margin-top: 5px; border-bottom: 2px solid #eee; padding-bottom: 8px;'>{cal_title}</h3>", unsafe_allow_html=True)
                
                schedule_html = "<div style='font-family: \"Helvetica Neue\", Helvetica, Arial, sans-serif; margin-bottom: 20px;'>"
                for row in pan["schedule"]:
                    badges_html = ""
                    for b in row["badges"]:
                        badges_html += f"<div style='color: {b['color']}; font-size: 11.5px; font-weight: 500; margin-top: 3px;'>{b['text']} ({b['start'].strftime('%I:%M')} - {b['end'].strftime('%I:%M%p')})</div>"
                    
                    schedule_html += f"""
<div style="display: flex; justify-content: space-between; align-items: flex-start; padding: 12px 5px; border-bottom: 1px solid #f2f2f2;">
<div style="flex: 1;">
<div style="font-size: 11px; color: #888; font-weight: 400; margin-bottom: 4px;">{row['time']}</div>
<div style="font-size: 15px; font-weight: 500; color: {row['color']};">{row['lord']}</div>
<div style="font-size: 12px; color: #666; margin-top: 2px; font-weight: 400;">{row['activity']}</div>
</div>
<div style="text-align: right; flex: 1;">
{badges_html}
</div>
</div>
"""
                schedule_html += "</div>"
                st.markdown(schedule_html, unsafe_allow_html=True)


            # --- TAB 3: TACTICAL STRATEGY (The Weather Cards) ---
            with tab3:
                focus = daily_weather["focus"]
                comm = daily_weather["communication"]
                energy = daily_weather["energy"]
                
                s_focus = "Primary Strategic Focus" if LANG=="English" else "முக்கிய வியூகம்"
                s_comm = "Communication & Data Weather" if LANG=="English" else "தகவல் தொடர்பு"
                s_energy = "Executive Vitality & Authority" if LANG=="English" else "ஆளுமை நிலை"

                weather_html = f"""
<div style="font-family: sans-serif;">
<h3 style="color: #2c3e50; margin-top: 5px; margin-bottom: 15px; font-size: 18px; border-bottom: 2px solid #eee; padding-bottom: 8px;">1. {s_focus}</h3>
<div style="background: #fff; border: 1px solid #eaeaea; border-left: 5px solid {focus['color']}; padding: 20px; border-radius: 6px; margin-bottom: 25px;">
<div style="font-size: 12px; color: #888; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px;"><b>Driver:</b> Moon in {daily_weather['positions']['Moon']}</div>
<div style="font-size: 17px; font-weight: bold; color: {focus['color']}; margin-bottom: 10px;">{focus['title']}</div>
<div style="font-size: 14px; color: #444; line-height: 1.6; margin-bottom: 10px;">{focus['desc']}</div>
<div style="font-size: 13px; color: #111; font-style: italic; background: #f9f9f9; padding: 10px; border-radius: 4px;">{focus['remedy']}</div>
</div>

<h3 style="color: #2c3e50; margin-bottom: 15px; font-size: 18px; border-bottom: 2px solid #eee; padding-bottom: 8px;">2. {s_comm}</h3>
<div style="background: #fff; border: 1px solid #eaeaea; border-left: 5px solid #27ae60; padding: 20px; border-radius: 6px; margin-bottom: 25px;">
<div style="font-size: 12px; color: #888; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px;"><b>Driver:</b> Mercury in {daily_weather['positions']['Mercury']}</div>
<div style="font-size: 17px; font-weight: bold; color: #2c3e50; margin-bottom: 10px;">{comm['title']}</div>
<div style="font-size: 14px; color: #444; line-height: 1.6; margin-bottom: 10px;">{comm['desc']}</div>
<div style="font-size: 13px; color: #111; font-style: italic; background: #f9f9f9; padding: 10px; border-radius: 4px;">{comm['remedy']}</div>
</div>

<h3 style="color: #2c3e50; margin-bottom: 15px; font-size: 18px; border-bottom: 2px solid #eee; padding-bottom: 8px;">3. {s_energy}</h3>
<div style="background: #fff; border: 1px solid #eaeaea; border-left: 5px solid #f39c12; padding: 20px; border-radius: 6px; margin-bottom: 30px;">
<div style="font-size: 12px; color: #888; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px;"><b>Driver:</b> Sun in {daily_weather['positions']['Sun']}</div>
<div style="font-size: 17px; font-weight: bold; color: #2c3e50; margin-bottom: 10px;">{energy['title']}</div>
<div style="font-size: 14px; color: #444; line-height: 1.6; margin-bottom: 10px;">{energy['desc']}</div>
<div style="font-size: 13px; color: #111; font-style: italic; background: #f9f9f9; padding: 10px; border-radius: 4px;">{energy['remedy']}</div>
</div>
</div>
                """
                st.markdown(weather_html, unsafe_allow_html=True)
