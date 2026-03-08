import streamlit as st
import swisseph as swe
from datetime import datetime, time
import json
import google.generativeai as genai
from supabase import create_client

# Ensure these match your actual engine file
from astro_engine import get_location_coordinates, get_utc_offset, calculate_10_porutham, ZODIAC, ZODIAC_TA

NAKSHATRAS = ["Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra", "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"]

@st.cache_resource
def init_connection():
    try: 
        return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    except Exception: 
        return None

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

# --- LIGHTWEIGHT DASHA CALCULATOR ---
def get_current_dasha(moon_lon, dob):
    DASHA_LORDS = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]
    DASHA_YEARS = [7, 20, 6, 10, 7, 18, 16, 19, 17]
    nak_idx = (moon_lon / (360/27))
    nak_fraction = nak_idx - int(nak_idx)
    lord_idx = int(nak_idx) % 9
    
    balance_years = (1.0 - nak_fraction) * DASHA_YEARS[lord_idx]
    age_years = (datetime.now().date() - dob).days / 365.25
    
    passed_years = balance_years
    curr_lord_idx = lord_idx
    if age_years < passed_years: return DASHA_LORDS[curr_lord_idx]
        
    while True:
        curr_lord_idx = (curr_lord_idx + 1) % 9
        if age_years < passed_years + DASHA_YEARS[curr_lord_idx]:
            return DASHA_LORDS[curr_lord_idx]
        passed_years += DASHA_YEARS[curr_lord_idx]

def calculate_match_chart(dob, tob, lat, lon, tz_str):
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    offset = get_utc_offset(tz_str, datetime.combine(dob, tob))
    jd_ut = swe.julday(dob.year, dob.month, dob.day, (tob.hour + (tob.minute/60.0)) - offset)
    
    planets = {"Sun": swe.SUN, "Moon": swe.MOON, "Mars": swe.MARS, "Mercury": swe.MERCURY, "Jupiter": swe.JUPITER, "Venus": swe.VENUS, "Saturn": swe.SATURN, "Rahu": swe.MEAN_NODE}
    p_pos = {p: int(swe.calc_ut(jd_ut, pid, swe.FLG_SIDEREAL)[0][0] / 30) + 1 for p, pid in planets.items()}
    
    moon_lon = swe.calc_ut(jd_ut, swe.MOON, swe.FLG_SIDEREAL)[0][0]
    lagna_rasi = int(swe.houses_ex(jd_ut, lat, lon, b'P', swe.FLG_SIDEREAL)[1][0]/30) + 1
    p_pos["Lagna"] = lagna_rasi
    
    m_l_dist = (p_pos["Mars"] - lagna_rasi + 1) if (p_pos["Mars"] >= lagna_rasi) else (p_pos["Mars"] + 12 - lagna_rasi + 1)
    m_m_dist = (p_pos["Mars"] - p_pos["Moon"] + 1) if (p_pos["Mars"] >= p_pos["Moon"]) else (p_pos["Mars"] + 12 - p_pos["Moon"] + 1)
    is_manglik = m_l_dist in [2, 4, 7, 8, 12] or m_m_dist in [2, 4, 7, 8, 12]
    
    nak_idx = int(moon_lon / 13.333333333)
    curr_dasha = get_current_dasha(moon_lon, dob)
    
    return {"Lagna": ZODIAC[lagna_rasi], "Rasi": ZODIAC[p_pos["Moon"]], "Rasi_Idx": p_pos["Moon"], "Nakshatra": NAKSHATRAS[nak_idx], "Nak_Idx": nak_idx, "Dasha": curr_dasha}

# --- PORUTHAM DEFINITIONS FOR UI ---
PORUTHAM_DEFS = {
    "Dina": "Measures day-to-day harmony, health, and freedom from routine sickness.",
    "Gana": "Assesses temperament, ego alignment, and overall psychological compatibility.",
    "Mahendra": "Indicates potential for wealth accumulation, progeny, and long-term bonding.",
    "Stree": "Evaluates domestic prosperity, longevity of the woman, and household joy.",
    "Yoni": "Determines physical chemistry, sexual compatibility, and mutual attraction.",
    "Rasi": "Analyzes the lineage harmony, broad worldviews, and life trajectories.",
    "Rasyadhipati": "Looks at the friendship between planetary lords (core motivations).",
    "Vasya": "Measures the magnetic attraction and devotion between the partners.",
    "Rajju": "The most critical metric; determines the longevity of the husband/marriage.",
    "Vedha": "Checks for specific energetic blockages or repulsions between birth stars."
}

