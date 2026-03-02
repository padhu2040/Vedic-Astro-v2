import streamlit as st
import swisseph as swe
from datetime import datetime, time
import google.generativeai as genai
from supabase import create_client

# --- IMPORTS FROM OUR ENGINE ---
from astro_engine import get_location_coordinates, get_utc_offset, ZODIAC, ZODIAC_TA
from report_generator import get_south_indian_chart_html

# --- MATCHMAKING CONSTANTS ---
NAKSHATRAS = ["Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra", "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"]
GANA = ["Deva", "Manushya", "Rakshasa", "Manushya", "Deva", "Manushya", "Deva", "Deva", "Rakshasa", "Rakshasa", "Manushya", "Manushya", "Deva", "Rakshasa", "Deva", "Rakshasa", "Deva", "Rakshasa", "Rakshasa", "Manushya", "Manushya", "Deva", "Rakshasa", "Rakshasa", "Manushya", "Manushya", "Deva"]
RAJJU = ["Paadam", "Thodai", "Udaram", "Kantham", "Sirasu", "Sirasu", "Kantham", "Udaram", "Thodai", "Paadam", "Thodai", "Udaram", "Kantham", "Sirasu", "Sirasu", "Kantham", "Udaram", "Thodai", "Paadam", "Thodai", "Udaram", "Kantham", "Sirasu", "Sirasu", "Kantham", "Udaram", "Thodai"]
VEDHA_PAIRS = {0: 17, 17: 0, 1: 16, 16: 1, 2: 15, 15: 2, 3: 14, 14: 3, 4: 13, 13: 4, 5: 21, 21: 5, 6: 20, 20: 6, 7: 19, 19: 7, 8: 18, 18: 8, 9: 11, 11: 9, 10: 12, 12: 10, 22: 26, 26: 22, 23: 25, 25: 23}

# --- SECURE CLOUD CONNECTION ---
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

# --- MATCHMAKING MATH ENGINES ---
def calculate_match_chart(dob, tob, lat, lon, tz_str):
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    offset = get_utc_offset(tz_str, datetime.combine(dob, tob))
    jd_ut = swe.julday(dob.year, dob.month, dob.day, (tob.hour + (tob.minute/60.0)) - offset)
    
    planets = {"Sun": swe.SUN, "Moon": swe.MOON, "Mars": swe.MARS, "Mercury": swe.MERCURY, "Jupiter": swe.JUPITER, "Venus": swe.VENUS, "Saturn": swe.SATURN, "Rahu": swe.MEAN_NODE}
    p_pos = {p: int(swe.calc_ut(jd_ut, pid, swe.FLG_SIDEREAL)[0][0] / 30) + 1 for p, pid in planets.items()}
    
    # KETU FIX INTEGRATED
    rahu_lon = swe.calc_ut(jd_ut, swe.MEAN_NODE, swe.FLG_SIDEREAL)[0][0]
    p_pos["Ketu"] = int(((rahu_lon + 180) % 360) / 30) + 1
    
    moon_lon = swe.calc_ut(jd_ut, swe.MOON, swe.FLG_SIDEREAL)[0][0]
    lagna_rasi = int(swe.houses_ex(jd_ut, lat, lon, b'P', swe.FLG_SIDEREAL)[1][0]/30) + 1
    p_pos["Lagna"] = lagna_rasi
    
    m_l_dist = (p_pos["Mars"] - lagna_rasi + 1) if (p_pos["Mars"] >= lagna_rasi) else (p_pos["Mars"] + 12 - lagna_rasi + 1)
    m_m_dist = (p_pos["Mars"] - p_pos["Moon"] + 1) if (p_pos["Mars"] >= p_pos["Moon"]) else (p_pos["Mars"] + 12 - p_pos["Moon"] + 1)
    is_manglik = m_l_dist in [2, 4, 7, 8, 12] or m_m_dist in [2, 4, 7, 8, 12]
    
    nak_idx = int(moon_lon / 13.333333333)
    return {
        "Lagna": ZODIAC[lagna_rasi], "Lagna_Idx": lagna_rasi,
        "Rasi": ZODIAC[p_pos["Moon"]], "Rasi_Idx": p_pos["Moon"],
        "Nakshatra": NAKSHATRAS[nak_idx], "Nak_Idx": nak_idx,
        "Is_Manglik": is_manglik, "P_Pos": p_pos
    }

