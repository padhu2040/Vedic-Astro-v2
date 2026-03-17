import streamlit as st
import swisseph as swe
from datetime import datetime, timezone, time, date
from supabase import create_client
import google.generativeai as genai
import json

# Ensure these match your actual engine file
from astro_engine import (
    get_location_coordinates, get_utc_offset, get_daily_executive_weather,
    get_daily_panchangam_metrics, get_advanced_personal_metrics, ZODIAC_TA, ZODIAC
)

st.set_page_config(page_title="Daily Cosmos", layout="centered")

# --- SECURITY GATEKEEPER ---
if "user" not in st.session_state or st.session_state.user is None:
    st.warning("🔒 Please log in to access the Daily Cosmos Dashboard.")
    st.stop()

user_id = st.session_state.user.id

# --- SECURE API SETUP ---
API_KEY = st.secrets.get("GEMINI_API_KEY", "")
if not API_KEY:
    try:
        from api_config import GEMINI_API_KEY
        API_KEY = GEMINI_API_KEY
    except Exception: 
        pass

@st.cache_resource
def init_connection():
    try: return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    except Exception: return None

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
                except Exception: pass
        except Exception: pass
    return profiles

# --- SIDEBAR (Consolidated UI) ---
with st.sidebar:
    st.markdown("<div style='font-size: 11px; font-weight: 600; color: #888; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 10px;'>Personal Strategy</div>", unsafe_allow_html=True)
    saved_profiles = load_profiles_from_db()
    profile_options = ["(No Profile Selected)"] + list(saved_profiles.keys())
    selected_profile = st.selectbox("Load Saved Profile", profile_options, label_visibility="collapsed")
    
    if selected_profile != "(No Profile Selected)":
        def_n = selected_profile
        def_dob = saved_profiles[selected_profile]["dob"]
        def_tob = saved_profiles[selected_profile]["tob"]
        def_loc = saved_profiles[selected_profile]["city"]
    else:
        def_n, def_dob, def_tob, def_loc = "", date(2000, 1, 1), time(12, 0), ""

    st.divider()
    st.markdown("<div style='font-size: 11px; font-weight: 600; color: #888; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 10px;'>Cosmic Coordinates</div>", unsafe_allow_html=True)
    target_date = st.date_input("Date", date.today())
    target_city = st.text_input("Location", value=def_loc if def_loc else "Chennai")
    LANG = st.selectbox("Language", ["English", "Tamil"])

st.title("Daily Cosmos")
st.markdown("<div style='color:#7f8c8d; margin-top:-15px; margin-bottom: 20px;'>Your personalized daily executive and energetic weather report.</div>", unsafe_allow_html=True)
st.divider()

with st.spinner("Calculating precision timelines and querying Oracle..."):
    try:
        lat_val, lon_val, tz_val = get_location_coordinates(target_city)
    except Exception:
        lat_val, lon_val, tz_val = 13.0827, 80.2707, "Asia/Kolkata"

    natal_lagna_rasi, natal_moon_rasi, natal_moon_lon = None, None, None
    jd_ut_natal = None
    
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

    pan = get_daily_panchangam_metrics(target_date=target_date, lat_val=lat_val, lon_val=lon_val, tz_name=tz_val, lang=LANG, user_lagna=natal_lagna_rasi, user_moon=natal_moon_rasi, natal_moon_lon=natal_moon_lon)
    
    daily_weather, adv_metrics = None, None
    if def_n:
        daily_weather = get_daily_executive_weather(pan['current_jd_ut'], natal_moon_rasi, natal_lagna_rasi, LANG)
        adv_metrics = get_advanced_personal_metrics(jd_ut_natal, pan['current_jd_ut'], lat_val, lon_val, LANG)

# --- 3-TAB CONSOLIDATED ARCHITECTURE ---
t1_name = "Overview" if LANG=="English" else "பஞ்சாங்கம்"
t2_name = "Strategy" if LANG=="English" else "வியூகம்"
t3_name = "Horai" if LANG=="English" else "ஓரை"

tab1, tab2, tab3 = st.tabs([t1_name, t2_name, t3_name])