# --- UI SETUP ---
st.set_page_config(page_title="Strategic Synergy", layout="wide")
st.title("Strategic Synergy")
st.markdown("<div style='color:#7f8c8d; margin-top:-15px; margin-bottom: 20px;'>Matchmaking (Porutham) & Partnership Matrix</div>", unsafe_allow_html=True)
st.divider()

with st.sidebar:
    LANG = st.radio("Language / மொழி", ["English", "Tamil"], horizontal=True, label_visibility="collapsed")
    st.divider()

rel_status = st.radio("Context", ["Exploring a Match", "Already Married / Committed"], horizontal=True, label_visibility="collapsed")
st.write("")

saved_profiles = load_profiles_from_db()
profile_options = ["(Select Profile)", "Enter Manually"] + list(saved_profiles.keys())

col_b, col_g = st.columns(2)
with col_b:
    st.markdown("##### Partner A (Subject)")
    sel_p1 = st.selectbox("Load Profile (A)", profile_options, key="sel_p1", label_visibility="collapsed")
    if sel_p1 in ["(Select Profile)", "Enter Manually"]: 
        def_n1, def_dob1, def_tob1, def_loc1 = "", datetime(2000, 1, 1).date(), time(12, 0), ""
    else: 
        def_n1, def_dob1, def_tob1, def_loc1 = sel_p1, saved_profiles[sel_p1]["dob"], saved_profiles[sel_p1]["tob"], saved_profiles[sel_p1]["city"]
    
    k1 = sel_p1.replace(" ", "_") if sel_p1 else "a"
    b_name = st.text_input("Name", value=def_n1, key=f"p1_n_{k1}")
    b_dob = st.date_input("Date of Birth", value=def_dob1, key=f"p1_d_{k1}")
    b_tob = st.time_input("Time of Birth", value=def_tob1, key=f"p1_t_{k1}")
    b_loc = st.text_input("City", value=def_loc1, key=f"p1_l_{k1}")

with col_g:
    st.markdown("##### Partner B (Counterpart)")
    sel_p2 = st.selectbox("Load Profile (B)", profile_options, key="sel_p2", label_visibility="collapsed")
    if sel_p2 in ["(Select Profile)", "Enter Manually"]: 
        def_n2, def_dob2, def_tob2, def_loc2 = "", datetime(2000, 1, 1).date(), time(12, 0), ""
    else: 
        def_n2, def_dob2, def_tob2, def_loc2 = sel_p2, saved_profiles[sel_p2]["dob"], saved_profiles[sel_p2]["tob"], saved_profiles[sel_p2]["city"]
    
    k2 = sel_p2.replace(" ", "_") if sel_p2 else "b"
    g_name = st.text_input("Name", value=def_n2, key=f"p2_n_{k2}")
    g_dob = st.date_input("Date of Birth", value=def_dob2, key=f"p2_d_{k2}")
    g_tob = st.time_input("Time of Birth", value=def_tob2, key=f"p2_t_{k2}")
    g_loc = st.text_input("City", value=def_loc2, key=f"p2_l_{k2}")

st.divider()
calc_btn = st.button("Generate Executive Synergy Report", type="primary", use_container_width=True)

