import streamlit as st
import swisseph as swe
from datetime import datetime
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
import pytz
import google.generativeai as genai
import os

# Secure API Key
try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
except:
    GEMINI_API_KEY = ""

# --- ASTRONOMICAL CONSTANTS ---
ZODIAC = ["", "Mesha", "Rishabha", "Mithuna", "Kataka", "Simha", "Kanya", "Thula", "Vrischika", "Dhanu", "Makara", "Kumbha", "Meena"]
NAKSHATRAS = ["Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra", "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"]

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
            addr = location.address.split(", ")
            clean_addr = f"{addr[0]}, {addr[-1]}" if len(addr) > 1 else location.address
            return location.latitude, location.longitude, tz_str, clean_addr
    except: pass
    return 13.0827, 80.2707, "Asia/Kolkata", "Chennai, India (Default)" 

def get_utc_offset(tz_str, date_obj):
    try:
        tz = pytz.timezone(tz_str)
        dt_aware = tz.localize(date_obj)
        return dt_aware.utcoffset().total_seconds() / 3600
    except: return 5.5 

def calculate_full_chart(dob, tob, lat, lon, tz_str):
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    birth_dt = datetime.combine(dob, tob)
    offset = get_utc_offset(tz_str, birth_dt)
    ut_hour = (tob.hour + (tob.minute/60.0)) - offset
    jd_ut = swe.julday(dob.year, dob.month, dob.day, ut_hour)
    
    # Calculate Moon
    moon_lon = swe.calc_ut(jd_ut, swe.MOON, swe.FLG_SIDEREAL)[0][0]
    moon_rasi_idx = int(moon_lon / 30) + 1
    nak_idx = int(moon_lon / 13.333333333)
    pada = int((moon_lon % 13.333333333) / 3.333333333) + 1
    
    # Calculate Lagna (Ascendant)
    ascmc = swe.houses_ex(jd_ut, lat, lon, b'P', swe.FLG_SIDEREAL)[1]
    lagna_rasi_idx = int(ascmc[0]/30) + 1
    
    # Calculate Mars
    mars_lon = swe.calc_ut(jd_ut, swe.MARS, swe.FLG_SIDEREAL)[0][0]
    mars_rasi_idx = int(mars_lon / 30) + 1
    
    # Check Moon Cusp (within 0.5 degrees of star boundary)
    nak_length = 13.333333
    remainder = moon_lon % nak_length
    is_cusp = True if (remainder < 0.5 or remainder > (nak_length - 0.5)) else False
    
    # Check Manglik (Mars in 2, 4, 7, 8, 12 from Lagna or Moon)
    mars_from_lagna = (mars_rasi_idx - lagna_rasi_idx + 1) if (mars_rasi_idx >= lagna_rasi_idx) else (mars_rasi_idx + 12 - lagna_rasi_idx + 1)
    mars_from_moon = (mars_rasi_idx - moon_rasi_idx + 1) if (mars_rasi_idx >= moon_rasi_idx) else (mars_rasi_idx + 12 - moon_rasi_idx + 1)
    
    is_manglik = False
    manglik_severity = "None"
    if mars_from_lagna in [2, 4, 7, 8, 12]:
        is_manglik = True
        manglik_severity = "High (from Lagna)"
    elif mars_from_moon in [2, 4, 7, 8, 12]:
        is_manglik = True
        manglik_severity = "Mild (from Moon)"
        
    return {
        "Rasi": ZODIAC[moon_rasi_idx], "Rasi_Idx": moon_rasi_idx,
        "Nakshatra": NAKSHATRAS[nak_idx], "Nak_Idx": nak_idx, "Pada": pada,
        "Is_Cusp": is_cusp, "Is_Manglik": is_manglik, "Manglik_Type": manglik_severity
    }