# --- TAB 1: OVERVIEW ---
with tab1:
    lbl = {
        "ast": "Astronomical Elements" if LANG=="English" else "வானியல்",
        "sun_r": "Sunrise" if LANG=="English" else "உதயம்",
        "sun_s": "Sunset" if LANG=="English" else "அஸ்தமனம்",
        "yoga": "Nithya Yoga" if LANG=="English" else "நித்திய யோகம்",
        "tara": "Personal Tarabalam" if LANG=="English" else "தாராபலம்",
        "vrata": "Special Day / Deity" if LANG=="English" else "விசேஷ நாள் / தெய்வம்",
        "ausp": "Auspicious Timings" if LANG=="English" else "நல்ல நேரங்கள்",
        "inausp": "Obstacles & Cautions" if LANG=="English" else "தடை நேரங்கள்",
        "sr": "Sraardha Tithi" if LANG=="English" else "ஸ்ரார்த்த திதி",
        "suba": "Subakariyam" if LANG=="English" else "சுபகாரியம்"
    }

    tara_row = f'<div class="m-card" style="grid-column: span 2;"><div class="c-head">{lbl["tara"]}</div><div class="card-row" style="flex-direction:column; align-items:flex-start; border:none; padding-top:0; padding-bottom:0;"><div style="display:flex; width:100%; justify-content:space-between; margin-bottom:6px;"><span class="row-lbl" style="font-size:14px; font-weight:500;">Alignment for your Star</span><span class="row-val" style="color:{pan["tara_color"]}; font-size:15px; font-weight:bold;">{pan["tara_name"]}</span></div><div style="font-size:12.5px; color:#555; line-height:1.4;">{pan["tara_action"]}</div></div></div>' if def_n else ""
    moon_color = "#e0e0e0" if pan['is_waxing'] else "#34495e"
    moon_icon = f'<div style="width:12px; height:12px; border-radius:50%; background:{moon_color}; border:1px solid #ccc; display:inline-block; margin-right:6px;"></div>'
    v_icon_html = f'<div style="font-size:32px; filter:grayscale(100%) brightness(80%); opacity:0.85; margin-right:15px;">{pan["v_icon"]}</div>'

    grid_html = f"""<style>.grid-container {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; margin-bottom: 20px; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; }}.m-card {{ background: #ffffff; border: 1px solid #eaeaea; border-radius: 4px; padding: 16px; display: flex; flex-direction: column; box-shadow: 0 1px 2px rgba(0,0,0,0.02); min-height: 120px; }}.c-head {{ font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; color: #888; font-weight: 500; margin-bottom: 12px; border-bottom: 1px solid #f9f9f9; padding-bottom: 4px; }}.card-row {{ display: flex; justify-content: space-between; align-items: baseline; border-bottom: 1px solid #f7f7f7; padding: 8px 0; }}.card-row:last-child {{ border-bottom: none; }}.row-lbl {{ font-size: 12.5px; color: #7f8c8d; font-weight: 400; }}.row-val {{ font-size: 13.5px; color: #222; font-weight: 500; text-align: right; }}.time-sub {{ font-size: 10.5px; color: #999; width: 100%; text-align: right; margin-top: 3px; font-weight: 400; }}</style>
<div class="grid-container">
<div class="m-card" style="flex-direction: row; align-items: center; padding: 12px;"><div style="flex: 1; border-right: 1px solid #eee; padding-right: 12px; text-align: center;"><div style="font-size: 32px; font-weight: 300; color: #111; line-height: 1;">{pan['day_num']}</div><div style="font-size: 12px; color: #7f8c8d; font-weight: 400; margin-top: 4px;">{pan['day_en']}<br>{pan['month_year_en']}</div></div><div style="flex: 1; padding-left: 12px; text-align: center;"><div style="font-size: 32px; font-weight: 300; color: #2c3e50; line-height: 1;">{pan['date_ta']}</div><div style="font-size: 12px; color: #7f8c8d; font-weight: 400; margin-top: 4px;">{pan['day_ta']}<br>{pan['tamil_year']} {pan['month_ta']}</div></div></div>
<div class="m-card" style="justify-content: center;"><div style="font-size: 20px; font-weight: 400; color: #111; margin-bottom: 4px; display:flex; align-items:center;">{moon_icon}{pan['tithi_short']}</div><div style="font-size: 12.5px; color: #555; margin-bottom: 8px;">{pan['paksha']}</div><div style="font-size: 11px; color: #888; border-top: 1px dashed #eee; padding-top: 6px; line-height: 1.5;">Ends @ {pan['t_end']} ➔ {pan['t_next']}<br><span style="color:#2c3e50;">{lbl['sr']}: {pan['sr_tithi']}</span><br>{pan['countdown']}<br>{pan['dasami_str']}</div></div>
<div class="m-card" style="grid-column: span 2;"><div class="c-head">{lbl['vrata']}</div><div style="display:flex; align-items:center; margin-bottom:12px; border-bottom: 1px solid #f9f9f9; padding-bottom:10px;">{v_icon_html}<div><div style="font-size:16px; font-weight:500; color:#222; margin-bottom:4px;">{pan['v_name']}</div><div style="font-size:12.5px; color:#f39c12; font-style:italic;">{pan['v_mantra']}</div></div></div><div class="card-row" style="border:none;"><span class="row-lbl">{lbl['suba']}</span><span class="row-val" style="font-size:12px; color:#555; text-align:right;">{pan['suba_str']}</span></div></div>
<div class="m-card" style="grid-column: span 2;"><div class="c-head">{lbl['ast']}</div><div style="flex-grow: 1; display: flex; flex-direction: column;"><div class="card-row"><span class="row-lbl">{lbl['sun_r']} / {lbl['sun_s']}</span><span class="row-val">{pan['sunrise']} - {pan['sunset']}</span></div><div class="card-row" style="flex-direction:column; align-items:flex-start;"><div style="display:flex; width:100%; justify-content:space-between;"><span class="row-lbl">Rasi & Star</span><span class="row-val">{pan['rasi']} / {pan['nakshatra']}</span></div><div class="time-sub">Star ends @ {pan['n_end']} ➔ {pan['n_next']}<br>Rasi ends @ {pan['r_end']} ➔ {pan['r_next']}</div></div><div class="card-row" style="flex-direction:column; align-items:flex-start; border-bottom:none;"><div style="display:flex; width:100%; justify-content:space-between;"><span class="row-lbl">{lbl['yoga']}</span><span class="row-val">{pan['yoga']}</span></div><div class="time-sub">Ends @ {pan['y_end']} ➔ {pan['y_next']}</div><div style="font-size: 11.5px; color: #444; margin-top: 6px; line-height: 1.4;">{pan['y_action']}</div><div style="font-size: 10.5px; color: #d35400; margin-top: 3px; font-style: italic;">{pan['y_remedy']}</div></div></div></div>
<div class="m-card" style="border-top: 2px solid #27ae60;"><div class="c-head" style="color: #27ae60;">{lbl['ausp']}</div><div style="flex-grow: 1; display: flex; flex-direction: column; justify-content: flex-end;"><div class="card-row"><span class="row-lbl">Nalla Neram</span><span class="row-val" style="font-size:12.5px;">{pan['nn']}</span></div><div class="card-row" style="border-bottom:none;"><span class="row-lbl">Gowri Neram</span><span class="row-val" style="font-size:12.5px;">{pan['gnn']}</span></div></div></div>
<div class="m-card" style="border-top: 2px solid #c0392b;"><div class="c-head" style="color: #c0392b;">{lbl['inausp']}</div><div style="flex-grow: 1; display: flex; flex-direction: column; justify-content: flex-end;"><div class="card-row"><span class="row-lbl">Rahu Kalam</span><span class="row-val">{pan['rk']}</span></div><div class="card-row"><span class="row-lbl">Yemagandam</span><span class="row-val">{pan['yg']}</span></div><div class="card-row" style="flex-direction:column; align-items:flex-start; border:none; padding-top:12px; margin-top:6px; border-top: 1px dashed #eee;"><span class="row-lbl" style="color:#c0392b; font-weight:500; margin-bottom:4px;">Chandrashtama for:</span><span class="row-val" style="text-align:left; font-size:11.5px;">{pan['ch_naks']}</span></div></div></div>
{tara_row}
</div>"""
    st.markdown(grid_html, unsafe_allow_html=True)