# --- GLOBAL CSS FOR FLAT EXECUTIVE CARDS & NEW SUMMARY GRID ---
css_block = """<style>
.bp-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px; margin-bottom: 20px; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; }
.bp-card { background: #ffffff; border: 1px solid #eaeaea; border-radius: 4px; padding: 20px; display: flex; flex-direction: column; box-shadow: 0 1px 2px rgba(0,0,0,0.01); }
.bp-head { font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; color: #888; font-weight: 500; margin-bottom: 12px; border-bottom: 1px solid #f9f9f9; padding-bottom: 6px; display: flex; justify-content: space-between; }
.bp-desc { font-size: 13.5px; color: #444; line-height: 1.6; font-weight: 400; margin-bottom:12px; }
.bp-def { font-size: 11px; color: #95a5a6; font-style: italic; border-top: 1px dashed #eee; padding-top: 8px; margin-top: auto; }
.tag-harness { display:inline-block; font-size: 10.5px; color: #2E7D32; background: #E8F5E9; border: 1px solid #C8E6C9; padding: 2px 6px; border-radius: 3px; font-weight: 600; margin-bottom: 6px; letter-spacing: 0.5px;}
.tag-mitigate { display:inline-block; font-size: 10.5px; color: #C0392B; background: #FDEDEC; border: 1px solid #FADBD8; padding: 2px 6px; border-radius: 3px; font-weight: 600; margin-bottom: 6px; letter-spacing: 0.5px;}

/* NEW CSS: Perfectly aligned grid for the bottom summary section */
.summary-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-top: 15px; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; }
.summary-card { background: #ffffff; border: 1px solid #eaeaea; border-top: 3px solid #3498db; border-radius: 4px; padding: 20px; height: 100%; display: flex; flex-direction: column; box-shadow: 0 1px 2px rgba(0,0,0,0.01); }
.summary-card.timeline { border-top-color: #2ecc71; }
.summary-card.remedy { border-top-color: #f1c40f; }
.summary-title { font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; color: #888; font-weight: 600; margin-bottom: 12px; border-bottom: 1px solid #f9f9f9; padding-bottom: 6px;}
</style>"""

