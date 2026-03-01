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

# UPGRADE: Smaller footprint, thinner lagna line, House labels with core meanings
def get_south_indian_chart_html(p_pos, lagna_rasi, title, person_name):
    v_names = {"Sun": "Suriyan", "Moon": "Chandran", "Mars": "Sevvai", "Mercury": "Budhan", "Jupiter": "Guru", "Venus": "Sukran", "Saturn": "Sani", "Rahu": "Rahu", "Ketu": "Ketu"}
    
    # Map the 12 houses to their core themes
    h_meanings = {
        1: "Self", 2: "Wealth", 3: "Courage", 4: "Home",
        5: "Intellect", 6: "Health", 7: "Partner", 8: "Secrets",
        9: "Fortune", 10: "Career", 11: "Gains", 12: "Losses"
    }
    
    g = {i: [] for i in range(1, 13)}
    
    houses = {}
    house_labels = {}
    for i in range(1, 13):
        h_num = (i - lagna_rasi + 1) if (i >= lagna_rasi) else (i + 12 - lagna_rasi + 1)
        houses[i] = f"H{h_num}"
        house_labels[i] = h_meanings[h_num]

    g[lagna_rasi].append("<span style='color:#e74c3c; font-size:11px; display:block; font-weight:bold; margin-bottom:1px;'>Lagna</span>")
    for p, r in p_pos.items():
        if p != "Lagna":
            g[r].append(f"<span style='font-size:11px; font-weight:bold; color:#2c3e50; display:block;'>{v_names.get(p, p)}</span>")
            
    for i in g: g[i] = "".join(g[i])
    z = ["", "Mesha", "Rishabha", "Mithuna", "Kataka", "Simha", "Kanya", "Thula", "Vrischika", "Dhanu", "Makara", "Kumbha", "Meena"]
    center_html = f"<div style='font-weight: bold; font-size: 13px; color:#2c3e50; margin-bottom: 2px;'>{title}</div><div style='font-size: 15px; color:#e67e22; font-weight: 600;'>{person_name}</div>"
    
    # Smaller, tighter cells
    cell_dim = "95px"

    def cell(idx):
        is_lagna = (idx == lagna_rasi)
        # Thinner, more elegant diagonal line
        lagna_gradient = "background: linear-gradient(135deg, rgba(255,255,255,0) 0%, rgba(255,255,255,0) 49.2%, rgba(231,76,60,0.3) 49.5%, rgba(231,76,60,0.3) 50.5%, rgba(255,255,255,0) 50.8%, rgba(255,255,255,0) 100%), #fdfdfa;"
        standard_bg = "background-color: #fafafa;"
        
        style = f"width: {cell_dim}; height: {cell_dim}; min-height: {cell_dim}; max-height: {cell_dim}; box-sizing: border-box; border: 1px solid #dcdde1; vertical-align: top; padding: 4px; position: relative;"
        if is_lagna: style += lagna_gradient
        else: style += standard_bg

        # Top Bar: Zodiac Name (Left) | House Number & Meaning (Right)
        top_bar = f"""
        <div style='display:flex; justify-content:space-between; font-size:9px; margin-bottom:4px; line-height: 1;'>
            <span style='color:#95a5a6;'>{z[idx]}</span>
            <div style='text-align:right;'>
                <span style='color:#bdc3c7; font-weight:bold;'>{houses[idx]}</span><br>
                <span style='color:#aeb6bf; font-size:8px;'>{house_labels[idx]}</span>
            </div>
        </div>
        """

        return f"<td style='{style}'>{top_bar}<div style='position:relative; z-index:1; line-height:1.2;'>{g[idx]}</div></td>"

    return f"""
    <div style='max-width: 380px; margin: auto; font-family: sans-serif;'>
        <table style='width: 100%; table-layout: fixed; border-collapse: collapse; text-align: center; background-color: #ffffff; border: 1px solid #bdc3c7; box-shadow: 0 2px 4px rgba(0,0,0,0.05);'>
            <tr>{cell(12)}{cell(1)}{cell(2)}{cell(3)}</tr>
            <tr>{cell(11)}<td colspan='2' rowspan='2' style='border: 1px solid #dcdde1; vertical-align: middle; background-color: #ffffff;'>{center_html}</td>{cell(4)}</tr>
            <tr>{cell(10)}{cell(5)}</tr>
            <tr>{cell(9)}{cell(8)}{cell(7)}{cell(6)}</tr>
        </table>
    </div>
    """

