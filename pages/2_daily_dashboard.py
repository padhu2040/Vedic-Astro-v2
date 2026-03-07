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
            panchangam = get_daily_panchangam_metrics(current_jd_ut, natal_moon_lon, tz_val)

            # --- TOP METRICS GRID ---
            metric_html = f"""
            <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin-bottom: 25px; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;">
                <div style="background: #fff; border: 1px solid #eaeaea; border-top: 3px solid {panchangam['tara_color']}; border-radius: 6px; padding: 15px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.02);">
                    <div style="font-size: 11px; color: #888; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px;">Tarabalam</div>
                    <div style="font-size: 13px; font-weight: bold; color: {panchangam['tara_color']};">{panchangam['tara_name']}</div>
                    <div style="font-size: 11px; color: #666; margin-top: 4px;">{panchangam['tara_desc']}</div>
                </div>
                <div style="background: #fff; border: 1px solid #eaeaea; border-top: 3px solid #2c3e50; border-radius: 6px; padding: 15px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.02);">
                    <div style="font-size: 11px; color: #888; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px;">Nalla Neram</div>
                    <div style="font-size: 13px; font-weight: bold; color: #2c3e50;">{panchangam['nalla_neram']}</div>
                </div>
                <div style="background: #fff; border: 1px solid #eaeaea; border-top: 3px solid #8e44ad; border-radius: 6px; padding: 15px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.02);">
                    <div style="font-size: 11px; color: #888; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px;">Active Horai</div>
                    <div style="font-size: 15px; font-weight: bold; color: #8e44ad;">{panchangam['horai']}</div>
                </div>
                <div style="background: #fff; border: 1px solid #eaeaea; border-top: 3px solid #2980b9; border-radius: 6px; padding: 15px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.02);">
                    <div style="font-size: 11px; color: #888; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px;">Moon ({panchangam['nakshatra']})</div>
                    <div style="font-size: 13px; font-weight: bold; color: #2980b9;">{panchangam['moon_phase_ta']}</div>
                </div>
            </div>
            """
            st.markdown(metric_html, unsafe_allow_html=True)

            # --- TACTICAL WEATHER CARDS ---
            focus = daily_weather["focus"]
            comm = daily_weather["communication"]
            
            st.markdown(f"""
            <div style="font-family: sans-serif;">
                <div style="background: #fff; border: 1px solid #eaeaea; border-left: 5px solid {focus['color']}; padding: 20px; border-radius: 6px; box-shadow: 0 2px 8px rgba(0,0,0,0.04); margin-bottom: 15px;">
                    <div style="font-size: 12px; color: #888; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px;"><b>Strategic Focus:</b> Moon in {daily_weather['positions']['Moon']}</div>
                    <div style="font-size: 18px; font-weight: bold; color: {focus['color']}; margin-bottom: 10px;">{focus['title']}</div>
                    <div style="font-size: 14px; color: #444; line-height: 1.6; margin-bottom: 10px;">{focus['desc']}</div>
                    <div style="font-size: 13px; color: #111; font-style: italic; background: #f9f9f9; padding: 10px; border-radius: 4px;">{focus['remedy']}</div>
                </div>
                <div style="background: #fff; border: 1px solid #eaeaea; border-left: 5px solid #27ae60; padding: 20px; border-radius: 6px; box-shadow: 0 2px 8px rgba(0,0,0,0.04); margin-bottom: 30px;">
                    <div style="font-size: 12px; color: #888; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px;"><b>Communication:</b> Mercury in {daily_weather['positions']['Mercury']}</div>
                    <div style="font-size: 18px; font-weight: bold; color: #2c3e50; margin-bottom: 10px;">{comm['title']}</div>
                    <div style="font-size: 14px; color: #444; line-height: 1.6; margin-bottom: 10px;">{comm['desc']}</div>
                    <div style="font-size: 13px; color: #111; font-style: italic; background: #f9f9f9; padding: 10px; border-radius: 4px;">{comm['remedy']}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # --- THE COSMIC CALENDAR (VERTICAL TIMELINE) ---
            st.markdown("<h3 style='color: #2c3e50; font-family: sans-serif; font-size: 20px; margin-top: 10px; border-bottom: 2px solid #eee; padding-bottom: 8px;'>The Cosmic Calendar (6 AM - 6 PM)</h3>", unsafe_allow_html=True)
            
            schedule_html = "<div style='font-family: sans-serif;'>"
            for row in panchangam["schedule"]:
                badges_html = ""
                for b in row["badges"]:
                    badges_html += f"<span style='background: {b['bg']}; color: {b['color']}; font-size: 11px; padding: 3px 6px; border-radius: 4px; font-weight: bold; margin-left: 6px; white-space: nowrap; display: inline-block; margin-bottom: 4px;'>{b['text']}</span>"
                
                schedule_html += f"""
                <div style="display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; padding: 12px 15px; margin-bottom: 8px; border-radius: 6px; background-color: {row['style']['bg']}; border-left: 4px solid {row['style']['border']}; box-shadow: 0 1px 3px rgba(0,0,0,0.02);">
                    <div style="flex: 1; min-width: 100px; font-size: 13px; color: #555; font-weight: bold;">{row['time']}</div>
                    <div style="flex: 1; min-width: 120px; font-size: 14px; color: #333; font-weight: bold;">{row['lord']}</div>
                    <div style="flex: 2; text-align: right; line-height: 1.8;">{badges_html}</div>
                </div>
                """
            schedule_html += "</div>"
            st.markdown(schedule_html, unsafe_allow_html=True)
