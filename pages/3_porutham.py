import streamlit as st
import swisseph as swe
from datetime import datetime, time
import json
import google.generativeai as genai
from supabase import create_client

# Note: Ensure these imports are available in your environment
from astro_engine import get_location_coordinates, get_utc_offset, calculate_10_porutham, ZODIAC, ZODIAC_TA
from report_generator import get_south_indian_chart_html

NAKSHATRAS = ["Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra", "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"]

@st.cache_resource
def init_connection():
    try:
        return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    except Exception as e:
        st.sidebar.error(f"Supabase Connection Failed: {e}")
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
                except: continue
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
    # Simple house calculation
    houses, ascmc = swe.houses_ex(jd_ut, lat, lon, b'P', swe.FLG_SIDEREAL)
    lagna_rasi = int(ascmc[0]/30) + 1
    p_pos["Lagna"] = lagna_rasi
    
    m_l_dist = (p_pos["Mars"] - lagna_rasi + 1) if (p_pos["Mars"] >= lagna_rasi) else (p_pos["Mars"] + 12 - lagna_rasi + 1)
    m_m_dist = (p_pos["Mars"] - p_pos["Moon"] + 1) if (p_pos["Mars"] >= p_pos["Moon"]) else (p_pos["Mars"] + 12 - p_pos["Moon"] + 1)
    is_manglik = m_l_dist in [2, 4, 7, 8, 12] or m_m_dist in [2, 4, 7, 8, 12]
    
    nak_idx = int(moon_lon / (360/27))
    return {"Lagna": ZODIAC[lagna_rasi], "Lagna_Idx": lagna_rasi, "Rasi": ZODIAC[p_pos["Moon"]], "Rasi_Idx": p_pos["Moon"], "Nakshatra": NAKSHATRAS[nak_idx], "Nak_Idx": nak_idx, "Is_Manglik": is_manglik, "P_Pos": p_pos}

# ... [Keep your get_executive_insight and UI setup code here] ...

if calc_btn:
    if not b_name or not b_loc or not g_name or not g_loc: 
        st.error("Please ensure all Name and City fields are filled out!")
    else:
        with st.spinner("Analyzing Synergy..."):
            st.markdown(css_block, unsafe_allow_html=True)
            
            # 1. Core Calculations
            b_lat, b_lon, b_tz = get_location_coordinates(b_loc)
            g_lat, g_lon, g_tz = get_location_coordinates(g_loc)
            b_data = calculate_match_chart(b_dob, b_tob, b_lat, b_lon, b_tz)
            g_data = calculate_match_chart(g_dob, g_tob, g_lat, g_lon, g_tz)
            score, porutham_results = calculate_10_porutham(b_data['Nak_Idx'], g_data['Nak_Idx'], b_data['Rasi_Idx'], g_data['Rasi_Idx'], b_name, g_name)

            # 2. AI Data Fetching
            API_KEY = st.secrets.get("GEMINI_API_KEY", "")
            ai_content = None
            if API_KEY:
                try:
                    genai.configure(api_key=API_KEY)
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    
                    prompt = f"""
                    Analyze Vedic compatibility for {b_name} ({b_data['Nakshatra']}) and {g_name} ({g_data['Nakshatra']}).
                    Return ONLY a JSON object in {LANG} with keys: 'summary' (with subkeys 'psychological', 'wealth', 'harnessing') 
                    and 'porutham_insights' (with keys for Dina, Gana, Mahendra, Rajju, Rasi, Rasi Adhipathi, Vasiya, Stree, Vedha, Nadi).
                    """
                    resp = model.generate_content(prompt)
                    # Strip markdown code blocks if AI includes them
                    clean_json = resp.text.replace('```json', '').replace('```', '').strip()
                    ai_content = json.loads(clean_json)
                except Exception as e:
                    st.warning(f"AI Insight unavailable: {e}")

            # 3. Display Results
            st.subheader(f"Compatibility Score: {score}/10")
            
            html_grid = '<div class="bp-grid">'
            for key, res in porutham_results.items():
                is_match = res.get('match', False)
                tag_class = "tag-harness" if is_match else "tag-mitigate"
                tag_text = "FAVORABLE" if is_match else "REQUIRES ATTENTION"
                
                # Use AI insight if available, else use fallback
                detailed_insight = ai_content['porutham_insights'].get(key, get_executive_insight(key, is_match, LANG)) if ai_content else get_executive_insight(key, is_match, LANG)
                
                html_grid += f"""
                <div class="bp-card">
                    <div class="bp-head"><span>{key}</span><span class="{tag_class}">{tag_text}</span></div>
                    <div class="bp-desc">{detailed_insight}</div>
                </div>
                """
            html_grid += '</div>'
            st.markdown(html_grid, unsafe_allow_html=True)

            if ai_content:
                st.markdown("### Strategic AI Summary")
                st.info(ai_content['summary']['psychological'])
                st.success(ai_content['summary']['wealth'])