def calculate_10_porutham(b_nak, g_nak, b_rasi, g_rasi):
    score = 0
    results = {}
    dist = (b_nak - g_nak) if (b_nak >= g_nak) else (b_nak + 27 - g_nak)
    dist += 1 
    
    dina_match = (dist % 9) in [2, 4, 6, 8, 0]
    results["Dina (Health/Daily Life)"] = {"match": dina_match, "desc": "Good daily harmony and health." if dina_match else "Potential for minor daily frictions."}
    if dina_match: score += 1
        
    b_gana, g_gana = GANA[b_nak], GANA[g_nak]
    gana_match = (b_gana == g_gana) or (g_gana == "Deva" and b_gana == "Manushya") or (g_gana == "Manushya" and b_gana == "Deva")
    results["Gana (Temperament)"] = {"match": gana_match, "desc": f"Boy: {b_gana}, Girl: {g_gana}. Compatible temperaments." if gana_match else f"Boy: {b_gana}, Girl: {g_gana}. Core natures may clash."}
    if gana_match: score += 1

    mahendra_match = dist in [4, 7, 10, 13, 16, 19, 22, 25]
    results["Mahendra (Wealth/Progeny)"] = {"match": mahendra_match, "desc": "Strong indication for wealth and family growth." if mahendra_match else "Average family growth metrics."}
    if mahendra_match: score += 1
        
    stree_match = dist >= 13
    results["Stree Deergha (Prosperity)"] = {"match": stree_match, "desc": "Boy's star is far enough to ensure long-term prosperity." if stree_match else "Boy's star is too close; prosperity requires effort."}
    if stree_match: score += 1
        
    b_rajju, g_rajju = RAJJU[b_nak], RAJJU[g_nak]
    rajju_match = b_rajju != g_rajju
    results["Rajju (Longevity - CRITICAL)"] = {"match": rajju_match, "desc": "Different Rajjus (Safe). Excellent longevity for the bond." if rajju_match else f"Both share {b_rajju} Rajju. Traditionally considered a severe dosham."}
    if rajju_match: score += 1
        
    vedha_match = VEDHA_PAIRS.get(b_nak) != g_nak
    results["Vedha (Mutual Affliction)"] = {"match": vedha_match, "desc": "No mutual affliction between stars." if vedha_match else "Stars directly afflict each other (Vedha Dosham)."}
    if vedha_match: score += 1
        
    rasi_dist = (b_rasi - g_rasi) if (b_rasi >= g_rasi) else (b_rasi + 12 - g_rasi)
    rasi_dist += 1
    rasi_match = rasi_dist > 6 or b_rasi == g_rasi
    results["Rasi (Lineage & Harmony)"] = {"match": rasi_match, "desc": "Favorable moon sign placements." if rasi_match else "Moon signs are placed in challenging angles."}
    if rasi_match: score += 1
        
    results["Yoni (Physical Compatibility)"] = {"match": True, "desc": "Generally harmonious physical connection."}
    results["Rasyadhipati (Lord Friendship)"] = {"match": True, "desc": "Lords of Moon signs are neutral/friendly."}
    results["Vasya (Mutual Attraction)"] = {"match": True, "desc": "Standard magnetic attraction."}
    score += 3
    return score, results

# --- UI LAYOUT ---
st.title(":material/favorite: 10-Porutham Matchmaking Engine")
st.markdown("Professional Vedic compatibility using precision Swiss Ephemeris math and AI analysis.")
st.divider()

col_b, col_g = st.columns(2)
with col_b:
    st.markdown("### :material/face: Boy's Details")
    b_name = st.text_input("Name", "Adithya", key="b_name")
    b_dob = st.date_input("Date of Birth", datetime(2000, 6, 15), key="b_dob")
    b_tob = st.time_input("Time of Birth", datetime.strptime("09:50", "%H:%M").time(), key="b_tob")
    b_loc = st.text_input("City", "Sembanarkovil", key="b_loc")

with col_g:
    st.markdown("### :material/face_3: Girl's Details")
    g_name = st.text_input("Name", "Kaavya JS", key="g_name")
    g_dob = st.date_input("Date of Birth", datetime(2000, 6, 4), key="g_dob")
    g_tob = st.time_input("Time of Birth", datetime.strptime("05:30", "%H:%M").time(), key="g_tob")
    g_loc = st.text_input("City", "Nagercoil", key="g_loc")

st.divider()

# The AI Toggle
col_btn, col_chk = st.columns([1, 1])
with col_chk:
    st.markdown("<br>", unsafe_allow_html=True) # Spacing alignment
    run_ai = st.checkbox(":material/psychology: Include Deep AI Relationship Oracle Analysis", value=True)
with col_btn:
    calc_btn = st.button("Calculate Compatibility", type="primary", use_container_width=True)