# --- TAB 2: STRATEGY (AI Upgraded) ---
with tab2:
    if not def_n:
        st.info("Select your profile from the sidebar to generate your deep personal analytics.")
    else:
        focus, comm = daily_weather["focus"], daily_weather["communication"]
        
        # --- AI MORNING BRIEFING ---
        st.markdown("### The Morning Briefing")
        ai_briefing = None
        if API_KEY:
            try:
                genai.configure(api_key=API_KEY)
                # Temperature 0.4 allows the AI to use slightly different phrasing day-to-day
                model = genai.GenerativeModel('gemini-2.5-flash', generation_config={"temperature": 0.4}) 
                
                briefing_prompt = f"""
                Act as an Elite Executive Astrologer. Write a 1-paragraph morning briefing for your client, {def_n}.
                Today's Date: {target_date}.
                Client's Data: 
                - Ashtakavarga Energy: {adv_metrics['bav_title']} ({adv_metrics['bav_desc']})
                - Macro Season: {adv_metrics['dasha_title']}
                - Daily Execution Focus: {focus['title']}
                
                Synthesize this into a highly actionable, empowering, and deeply personalized 3-sentence executive summary. Speak directly to them in the second person ('You'). Do not use generic astrology fluff; sound like a high-level strategist.
                """
                resp = model.generate_content(briefing_prompt)
                ai_briefing = resp.text.strip()
            except Exception as e:
                ai_briefing = "AI Oracle offline. Rely on the raw metrics below for today's strategy."
        
        if ai_briefing:
            st.info(ai_briefing)
        
        st.divider()
        st.markdown("### Energetic Breakdown")
        
        weather_html = f"""<style>.t-card {{ background: #fff; border: 1px solid #eaeaea; padding: 18px; border-radius: 4px; margin-bottom: 15px; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; box-shadow: 0 1px 2px rgba(0,0,0,0.01); }}.t-head {{ font-size: 11px; color: #888; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 6px; font-weight: 500; display: flex; justify-content: space-between; }}.t-title {{ font-size: 17px; font-weight: 500; margin-bottom: 8px; }}.t-desc {{ font-size: 13.5px; color: #444; line-height: 1.5; margin-bottom: 12px; font-weight: 300; }}.t-rem {{ font-size: 12.5px; color: #222; font-style: italic; background: #fafafa; padding: 10px; border-radius: 4px; border: 1px solid #f5f5f5; }}</style>
<div class="t-card" style="border-left: 3px solid {adv_metrics['bav_color']}; background: #fdfdfd;"><div class="t-head"><span>Ashtakavarga Strength</span> <span>Lunar Transit</span></div><div class="t-title" style="color: {adv_metrics['bav_color']};">{adv_metrics['bav_title']}</div><div class="t-desc">{adv_metrics['bav_desc']}</div><div class="t-rem" style="color: {adv_metrics['bav_color']}; background: none; border: none; padding: 0;"><b>Action:</b> {adv_metrics['bav_rem']}</div></div>
<div class="t-card" style="border-left: 3px solid #8e44ad;"><div class="t-head"><span>Current Life Season</span> <span>Vimshottari</span></div><div class="t-title" style="color: #8e44ad;">{adv_metrics['dasha_title']}</div><div class="t-desc">{adv_metrics['dasha_desc']}</div></div>
<div class="t-card" style="border-left: 3px solid #f39c12;"><div class="t-head"><span>Spatial Energy</span> <span>Compass</span></div><div class="t-title" style="color: #d35400;">{adv_metrics['dir_title']}</div><div class="t-desc" style="margin-bottom:0;">{adv_metrics['dir_desc']}</div></div>
<div class="t-card" style="border-left: 3px solid {focus['color']};"><div class="t-head"><span>Daily Execution</span> <span>Moon in {daily_weather['positions']['Moon']}</span></div><div class="t-title" style="color: {focus['color']};">{focus['title']}</div><div class="t-desc">{focus['desc']}</div><div class="t-rem">{focus['remedy']}</div></div>
<div class="t-card" style="border-left: 3px solid #27ae60;"><div class="t-head"><span>Communication</span> <span>Mercury in {daily_weather['positions']['Mercury']}</span></div><div class="t-title" style="color: #2c3e50;">{comm['title']}</div><div class="t-desc">{comm['desc']}</div><div class="t-rem">{comm['remedy']}</div></div>"""
        st.markdown(weather_html, unsafe_allow_html=True)


