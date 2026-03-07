import streamlit as st
import swisseph as swe
from datetime import datetime, timezone, time
from supabase import create_client
import pandas as pd
import plotly.express as px

# --- IMPORTS FROM OUR CUSTOM ENGINE ---
from astro_engine import (
    get_location_coordinates, get_utc_offset, get_daily_executive_weather,
    get_daily_panchangam_metrics, ZODIAC_TA, ZODIAC
)

st.set_page_config(page_title="Daily Executive Weather", layout="wide")

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
            <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin-bottom: 25px; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;">
                <div style="background: #fff; border: 1px solid #eaeaea; border-top: 3px solid {panchangam['tara_color']}; border-radius: 6px; padding: 15px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.02);">
                    <div style="font-size: 11px; color: #888; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px;">Personalized Tarabalam</div>
                    <div style="font-size: 14px; font-weight: bold; color: {panchangam['tara_color']};">{panchangam['tara_name']}</div>
                    <div style="font-size: 12px; color: #666; margin-top: 4px;">{panchangam['tara_desc']}</div>
                </div>
                <div style="background: #fff; border: 1px solid #eaeaea; border-top: 3px solid #8e44ad; border-radius: 6px; padding: 15px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.02);">
                    <div style="font-size: 11px; color: #888; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px;">Current Active Horai</div>
                    <div style="font-size: 16px; font-weight: bold; color: #8e44ad;">{panchangam['horai']}</div>
                </div>
                <div style="background: #fff; border: 1px solid #eaeaea; border-top: 3px solid #2980b9; border-radius: 6px; padding: 15px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.02);">
                    <div style="font-size: 11px; color: #888; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px;">Daily Moon Phase</div>
                    <div style="font-size: 14px; font-weight: bold; color: #2980b9;">{panchangam['nakshatra']}</div>
                    <div style="font-size: 12px; color: #666; margin-top: 4px;">{panchangam['paksha']}</div>
                </div>
            </div>
            """
            st.markdown(metric_html, unsafe_allow_html=True)

            # --- PLOTLY COSMIC CALENDAR ---
            st.markdown("<h3 style='color: #2c3e50; font-family: sans-serif; font-size: 20px; margin-top: 10px; border-bottom: 2px solid #eee; padding-bottom: 8px;'>The Cosmic Calendar (6 AM - 6 PM)</h3>", unsafe_allow_html=True)
            
            df = pd.DataFrame(panchangam["timeline_data"])
            
            # Custom Event Color Mapping
            color_map = {
                "Nalla Neram": "#27ae60", # Green
                "Rahu Kalam": "#e74c3c",  # Red
                "Yemagandam": "#e67e22",  # Orange
                "Sun Horai": "#f1c40f", "Moon Horai": "#bdc3c7", "Mars Horai": "#c0392b",
                "Mercury Horai": "#2ecc71", "Jupiter Horai": "#f39c12", "Venus Horai": "#9b59b6", "Saturn Horai": "#34495e"
            }

            fig = px.timeline(df, x_start="Start", x_end="Finish", y="Category", color="Event", text="Event", color_discrete_map=color_map)
            fig.update_yaxes(autorange="reversed", title_text="") # Reverse so Auspicious is on top
            fig.update_xaxes(tickformat="%I:%M %p", title_text="") # Format time nicely
            fig.update_layout(
                showlegend=False, height=300, margin=dict(l=0, r=20, t=20, b=20),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Helvetica Neue, sans-serif", size=12, color="#333")
            )
            # Make text inside bars white and clean
            fig.update_traces(textfont_color='white', textposition='inside')
            
            st.plotly_chart(fig, use_container_width=True)

            # --- TACTICAL WEATHER CARDS ---
            c1, c2 = st.columns(2)
            focus = daily_weather["focus"]
            comm = daily_weather["communication"]
            
            # Use raw HTML strings instead of f-strings inside Markdown to avoid code block parsing
            st.markdown(f"""
            <div style="font-family: sans-serif;">
                <div style="background: #fff; border: 1px solid #eaeaea; border-left: 5px solid {focus['color']}; padding: 20px; border-radius: 6px; box-shadow: 0 2px 8px rgba(0,0,0,0.04); margin-bottom: 20px;">
                    <div style="font-size: 12px; color: #888; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px;"><b>Strategic Focus:</b> Moon in {daily_weather['positions']['Moon']}</div>
                    <div style="font-size: 18px; font-weight: bold; color: {focus['color']}; margin-bottom: 10px;">{focus['title']}</div>
                    <div style="font-size: 14px; color: #444; line-height: 1.6; margin-bottom: 10px;">{focus['desc']}</div>
                    <div style="font-size: 13px; color: #111; font-style: italic; background: #f9f9f9; padding: 10px; border-radius: 4px;">{focus['remedy']}</div>
                </div>
                <div style="background: #fff; border: 1px solid #eaeaea; border-left: 5px solid #27ae60; padding: 20px; border-radius: 6px; box-shadow: 0 2px 8px rgba(0,0,0,0.04);">
                    <div style="font-size: 12px; color: #888; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px;"><b>Communication:</b> Mercury in {daily_weather['positions']['Mercury']}</div>
                    <div style="font-size: 18px; font-weight: bold; color: #2c3e50; margin-bottom: 10px;">{comm['title']}</div>
                    <div style="font-size: 14px; color: #444; line-height: 1.6; margin-bottom: 10px;">{comm['desc']}</div>
                    <div style="font-size: 13px; color: #111; font-style: italic; background: #f9f9f9; padding: 10px; border-radius: 4px;">{comm['remedy']}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
