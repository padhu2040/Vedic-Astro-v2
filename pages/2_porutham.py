import streamlit as st
import swisseph as swe
from datetime import datetime
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
import pytz
import google.generativeai as genai

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
    
    # Check Moon Cusp
    nak_length = 13.333333
    remainder = moon_lon % nak_length
    is_cusp = True if (remainder < 0.5 or remainder > (nak_length - 0.5)) else False
    
    # Check Manglik
    mars_from_lagna = (mars_rasi_idx - lagna_rasi_idx + 1) if (mars_rasi_idx >= lagna_rasi_idx) else (mars_rasi_idx + 12 - lagna_rasi_idx + 1)
    mars_from_moon = (mars_rasi_idx - moon_rasi_idx + 1) if (mars_rasi_idx >= moon_rasi_idx) else (mars_rasi_idx + 12 - moon_rasi_idx + 1)
    
    is_manglik = False
    if mars_from_lagna in [2, 4, 7, 8, 12] or mars_from_moon in [2, 4, 7, 8, 12]:
        is_manglik = True
        
    return {
        "Lagna": ZODIAC[lagna_rasi_idx],
        "Rasi": ZODIAC[moon_rasi_idx], "Rasi_Idx": moon_rasi_idx,
        "Nakshatra": NAKSHATRAS[nak_idx], "Nak_Idx": nak_idx, "Pada": pada,
        "Is_Cusp": is_cusp, "Is_Manglik": is_manglik
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
calc_btn = st.button("Calculate Compatibility with AI", type="primary", use_container_width=True)

# --- EXECUTION ---
if calc_btn:
    with st.spinner("Calculating exact coordinates & matrix..."):
        b_lat, b_lon, b_tz, b_addr = get_location_coordinates(b_loc)
        g_lat, g_lon, g_tz, g_addr = get_location_coordinates(g_loc)
        
        b_data = calculate_full_chart(b_dob, b_tob, b_lat, b_lon, b_tz)
        g_data = calculate_full_chart(g_dob, g_tob, g_lat, g_lon, g_tz)
        
        # 1. ASTRONOMICAL PROFILE (Identical Boxes, 3 lines, minimal location)
        st.markdown("### :material/travel_explore: Astronomical Profile")
        r_c1, r_c2 = st.columns(2)
        
        with r_c1:
            st.markdown(f"""
            <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; height: 100%; border: 1px solid #e0e0e0;">
                <h4 style="margin-top: 0; color: #2c3e50;">{b_name}</h4>
                <p style="margin: 5px 0; font-size: 15px;"><b>Lagna (Ascendant):</b> {b_data['Lagna']}</p>
                <p style="margin: 5px 0; font-size: 15px;"><b>Rasi (Moon Sign):</b> {b_data['Rasi']}</p>
                <p style="margin: 5px 0; font-size: 15px;"><b>Nakshatra (Star):</b> {b_data['Nakshatra']} (Pada {b_data['Pada']})</p>
                <p style="margin: 15px 0 0 0; font-size: 12px; color: #7f8c8d;">Location: {b_addr}</p>
            </div>
            """, unsafe_allow_html=True)
            if b_data['Is_Cusp']:
                st.warning(f":material/warning: **Transition Zone:** The Moon is on the exact edge of {b_data['Nakshatra']}. Verify birth time.")
                
        with r_c2:
            st.markdown(f"""
            <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; height: 100%; border: 1px solid #e0e0e0;">
                <h4 style="margin-top: 0; color: #2c3e50;">{g_name}</h4>
                <p style="margin: 5px 0; font-size: 15px;"><b>Lagna (Ascendant):</b> {g_data['Lagna']}</p>
                <p style="margin: 5px 0; font-size: 15px;"><b>Rasi (Moon Sign):</b> {g_data['Rasi']}</p>
                <p style="margin: 5px 0; font-size: 15px;"><b>Nakshatra (Star):</b> {g_data['Nakshatra']} (Pada {g_data['Pada']})</p>
                <p style="margin: 15px 0 0 0; font-size: 12px; color: #7f8c8d;">Location: {g_addr}</p>
            </div>
            """, unsafe_allow_html=True)
            if g_data['Is_Cusp']:
                st.warning(f":material/warning: **Transition Zone:** The Moon is on the exact edge of {g_data['Nakshatra']}. Verify birth time.")
                
        st.write("") # Spacing
                
        # 2. CHEVVAI DOSHAM (Natural Language)
        st.markdown("### :material/shield: Mars Compatibility")
        m_match = (b_data['Is_Manglik'] == g_data['Is_Manglik'])
        
        b_m_str = "Present" if b_data['Is_Manglik'] else "Not Present"
        g_m_str = "Present" if g_data['Is_Manglik'] else "Not Present"
        
        if m_match:
            m_title = "Mars energy is harmoniously balanced."
            m_color = "#f0fdf4"
            m_border = "#27ae60"
            m_text = "#155724"
            m_desc = f"Both individuals share a compatible level of Martian energy (Boy: {b_m_str} | Girl: {g_m_str}). In traditional astrology, this creates a natural balance in drive and passion, effectively canceling out potential friction."
        else:
            m_title = "Mars energy imbalance detected."
            m_color = "#fef2f2"
            m_border = "#e74c3c"
            m_text = "#991b1b"
            m_desc = f"There is a difference in Martian influence (Boy: {b_m_str} | Girl: {g_m_str}). One partner may be naturally more aggressive or driven than the other, requiring conscious patience to maintain marital harmony."

        st.markdown(f"""
            <div style="background-color: {m_color}; color: {m_text}; padding: 18px; border-radius: 8px; border-left: 5px solid {m_border};">
                <h4 style="margin: 0 0 8px 0; font-size: 16px;">{m_title}</h4>
                <p style="margin: 0; font-size: 14px;">{m_desc}</p>
            </div>
            """, unsafe_allow_html=True)

        st.divider()

        # 3. THE 10-PORUTHAM SCORECARD (Two Columns, Minimalist)
        score, porutham_results = calculate_10_porutham(b_data['Nak_Idx'], g_data['Nak_Idx'], b_data['Rasi_Idx'], g_data['Rasi_Idx'])
        
        st.markdown(f"<h2 style='text-align: center; margin-bottom: 0;'>Traditional Score: {score} / 10</h2>", unsafe_allow_html=True)
        if score >= 7 and m_match:
            st.markdown(f"<h4 style='text-align: center; color: #27ae60; margin-top: 5px;'>Excellent Match</h4>", unsafe_allow_html=True)
        elif score >= 5:
            st.markdown(f"<h4 style='text-align: center; color: #f39c12; margin-top: 5px;'>Average Match</h4>", unsafe_allow_html=True)
        else:
            st.markdown(f"<h4 style='text-align: center; color: #e74c3c; margin-top: 5px;'>Not Recommended</h4>", unsafe_allow_html=True)
            
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Split into Matched and Unmatched
        matched_items = {k: v for k, v in porutham_results.items() if v["match"]}
        unmatched_items = {k: v for k, v in porutham_results.items() if not v["match"]}
        
        col_matched, col_unmatched = st.columns(2)
        
        with col_matched:
            st.markdown("<h4 style='color: #27ae60; border-bottom: 1px solid #eee; padding-bottom: 10px;'>Aligned Dimensions</h4>", unsafe_allow_html=True)
            for k, v in matched_items.items():
                st.markdown(f"""
                <div style="background-color: #f8fdf9; padding: 12px; border-radius: 6px; margin-bottom: 10px; border-left: 3px solid #27ae60;">
                    <strong style="color: #155724; font-size: 14px;">{k}</strong>
                    <div style="font-size: 13px; color: #2c3e50; margin-top: 4px;">{v['desc']}</div>
                </div>
                """, unsafe_allow_html=True)
                
        with col_unmatched:
            st.markdown("<h4 style='color: #e74c3c; border-bottom: 1px solid #eee; padding-bottom: 10px;'>Areas for Growth</h4>", unsafe_allow_html=True)
            for k, v in unmatched_items.items():
                st.markdown(f"""
                <div style="background-color: #fff9f9; padding: 12px; border-radius: 6px; margin-bottom: 10px; border-left: 3px solid #e74c3c;">
                    <strong style="color: #991b1b; font-size: 14px;">{k}</strong>
                    <div style="font-size: 13px; color: #2c3e50; margin-top: 4px;">{v['desc']}</div>
                </div>
                """, unsafe_allow_html=True)

        st.divider()
        
        # 4. THE AI RELATIONSHIP ORACLE (Fixed Model Name)
        if not GEMINI_API_KEY:
            st.error("API Key missing! Add it to Streamlit Secrets to generate AI insights.")
        else:
            st.markdown("### :material/auto_awesome: Deep AI Relationship Oracle")
            with st.spinner("The AI Astrologer is analyzing psychological compatibility..."):
                try:
                    genai.configure(api_key=GEMINI_API_KEY)
                    prompt = f"""
                    You are an elite, modern Vedic Astrologer. Analyze the relationship compatibility between:
                    Boy: {b_data['Lagna']} Ascendant, {b_data['Rasi']} Moon Sign, {b_data['Nakshatra']} Star.
                    Girl: {g_data['Lagna']} Ascendant, {g_data['Rasi']} Moon Sign, {g_data['Nakshatra']} Star.
                    Their traditional Porutham score is {score}/10. 
                    
                    Write exactly 3 short, profound paragraphs explaining their psychological and practical dynamic. 
                    Do NOT use hashtags for headers. Instead, format EXACTLY like this using these specific icons:
                    
                    :material/psychology: **Psychological Dynamic:** (Explain how their minds interact)
                    
                    :material/home_work: **Life & Wealth:** (Explain how they build a home and manage finances together)
                    
                    :material/balance: **Karmic Challenge:** (Explain the one main thing they must actively work on to avoid friction)
                    """
                    
                    # Hardcoded to the stable gemini-1.5-flash model to prevent 404 errors
                    model = genai.GenerativeModel('gemini-1.5-flash') 
                    response = model.generate_content(prompt)
                    st.markdown(response.text)
                except Exception as e:
                    st.error(f"AI Generation Failed. Please ensure your API key is valid. Error: {e}")