# --- TAB 3: HORAI ---
with tab3:
    if def_n: 
        st.markdown("<div style='font-size: 12px; color: #7f8c8d; margin-bottom: 15px;'>Note: Highlighted <span style='background: #2c3e50; color: #fff; padding: 2px 4px; border-radius: 2px; font-size: 9px;'>POWER</span> blocks indicate highly favorable timings based on your Lagna and Moon Rasi.</div>", unsafe_allow_html=True)
    
    schedule_html = "<div style='font-family: \"Helvetica Neue\", Helvetica, Arial, sans-serif; max-height: 400px; overflow-y: auto; padding-right: 5px;'>"
    for row in pan["schedule"]:
        bg_col, border, indicator = "#ffffff", "border-bottom: 1px solid #f2f2f2;", ""
        if row['is_current']:
            bg_col, border = "#f9fbf9", f"border-left: 3px solid {row['color']}; border-bottom: 1px solid #e0e0e0;"
            indicator = "<span style='border: 1px solid #27ae60; color: #27ae60; padding: 1px 4px; border-radius: 2px; font-size: 9px; font-weight: 600; margin-left: 8px;'>NOW</span>"
        if row.get('is_power', False):
            indicator += " <span style='background: #2c3e50; color: #fff; padding: 2px 4px; border-radius: 2px; font-size: 9px; font-weight: 600; margin-left: 6px;'>POWER</span>"
        schedule_html += f"<div style='display: flex; justify-content: space-between; align-items: center; padding: 12px 10px; background-color: {bg_col}; {border} margin-bottom: 4px; border-radius: 4px;'><div style='display:flex; flex-direction:column;'><span style='font-size: 11px; color: #999; font-weight: 400; margin-bottom: 2px;'>{row['time']} {indicator}</span><span style='font-size: 15px; font-weight: 500; color: {row['color']};'>{row['lord']}</span></div><div style='text-align: right;'><span style='font-size: 12.5px; color: #555; font-weight: 400;'>{row['activity']}</span></div></div>"
    
    st.markdown(schedule_html + "</div>", unsafe_allow_html=True)
