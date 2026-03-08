import streamlit as st
import swisseph as swe
from datetime import datetime, time
import google.generativeai as genai
from supabase import create_client

from astro_engine import get_location_coordinates, get_utc_offset, calculate_10_porutham, ZODIAC, ZODIAC_TA
from report_generator import get_south_indian_chart_html

NAKSHATRAS = ["Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra", "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"]

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

def calculate_match_chart(dob, tob, lat, lon, tz_str):
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    offset = get_utc_offset(tz_str, datetime.combine(dob, tob))
    jd_ut = swe.julday(dob.year, dob.month, dob.day, (tob.hour + (tob.minute/60.0)) - offset)
    
    planets = {"Sun": swe.SUN, "Moon": swe.MOON, "Mars": swe.MARS, "Mercury": swe.MERCURY, "Jupiter": swe.JUPITER, "Venus": swe.VENUS, "Saturn": swe.SATURN, "Rahu": swe.MEAN_NODE}
    p_pos = {p: int(swe.calc_ut(jd_ut, pid, swe.FLG_SIDEREAL)[0][0] / 30) + 1 for p, pid in planets.items()}
    
    rahu_lon = swe.calc_ut(jd_ut, swe.MEAN_NODE, swe.FLG_SIDEREAL)[0][0]
    p_pos["Ketu"] = int(((rahu_lon + 180) % 360) / 30) + 1
    
    moon_lon = swe.calc_ut(jd_ut, swe.MOON, swe.FLG_SIDEREAL)[0][0]
    lagna_rasi = int(swe.houses_ex(jd_ut, lat, lon, b'P', swe.FLG_SIDEREAL)[1][0]/30) + 1
    p_pos["Lagna"] = lagna_rasi
    
    m_l_dist = (p_pos["Mars"] - lagna_rasi + 1) if (p_pos["Mars"] >= lagna_rasi) else (p_pos["Mars"] + 12 - lagna_rasi + 1)
    m_m_dist = (p_pos["Mars"] - p_pos["Moon"] + 1) if (p_pos["Mars"] >= p_pos["Moon"]) else (p_pos["Mars"] + 12 - p_pos["Moon"] + 1)
    is_manglik = m_l_dist in [2, 4, 7, 8, 12] or m_m_dist in [2, 4, 7, 8, 12]
    
    nak_idx = int(moon_lon / 13.333333333)
    return {"Lagna": ZODIAC[lagna_rasi], "Lagna_Idx": lagna_rasi, "Rasi": ZODIAC[p_pos["Moon"]], "Rasi_Idx": p_pos["Moon"], "Nakshatra": NAKSHATRAS[nak_idx], "Nak_Idx": nak_idx, "Is_Manglik": is_manglik, "P_Pos": p_pos}

def get_executive_insight(key, is_match, lang):
    """Maps traditional Porutham keys to modern executive insights."""
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

# --- UI START ---
st.title("Strategic Synergy")
st.markdown("<div style='color:#7f8c8d; margin-top:-15px; margin-bottom: 20px;'>Matchmaking (Porutham) & Partnership Matrix</div>", unsafe_allow_html=True)
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
    st.markdown("### 👨 Partner A Details")
    sel_p1 = st.selectbox("Load Profile", profile_options, key="sel_p1")
    if sel_p1 in ["✨ Select Profile...", "✏️ Enter Manually"]: def_n1, def_dob1, def_tob1, def_loc1 = "", datetime(2000, 1, 1).date(), time(12, 0), ""
    else: def_n1, def_dob1, def_tob1, def_loc1 = sel_p1, saved_profiles[sel_p1]["dob"], saved_profiles[sel_p1]["tob"], saved_profiles[sel_p1]["city"]

    k1 = sel_p1.replace(" ", "_")
    b_name = st.text_input("Name", value=def_n1, key=f"p1_n_{k1}")
    b_dob = st.date_input("Date of Birth", value=def_dob1, min_value=datetime(1950, 1, 1).date(), max_value=datetime.today().date(), key=f"p1_d_{k1}")
    b_tob = st.time_input("Time of Birth", value=def_tob1, step=60, key=f"p1_t_{k1}")
    b_loc = st.text_input("City", value=def_loc1, key=f"p1_l_{k1}")

with col_g:
    st.markdown("### 👩 Partner B Details")
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

