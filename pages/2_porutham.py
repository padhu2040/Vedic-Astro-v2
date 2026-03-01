import streamlit as st
import swisseph as swe
from datetime import datetime
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
import pytz

# Constants for UI
ZODIAC = ["", "Mesha", "Rishabha", "Mithuna", "Kataka", "Simha", "Kanya", "Thula", "Vrischika", "Dhanu", "Makara", "Kumbha", "Meena"]
NAKSHATRAS = ["Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra", "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"]

# --- HELPER FUNCTIONS ---
@st.cache_data
def get_location_coordinates(query):
    try:
        geolocator = Nominatim(user_agent="vedic_astro_match")
        location = geolocator.geocode(query)
        if location:
            tf = TimezoneFinder()
            tz_str = tf.timezone_at(lng=location.longitude, lat=location.latitude)
            return location.latitude, location.longitude, tz_str
    except:
        pass
    return 13.0827, 80.2707, "Asia/Kolkata" # Default to Chennai

def get_utc_offset(tz_str, date_obj):
    try:
        tz = pytz.timezone(tz_str)
        dt_aware = tz.localize(date_obj)
        return dt_aware.utcoffset().total_seconds() / 3600
    except: 
        return 5.5 

def calculate_moon_details(dob, tob, lat, lon, tz_str):
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    birth_dt = datetime.combine(dob, tob)
    offset = get_utc_offset(tz_str, birth_dt)
    
    ut_hour = (tob.hour + (tob.minute/60.0)) - offset
    jd_ut = swe.julday(dob.year, dob.month, dob.day, ut_hour)
    
    # Calculate Moon Position
    moon_res = swe.calc_ut(jd_ut, swe.MOON, swe.FLG_SIDEREAL)[0]
    moon_lon = moon_res[0]
    
    rasi_idx = int(moon_lon / 30) + 1
    nak_idx = int(moon_lon / 13.333333333)
    pada = int((moon_lon % 13.333333333) / 3.333333333) + 1
    
    return ZODIAC[rasi_idx], NAKSHATRAS[nak_idx], pada, nak_idx, rasi_idx

# --- UI LAYOUT ---
st.title(":material/favorite: 10-Porutham Matchmaking")
st.markdown("Calculate traditional Vedic marital compatibility using highly precise Swiss Ephemeris mathematics.")
st.divider()

# Dual Input Columns
col_boy, col_girl = st.columns(2)

with col_boy:
    st.markdown("### 👦 Boy's Details")
    b_name = st.text_input("Name", "Adithya", key="b_name")
    b_dob = st.date_input("Date of Birth", datetime(1999, 1, 1), key="b_dob") # Update with exact DOB when testing
    b_tob = st.time_input("Time of Birth", datetime.strptime("09:50", "%H:%M").time(), key="b_tob")
    b_loc = st.text_input("City", "Chennai", key="b_loc")

with col_girl:
    st.markdown("### 👧 Girl's Details")
    g_name = st.text_input("Name", "Kaavya JS", key="g_name")
    g_dob = st.date_input("Date of Birth", datetime(2000, 1, 1), key="g_dob") # Update with exact DOB when testing
    g_tob = st.time_input("Time of Birth", datetime.strptime("12:00", "%H:%M").time(), key="g_tob")
    g_loc = st.text_input("City", "Bangalore", key="g_loc")

st.divider()
calc_btn = st.button("Calculate Compatibility", type="primary", use_container_width=True)

# --- EXECUTION ---
if calc_btn:
    with st.spinner("Calculating precise astronomical coordinates..."):
        # 1. Fetch Coordinates
        b_lat, b_lon, b_tz = get_location_coordinates(b_loc)
        g_lat, g_lon, g_tz = get_location_coordinates(g_loc)
        
        # 2. Calculate Astrological Data
        b_rasi, b_nak, b_pada, b_nak_idx, b_rasi_idx = calculate_moon_details(b_dob, b_tob, b_lat, b_lon, b_tz)
        g_rasi, g_nak, g_pada, g_nak_idx, g_rasi_idx = calculate_moon_details(g_dob, g_tob, g_lat, g_lon, g_tz)
        
        # 3. Display Results beautifully
        st.markdown("### 🔭 Astronomical Profile")
        res_col1, res_col2 = st.columns(2)
        
        with res_col1:
            st.info(f"**{b_name}'s Data**\n\n**Rasi (Moon Sign):** {b_rasi}\n\n**Nakshatra (Star):** {b_nak}\n\n**Pada (Quarter):** {b_pada}")
            
        with res_col2:
            st.success(f"**{g_name}'s Data**\n\n**Rasi (Moon Sign):** {g_rasi}\n\n**Nakshatra (Star):** {g_nak}\n\n**Pada (Quarter):** {g_pada}")
            
        st.warning("⏳ **The 10-Porutham Matrix is ready to be hooked up to these coordinates!**")