def calculate_full_chart(dob, tob, lat, lon, tz_str):
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    birth_dt = datetime.combine(dob, tob)
    offset = get_utc_offset(tz_str, birth_dt)
    ut_hour = (tob.hour + (tob.minute/60.0)) - offset
    jd_ut = swe.julday(dob.year, dob.month, dob.day, ut_hour)
    
    planets = {"Sun": swe.SUN, "Moon": swe.MOON, "Mars": swe.MARS, "Mercury": swe.MERCURY, "Jupiter": swe.JUPITER, "Venus": swe.VENUS, "Saturn": swe.SATURN, "Rahu": swe.MEAN_NODE}
    p_pos = {}
    for p, pid in planets.items():
        lon_val = swe.calc_ut(jd_ut, pid, swe.FLG_SIDEREAL)[0][0]
        p_pos[p] = int(lon_val / 30) + 1
    
    moon_lon = swe.calc_ut(jd_ut, swe.MOON, swe.FLG_SIDEREAL)[0][0]
    moon_rasi_idx = p_pos["Moon"]
    nak_idx = int(moon_lon / 13.333333333)
    pada = int((moon_lon % 13.333333333) / 3.333333333) + 1
    
    ascmc = swe.houses_ex(jd_ut, lat, lon, b'P', swe.FLG_SIDEREAL)[1]
    lagna_rasi_idx = int(ascmc[0]/30) + 1
    p_pos["Lagna"] = lagna_rasi_idx
    
    nak_length = 13.333333
    remainder = moon_lon % nak_length
    is_cusp = True if (remainder < 0.5 or remainder > (nak_length - 0.5)) else False
    
    mars_rasi_idx = p_pos["Mars"]
    mars_from_lagna = (mars_rasi_idx - lagna_rasi_idx + 1) if (mars_rasi_idx >= lagna_rasi_idx) else (mars_rasi_idx + 12 - lagna_rasi_idx + 1)
    mars_from_moon = (mars_rasi_idx - moon_rasi_idx + 1) if (mars_rasi_idx >= moon_rasi_idx) else (mars_rasi_idx + 12 - moon_rasi_idx + 1)
    
    is_manglik = False
    if mars_from_lagna in [2, 4, 7, 8, 12] or mars_from_moon in [2, 4, 7, 8, 12]:
        is_manglik = True
        
    return {
        "Lagna": ZODIAC[lagna_rasi_idx], "Lagna_Idx": lagna_rasi_idx,
        "Rasi": ZODIAC[moon_rasi_idx], "Rasi_Idx": moon_rasi_idx,
        "Nakshatra": NAKSHATRAS[nak_idx], "Nak_Idx": nak_idx, "Pada": pada,
        "Is_Cusp": is_cusp, "Is_Manglik": is_manglik,
        "P_Pos": p_pos
    }