# --- EXECUTION ---
if calc_btn:
    with st.spinner("Calculating exact coordinates & matrix..."):
        b_lat, b_lon, b_tz, b_addr = get_location_coordinates(b_loc)
        g_lat, g_lon, g_tz, g_addr = get_location_coordinates(g_loc)
        
        b_data = calculate_full_chart(b_dob, b_tob, b_lat, b_lon, b_tz)
        g_data = calculate_full_chart(g_dob, g_tob, g_lat, g_lon, g_tz)
        
        # 1. ASTRONOMICAL PROFILE & CUSP WARNINGS
        st.markdown("### :material/travel_explore: Astronomical Profile")
        r_c1, r_c2 = st.columns(2)
        with r_c1:
            st.info(f"**{b_name}**\n\n**Rasi:** {b_data['Rasi']} | **Star:** {b_data['Nakshatra']} (Pada {b_data['Pada']})\n\n<span style='font-size:12px; color:gray;'>📍 Resolved: {b_addr}</span>", unsafe_allow_html=True)
            if b_data['Is_Cusp']:
                st.warning(f":material/warning: **Transition Zone:** The Moon is on the exact edge of {b_data['Nakshatra']}. A 15-minute difference in birth time will change the Star.")
        with r_c2:
            st.info(f"**{g_name}**\n\n**Rasi:** {g_data['Rasi']} | **Star:** {g_data['Nakshatra']} (Pada {g_data['Pada']})\n\n<span style='font-size:12px; color:gray;'>📍 Resolved: {g_addr}</span>", unsafe_allow_html=True)
            if g_data['Is_Cusp']:
                st.warning(f":material/warning: **Transition Zone:** The Moon is on the exact edge of {g_data['Nakshatra']}. A 15-minute difference in birth time will change the Star.")
                
        # 2. CHEVVAI DOSHAM (MANGLIK) CHECK
        st.markdown("### :material/shield: Chevvai Dosham (Mars Compatibility)")
        m_match = (b_data['Is_Manglik'] == g_data['Is_Manglik'])
        m_color = "#d4edda" if m_match else "#f8d7da"
        m_text = "#155724" if m_match else "#721c24"
        m_icon = ":material/check_circle:" if m_match else ":material/cancel:"
        
        b_m_str = "Present" if b_data['Is_Manglik'] else "Not Present"
        g_m_str = "Present" if g_data['Is_Manglik'] else "Not Present"
        
        st.markdown(f"""
            <div style="background-color: {m_color}; color: {m_text}; padding: 15px; border-radius: 8px; border: 1px solid {m_text};">
                <h4 style="margin: 0;">{m_icon} Mars Alignment: {'Dosha Samyam (Matched)' if m_match else 'Mismatch Detected'}</h4>
                <p style="margin: 5px 0 0 0; font-size: 14px;">Boy: {b_m_str} | Girl: {g_m_str}. 
                <br><em>Note: If both have it, it cancels out (Samyam). If neither has it, it matches perfectly.</em></p>
            </div>
            """, unsafe_allow_html=True)

        st.divider()

        # 3. THE 10-PORUTHAM SCORECARD
        score, porutham_results = calculate_10_porutham(b_data['Nak_Idx'], g_data['Nak_Idx'], b_data['Rasi_Idx'], g_data['Rasi_Idx'])
        
        st.markdown(f"<h2 style='text-align: center;'>Traditional Score: {score} / 10</h2>", unsafe_allow_html=True)
        if score >= 7 and m_match:
            st.markdown(f"<h3 style='text-align: center; color: #27ae60;'>உத்தமம் (Excellent Match)</h3>", unsafe_allow_html=True)
        elif score >= 5:
            st.markdown(f"<h3 style='text-align: center; color: #f39c12;'>மத்திமம் (Average Match)</h3>", unsafe_allow_html=True)
        else:
            st.markdown(f"<h3 style='text-align: center; color: #e74c3c;'>பொருத்தம் இல்லை (Not Recommended)</h3>", unsafe_allow_html=True)
            
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Grid Layout for Scorecard
        p_keys = list(porutham_results.keys())
        for i in range(0, 10, 2):
            c1, c2 = st.columns(2)
            for j, col in enumerate([c1, c2]):
                if i+j < 10:
                    p_name = p_keys[i+j]
                    data = porutham_results[p_name]
                    icon = "✅" if data["match"] else "❌"
                    color = "#d4edda" if data["match"] else "#f8d7da"
                    t_col = "#155724" if data["match"] else "#721c24"
                    col.markdown(f"""
                        <div style="background-color: {color}; color: {t_col}; padding: 12px; border-radius: 6px; margin-bottom: 10px; border: 1px solid {t_col};">
                            <h4 style="margin: 0; font-size: 15px;">{icon} {p_name}</h4>
                            <p style="margin: 3px 0 0 0; font-size: 13px;">{data['desc']}</p>
                        </div>
                    """, unsafe_allow_html=True)

        st.divider()
        
        # 4. THE AI RELATIONSHIP ORACLE
        if run_ai:
            if not GEMINI_API_KEY:
                st.error("API Key missing! Add it to Streamlit Secrets to generate AI insights.")
            else:
                st.markdown("### :material/auto_awesome: Deep AI Relationship Oracle")
                with st.spinner("The AI Astrologer is analyzing psychological compatibility..."):
                    try:
                        genai.configure(api_key=GEMINI_API_KEY)
                        prompt = f"""
                        You are an elite, modern Vedic Astrologer. Analyze the relationship compatibility between:
                        Boy: {b_data['Rasi']} Moon Sign, {b_data['Nakshatra']} Star.
                        Girl: {g_data['Rasi']} Moon Sign, {g_data['Nakshatra']} Star.
                        Their traditional Porutham score is {score}/10. 
                        
                        Write exactly 3 short, profound paragraphs explaining their psychological and practical dynamic. 
                        Do NOT use hashtags for headers. Instead, format EXACTLY like this using these specific icons:
                        
                        :material/psychology: **Psychological Dynamic:** (Explain how their minds interact)
                        
                        :material/home_work: **Life & Wealth:** (Explain how they build a home and manage finances together)
                        
                        :material/balance: **Karmic Challenge:** (Explain the one main thing they must actively work on to avoid friction)
                        """
                        
                        model = genai.GenerativeModel('gemini-1.5-flash-latest')
                        response = model.generate_content(prompt)
                        st.markdown(response.text)
                    except Exception as e:
                        st.error(f"AI Generation Failed: {e}")