if calc_btn:
    if not b_name or not b_loc or not g_name or not g_loc: 
        st.error("Please ensure all Name and City fields are filled out!")
    else:
        with st.spinner("Calculating dashas, math matrices, and querying Deep AI Oracle..."):
            st.markdown(css_block, unsafe_allow_html=True)
            
            # 1. Coordinate & Astrological Calculations
            b_lat, b_lon, b_tz = get_location_coordinates(b_loc)
            g_lat, g_lon, g_tz = get_location_coordinates(g_loc)
            
            b_data = calculate_match_chart(b_dob, b_tob, b_lat, b_lon, b_tz)
            g_data = calculate_match_chart(g_dob, g_tob, g_lat, g_lon, g_tz)
            
            score, porutham_results = calculate_10_porutham(b_data['Nak_Idx'], g_data['Nak_Idx'], b_data['Rasi_Idx'], g_data['Rasi_Idx'], b_name, g_name)

            # Build empathetic instructions based on the math
            ai_math_directives = ""
            for key, res in porutham_results.items():
                status = "Harmonious" if res.get('match') else "Requires conscious navigation and compromise"
                ai_math_directives += f"- {key}: Mathematically, this is {status}. Explain this dynamic compassionately.\n"

            # 2. Advanced AI Fetching
            API_KEY = st.secrets.get("GEMINI_API_KEY", "")
            ai_data = None
            
            if API_KEY:
                try:
                    genai.configure(api_key=API_KEY)
                    model = genai.GenerativeModel('gemini-2.5-flash') 
                    
                    json_schema = """
                    {
                        "summary": {
                            "time_forecast": "1 cohesive paragraph utilizing their current Dasha periods to forecast their relationship timeline and its impact over the next 5 years.",
                            "psychological": "1 cohesive paragraph analyzing their emotional alignment and psychological friction points.",
                            "remedy": "1 cohesive paragraph providing a specific traditional Vedic Upaya (mantra/donation) AND a modern scientific/psychological strategy (e.g., specific communication frameworks) to mitigate their weakest point."
                        },
                        "porutham_insights": {
                            "Dina": "1-2 empathetic sentences explaining the mathematical result.",
                            "Gana": "1-2 empathetic sentences explaining the mathematical result.",
                            "Mahendra": "1-2 empathetic sentences explaining the mathematical result.",
                            "Rajju": "1-2 empathetic sentences explaining the mathematical result.",
                            "Rasi": "1-2 empathetic sentences explaining the mathematical result.",
                            "Rasyadhipati": "1-2 empathetic sentences explaining the mathematical result.",
                            "Yoni": "1-2 empathetic sentences explaining the mathematical result.",
                            "Vasya": "1-2 empathetic sentences explaining the mathematical result.",
                            "Stree": "1-2 empathetic sentences explaining the mathematical result.",
                            "Vedha": "1-2 empathetic sentences explaining the mathematical result."
                        }
                    }
                    """
                    
                    prompt = f"""
                    Act as an elite Vedic Astrologer and Modern Relationship Counselor. Analyze {b_name} (Star: {b_data['Nakshatra']}, Moon: {b_data['Rasi']}) and {g_name} (Star: {g_data['Nakshatra']}, Moon: {g_data['Rasi']}).
                    Current Time Data: {b_name} is in {b_data['Dasha']} Mahadasha. {g_name} is in {g_data['Dasha']} Mahadasha.
                    Relationship Context: {rel_status}.
                    
                    CRITICAL INSTRUCTIONS: 
                    1. EMPATHY & TONE: Write in an objective, deeply empathetic THIRD-PERSON perspective. Do NOT use harsh, robotic language. Reframe mismatches as "opportunities for growth" or areas requiring "conscious nurturing."
                    2. MATH ALIGNMENT: You MUST base your insights on the exact mathematical results below.
                    3. REMEDIES: The remedy section MUST include both an ancient Vedic text/mantra solution and a modern psychological tool.
                    4. FORMATTING: Return plain text within the JSON values. Do NOT use bullet points or markdown formatting.
                    
                    Mathematical Results:
                    {ai_math_directives}
                    
                    Return ONLY a JSON object strictly following this structure:
                    {json_schema}
                    """
                    
                    resp = model.generate_content(prompt)
                    clean_resp = resp.text.replace('```json', '').replace('```', '').strip()
                    ai_data = json.loads(clean_resp)
                except Exception as e:
                    st.warning(f"AI Oracle offline or parsing failed. ({e})")

            # 3. Output Rendering
            st.subheader(f"Compatibility Score: {score}/10")
            
            html_grid = '<div class="bp-grid">'
            for key, res in porutham_results.items():
                is_match = res.get('match', False)
                tag_class = "tag-harness" if is_match else "tag-mitigate"
                tag_text = "FAVORABLE" if is_match else "MITIGATE"
                
                insight_text = "Analysis unavailable."
                base_key = key.split(' ')[0].strip()
                
                if ai_data and 'porutham_insights' in ai_data:
                    for ai_key, ai_val in ai_data['porutham_insights'].items():
                        if ai_key.lower() == base_key.lower():
                            insight_text = ai_val
                            break
                            
                def_text = ""
                for p_key, p_val in PORUTHAM_DEFS.items():
                    if p_key.lower() == base_key.lower():
                        def_text = p_val
                        break
                
                html_grid += f'<div class="bp-card"><div class="bp-head"><span>{key}</span><span class="{tag_class}">{tag_text}</span></div><div class="bp-desc">{insight_text}</div><div class="bp-def">{def_text}</div></div>'
                
            html_grid += '</div>'
            st.markdown(html_grid, unsafe_allow_html=True)
            
            # 4. NEW: Custom CSS Grid for Strategic Summary (Equal heights & identical fonts)
            if ai_data and 'summary' in ai_data:
                st.divider()
                st.markdown("### Strategic Alignment & Timeline Forecast")
                
                summary_grid_html = f"""
                <div class="summary-grid">
                    <div class="summary-card">
                        <div class="summary-title">Psychological Alignment</div>
                        <div class="bp-desc">{ai_data['summary'].get('psychological', '')}</div>
                    </div>
                    
                    <div class="summary-card timeline">
                        <div class="summary-title">Timeline Forecast ({b_data['Dasha']} / {g_data['Dasha']})</div>
                        <div class="bp-desc">{ai_data['summary'].get('time_forecast', '')}</div>
                    </div>
                    
                    <div class="summary-card remedy">
                        <div class="summary-title">Integrated Remedial Action</div>
                        <div class="bp-desc">{ai_data['summary'].get('remedy', '')}</div>
                    </div>
                </div>
                """
                st.markdown(summary_grid_html, unsafe_allow_html=True)
