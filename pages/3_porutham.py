import streamlit as st
import swisseph as swe
from datetime import datetime, time
import json
import google.generativeai as genai
from supabase import create_client

# Ensure these imports are correctly pointing to your actual engine file
from astro_engine import get_location_coordinates, get_utc_offset, calculate_10_porutham, ZODIAC, ZODIAC_TA

NAKSHATRAS = ["Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra", "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"]

@st.cache_resource
def init_connection():
    try: 
        return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    except Exception as e: 
        st.sidebar.error("Supabase connection skipped or failed.")
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

def calculate_match_chart(dob, tob, lat, lon, tz_str):
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    offset = get_utc_offset(tz_str, datetime.combine(dob, tob))
    jd_ut = swe.julday(dob.year, dob.month, dob.day, (tob.hour + (tob.minute/60.0)) - offset)
    
    planets = {"Sun": swe.SUN, "Moon": swe.MOON, "Mars": swe.MARS, "Mercury": swe.MERCURY, "Jupiter": swe.JUPITER, "Venus": swe.VENUS, "Saturn": swe.SATURN, "Rahu": swe.MEAN_NODE}
    p_pos = {p: int(swe.calc_ut(jd_ut, pid, swe.FLG_SIDEREAL)[0][0] / 30) + 1 for p, pid in planets.items()}
    
    rahu_lon = swe.calc_ut(jd_ut, swe.MEAN_NODE, swe.FLG_SIDEREAL)[0][0]
    p_pos["Ketu"] = int(((rahu_lon + 180) % 360) / 30) + 1
    
    moon_lon = swe.calc_ut(jd_ut, swe.MOON, swe.FLG_SIDEREAL)[0][0]
    houses, ascmc = swe.houses_ex(jd_ut, lat, lon, b'P', swe.FLG_SIDEREAL)
    lagna_rasi = int(ascmc[0]/30) + 1
    p_pos["Lagna"] = lagna_rasi
    
    m_l_dist = (p_pos["Mars"] - lagna_rasi + 1) if (p_pos["Mars"] >= lagna_rasi) else (p_pos["Mars"] + 12 - lagna_rasi + 1)
    m_m_dist = (p_pos["Mars"] - p_pos["Moon"] + 1) if (p_pos["Mars"] >= p_pos["Moon"]) else (p_pos["Mars"] + 12 - p_pos["Moon"] + 1)
    is_manglik = m_l_dist in [2, 4, 7, 8, 12] or m_m_dist in [2, 4, 7, 8, 12]
    
    nak_idx = int(moon_lon / 13.333333333)
    return {"Lagna": ZODIAC[lagna_rasi], "Lagna_Idx": lagna_rasi, "Rasi": ZODIAC[p_pos["Moon"]], "Rasi_Idx": p_pos["Moon"], "Nakshatra": NAKSHATRAS[nak_idx], "Nak_Idx": nak_idx, "Is_Manglik": is_manglik, "P_Pos": p_pos}

def get_executive_insight(key, is_match, lang):
    insights = {
        "Dina": ("Excellent sync in daily routines. Build shared habits.", "Expect friction in daily routines. Give each other independent space."),
        "Gana": ("Temperaments align beautifully. Synergy is natural.", "Potential for ego clashes. Communication must be structured and objective."),
        "Mahendra": ("Highly favorable for starting joint ventures or building assets.", "Financial growth relies on individual effort rather than combined synergy."),
        "Rajju": ("No fatal astrological conflicts. The foundation is highly secure.", "SEVERE RISK: Same Rajju detected. Traditional astrology advises against this union."),
        "Rasi": ("Worldviews and life trajectories are naturally parallel.", "Conflicting worldviews. Will require constant compromise and diplomacy."),
        "Rasi Adhipathi": ("Core motivations and planetary rulers are allied.", "Planetary rulers are hostile. Requires conscious effort to align goals."),
        "Vasiya": ("High natural magnetism and mutual understanding.", "Attraction requires active nurturing; it may not be automatic."),
        "Stree": ("Strong foundation for long-term prosperity and wealth accumulation.", "Prosperity requires structured financial planning, avoiding impulsive decisions."),
        "Vedha": ("No energetic blockages detected.", "Energetic affliction present. Proceed with strict caution."),
        "Nadi": ("Genetic and energetic compatibility is strong.", "Pulse mismatch detected. Health and wellness require extra attention.")
    }
    for ik, iv in insights.items():
        if ik.lower() in key.lower():
            return iv[0] if is_match else iv[1]
    
    if is_match: return "Leverage this alignment for combined growth." if lang == "English" else "இந்த பொருத்தத்தை உங்கள் கூட்டு வளர்ச்சிக்காகப் பயன்படுத்தவும்."
    return "Requires active communication and boundaries to mitigate friction." if lang == "English" else "கருத்து வேறுபாடுகளைத் தவிர்க்க தெளிவான புரிதல் அவசியம்."

