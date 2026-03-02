import streamlit as st
import swisseph as swe
from datetime import datetime, time
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
import pytz
import google.generativeai as genai
from supabase import create_client, Client

# --- SETUP SUPABASE CONNECTION ---
@st.cache_resource
def init_connection():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
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
                    try:
                        parsed_tob = datetime.strptime(tob_str, "%H:%M:%S").time()
                    except ValueError:
                        parsed_tob = datetime.strptime(tob_str, "%H:%M").time()
                    profiles[name] = {"dob": parsed_dob, "tob": parsed_tob, "city": city}
                except: pass
        except: pass
    return profiles

# --- ASTRONOMICAL CONSTANTS ---
ZODIAC = ["", "Mesha", "Rishabha", "Mithuna", "Kataka", "Simha", "Kanya", "Thula", "Vrischika", "Dhanu", "Makara", "Kumbha", "Meena"]
NAKSHATRAS = ["Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra", "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"]

@st.cache_data
def get_location_coordinates(query):
    try:
        geolocator = Nominatim(user_agent="vedic_astro_daily")
        location = geolocator.geocode(query)
        if location:
            tf = TimezoneFinder()
            tz_str = tf.timezone_at(lng=location.longitude, lat=location.latitude)
            return location.latitude, location.longitude, tz_str
    except: pass
    return 13.0827, 80.2707, "Asia/Kolkata" 

def get_utc_offset(tz_str, date_obj):
    try:
        return pytz.timezone(tz_str).localize(date_obj).utcoffset().total_seconds() / 3600
    except: return 5.5 

def calculate_planetary_positions(calc_date, calc_time, lat, lon, tz_str):
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    offset = get_utc_offset(tz_str, datetime.combine(calc_date, calc_time))
    jd_ut = swe.julday(calc_date.year, calc_date.month, calc_date.day, (calc_time.hour + (calc_time.minute/60.0)) - offset)
    
    pos = {}
    for p, pid in {"Sun": swe.SUN, "Moon": swe.MOON, "Mars": swe.MARS, "Mercury": swe.MERCURY, "Jupiter": swe.JUPITER, "Venus": swe.VENUS, "Saturn": swe.SATURN}.items():
        lon_val = swe.calc_ut(jd_ut, pid, swe.FLG_SIDEREAL)[0][0]
        pos[p] = {"lon": lon_val, "rasi_idx": int(lon_val / 30) + 1, "rasi": ZODIAC[int(lon_val / 30) + 1]}
        if p == "Moon": pos[p]["nakshatra"] = NAKSHATRAS[int(lon_val / 13.333333333)]
            
    pos["Lagna"] = {"rasi": ZODIAC[int(swe.houses_ex(jd_ut, lat, lon, b'P', swe.FLG_SIDEREAL)[1][0]/30) + 1]}
    return pos

# --- UI LAYOUT ---
st.title(":material/calendar_today: Daily Planetary Insights")
st.markdown("Navigate your day with cosmic awareness.")
st.divider()

saved_profiles = load_profiles_from_db()
profile_options = ["Custom Entry"] + list(saved_profiles.keys())

today_date = st.date_input("Forecast Date", datetime.now().date())

st.markdown("### :material/account_circle: Your Exact Details")
col_sel, _ = st.columns([1, 1])
with col_sel:
    selected_profile = st.selectbox("Load Saved Profile", profile_options)
    
def_n, def_dob, def_tob, def_loc = "Padmanabhan", datetime(1977, 11, 14).date(), time(1, 45), "Saidapet, Chennai"

if selected_profile != "Custom Entry":
    def_n = selected_profile
    def_dob = saved_profiles[selected_profile]["dob"]
    def_tob = saved_profiles[selected_profile]["tob"]
    def_loc = saved_profiles[selected_profile]["city"]

col_input, _ = st.columns([1, 1])
with col_input:
    # DYNAMIC KEYS FIX
    k = selected_profile.replace(" ", "_")
    u_name = st.text_input("Name", value=def_n, key=f"d_name_{k}")
    u_dob = st.date_input("Date of Birth", value=def_dob, min_value=datetime(1950, 1, 1).date(), key=f"d_dob_{k}")
    u_tob = st.time_input("Time of Birth", value=def_tob, step=60, key=f"d_tob_{k}")
    u_loc = st.text_input("City", value=def_loc, key=f"d_loc_{k}")

calc_btn = st.button("Generate Deep AI Forecast", type="primary", use_container_width=True)

if calc_btn:
    with st.spinner("Aligning chart..."):
        u_lat, u_lon, u_tz = get_location_coordinates(u_loc)
        n_chart = calculate_planetary_positions(u_dob, u_tob, u_lat, u_lon, u_tz)
        t_chart = calculate_planetary_positions(today_date, time(12, 0), u_lat, u_lon, u_tz)
        
        moon_dist = (t_chart['Moon']['rasi_idx'] - n_chart['Moon']['rasi_idx'] + 1) if (t_chart['Moon']['rasi_idx'] >= n_chart['Moon']['rasi_idx']) else (t_chart['Moon']['rasi_idx'] + 12 - n_chart['Moon']['rasi_idx'] + 1)
        
        st.info(f"Today's Moon is in {t_chart['Moon']['rasi']} ({moon_dist}th house from your natal Moon in {n_chart['Moon']['rasi']}).")
        
        if moon_dist == 8:
            st.error("**Alert: Chandrashtama Day**\nThe Moon is in your 8th house. Avoid new beginnings.", icon=":material/warning:")
            
        try:
            GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
            genai.configure(api_key=GEMINI_API_KEY)
            st.markdown("### :material/auto_awesome: Today's Insight")
            
            prompt = f"Write a personalized Vedic daily horoscope for {u_name}. Moon is {moon_dist}th house from Natal moon. Keep it highly practical."
            model = genai.GenerativeModel('gemini-1.5-flash')
            st.markdown(model.generate_content(prompt).text)
        except Exception as e:
            st.error(f"AI Generation Failed: {e}")
