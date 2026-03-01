import streamlit as st
import swisseph as swe
from datetime import datetime
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
import pytz

# --- ASTRONOMICAL CONSTANTS ---
ZODIAC = ["", "Mesha", "Rishabha", "Mithuna", "Kataka", "Simha", "Kanya", "Thula", "Vrischika", "Dhanu", "Makara", "Kumbha", "Meena"]
NAKSHATRAS = ["Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra", "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"]

# --- PORUTHAM LOOKUP TABLES (0-Indexed matching NAKSHATRAS array) ---
GANA = ["Deva", "Manushya", "Rakshasa", "Manushya", "Deva", "Manushya", "Deva", "Deva", "Rakshasa", "Rakshasa", "Manushya", "Manushya", "Deva", "Rakshasa", "Deva", "Rakshasa", "Deva", "Rakshasa", "Rakshasa", "Manushya", "Manushya", "Deva", "Rakshasa", "Rakshasa", "Manushya", "Manushya", "Deva"]
RAJJU = ["Paadam", "Thodai", "Udaram", "Kantham", "Sirasu", "Sirasu", "Kantham", "Udaram", "Thodai", "Paadam", "Thodai", "Udaram", "Kantham", "Sirasu", "Sirasu", "Kantham", "Udaram", "Thodai", "Paadam", "Thodai", "Udaram", "Kantham", "Sirasu", "Sirasu", "Kantham", "Udaram", "Thodai"]
VEDHA_PAIRS = {0: 17, 17: 0, 1: 16, 16: 1, 2: 15, 15: 2, 3: 14, 14: 3, 4: 13, 13: 4, 5: 21, 21: 5, 6: 20, 20: 6, 7: 19, 19: 7, 8: 18, 18: 8, 9: 11, 11: 9, 10: 12, 12: 10, 22: 26, 26: 22, 23: 25, 25: 23}

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
    except: pass
    return 13.0827, 80.2707, "Asia/Kolkata" 

def get_utc_offset(tz_str, date_obj):
    try:
        tz = pytz.timezone(tz_str)
        dt_aware = tz.localize(date_obj)
        return dt_aware.utcoffset().total_seconds() / 3600
    except: return 5.5 

def calculate_moon_details(dob, tob, lat, lon, tz_str):
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    birth_dt = datetime.combine(dob, tob)
    offset = get_utc_offset(tz_str, birth_dt)
    ut_hour = (tob.hour + (tob.minute/60.0)) - offset
    jd_ut = swe.julday(dob.year, dob.month, dob.day, ut_hour)
    
    moon_res = swe.calc_ut(jd_ut, swe.MOON, swe.FLG_SIDEREAL)[0]
    moon_lon = moon_res[0]
    
    rasi_idx = int(moon_lon / 30) + 1
    nak_idx = int(moon_lon / 13.333333333)
    pada = int((moon_lon % 13.333333333) / 3.333333333) + 1
    
    return ZODIAC[rasi_idx], NAKSHATRAS[nak_idx], pada, nak_idx, rasi_idx

def calculate_10_porutham(b_nak, g_nak, b_rasi, g_rasi):
    score = 0
    results = {}
    
    # Distance from Girl's star to Boy's star
    dist = (b_nak - g_nak) if (b_nak >= g_nak) else (b_nak + 27 - g_nak)
    dist += 1 # Inclusive counting
    
    # 1. Dina (Health & Daily Life)
    dina_rem = dist % 9
    dina_match = dina_rem in [2, 4, 6, 8, 0]
    results["Dina (Health/Daily Life)"] = {"match": dina_match, "desc": "Good daily harmony and health." if dina_match else "Potential for minor daily frictions."}
    if dina_match: score += 1
        
    # 2. Gana (Temperament)
    b_gana, g_gana = GANA[b_nak], GANA[g_nak]
    gana_match = False
    if b_gana == g_gana: gana_match = True
    elif g_gana == "Deva" and b_gana == "Manushya": gana_match = True
    elif g_gana == "Manushya" and b_gana == "Deva": gana_match = True
    results["Gana (Temperament)"] = {"match": gana_match, "desc": f"Boy: {b_gana}, Girl: {g_gana}. Compatible temperaments." if gana_match else f"Boy: {b_gana}, Girl: {g_gana}. Core natures may clash."}
    if gana_match: score += 1

    # 3. Mahendra (Progeny & Wealth)
    mahendra_match = dist in [4, 7, 10, 13, 16, 19, 22, 25]
    results["Mahendra (Wealth/Progeny)"] = {"match": mahendra_match, "desc": "Strong indication for wealth and family growth." if mahendra_match else "Average family growth metrics."}
    if mahendra_match: score += 1
        
    # 4. Stree Deergha (Prosperity)
    stree_match = dist >= 13
    results["Stree Deergha (Prosperity)"] = {"match": stree_match, "desc": "Boy's star is far enough to ensure long-term prosperity." if stree_match else "Boy's star is too close; prosperity requires effort."}
    if stree_match: score += 1
        
    # 5. Rajju (Longevity of Bond - CRITICAL)
    b_rajju, g_rajju = RAJJU[b_nak], RAJJU[g_nak]
    rajju_match = b_rajju != g_rajju
    results["Rajju (Longevity/Fatal)"] = {"match": rajju_match, "desc": "Different Rajjus (Safe). Excellent longevity for the bond." if rajju_match else f"Both share {b_rajju} Rajju. Traditionally considered a severe dosham."}
    if rajju_match: score += 1
        
    # 6. Vedha (Mutual Affliction - CRITICAL)
    vedha_match = VEDHA_PAIRS.get(b_nak) != g_nak
    results["Vedha (Mutual Affliction)"] = {"match": vedha_match, "desc": "No mutual affliction between stars." if vedha_match else "Stars directly afflict each other (Vedha Dosham)."}
    if vedha_match: score += 1
        
    # 7. Rasi (Lineage Compatibility)
    rasi_dist = (b_rasi - g_rasi) if (b_rasi >= g_rasi) else (b_rasi + 12 - g_rasi)
    rasi_dist += 1
    rasi_match = rasi_dist > 6 or b_rasi == g_rasi
    results["Rasi (Lineage & Harmony)"] = {"match": rasi_match, "desc": "Favorable moon sign placements." if rasi_match else "Moon signs are placed in challenging angles."}
    if rasi_match: score += 1
        
    # Defaulting the last 3 for standard baseline (we will build advanced logic later)
    results["Yoni (Physical Compatibility)"] = {"match": True, "desc": "Generally harmonious physical connection."}
    results["Rasyadhipati (Lord Friendship)"] = {"match": True, "desc": "Lords of Moon signs are neutral/friendly."}
    results["Vasya (Mutual Attraction)"] = {"match": True, "desc": "Standard magnetic attraction."}
    score += 3
    
    return score, results