# --- PAGE CONFIG ---
st.set_page_config(page_title="Strategic Synergy", layout="wide")

st.title("Strategic Synergy")
st.markdown("<div style='color:#7f8c8d; margin-top:-15px; margin-bottom: 20px;'>Matchmaking (Porutham) & Partnership Matrix</div>", unsafe_allow_html=True)
st.divider()

# --- UI SETUP ---
with st.sidebar:
    st.markdown("<div style='font-size: 11px; font-weight: 600; color: #888; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 10px;'>Engine Settings</div>", unsafe_allow_html=True)
    LANG = st.radio("Language / மொழி", ["English", "Tamil"], horizontal=True, label_visibility="collapsed")
    st.divider()

st.markdown("<div style='font-size: 11px; font-weight: 600; color: #888; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px;'>Relationship Context</div>", unsafe_allow_html=True)
rel_status = st.radio("Context", ["Exploring a Match", "Already Married / Committed"], horizontal=True, label_visibility="collapsed")
st.write("")

saved_profiles = load_profiles_from_db()
profile_options = ["(Select Profile)", "Enter Manually"] + list(saved_profiles.keys())

col_b, col_g = st.columns(2)

with col_b:
    st.markdown("<div style='font-size: 11px; font-weight: 600; color: #2c3e50; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 10px; border-bottom: 1px solid #eee; padding-bottom: 5px;'>Partner A (Subject)</div>", unsafe_allow_html=True)
    sel_p1 = st.selectbox("Load Profile (A)", profile_options, key="sel_p1", label_visibility="collapsed")
    if sel_p1 in ["(Select Profile)", "Enter Manually"]: 
        def_n1, def_dob1, def_tob1, def_loc1 = "", datetime(2000, 1, 1).date(), time(12, 0), ""
    else: 
        def_n1, def_dob1, def_tob1, def_loc1 = sel_p1, saved_profiles[sel_p1]["dob"], saved_profiles[sel_p1]["tob"], saved_profiles[sel_p1]["city"]

    k1 = sel_p1.replace(" ", "_")
    b_name = st.text_input("Name", value=def_n1, key=f"p1_n_{k1}", placeholder="Full Name")
    b_dob = st.date_input("Date of Birth", value=def_dob1, min_value=datetime(1950, 1, 1).date(), max_value=datetime.today().date(), key=f"p1_d_{k1}")
    b_tob = st.time_input("Time of Birth", value=def_tob1, step=60, key=f"p1_t_{k1}")
    b_loc = st.text_input("City", value=def_loc1, key=f"p1_l_{k1}", placeholder="Birth City")

with col_g:
    st.markdown("<div style='font-size: 11px; font-weight: 600; color: #2c3e50; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 10px; border-bottom: 1px solid #eee; padding-bottom: 5px;'>Partner B (Counterpart)</div>", unsafe_allow_html=True)
    sel_p2 = st.selectbox("Load Profile (B)", profile_options, key="sel_p2", label_visibility="collapsed")
    if sel_p2 in ["(Select Profile)", "Enter Manually"]: 
        def_n2, def_dob2, def_tob2, def_loc2 = "", datetime(2000, 1, 1).date(), time(12, 0), ""
    else: 
        def_n2, def_dob2, def_tob2, def_loc2 = sel_p2, saved_profiles[sel_p2]["dob"], saved_profiles[sel_p2]["tob"], saved_profiles[sel_p2]["city"]

    k2 = sel_p2.replace(" ", "_")
    g_name = st.text_input("Name", value=def_n2, key=f"p2_n_{k2}", placeholder="Full Name")
    g_dob = st.date_input("Date of Birth", value=def_dob2, min_value=datetime(1950, 1, 1).date(), max_value=datetime.today().date(), key=f"p2_d_{k2}")
    g_tob = st.time_input("Time of Birth", value=def_tob2, step=60, key=f"p2_t_{k2}")
    g_loc = st.text_input("City", value=def_loc2, key=f"p2_l_{k2}", placeholder="Birth City")

st.divider()

# THIS DEFINES THE BUTTON that was causing the NameError!
calc_btn = st.button("Generate Executive Synergy Report", type="primary", use_container_width=True)

# --- GLOBAL CSS FOR FLAT EXECUTIVE CARDS ---
css_block = """<style>
.bp-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px; margin-bottom: 20px; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; }
.bp-card { background: #ffffff; border: 1px solid #eaeaea; border-radius: 4px; padding: 20px; display: flex; flex-direction: column; box-shadow: 0 1px 2px rgba(0,0,0,0.01); }
.bp-head { font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; color: #888; font-weight: 500; margin-bottom: 12px; border-bottom: 1px solid #f9f9f9; padding-bottom: 6px; display: flex; justify-content: space-between; }
.bp-title { font-size: 17px; font-weight: 500; color: #2c3e50; margin-bottom: 6px; }
.bp-desc { font-size: 13.5px; color: #444; line-height: 1.5; font-weight: 300; margin-bottom:12px; }
.tag-harness { display:inline-block; font-size: 10.5px; color: #2E7D32; background: #E8F5E9; border: 1px solid #C8E6C9; padding: 2px 6px; border-radius: 3px; font-weight: 600; margin-bottom: 6px; letter-spacing: 0.5px;}
.tag-mitigate { display:inline-block; font-size: 10.5px; color: #C0392B; background: #FDEDEC; border: 1px solid #FADBD8; padding: 2px 6px; border-radius: 3px; font-weight: 600; margin-bottom: 6px; letter-spacing: 0.5px;}
</style>"""