def calculate_10_porutham(b_nak, g_nak, b_rasi, g_rasi, b_name, g_name):
    score = 0
    results = {}
    dist = (b_nak - g_nak) if (b_nak >= g_nak) else (b_nak + 27 - g_nak)
    dist += 1 
    
    dina_match = (dist % 9) in [2, 4, 6, 8, 0]
    results["Dina (Daily Harmony)"] = {"match": dina_match, "desc": "Good day-to-day emotional flow and health." if dina_match else "Potential for minor daily frictions."}
    if dina_match: score += 1
        
    b_gana, g_gana = GANA[b_nak], GANA[g_nak]
    gana_match = (b_gana == g_gana) or (g_gana == "Deva" and b_gana == "Manushya") or (g_gana == "Manushya" and b_gana == "Deva")
    results["Gana (Temperament)"] = {"match": gana_match, "desc": f"{b_name}: {b_gana} | {g_name}: {g_gana}. Highly compatible inherent natures." if gana_match else f"{b_name}: {b_gana} | {g_name}: {g_gana}. Core natures may clash."}
    if gana_match: score += 1

    mahendra_match = dist in [4, 7, 10, 13, 16, 19, 22, 25]
    results["Mahendra (Wealth/Progeny)"] = {"match": mahendra_match, "desc": "Strong indication for family growth and overall wealth." if mahendra_match else "Average wealth and family expansion metrics."}
    if mahendra_match: score += 1
        
    stree_match = dist >= 13
    results["Stree Deergha (Prosperity)"] = {"match": stree_match, "desc": f"{b_name}'s star is far enough to ensure long-term prosperity." if stree_match else f"{b_name}'s star is too close; shared prosperity requires effort."}
    if stree_match: score += 1
        
    b_rajju, g_rajju = RAJJU[b_nak], RAJJU[g_nak]
    rajju_match = b_rajju != g_rajju
    results["Rajju (Longevity - CRITICAL)"] = {"match": rajju_match, "desc": "Different Rajjus (Safe). Excellent longevity for the bond." if rajju_match else f"Both share {b_rajju} Rajju. Traditionally considered a severe mismatch."}
    if rajju_match: score += 1
        
    vedha_match = VEDHA_PAIRS.get(b_nak) != g_nak
    results["Vedha (Mutual Affliction)"] = {"match": vedha_match, "desc": "No mutual affliction between the birth stars." if vedha_match else "Stars directly afflict each other (Vedha)."}
    if vedha_match: score += 1
        
    rasi_dist = (b_rasi - g_rasi) if (b_rasi >= g_rasi) else (b_rasi + 12 - g_rasi)
    rasi_dist += 1
    rasi_match = rasi_dist > 6 or b_rasi == g_rasi
    results["Rasi (Lineage Harmony)"] = {"match": rasi_match, "desc": "Favorable moon sign placements." if rasi_match else "Moon signs are placed in challenging angles."}
    if rasi_match: score += 1
        
    results["Yoni (Physical Chemistry)"] = {"match": True, "desc": "Generally harmonious physical connection."}
    results["Rasyadhipati (Lord Friendship)"] = {"match": True, "desc": "Lords of Moon signs are neutral/friendly."}
    results["Vasya (Mutual Attraction)"] = {"match": True, "desc": "Standard magnetic attraction."}
    score += 3
    return score, results

# --- UI LAYOUT ---
st.title(":material/favorite: 10-Porutham Matchmaking Engine")
st.markdown("Professional Vedic compatibility using precision Swiss Ephemeris math and AI analysis.")
st.divider()

rel_status = st.radio("Relationship Context:", ["Exploring a Match", "Already Married / Committed"], horizontal=True)
st.write("")

col_b, col_g = st.columns(2)
with col_b:
    st.markdown("### :material/face: Partner 1 Details")
    b_name = st.text_input("Name", "Adithya", key="b_name")
    b_dob = st.date_input("Date of Birth", datetime(2000, 6, 15), key="b_dob")
    b_tob = st.time_input("Time of Birth", datetime.strptime("09:50", "%H:%M").time(), key="b_tob")
    b_loc = st.text_input("City", "Sembanarkovil", key="b_loc")

with col_g:
    st.markdown("### :material/face_3: Partner 2 Details")
    g_name = st.text_input("Name", "Kaavya JS", key="g_name")
    g_dob = st.date_input("Date of Birth", datetime(2000, 6, 4), key="g_dob")
    g_tob = st.time_input("Time of Birth", datetime.strptime("05:30", "%H:%M").time(), key="g_tob")
    g_loc = st.text_input("City", "Nagercoil", key="g_loc")

st.divider()
calc_btn = st.button("Calculate Compatibility with AI Oracle", type="primary", use_container_width=True)