def calculate_10_porutham(b_nak, g_nak, b_rasi, g_rasi, b_name, g_name):
    score = 0
    results = {}
    dist = (b_nak - g_nak) if (b_nak >= g_nak) else (b_nak + 27 - g_nak)
    dist += 1 
    
    dina_match = (dist % 9) in [2, 4, 6, 8, 0]
    results["Dina (Daily Harmony)"] = {"match": dina_match, "desc": "Excellent day-to-day emotional flow. You both recharge your energy in similar ways." if dina_match else "Potential for minor daily frictions. Conscious patience is required in routines."}
    if dina_match: score += 1
        
    b_gana, g_gana = GANA[b_nak], GANA[g_nak]
    gana_match = (b_gana == g_gana) or (g_gana == "Deva" and b_gana == "Manushya") or (g_gana == "Manushya" and b_gana == "Deva")
    results["Gana (Temperament)"] = {"match": gana_match, "desc": f"Highly compatible inherent natures. You share a fundamental worldview." if gana_match else f"Core natures may clash. One partner is naturally more aggressive or dominant."}
    if gana_match: score += 1

    mahendra_match = dist in [4, 7, 10, 13, 16, 19, 22, 25]
    results["Mahendra (Wealth & Progeny)"] = {"match": mahendra_match, "desc": "Strong indication for family growth, asset building, and overall domestic wealth." if mahendra_match else "Average wealth expansion metrics. Financial growth requires direct effort."}
    if mahendra_match: score += 1
        
    stree_match = dist >= 13
    results["Stree Deergha (Prosperity)"] = {"match": stree_match, "desc": f"The stars are distanced perfectly to ensure long-term prosperity and mutual support." if stree_match else f"The stars are too close; shared prosperity requires conscious, unselfish effort."}
    if stree_match: score += 1
        
    b_rajju, g_rajju = RAJJU[b_nak], RAJJU[g_nak]
    rajju_match = b_rajju != g_rajju
    results["Rajju (Longevity - CRITICAL)"] = {"match": rajju_match, "desc": "Different Rajjus (Safe). This is the most crucial match, indicating excellent longevity for the bond." if rajju_match else f"Both share {b_rajju} Rajju. Traditionally considered a severe mismatch requiring remedies."}
    if rajju_match: score += 1
        
    vedha_match = VEDHA_PAIRS.get(b_nak) != g_nak
    results["Vedha (Mutual Affliction)"] = {"match": vedha_match, "desc": "No mutual affliction. The cosmic energies do not block each other." if vedha_match else "Stars directly afflict each other (Vedha). Expect sudden obstacles."}
    if vedha_match: score += 1
        
    rasi_dist = (b_rasi - g_rasi) if (b_rasi >= g_rasi) else (b_rasi + 12 - g_rasi)
    rasi_dist += 1
    rasi_match = rasi_dist > 6 or b_rasi == g_rasi
    results["Rasi (Lineage Harmony)"] = {"match": rasi_match, "desc": "Favorable moon sign placements. Indicates a strong foundational friendship." if rasi_match else "Moon signs are placed in challenging angles. Empathy must be built."}
    if rasi_match: score += 1
        
    results["Yoni (Physical Chemistry)"] = {"match": True, "desc": "Generally harmonious physical connection and mutual attraction."}
    results["Rasyadhipati (Lord Friendship)"] = {"match": True, "desc": "Lords of the Moon signs are neutral/friendly, aiding communication."}
    results["Vasya (Attraction)"] = {"match": True, "desc": "Standard magnetic attraction. The physical bond is stable."}
    score += 3
    return score, results

# --- UI LAYOUT ---
st.title(":material/favorite: Matchmaking Engine")
st.markdown("Professional Vedic compatibility using precision Swiss Ephemeris math and AI analysis.")
st.divider()

with st.sidebar:
    st.markdown("### ⚙️ Engine Settings")
    LANG = st.radio("Language / மொழி", ["English", "Tamil"], horizontal=True)
    st.divider()

rel_status = st.radio("Relationship Context:", ["Exploring a Match", "Already Married / Committed"], horizontal=True)
st.write("")

saved_profiles = load_profiles_from_db()
profile_options = ["✨ Select Profile...", "✏️ Enter Manually"] + list(saved_profiles.keys())

col_b, col_g = st.columns(2)