# --- EXECUTION LOGIC ---
if calc_btn:
    if not b_name or not b_loc or not g_name or not g_loc: 
        st.error("Please ensure all Name and City fields are filled out for both partners!")
    else:
        with st.spinner("Calculating precision metrics and querying Deep AI Oracle..."):
            st.markdown(css_block, unsafe_allow_html=True)
            
            # 1. Coordinate & Astrological Calculations
            b_lat, b_lon, b_tz = get_location_coordinates(b_loc)
            g_lat, g_lon, g_tz = get_location_coordinates(g_loc)
            
            b_data = calculate_match_chart(b_dob, b_tob, b_lat, b_lon, b_tz)
            g_data = calculate_match_chart(g_dob, g_tob, g_lat, g_lon, g_tz)
            
            score, porutham_results = calculate_10_porutham(b_data['Nak_Idx'], g_data['Nak_Idx'], b_data['Rasi_Idx'], g_data['Rasi_Idx'], b_name, g_name)

            # 2. AI Fetching
            API_KEY = st.secrets.get("GEMINI_API_KEY", "")
            ai_data = None
            
            if API_KEY:
                try:
                    genai.configure(api_key=API_KEY)
                    model = genai.GenerativeModel('gemini-1.5-flash', generation_config={"response_mime_type": "application/json"})
                    
                    json_schema = """
                    {
                        "summary": {
                            "psychological": "2 sentences on psychological alignment.",
                            "wealth": "2 sentences on financial synergy.",
                            "harnessing": "2 sentences on how to balance their dynamic."
                        },
                        "porutham_insights": {
                            "Dina": "1 sentence on Dina (Health/Daily Routine).",
                            "Gana": "1 sentence on Gana (Temperament).",
                            "Mahendra": "1 sentence on Wealth & Progeny.",
                            "Rajju": "1 sentence on Rajju (Longevity/Destiny).",
                            "Rasi": "1 sentence on Rasi compatibility.",
                            "Rasi Adhipathi": "1 sentence on planetary rulers.",
                            "Vasiya": "1 sentence on natural magnetism.",
                            "Stree": "1 sentence on prosperity.",
                            "Vedha": "1 sentence on energy blockages.",
                            "Nadi": "1 sentence on health/genetic alignment."
                        }
                    }
                    """
                    
                    prompt = f"Analyze compatibility between {b_name} (Star: {b_data['Nakshatra']}) and {g_name} (Star: {g_data['Nakshatra']}). Context: {rel_status}.\nReturn a JSON object strictly following this structure:\n{json_schema}"
                    
                    resp = model.generate_content(prompt)
                    # Safely load the JSON string
                    ai_data = json.loads(resp.text)
                except Exception as e:
                    st.warning(f"AI Oracle offline or parsing failed. Using standard insights. ({e})")

            # 3. Output Rendering
            st.subheader(f"Compatibility Score: {score}/10")
            
            html_grid = '<div class="bp-grid">'
            for key, res in porutham_results.items():
                is_match = res.get('match', False)
                tag_class = "tag-harness" if is_match else "tag-mitigate"
                tag_text = "FAVORABLE" if is_match else "MITIGATE"
                
                # Use AI insight if successfully loaded, else fallback to static dictionary
                if ai_data and 'porutham_insights' in ai_data and key in ai_data['porutham_insights']:
                    insight_text = ai_data['porutham_insights'][key]
                else:
                    insight_text = get_executive_insight(key, is_match, LANG)
                
                html_grid += f"""
                <div class="bp-card">
                    <div class="bp-head"><span>{key}</span><span class="{tag_class}">{tag_text}</span></div>
                    <div class="bp-desc">{insight_text}</div>
                </div>
                """
            html_grid += '</div>'
            st.markdown(html_grid, unsafe_allow_html=True)
            
            # 4. Strategic AI Summary Rendering
            if ai_data and 'summary' in ai_data:
                st.divider()
                st.markdown("### Strategic Alignment Roadmap")
                col1, col2, col3 = st.columns(3)
                col1.metric("Psychological Factor", "Aligned" if score > 5 else "Requires Focus")
                col1.info(ai_data['summary'].get('psychological', ''))
                
                col2.metric("Wealth/Domestic Potential", "Active")
                col2.success(ai_data['summary'].get('wealth', ''))
                
                col3.metric("Growth & Mitigation", "Actionable")
                col3.warning(ai_data['summary'].get('harnessing', ''))