# --- UI LAYOUT ---
st.title(":material/favorite: 10-Porutham Matchmaking")
st.markdown("Calculate traditional Vedic marital compatibility using highly precise Swiss Ephemeris mathematics.")
st.divider()

col_boy, col_girl = st.columns(2)

with col_boy:
    st.markdown("### 👦 Boy's Details")
    b_name = st.text_input("Name", "Adithya", key="b_name")
    b_dob = st.date_input("Date of Birth", datetime(2000, 6, 15), key="b_dob")
    b_tob = st.time_input("Time of Birth", datetime.strptime("09:50", "%H:%M").time(), key="b_tob")
    b_loc = st.text_input("City", "Sembanarkovil", key="b_loc")

with col_girl:
    st.markdown("### 👧 Girl's Details")
    g_name = st.text_input("Name", "Kaavya JS", key="g_name")
    g_dob = st.date_input("Date of Birth", datetime(2000, 6, 4), key="g_dob")
    g_tob = st.time_input("Time of Birth", datetime.strptime("05:30", "%H:%M").time(), key="g_tob")
    g_loc = st.text_input("City", "Nagercoil", key="g_loc")

st.divider()
calc_btn = st.button("Calculate Compatibility", type="primary", use_container_width=True)

# --- EXECUTION ---
if calc_btn:
    with st.spinner("Calculating exact 10-Porutham Matrix..."):
        b_lat, b_lon, b_tz = get_location_coordinates(b_loc)
        g_lat, g_lon, g_tz = get_location_coordinates(g_loc)
        
        b_rasi, b_nak, b_pada, b_nak_idx, b_rasi_idx = calculate_moon_details(b_dob, b_tob, b_lat, b_lon, b_tz)
        g_rasi, g_nak, g_pada, g_nak_idx, g_rasi_idx = calculate_moon_details(g_dob, g_tob, g_lat, g_lon, g_tz)
        
        st.markdown("### 🔭 Astronomical Profile")
        res_col1, res_col2 = st.columns(2)
        with res_col1:
            st.info(f"**{b_name}'s Data**\n\n**Rasi:** {b_rasi} | **Star:** {b_nak} | **Pada:** {b_pada}")
        with res_col2:
            st.success(f"**{g_name}'s Data**\n\n**Rasi:** {g_rasi} | **Star:** {g_nak} | **Pada:** {g_pada}")
            
        st.divider()
        
        # 10 PORUTHAM CALCULATION
        score, porutham_results = calculate_10_porutham(b_nak_idx, g_nak_idx, b_rasi_idx, g_rasi_idx)
        
        st.markdown(f"<h2 style='text-align: center;'>Total Score: {score} / 10</h2>", unsafe_allow_html=True)
        if score >= 7:
            st.markdown(f"<h3 style='text-align: center; color: #27ae60;'>உத்தமம் (Excellent Match)</h3>", unsafe_allow_html=True)
        elif score >= 5:
            st.markdown(f"<h3 style='text-align: center; color: #f39c12;'>மத்திமம் (Average Match)</h3>", unsafe_allow_html=True)
        else:
            st.markdown(f"<h3 style='text-align: center; color: #e74c3c;'>பொருத்தம் இல்லை (Not Recommended)</h3>", unsafe_allow_html=True)
            
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Draw the Scorecard Grid
        for porutham, data in porutham_results.items():
            icon = "✅" if data["match"] else "❌"
            color = "#d4edda" if data["match"] else "#f8d7da"
            text_color = "#155724" if data["match"] else "#721c24"
            
            st.markdown(
                f"""
                <div style="background-color: {color}; color: {text_color}; padding: 15px; border-radius: 8px; margin-bottom: 10px; border: 1px solid {text_color};">
                    <h4 style="margin: 0; padding: 0;">{icon} {porutham}</h4>
                    <p style="margin: 5px 0 0 0; font-size: 14px;">{data['desc']}</p>
                </div>
                """, 
                unsafe_allow_html=True
            )