# --- GLOBAL CSS FOR FLAT EXECUTIVE CARDS ---
css_block = """<style>
.bp-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px; margin-bottom: 20px; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; }
.bp-card { background: #ffffff; border: 1px solid #eaeaea; border-radius: 4px; padding: 20px; display: flex; flex-direction: column; box-shadow: 0 1px 2px rgba(0,0,0,0.01); }
.bp-head { font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; color: #888; font-weight: 500; margin-bottom: 12px; border-bottom: 1px solid #f9f9f9; padding-bottom: 6px; display: flex; justify-content: space-between; }
.bp-title { font-size: 17px; font-weight: 500; color: #2c3e50; margin-bottom: 6px; }
.bp-desc { font-size: 13.5px; color: #444; line-height: 1.5; font-weight: 300; margin-bottom:12px; }
.tag-harness { display:inline-block; font-size: 10.5px; color: #2E7D32; background: #E8F5E9; border: 1px solid #C8E6C9; padding: 2px 6px; border-radius: 3px; font-weight: 600; margin-bottom: 6px; }
.tag-mitigate { display:inline-block; font-size: 10.5px; color: #C0392B; background: #FDEDEC; border: 1px solid #FADBD8; padding: 2px 6px; border-radius: 3px; font-weight: 600; margin-bottom: 6px; }
.insight-text { font-size: 12.5px; color: #222; font-style: italic; background: #fafafa; padding: 10px; border-radius: 4px; border: 1px solid #f5f5f5; }
</style>"""