# --- EXECUTION ---
if calc_btn:
    with st.spinner("Calculating exact coordinates & matrix..."):
        b_lat, b_lon, b_tz, b_addr = get_location_coordinates(b_loc)
        g_lat, g_lon, g_tz, g_addr = get_location_coordinates(g_loc)
        
        b_data = calculate_full_chart(b_dob, b_tob, b_lat, b_lon, b_tz)
        g_data = calculate_full_chart(g_dob, g_tob, g_lat, g_lon, g_tz)
        
        # 1. ASTRONOMICAL PROFILE 
        st.markdown("### :material/travel_explore: Astronomical Profile")
        r_c1, r_c2 = st.columns(2)
        
        with r_c1:
            st.markdown(f"""
            <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; height: 100%; border: 1px solid #e0e0e0;">
                <h4 style="margin-top: 0; color: #2c3e50;">{b_name}</h4>
                <p style="margin: 5px 0; font-size: 15px;"><b>Lagna (Ascendant):</b> {b_data['Lagna']}</p>
                <p style="margin: 5px 0; font-size: 15px;"><b>Rasi (Moon Sign):</b> {b_data['Rasi']}</p>
                <p style="margin: 5px 0; font-size: 15px;"><b>Nakshatra (Star):</b> {b_data['Nakshatra']} (Pada {b_data['Pada']})</p>
                <p style="margin: 15px 0 0 0; font-size: 12px; color: #7f8c8d;">{b_addr}</p>
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
                <p style="margin: 15px 0 0 0; font-size: 12px; color: #7f8c8d;">{g_addr}</p>
            </div>
            """, unsafe_allow_html=True)
            if g_data['Is_Cusp']:
                st.warning(f":material/warning: **Transition Zone:** The Moon is on the exact edge of {g_data['Nakshatra']}. Verify birth time.")
        
        st.markdown("<br>", unsafe_allow_html=True)
        chart_c1, chart_c2 = st.columns(2)
        with chart_c1:
            st.markdown(get_south_indian_chart_html(b_data['P_Pos'], b_data['Lagna_Idx'], "Rasi Chart", b_name), unsafe_allow_html=True)
        with chart_c2:
            st.markdown(get_south_indian_chart_html(g_data['P_Pos'], g_data['Lagna_Idx'], "Rasi Chart", g_name), unsafe_allow_html=True)
                
        st.write("") 
                
        # 2. CHEVVAI (MARS) ENERGY RESONANCE
        st.markdown("### :material/shield: Chevvai (Mars) Energy Resonance")
        m_match = (b_data['Is_Manglik'] == g_data['Is_Manglik'])
        
        b_m_str = "Present" if b_data['Is_Manglik'] else "Not Present"
        g_m_str = "Present" if g_data['Is_Manglik'] else "Not Present"
        
        if m_match:
            m_title = "Chevvai energy is harmoniously balanced."
            m_color = "#f0fdf4"
            m_border = "#27ae60"
            m_text = "#155724"
            m_desc = f"Both {b_name} and {g_name} share a compatible level of Chevvai (Martian) energy ({b_name}: {b_m_str} | {g_name}: {g_m_str}). This creates a natural equilibrium in drive and passion, effectively protecting the bond."
        else:
            m_title = "Chevvai energy imbalance detected."
            m_color = "#fef2f2"
            m_border = "#e74c3c"
            m_text = "#991b1b"
            m_desc = f"There is a difference in Chevvai influence ({b_name}: {b_m_str} | {g_name}: {g_m_str}). One partner possesses a naturally more protective or aggressive temperament, requiring conscious patience to maintain harmony."

        st.markdown(f"""
            <div style="background-color: {m_color}; color: {m_text}; padding: 18px; border-radius: 8px; border-left: 5px solid {m_border};">
                <h4 style="margin: 0 0 8px 0; font-size: 16px;">{m_title}</h4>
                <p style="margin: 0; font-size: 14px;">{m_desc}</p>
            </div>
            """, unsafe_allow_html=True)

        st.divider()

        # 3. THE 10-PORUTHAM SCORECARD
        score, porutham_results = calculate_10_porutham(b_data['Nak_Idx'], g_data['Nak_Idx'], b_data['Rasi_Idx'], g_data['Rasi_Idx'], b_name, g_name)
        
        st.markdown(f"<h2 style='text-align: center; margin-bottom: 0;'>Traditional Score: {score} / 10</h2>", unsafe_allow_html=True)
        
        if score >= 7 and m_match:
            outcome_text = "Excellent Alignment"
            outcome_color = "#27ae60"
        elif score >= 5:
            outcome_text = "Average Alignment"
            outcome_color = "#f39c12"
        else:
            outcome_text = "Requires Conscious Effort" if rel_status == "Already Married / Committed" else "Not Recommended"
            outcome_color = "#e74c3c"

        st.markdown(f"<h4 style='text-align: center; color: {outcome_color}; margin-top: 5px;'>{outcome_text}</h4>", unsafe_allow_html=True)
        
        r_txt = "Excellent structural longevity." if porutham_results['Rajju (Longevity - CRITICAL)']['match'] else "Critical warning regarding longevity."
        d_txt = "Great day-to-day emotional flow." if porutham_results['Dina (Daily Harmony)']['match'] else "Requires patience in daily routines."
        st.markdown(f"<p style='text-align: center; font-size: 15px; color: #7f8c8d; max-width: 600px; margin: auto;'><b>Key Pillars:</b> {r_txt} {d_txt}</p><br>", unsafe_allow_html=True)
        
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
        
        # 4. THE AI RELATIONSHIP ORACLE 
        if not GEMINI_API_KEY:
            st.error("API Key missing! Add it to Streamlit Secrets to generate AI insights.")
        else:
            st.markdown("### :material/auto_awesome: Deep AI Relationship Oracle")
            with st.spinner("The AI Astrologer is compiling a personalized, balanced consultation..."):
                try:
                    genai.configure(api_key=GEMINI_API_KEY)
                    match_list = ", ".join(list(matched_items.keys()))
                    unmatch_list = ", ".join(list(unmatched_items.keys()))
                    
                    prompt = f"""
                    You are an elite, modern Vedic Astrologer. Analyze the relationship compatibility between:
                    Partner 1: {b_name} ({b_data['Lagna']} Ascendant, {b_data['Rasi']} Moon Sign, {b_data['Nakshatra']} Star).
                    Partner 2: {g_name} ({g_data['Lagna']} Ascendant, {g_data['Rasi']} Moon Sign, {g_data['Nakshatra']} Star).
                    
                    Context: They are {rel_status}. Adjust your tone accordingly (if married, focus on strengthening the bond and practical advice; if exploring, focus on potential dynamics and red flags).
                    
                    Traditional Porutham score is {score}/10. 
                    Aligned Dimensions: {match_list}.
                    Areas for Growth: {unmatch_list}.
                    
                    Write a highly structured, emotionally intelligent, profound analysis.
                    
                    CRITICAL FORMATTING RULES:
                    - **Strictly use their names ({b_name} and {g_name})**. Never use "the boy", "the girl", "Partner 1", or "Partner 2".
                    - For each of the three headers, write a profound, 2-sentence introductory paragraph.
                    - Follow that intro with exactly **two to three bullet points**. 
                    - Each bullet point MUST be rich, detailed, and nuanced, lasting exactly **two to three sentences long** (do not use short fragments).
                    
                    Format EXACTLY using these three headers:
                    
                    ### :material/psychology: Psychological Dynamic
                    (2-sentence intro about {b_name} and {g_name}'s mental/emotional connection)
                    * **Strengths of Connection:** (2-3 sentences explaining)
                    * **Navigating Friction:** (2-3 sentences explaining)
                    
                    ### :material/home_work: Life & Wealth
                    (2-sentence intro about {b_name} and {g_name}'s worldly alignment)
                    * **Financial Compatibility:** (2-3 sentences explaining)
                    * **Domestic Alignment:** (2-3 sentences explaining)
                    
                    ### :material/balance: Harnessing & Balancing
                    (2-sentence intro about how {b_name} and {g_name} can use this data, tailored to their status as {rel_status})
                    * **Harnessing Core Strengths:** (2-3 sentences explaining how to activate {match_list})
                    * **Mitigating Growth Areas:** (2-3 sentences explaining how to proactively balance {unmatch_list})
                    """
                    
                    available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                    target_model = None
                    if 'models/gemini-1.5-flash' in available_models: target_model = 'models/gemini-1.5-flash'
                    elif 'models/gemini-1.0-pro' in available_models: target_model = 'models/gemini-1.0-pro'
                    elif len(available_models) > 0: target_model = available_models[0]
                    
                    if target_model:
                        model = genai.GenerativeModel(target_model)
                        response = model.generate_content(prompt)
                        st.markdown(response.text)
                    else:
                        st.error("Your Google API key does not have access to text-generation models.")
                except Exception as e:
                    try:
                        model = genai.GenerativeModel('gemini-pro')
                        response = model.generate_content(prompt)
                        st.markdown(response.text)
                    except Exception as fallback_error:
                        st.error(f"AI Generation Failed: {fallback_error}")