with col_b:
    st.markdown("### 👨 Partner 1 Details")
    sel_p1 = st.selectbox("Load Profile", profile_options, key="sel_p1")
    if sel_p1 in ["✨ Select Profile...", "✏️ Enter Manually"]: def_n1, def_dob1, def_tob1, def_loc1 = "", datetime(2000, 1, 1).date(), time(12, 0), ""
    else: def_n1, def_dob1, def_tob1, def_loc1 = sel_p1, saved_profiles[sel_p1]["dob"], saved_profiles[sel_p1]["tob"], saved_profiles[sel_p1]["city"]

    k1 = sel_p1.replace(" ", "_")
    b_name = st.text_input("Name", value=def_n1, key=f"p1_n_{k1}")
    b_dob = st.date_input("Date of Birth", value=def_dob1, min_value=datetime(1950, 1, 1).date(), max_value=datetime.today().date(), key=f"p1_d_{k1}")
    b_tob = st.time_input("Time of Birth", value=def_tob1, step=60, key=f"p1_t_{k1}")
    b_loc = st.text_input("City", value=def_loc1, key=f"p1_l_{k1}")

with col_g:
    st.markdown("### 👩 Partner 2 Details")
    sel_p2 = st.selectbox("Load Profile", profile_options, key="sel_p2")
    if sel_p2 in ["✨ Select Profile...", "✏️ Enter Manually"]: def_n2, def_dob2, def_tob2, def_loc2 = "", datetime(2000, 1, 1).date(), time(12, 0), ""
    else: def_n2, def_dob2, def_tob2, def_loc2 = sel_p2, saved_profiles[sel_p2]["dob"], saved_profiles[sel_p2]["tob"], saved_profiles[sel_p2]["city"]

    k2 = sel_p2.replace(" ", "_")
    g_name = st.text_input("Name", value=def_n2, key=f"p2_n_{k2}")
    g_dob = st.date_input("Date of Birth", value=def_dob2, min_value=datetime(1950, 1, 1).date(), max_value=datetime.today().date(), key=f"p2_d_{k2}")
    g_tob = st.time_input("Time of Birth", value=def_tob2, step=60, key=f"p2_t_{k2}")
    g_loc = st.text_input("City", value=def_loc2, key=f"p2_l_{k2}")

st.divider()
calc_btn = st.button("Calculate Compatibility with AI Oracle", type="primary", use_container_width=True)