if calc_btn:
    if not b_name or not b_loc or not g_name or not g_loc: st.error("Please ensure all Name and City fields are filled out for both partners!")
    else:
        with st.spinner("Calculating exact coordinates & relationship matrix..."):
            st.markdown(css_block, unsafe_allow_html=True)
            
            b_lat, b_lon, b_tz = get_location_coordinates(b_loc)
            g_lat, g_lon, g_tz = get_location_coordinates(g_loc)
            
            b_data = calculate_match_chart(b_dob, b_tob, b_lat, b_lon, b_tz)
            g_data = calculate_match_chart(g_dob, g_tob, g_lat, g_lon, g_tz)
            
            b_lagna = ZODIAC_TA.get(b_data['Lagna_Idx'], "") if LANG == "Tamil" else b_data['Lagna']
            b_rasi = ZODIAC_TA.get(b_data['Rasi_Idx'], "") if LANG == "Tamil" else b_data['Rasi']
            g_lagna = ZODIAC_TA.get(g_data['Lagna_Idx'], "") if LANG == "Tamil" else g_data['Lagna']
            g_rasi = ZODIAC_TA.get(g_data['Rasi_Idx'], "") if LANG == "Tamil" else g_data['Rasi']
            
            # Upgrade Identity Cards to Executive Style
            astro_html = f"""
<div class="bp-grid">
<div class="bp-card" style="border-top: 3px solid #2980b9;">
<div class="bp-head"><span>Identity</span> <span>Partner A</span></div>
<div class="bp-title">{b_name}</div>
<div class="bp-desc" style="margin-bottom:0;"><b>Lagna:</b> {b_lagna}<br><b>Rasi:</b> {b_rasi}<br><b>Star:</b> {b_data['Nakshatra']}</div>
</div>
<div class="bp-card" style="border-top: 3px solid #8e44ad;">
<div class="bp-head"><span>Identity</span> <span>Partner B</span></div>
<div class="bp-title">{g_name}</div>
<div class="bp-desc" style="margin-bottom:0;"><b>Lagna:</b> {g_lagna}<br><b>Rasi:</b> {g_rasi}<br><b>Star:</b> {g_data['Nakshatra']}</div>
</div>
</div>"""
            st.markdown(astro_html, unsafe_allow_html=True)
            
            st.write("")
            chart_c1, chart_c2 = st.columns(2)
            with chart_c1: st.markdown(get_south_indian_chart_html(b_data['P_Pos'], b_data['Lagna_Idx'], f"{b_name} Rasi Chart", LANG), unsafe_allow_html=True)
            with chart_c2: st.markdown(get_south_indian_chart_html(g_data['P_Pos'], g_data['Lagna_Idx'], f"{g_name} Rasi Chart", LANG), unsafe_allow_html=True)
                    
            st.write("") 
            score, porutham_results = calculate_10_porutham(b_data['Nak_Idx'], g_data['Nak_Idx'], b_data['Rasi_Idx'], g_data['Rasi_Idx'], b_name, g_name)
            
            # Upgrade Manglik Card
            m_match = (b_data['Is_Manglik'] == g_data['Is_Manglik'])
            m_color = "#27ae60" if m_match else "#c0392b"
            m_tag = "BALANCED" if m_match else "IMBALANCE DETECTED"
            m_title = "Chevvai (Mars) Dosham"
            m_desc = "Both partners share a compatible level of Martian energy, protecting the bond." if m_match else "There is a difference in Chevvai influence. Conscious patience is required to maintain harmony."
            
            m_html = f"""<div class="bp-grid" style="grid-template-columns: 1fr; margin-top:20px;">
<div class="bp-card" style="border-left: 3px solid {m_color};">
<div class="bp-head"><span>Mars Energy</span> <span style="color:{m_color}; font-weight:bold;">{m_tag}</span></div>
<div class="bp-title">{m_title}</div>
<div class="bp-desc" style="margin-bottom:0;">{m_desc}</div>
</div>
</div>"""
            st.markdown(m_html, unsafe_allow_html=True)
            
            st.divider()
            
            # Alignment Score Header
            score_color = "#27ae60" if score >= 6 else "#f39c12" if score >= 4 else "#c0392b"
            status_tag = "APPROVED" if score >= 6 else "CAUTION" if score >= 4 else "HIGH RISK"
            score_html = f"""<div class="bp-grid" style="grid-template-columns: 1fr;">
<div class="bp-card" style="border-top: 3px solid {score_color}; flex-direction:row; justify-content:space-between; align-items:center;">
<div>
<div class="bp-head" style="border:none; margin:0; padding:0;">Overall Alignment Score</div>
<div style="font-size:42px; font-weight:300; color:#111; line-height:1; margin-top:5px;">{score}<span style="font-size:16px; color:#888;">/10</span></div>
</div>
<div style="text-align:right;">
<span style="background:{score_color}; color:#fff; padding: 4px 10px; border-radius: 3px; font-size: 11px; font-weight: bold; letter-spacing: 0.5px;">{status_tag}</span>
</div>
</div>
</div>"""
            st.markdown(score_html, unsafe_allow_html=True)
            
            # Process Porutham Dictionary into Executive Cards
            matched_items = {k: v for k, v in porutham_results.items() if v["match"]}
            unmatched_items = {k: v for k, v in porutham_results.items() if not v["match"]}
            
            grid_html = """<div class="bp-grid">"""
            
            for k, v in porutham_results.items():
                is_match = v["match"]
                card_border = "#2E7D32" if is_match else "#C0392B"
                status_text = "ALIGNED" if is_match else "MISALIGNED"
                tag_class = "tag-harness" if is_match else "tag-mitigate"
                tag_label = "HARNESS STRENGTH" if is_match else "MITIGATE RISK"
                insight = get_executive_insight(k, is_match, LANG)

                grid_html += f"""
<div class="bp-card" style="border-top: 3px solid {card_border};">
<div class="bp-head"><span>{k}</span> <span style="color:{card_border}; font-weight:bold;">{status_text}</span></div>
<div class="bp-desc">{v['desc']}</div>
<div style="margin-top:auto; padding-top:12px; border-top: 1px dashed #eee;">
<div class="{tag_class}">{tag_label}</div>
<div class="insight-text">{insight}</div>
</div>
</div>"""
            
            grid_html += "</div>"
            st.markdown(grid_html, unsafe_allow_html=True)

            st.divider()
            
            # --- AI ORACLE REMAINS UNTOUCHED ---
            API_KEY = st.secrets.get("GEMINI_API_KEY", "")
            if not API_KEY:
                try:
                    from api_config import GEMINI_API_KEY
                    API_KEY = GEMINI_API_KEY
                except: pass

            if not API_KEY: st.error("API Key missing! Add it to Streamlit Secrets to generate AI insights.")
            else:
                st.markdown("### 💬 Deep AI Relationship Oracle")
                with st.spinner("The AI Astrologer is compiling a personalized consultation..."):
                    try:
                        genai.configure(api_key=API_KEY)
                        match_list = ", ".join(list(matched_items.keys()))
                        unmatch_list = ", ".join(list(unmatched_items.keys()))
                        
                        prompt = f"""
                        You are an elite Vedic Astrologer analyzing compatibility between {b_name} and {g_name} who are {rel_status}.
                        Traditional Score: {score}/10. Aligned: {match_list}. Unmatched: {unmatch_list}.
                        Write a deep analysis using these EXACT headers. If language is Tamil, reply in full Tamil. Language requested: {LANG}.
                        
                        ### 🧠 Psychological Dynamic
                        (2-sentence intro, then 2 bullet points on strengths and friction)
                        
                        ### 🏡 Life & Wealth
                        (2-sentence intro, then 2 bullet points on money and domestic alignment)
                        
                        ### ⚖️ Harnessing & Balancing
                        (2-sentence intro, then 2 bullet points on how to use their strengths to overcome their weaknesses)
                        """
                        
                        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                        target_model = available_models[0] if available_models else 'gemini-1.5-flash'
                        for m in available_models:
                            if 'gemini-1.5-flash' in m: target_model = m; break
                            elif '1.5-pro' in m or '1.0-pro' in m: target_model = m
                        
                        model = genai.GenerativeModel(target_model)
                        st.markdown(model.generate_content(prompt).text)
                    except Exception as e: st.error(f"AI Generation Failed. Details: {e}")