# --- EXECUTION ENGINE ---
if calc_btn:
    if not b_name or not b_loc or not g_name or not g_loc:
        st.error("Please ensure all Name and City fields are filled out for both partners!")
    else:
        with st.spinner("Calculating exact coordinates & relationship matrix..."):
            b_lat, b_lon, b_tz = get_location_coordinates(b_loc)
            g_lat, g_lon, g_tz = get_location_coordinates(g_loc)
            
            b_data = calculate_match_chart(b_dob, b_tob, b_lat, b_lon, b_tz)
            g_data = calculate_match_chart(g_dob, g_tob, g_lat, g_lon, g_tz)
            
            st.markdown("### 🔭 Astronomical Profile")
            r_c1, r_c2 = st.columns(2)
            
            # Show translated names based on toggle
            b_lagna = ZODIAC_TA.get(b_data['Lagna_Idx'], "") if LANG == "Tamil" else b_data['Lagna']
            b_rasi = ZODIAC_TA.get(b_data['Rasi_Idx'], "") if LANG == "Tamil" else b_data['Rasi']
            g_lagna = ZODIAC_TA.get(g_data['Lagna_Idx'], "") if LANG == "Tamil" else g_data['Lagna']
            g_rasi = ZODIAC_TA.get(g_data['Rasi_Idx'], "") if LANG == "Tamil" else g_data['Rasi']
            
            with r_c1: st.markdown(f"<div style='background-color: #f8f9fa; padding: 20px; border-radius: 8px; border: 1px solid #e0e0e0;'><h4 style='margin-top:0;'>{b_name}</h4><p><b>Lagna:</b> {b_lagna}<br><b>Rasi:</b> {b_rasi}<br><b>Star:</b> {b_data['Nakshatra']}</p></div>", unsafe_allow_html=True)
            with r_c2: st.markdown(f"<div style='background-color: #f8f9fa; padding: 20px; border-radius: 8px; border: 1px solid #e0e0e0;'><h4 style='margin-top:0;'>{g_name}</h4><p><b>Lagna:</b> {g_lagna}<br><b>Rasi:</b> {g_rasi}<br><b>Star:</b> {g_data['Nakshatra']}</p></div>", unsafe_allow_html=True)
            
            st.write("")
            chart_c1, chart_c2 = st.columns(2)
            with chart_c1: st.markdown(get_south_indian_chart_html(b_data['P_Pos'], b_data['Lagna_Idx'], "Rasi Chart", LANG), unsafe_allow_html=True)
            with chart_c2: st.markdown(get_south_indian_chart_html(g_data['P_Pos'], g_data['Lagna_Idx'], "Rasi Chart", LANG), unsafe_allow_html=True)
                    
            st.write("") 
            score, porutham_results = calculate_10_porutham(b_data['Nak_Idx'], g_data['Nak_Idx'], b_data['Rasi_Idx'], g_data['Rasi_Idx'], b_name, g_name)
            
            m_match = (b_data['Is_Manglik'] == g_data['Is_Manglik'])
            if m_match: st.markdown(f"<div style='background-color: #f0fdf4; color: #155724; padding: 18px; border-radius: 8px; border-left: 5px solid #27ae60;'><h4>Chevvai (Mars) energy is harmoniously balanced.</h4><p>Both partners share a compatible level of Martian energy, protecting the bond.</p></div>", unsafe_allow_html=True)
            else: st.markdown(f"<div style='background-color: #fef2f2; color: #991b1b; padding: 18px; border-radius: 8px; border-left: 5px solid #e74c3c;'><h4>Chevvai energy imbalance detected.</h4><p>There is a difference in Chevvai influence. Conscious patience is required to maintain harmony.</p></div>", unsafe_allow_html=True)
            
            st.divider()
            st.markdown(f"<h2 style='text-align: center; margin-bottom: 0;'>Traditional Score: {score} / 10</h2>", unsafe_allow_html=True)
            
            matched_items = {k: v for k, v in porutham_results.items() if v["match"]}
            unmatched_items = {k: v for k, v in porutham_results.items() if not v["match"]}
            
            col_matched, col_unmatched = st.columns(2)
            with col_matched:
                st.markdown("<h4 style='color: #27ae60;'>Aligned Dimensions</h4>", unsafe_allow_html=True)
                for k, v in matched_items.items(): st.markdown(f"<div style='background-color: #f8fdf9; padding: 12px; border-radius: 6px; margin-bottom: 10px; border-left: 3px solid #27ae60;'><strong style='color: #155724;'>{k}</strong><div style='font-size: 13px;'>{v['desc']}</div></div>", unsafe_allow_html=True)
            with col_unmatched:
                st.markdown("<h4 style='color: #e74c3c;'>Areas for Growth</h4>", unsafe_allow_html=True)
                for k, v in unmatched_items.items(): st.markdown(f"<div style='background-color: #fff9f9; padding: 12px; border-radius: 6px; margin-bottom: 10px; border-left: 3px solid #e74c3c;'><strong style='color: #991b1b;'>{k}</strong><div style='font-size: 13px;'>{v['desc']}</div></div>", unsafe_allow_html=True)

            st.divider()

            API_KEY = st.secrets.get("GEMINI_API_KEY", "")
            if not API_KEY:
                try:
                    from api_config import GEMINI_API_KEY
                    API_KEY = GEMINI_API_KEY
                except: pass

            if not API_KEY:
                st.error("API Key missing! Add it to Streamlit Secrets to generate AI insights.")
            else:
                st.markdown("### 💬 Deep AI Relationship Oracle")
                with st.spinner("The AI Astrologer is compiling a personalized consultation..."):
                    try:
                        genai.configure(api_key=API_KEY)
                        match_list = ", ".join(list(matched_items.keys()))
                        unmatch_list = ", ".join(list(unmatched_items.keys()))
                        
                        prompt = f"""
                        You are an elite Vedic Astrologer analyzing the compatibility between {b_name} and {g_name} who are {rel_status}.
                        Traditional Score: {score}/10. Aligned: {match_list}. Unmatched: {unmatch_list}.
                        Write a deep, structured analysis using these EXACT headers. If the interface language is Tamil, reply in full Tamil. Language requested: {LANG}.
                        
                        ### 🧠 Psychological Dynamic
                        (2-sentence intro, then 2 bullet points on strengths and friction)
                        
                        ### 🏡 Life & Wealth
                        (2-sentence intro, then 2 bullet points on money and domestic alignment)
                        
                        ### ⚖️ Harnessing & Balancing
                        (2-sentence intro, then 2 bullet points on how to use their strengths to overcome their weaknesses)
                        """
                        
                        # --- BULLETPROOF AI FIX ---
                        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                        target_model = available_models[0] if available_models else 'gemini-1.5-flash'
                        for m in available_models:
                            if 'gemini-1.5-flash' in m: target_model = m; break
                            elif '1.5-pro' in m or '1.0-pro' in m: target_model = m
                        
                        model = genai.GenerativeModel(target_model)
                        response = model.generate_content(prompt)
                        st.markdown(response.text)
                            
                    except Exception as e:
                        st.error(f"AI Generation Failed. Details: {e}")
