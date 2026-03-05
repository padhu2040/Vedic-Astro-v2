import streamlit as st
import swisseph as swe
from datetime import datetime, time
import google.generativeai as genai
from supabase import create_client
import plotly.graph_objects as go
import urllib.parse
import re

# --- IMPORTS FROM OUR CUSTOM ENGINES ---
from astro_engine import (
    get_location_coordinates, get_utc_offset, get_bhava_chalit, get_navamsa_chart, get_dasamsa_chart,
    determine_house, get_dignity, calculate_sav_score, get_nakshatra_details, scan_yogas,
    analyze_career_professional, analyze_education, analyze_health, analyze_love_marriage,
    generate_annual_forecast, get_transit_data_advanced, analyze_karmic_axis, get_house_strength_analysis,
    generate_mahadasha_table, generate_current_next_bhukti, get_micro_transits,
    t_p, t_p_eng, ZODIAC_TA, ZODIAC
)
from report_generator import get_south_indian_chart_html, generate_pdf_report
from database import identity_db, RASI_RULERS, lifestyle_guidance
from tamil_lang import TAMIL_IDENTITY_DB, TAMIL_LIFESTYLE

# --- SECURE API SETUP ---
API_KEY = st.secrets.get("GEMINI_API_KEY", "")
if not API_KEY:
    try:
        from api_config import GEMINI_API_KEY
        API_KEY = GEMINI_API_KEY
    except: pass

st.set_page_config(page_title="Vedic Astro AI Engine", layout="wide")

if 'report_generated' not in st.session_state: st.session_state.report_generated = False
if 'messages' not in st.session_state: st.session_state.messages = []

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

# --- 360 DEGREE MBTI & ENNEAGRAM ENGINE ---
def generate_360_mbti_persona(p_pos, lagna_rasi, sav_scores):
    fire_air = [1, 3, 5, 7, 9, 11]
    extro_score = sum(1 for p, r in p_pos.items() if r in fire_air)
    extro_pct = int((extro_score / len(p_pos)) * 100) if len(p_pos) > 0 else 50
    letter_1 = "E" if extro_pct >= 50 else "I"

    earth_signs = [2, 6, 10]
    sens_score = sum(1.5 for p, r in p_pos.items() if r in earth_signs)
    if p_pos.get("Saturn") in earth_signs: sens_score += 1
    sens_pct = int((sens_score / len(p_pos)) * 100)
    int_pct = 100 - sens_pct
    letter_2 = "S" if sens_pct > 50 else "N"

    think_pct = 50
    if p_pos.get("Moon", 1) in [4, 8, 12]: think_pct -= 15 
    if p_pos.get("Venus", 1) in [4, 8, 12]: think_pct -= 10
    if p_pos.get("Mercury", 1) in [3, 6, 7, 11]: think_pct += 15 
    if p_pos.get("Saturn", 1) in [3, 6, 7, 10, 11]: think_pct += 10
    think_pct = max(10, min(90, think_pct))
    letter_3 = "T" if think_pct >= 50 else "F"

    mutable_signs = [3, 6, 9, 12]
    perceiving_score = sum(1 for p, r in p_pos.items() if r in mutable_signs)
    perceiving_pct = int((perceiving_score / len(p_pos)) * 100)
    judging_pct = 100 - perceiving_pct
    letter_4 = "P" if perceiving_pct > 50 else "J"

    mbti_code = f"{letter_1}{letter_2}{letter_3}{letter_4}"

    mbti_profiles = {
        "INTJ": {"title": "The Architect", "desc": "You are a strategic, fiercely independent visionary. You approach life as a giant chessboard, always planning several moves ahead. You thrive on turning complex theories into actionable, high-level systems."},
        "INTP": {"title": "The Logician", "desc": "You are an innovative and deeply analytical thinker. You draw energy from unraveling the underlying principles of the universe, preferring abstract concepts and relentless intellectual exploration over mundane routines."},
        "ENTJ": {"title": "The Commander", "desc": "You are a bold, authoritative, and fiercely driven leader. You naturally see inefficiency and instantly know how to organize people and systems to achieve massive, overarching goals."},
        "ENTP": {"title": "The Debater", "desc": "You are a quick-witted, audacious intellectual. You love playing devil's advocate, tearing apart traditional systems, and brainstorming highly unconventional solutions to complex problems."},
        "INFJ": {"title": "The Advocate", "desc": "You are a quiet, mystical, and deeply inspiring force. You possess a profound intuition about human nature and dedicate your life to realizing a highly idealized vision of the future."},
        "INFP": {"title": "The Mediator", "desc": "You are a poetic, altruistic, and deeply empathetic soul. You are driven by an unshakeable set of inner values and seek harmony, authentic self-expression, and meaningful connections."},
        "ENFJ": {"title": "The Protagonist", "desc": "You are a charismatic, deeply empathetic, and natural-born leader. You possess an uncanny ability to inspire those around you, drawing energy from helping others reach their ultimate potential."},
        "ENFP": {"title": "The Campaigner", "desc": "You are an enthusiastic, wildly creative, and sociable spirit. You see life as a massive web of interconnected possibilities and thrive when you are free to explore new ideas and deep relationships."},
        "ISTJ": {"title": "The Logistician", "desc": "You are the backbone of society—practical, fact-minded, and fiercely reliable. You operate with unwavering logic and take pride in executing your duties perfectly, step by calculated step."},
        "ISFJ": {"title": "The Defender", "desc": "You are a deeply dedicated, warm, and highly observant protector. You draw energy from maintaining stability, honoring traditions, and quietly ensuring the people you care about are safe and secure."},
        "ESTJ": {"title": "The Executive", "desc": "You are an unsurpassed manager of people and processes. You value tradition, order, and dignity, bringing people together to execute projects efficiently and strictly by the book."},
        "ESFJ": {"title": "The Consul", "desc": "You are an extraordinarily caring, social, and community-minded leader. You draw immense energy from orchestrating harmony in your environment and ensuring everyone feels supported and valued."},
        "ISTP": {"title": "The Virtuoso", "desc": "You are a bold, practical, and highly adaptable master of your environment. You learn by doing, tearing things apart, and figuring out how they work with cool, detached logic."},
        "ISFP": {"title": "The Adventurer", "desc": "You are a flexible, charming, and highly aesthetic creator. You live totally in the present moment, using your rich inner emotional world to push the boundaries of conventional expression."},
        "ESTP": {"title": "The Entrepreneur", "desc": "You are a smart, energetic, and thrill-seeking operator. You do not just read the manual—you jump straight into the action, fixing problems on the fly and navigating risks with unmatched charm."},
        "ESFP": {"title": "The Entertainer", "desc": "You are spontaneous, highly energetic, and deeply observant. Life is a stage to you, and you draw immense energy from engaging with your environment and bringing joy to the people around you."}
    }
    
    corp_score = sav_scores[(lagna_rasi - 1 + 5) % 12]
    biz_score = sav_scores[(lagna_rasi - 1 + 6) % 12]
    prof_text = "Professionally, you possess a natural entrepreneurial spirit. You are built for equity, independent ventures, and leveraging strategic partnerships over standard employment." if biz_score > corp_score else "Professionally, you have a massive competitive advantage in structured corporate environments. You easily out-work rivals and thrive in complex hierarchies."
    profile = mbti_profiles.get(mbti_code, {"title": "The Strategist", "desc": "You are a highly analytical and adaptable individual."})

    return {
        "code": mbti_code, "title": profile["title"], "desc": profile["desc"],
        "extro_pct": extro_pct, "int_pct": int_pct, "think_pct": think_pct, "judging_pct": judging_pct, "prof_text": prof_text
    }

def get_enneagram_data(p_lon_absolute):
    degrees = {}
    for p in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]:
        if p in p_lon_absolute:
            deg = p_lon_absolute[p] % 30
            if p in ["Rahu", "Ketu"]: deg = 30 - deg
            degrees[p] = deg
            
    sorted_planets = sorted(degrees.items(), key=lambda x: x[1], reverse=True)
    ak = sorted_planets[0][0]
    amk = sorted_planets[1][0] if len(sorted_planets) > 1 else ak
    
    enneagram_map = {
        "Saturn": ("Type 1: The Reformer", "building structural perfection and integrity"),
        "Moon": ("Type 2: The Helper", "creating deep emotional bonds and being loved"),
        "Sun": ("Type 3: The Achiever", "achieving absolute success, value, and admiration"),
        "Ketu": ("Type 4: The Individualist", "finding profound, unique personal significance"),
        "Mercury": ("Type 5: The Investigator", "mastering complex knowledge and absolute competence"),
        "Venus": ("Type 6: The Loyalist", "establishing unbreakable security and aligned partnerships"),
        "Rahu": ("Type 7: The Enthusiast", "experiencing limitless freedom and boundary expansion"),
        "Mars": ("Type 8: The Challenger", "maintaining total control and protecting autonomy"),
        "Jupiter": ("Type 9: The Peacemaker", "sustaining internal peace, wisdom, and harmony")
    }
    
    vd_map = {
        "Sun": {"growth": "Mars", "stress": "Venus"}, "Moon": {"growth": "Venus", "stress": "Mars"},
        "Mars": {"growth": "Saturn", "stress": "Moon"}, "Mercury": {"growth": "Mercury", "stress": "Jupiter"},
        "Jupiter": {"growth": "Moon", "stress": "Saturn"}, "Venus": {"growth": "Jupiter", "stress": "Mercury"},
        "Saturn": {"growth": "Venus", "stress": "Mars"}, "Rahu": {"growth": "Mercury", "stress": "Jupiter"},
        "Ketu": {"growth": "Jupiter", "stress": "Mercury"}
    }

    growth_traits = {
        "Sun": "radiant leadership, empowering others, and true authority without ego",
        "Moon": "deep emotional intelligence, intuitive nurturing, and adaptable resilience",
        "Mars": "fearless execution, protective strength, and decisive courage",
        "Mercury": "brilliant communication, objective data analysis, and extreme adaptability",
        "Jupiter": "expansive wisdom, ethical guidance, and maintaining a high-level strategic vision",
        "Venus": "harmonious diplomacy, unconditional devotion, and aesthetic brilliance",
        "Saturn": "iron discipline, enduring patience, and building unbreakable foundations",
        "Rahu": "innovative disruption, fearless boundary-breaking, and visionary ambition",
        "Ketu": "profound detachment, spiritual mastery, and ego-less observation"
    }

    stress_traits = {
        "Sun": "arrogance, tyrannical micro-management, and a desperate need for external validation",
        "Moon": "irrational fear, moodiness, and emotionally manipulative behavior",
        "Mars": "reckless aggression, destructive impatience, and unnecessary conflict",
        "Mercury": "paralyzing overthinking, anxious scattered focus, and deceitful communication",
        "Jupiter": "rigid dogmatism, preachy arrogance, and reckless over-optimism",
        "Venus": "hedonistic indulgence, superficial vanity, and people-pleasing at the cost of your vision",
        "Saturn": "paralyzing fear, depressive isolation, and harsh, rigid control",
        "Rahu": "chaotic instability, deceptive illusions, and insatiable, toxic hunger",
        "Ketu": "apathetic withdrawal, nihilistic despair, and self-sabotaging isolation"
    }
    
    growth_planet = vd_map.get(ak, {}).get("growth", "Jupiter")
    stress_planet = vd_map.get(ak, {}).get("stress", "Saturn")
    
    # 2nd Person Coaching with explicit Tamil/English names and elaborated traits
    g_p_name = t_p_eng.get(growth_planet, growth_planet)
    s_p_name = t_p_eng.get(stress_planet, stress_planet)

    growth_coaching = f"Your ultimate path to growth requires you to move toward the highest expression of <b>{g_p_name}</b>. This means actively cultivating {growth_traits.get(growth_planet, 'its highest energy')}. True authority will follow when you stop relying on your baseline instincts and embrace this advanced operating state."
    stress_coaching = f"Under severe executive stress, you disintegrate into the shadow of <b>{s_p_name}</b>. You lose your natural decisive edge and begin operating from fear, adopting toxic traits like {stress_traits.get(stress_planet, 'reactive behavior')}. You must recognize these triggers immediately."

    return {
        "ak_planet": t_p_eng.get(ak, ak), "ak_type": enneagram_map.get(ak)[0], "ak_desire": enneagram_map.get(ak)[1],
        "amk_planet": t_p_eng.get(amk, amk), "amk_type": enneagram_map.get(amk)[0],
        "growth_planet": g_p_name, "growth_coaching": growth_coaching,
        "stress_planet": s_p_name, "stress_coaching": stress_coaching
    }

def get_coaching_rules(sav_scores, lagna_rasi, current_md, ennea_desire):
    lowest_house_idx = min(range(12), key=lambda i: sav_scores[(lagna_rasi - 1 + i) % 12])
    lowest_house = lowest_house_idx + 1
    
    house_tips = {
        1: "Protect your personal vitality; do not burn out trying to be everything to everyone.",
        2: "Systematize your finances. Avoid impulsive resource allocation when stressed.",
        3: "Communicate clearly and do not hesitate to take calculated executive risks.",
        4: "Fiercely protect your private time and home life from professional intrusion.",
        5: "Delegate repetitive tasks; your bottleneck is trying to do all the creative work yourself.",
        6: "You absorb workplace stress easily. Build strict boundaries with toxic corporate environments.",
        7: "Do not compromise your vision just to keep the peace in strategic partnerships.",
        8: "Embrace sudden changes in the market instead of resisting necessary transformations.",
        9: "Stay open to new philosophies; avoid rigid dogmatism in your strategic approach.",
        10: "Patience is key. True authority takes time to build; do not rush the executive process.",
        11: "Audit your network. Cut out professional connections that drain your energy rather than providing ROI.",
        12: "Prioritize deep rest. You are prone to burnout from poor boundary setting."
    }
    
    md_focus = {
        "Suriyan": "stepping into visible leadership and building your personal brand",
        "Chandran": "cultivating emotional intelligence and nurturing team environments",
        "Sevvai": "aggressive execution, rapid scaling, and fearless problem-solving",
        "Budhan": "data analysis, strategic communication, and optimizing operational workflows",
        "Guru": "mentorship, ethical expansion, and high-level strategic planning",
        "Sukran": "relationship building, aesthetic refinement, and diplomatic alliances",
        "Sani": "extreme patience, building foundational infrastructure, and delayed gratification",
        "Rahu": "unconventional innovation, disrupting the status quo, and massive leaps of faith",
        "Ketu": "deep research, backend mastery, and detached observation"
    }

    # Find the English equivalent of the Dasha for the dictionary lookup
    current_md_eng = "Guru" # Fallback
    if current_md:
        for eng_k, tam_v in t_p.items():
            if current_md == tam_v or current_md == t_p_eng.get(eng_k, eng_k):
                current_md_eng = t_p_eng.get(eng_k, eng_k)
                break

    focus_text = md_focus.get(current_md_eng, "mastering your current operational phase before expanding")
    
    rule_1 = house_tips.get(lowest_house, "Maintain structural discipline.")
    rule_2 = f"You are currently operating in a <b>{current_md}</b> Mahadasha phase. Align your immediate strategic goals with the energy of this planet—specifically focusing on <i>{focus_text}</i>—rather than forcing outcomes that belong in a different season." if current_md else "Focus on mastering your current operational phase before expanding."
    rule_3 = f"Success for you is not just financial wealth; your ultimate metric for a life well-lived is {ennea_desire}."
    
    return [rule_1, rule_2, rule_3]

def get_d10_traits(d10_lord):
    traits = {
        "Sun": "unwavering confidence, centralizing authority, and inspiring your team through bold visibility",
        "Moon": "empathetic leadership, reading the room intuitively, and nurturing human capital",
        "Mars": "rapid problem-solving, cutting through red tape, and taking fearless initiative",
        "Mercury": "flawless articulation, data-driven strategy, and highly adaptable pivoting",
        "Jupiter": "ethical oversight, big-picture philosophy, and acting as a wise counselor to your peers",
        "Venus": "elite relationship management, creating harmonious alliances, and focusing on aesthetic perfection",
        "Saturn": "meticulous structuring, unshakeable patience, and enforcing rigorous discipline"
    }
    return traits.get(d10_lord, "focus and precision")


# --- UI HEADER ---
st.title(":material/account_circle: Deep Horoscope Engine")
st.markdown("Generate a complete, personalized Vedic astrological profile.")
st.divider()

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("### ⚙️ Engine Settings")
    LANG = st.radio("Language / மொழி", ["English", "Tamil"], horizontal=True)
    st.divider()
    
    st.markdown("### 👤 Birth Details")
    saved_profiles = load_profiles_from_db()
    profile_options = ["✨ Select Profile...", "✏️ Enter Manually"] + list(saved_profiles.keys())
    selected_profile = st.selectbox("Load Saved Profile", profile_options)
    
    if selected_profile in ["✨ Select Profile...", "✏️ Enter Manually"]:
        def_n, def_dob, def_tob, def_loc = "", datetime(2000, 1, 1).date(), time(12, 0), ""
    else:
        def_n = selected_profile
        def_dob = saved_profiles[selected_profile]["dob"]
        def_tob = saved_profiles[selected_profile]["tob"]
        def_loc = saved_profiles[selected_profile]["city"]

    k = selected_profile.replace(" ", "_")
    name_in = st.text_input("Name", value=def_n, key=f"h_name_{k}")
    dob_in = st.date_input("Date of Birth", value=def_dob, min_value=datetime(1950, 1, 1).date(), key=f"h_dob_{k}")
    tob_in = st.time_input("Time of Birth", value=def_tob, step=60, key=f"h_tob_{k}")
    city = st.text_input("City", value=def_loc, key=f"h_loc_{k}")
    f_year = st.number_input("Forecast Year", min_value=datetime.now().year, max_value=2050, value=2026)
    
    lat_val, lon_val, tz_val = 13.0827, 80.2707, "Asia/Kolkata" 
    if city:
        lat_val, lon_val, tz_val = get_location_coordinates(city)
    
    calc_btn = st.button("Generate Report", type="primary", use_container_width=True)
    if calc_btn:
        if not name_in or not city: st.error("Please enter a Name and City!")
        else: st.session_state.report_generated = True

# --- MAIN EXECUTION ---
if st.session_state.report_generated:
    with st.spinner("Calculating exact astronomical data..." if LANG=="English" else "ஜாதகம் கணிக்கப்படுகிறது..."):
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        birth_dt = datetime.combine(dob_in, tob_in)
        offset = get_utc_offset(tz_val, birth_dt)
        ut_hour = (tob_in.hour + (tob_in.minute/60.0)) - offset
        jd_ut = swe.julday(dob_in.year, dob_in.month, dob_in.day, ut_hour)
        
        bhava_cusps = get_bhava_chalit(jd_ut, lat_val, lon_val)
        ascmc = swe.houses_ex(jd_ut, lat_val, lon_val, b'P', swe.FLG_SIDEREAL)[1]
        lagna_rasi = int(ascmc[0]/30)+1
        d9_lagna = get_navamsa_chart(ascmc[0])
        d10_lagna = get_dasamsa_chart(ascmc[0])
        d10_lord = RASI_RULERS.get(d10_lagna, "Sun")
        
        moon_res = swe.calc_ut(jd_ut, swe.MOON, swe.FLG_SIDEREAL)[0]
        moon_rasi = int(moon_res[0]/30)+1
        current_age = datetime.now().year - dob_in.year

        planets = {"Sun": swe.SUN, "Moon": swe.MOON, "Mars": swe.MARS, "Mercury": swe.MERCURY, "Jupiter": swe.JUPITER, "Venus": swe.VENUS, "Saturn": swe.SATURN, "Rahu": swe.MEAN_NODE}
        p_pos, p_d9, p_d10, p_lon_absolute, bhava_placements = {}, {}, {}, {}, {}
        master_table = []
        
        for p, pid in planets.items():
            res = swe.calc_ut(jd_ut, pid, swe.FLG_SIDEREAL)[0]
            p_lon_absolute[p] = res[0]
            r1 = int(res[0]/30)+1
            p_pos[p] = r1
            p_d9[p] = get_navamsa_chart(res[0])
            p_d10[p] = get_dasamsa_chart(res[0])
            bhava_h = determine_house(res[0], bhava_cusps)
            bhava_placements[p] = bhava_h 
            h = (r1 - lagna_rasi + 1) if (r1 - lagna_rasi + 1) > 0 else (r1 - lagna_rasi + 1) + 12
            dig = get_dignity(p, r1)
            status = "VARGOTTAMA" if r1 == p_d9[p] else "ROYAL" if dig == "Exalted" else "WEAK" if dig == "Neecha" else "Avg"
            master_table.append({"Planet": t_p.get(p, p) if LANG == "Tamil" else t_p_eng.get(p, p), "Rasi": ZODIAC_TA.get(r1, "") if LANG=="Tamil" else ZODIAC[r1], "House": h, "Bhava": bhava_h, "Dignity": dig, "Status": status})

        # KETU INTEGRATION
        ketu_lon = (p_lon_absolute["Rahu"] + 180) % 360
        p_lon_absolute["Ketu"] = ketu_lon
        p_pos["Ketu"] = int(ketu_lon/30) + 1
        p_d9["Ketu"] = get_navamsa_chart(ketu_lon)
        bhava_placements["Ketu"] = determine_house(ketu_lon, bhava_cusps)
        k_h = (p_pos["Ketu"] - lagna_rasi + 1) if (p_pos["Ketu"] - lagna_rasi + 1) > 0 else (p_pos["Ketu"] - lagna_rasi + 1) + 12
        master_table.append({"Planet": t_p.get("Ketu", "Ketu") if LANG=="Tamil" else "Ketu", "Rasi": ZODIAC[p_pos["Ketu"]], "House": k_h, "Bhava": bhava_placements["Ketu"], "Dignity": get_dignity("Ketu", p_pos["Ketu"]), "Status": "Avg"})

        p_pos["Lagna"] = lagna_rasi
        p_d9["Lagna"] = d9_lagna
        sav_scores = calculate_sav_score(p_pos, lagna_rasi)
        nak, lord = get_nakshatra_details(moon_res[0])
        
        # DATA COMPILATION
        karmic_txt = analyze_karmic_axis(p_pos, lagna_rasi, lang=LANG)
        yogas = scan_yogas(p_pos, lagna_rasi, lang=LANG)
        career_txt = analyze_career_professional(p_pos, d10_lagna, lagna_rasi, sav_scores, bhava_placements, lang=LANG)
        
        # Inject D10 Clarity dynamically
        d10_lord_name = t_p_eng.get(d10_lord, d10_lord)
        career_txt.append(f"**Leaning into {d10_lord_name}'s core traits means:** Executing with {get_d10_traits(d10_lord)}. Avoid copying others; this specific energetic style is your ultimate professional weapon.")
        
        edu_txt = analyze_education(p_pos, lagna_rasi, lang=LANG)
        health_txt = analyze_health(p_pos, lagna_rasi, lang=LANG)
        love_txt = analyze_love_marriage(lagna_rasi, d9_lagna, p_d9, p_pos, lang=LANG)
        fc = generate_annual_forecast(moon_rasi, sav_scores, f_year, current_age, lang=LANG)
        micro_transits = get_micro_transits(f_year, p_lon_absolute, lang=LANG)
        mahadasha_data = generate_mahadasha_table(moon_res[0], datetime.combine(dob_in, tob_in), lang=LANG)
        phases, pd_info = generate_current_next_bhukti(moon_res[0], datetime.combine(dob_in, tob_in), bhava_placements, lang=LANG)
        
        t_data = get_transit_data_advanced(f_year)
        transit_texts = [f"**{p}:** {d['Rasi']} ➔ {d['NextSignIdx']} ({d['NextDate']})" for p, d in t_data.items()]

        report_id_data = (TAMIL_IDENTITY_DB if LANG == "Tamil" else identity_db).get(ZODIAC[lagna_rasi], {})
        guide = TAMIL_LIFESTYLE.get(RASI_RULERS.get(moon_rasi, "Moon"), {}) if LANG == "Tamil" else lifestyle_guidance.get(RASI_RULERS.get(moon_rasi, "Moon"), {})

        # 360 ENGINES
        mbti_data = generate_360_mbti_persona(p_pos, lagna_rasi, sav_scores)
        ennea_data = get_enneagram_data(p_lon_absolute)
        current_md = pd_info['MD'] if pd_info else None
        coaching_rules = get_coaching_rules(sav_scores, lagna_rasi, current_md, ennea_data['ak_desire'])

        # --- TOP INFO SECTION ---
        c_left, c_right = st.columns([3, 1])
        l_name = ZODIAC_TA.get(lagna_rasi, "") if LANG == "Tamil" else ZODIAC[lagna_rasi]
        m_name = ZODIAC_TA.get(moon_rasi, "") if LANG == "Tamil" else ZODIAC[moon_rasi]
        
        with c_left:
            st.subheader(f"Analysis for {name_in}" if LANG=="English" else f"ஜோதிட அறிக்கை: {name_in}")
            st.markdown(f"> **{'லக்னம்' if LANG=='Tamil' else 'Lagna'}:** {l_name} | **{'ராசி' if LANG=='Tamil' else 'Moon'}:** {m_name} | **{'நட்சத்திரம்' if LANG=='Tamil' else 'Star'}:** {nak}")
        
        with c_right:
            pdf_bytes, pdf_error = generate_pdf_report(
                name_in=name_in, p_pos=p_pos, p_d9=p_d9, lagna_rasi=lagna_rasi, sav_scores=sav_scores, 
                career_txt=career_txt, edu_txt=edu_txt, health_txt=health_txt, love_txt=love_txt, 
                karmic_txt=karmic_txt, id_data=report_id_data, lagna_str=l_name, moon_str=m_name, 
                star_str=nak, yogas=yogas, fc=fc, micro_transits=micro_transits, 
                mahadasha_data=mahadasha_data, master_table=master_table, phases=phases, pd_info=pd_info, guide=guide, 
                transit_texts=transit_texts, lang=LANG
            )
            if pdf_bytes:
                st.download_button(label="📄 Download PDF Report" if LANG=="English" else "📄 ஜாதகத்தை பதிவிறக்க", data=pdf_bytes, file_name=f"{name_in}_Astro_Report.pdf", mime="application/pdf", type="primary")

        # --- UI TABS ---
        tb_lbls = ["360° Persona", "Profile & Placements", "Destiny Radar", "Executive Playbook", "Love & Health", "Yogas & Forecast", "Roadmap", "💬 Oracle"] if LANG == "English" else ["360° ஆளுமை", "சுயவிவரம்", "அஷ்டகவர்க்கம்", "நிர்வாக வியூகம்", "திருமணம்", "யோகங்கள்", "தசா புக்தி", "💬 ஜோதிடர்"]
        t1, t2, t3, t4, t5, t6, t7, t8 = st.tabs(tb_lbls)

        # --- TAB 1: THE MONOCHROME MBTI PERSONA ---
        with t1:
            e_txt = "You draw energy from the external environment and social interaction." if mbti_data['extro_pct'] >= 50 else "You draw energy from your inner world of ideas and quiet reflection."
            s_txt = "You process information through tangible facts, details, and present reality." if (100 - mbti_data['int_pct']) > 50 else "You process information through patterns, future possibilities, and abstract concepts."
            t_txt = "You make decisions based on objective logic, structure, and impersonal analysis." if mbti_data['think_pct'] >= 50 else "You make decisions based on personal values, empathy, and social harmony."
            j_txt = "You approach life with structure, planning, and a desire for closure." if mbti_data['judging_pct'] >= 50 else "You approach life with flexibility, adaptability, and keeping your options open."
            
            def draw_mbti_bar_html(title, energy_txt, left_lbl, right_lbl, pct_left):
                pct_right = 100 - pct_left
                active_left = "#2c3e50" if pct_left >= 50 else "#dcdcdc"
                active_right = "#2c3e50" if pct_right > 50 else "#dcdcdc"
                return f"""
<div style="margin-bottom: 25px; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;">
<div style="text-align: center; margin-bottom: 8px;">
<div style="font-size: 16px; font-weight: bold; color: #111;">{title}</div>
<div style="font-size: 13px; color: #555; font-style: italic; margin-top: 4px;">{energy_txt}</div>
</div>
<div style="display: flex; justify-content: space-between; font-size: 12px; font-weight: bold; color: #555; margin-bottom: 6px;">
<span style="color: {active_left};">{pct_left}% {left_lbl}</span>
<span style="color: {active_right};">{right_lbl} {pct_right}%</span>
</div>
<div style="width: 100%; height: 10px; display: flex; overflow: hidden; gap: 4px;">
<div style="width: {pct_left}%; background-color: {active_left}; border-radius: 5px 0 0 5px;"></div>
<div style="width: {pct_right}%; background-color: {active_right}; border-radius: 0 5px 5px 0;"></div>
</div>
</div>
"""
            
            mbti_html = f"""
<div style="padding: 20px 0; color: #333; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;">
<h2 style="text-align: center; color: #111; font-size: 28px; margin-bottom: 4px; font-weight: 800;">{mbti_data['title']}</h2>
<div style="text-align: center; color: #7f8c8d; font-size: 14px; font-weight: bold; letter-spacing: 2px; margin-bottom: 8px;">{mbti_data['code']}</div>
<p style="text-align: center; color: #666; font-size: 15px; margin-top: 0; font-style: italic;">Your core psychological operating system.</p>
<hr style="border: 0; border-top: 1px solid #EBE6DC; margin: 30px 0;">
<div style="display: flex; gap: 40px; margin-bottom: 30px;">
<div style="flex: 1;">
<h3 style="color: #111; margin-top: 0; border-bottom: 2px solid #2c3e50; padding-bottom: 5px; display: inline-block; font-size: 18px;">The Core Identity</h3>
<p style="line-height: 1.6; font-size: 15px; color: #444;">{mbti_data['desc']}</p>
</div>
<div style="flex: 1;">
<h3 style="color: #111; margin-top: 0; border-bottom: 2px solid #2c3e50; padding-bottom: 5px; display: inline-block; font-size: 18px;">Professional Focus</h3>
<p style="line-height: 1.6; font-size: 15px; color: #444;">{mbti_data['prof_text']}</p>
</div>
</div>
<hr style="border: 0; border-top: 1px solid #EBE6DC; margin: 30px 0;">
<h3 style="text-align: center; color: #111; margin-bottom: 30px; font-size: 20px;">Cognitive Sliders</h3>
<div style="max-width: 650px; margin: 0 auto;">
{draw_mbti_bar_html("Energy Orientation", e_txt, "EXTRAVERTED", "INTROVERTED", mbti_data['extro_pct'])}
{draw_mbti_bar_html("Information Processing", s_txt, "SENSING", "INTUITIVE", 100 - mbti_data['int_pct'])}
{draw_mbti_bar_html("Decision Making", t_txt, "THINKING", "FEELING", mbti_data['think_pct'])}
{draw_mbti_bar_html("World Structure", j_txt, "JUDGING", "PERCEIVING", mbti_data['judging_pct'])}
</div>
</div>
"""
            st.markdown(mbti_html, unsafe_allow_html=True)

        with t2:
            st.markdown(f"<h3 style='text-align: center; margin-top:20px;'>{'Birth Chart (Rasi)' if LANG=='English' else 'ராசி சக்கரம்'}</h3>", unsafe_allow_html=True)
            st.markdown(get_south_indian_chart_html(p_pos, lagna_rasi, "ராசி சக்கரம்" if LANG=="Tamil" else "Rasi Chart", LANG), unsafe_allow_html=True)
            
            headers = ["கிரகம்", "ராசி", "பாவம்", "பலம்", "நிலை"] if LANG == "Tamil" else ["Planet", "Rasi", "House", "Dignity", "Status"]
            table_md = f"<table style='width: 80%; margin: 30px auto; border-collapse: collapse; font-family: sans-serif; font-size: 15px; text-align: center;'><tr style='background-color: #f8f9fa; border-bottom: 2px solid #ccc;'><th style='padding: 12px 8px;'>{headers[0]}</th><th style='padding: 12px 8px;'>{headers[1]}</th><th style='padding: 12px 8px;'>{headers[2]}</th><th style='padding: 12px 8px;'>{headers[3]}</th><th style='padding: 12px 8px;'>{headers[4]}</th></tr>"
            for row in master_table:
                table_md += f"<tr style='border-bottom: 1px solid #eee;'><td style='padding: 12px 8px;'><b>{row['Planet']}</b></td><td style='padding: 12px 8px;'>{row['Rasi']}</td><td style='padding: 12px 8px;'>{row['House']}</td><td style='padding: 12px 8px;'>{row['Dignity']}</td><td style='padding: 12px 8px;'>{row['Status']}</td></tr>"
            table_md += "</table>"
            st.markdown(table_md, unsafe_allow_html=True)

        with t3:
            p_lbl = "பாவம்" if LANG == "Tamil" else "H"
            cats_labels = [f"{p_lbl} {i+1}" for i in range(12)]
            vals = [sav_scores[(lagna_rasi-1+i)%12] for i in range(12)]
            text_colors = ['#27ae60' if v >= 30 else '#e74c3c' if v < 25 else '#333333' for v in vals]
            fig_bar = go.Figure(data=[go.Bar(x=vals, y=cats_labels, orientation='h', marker_color='#bdc3c7', text=[f"<b>{v}</b>" for v in vals], textposition='outside', textfont=dict(color=text_colors, size=14))])
            fig_bar.add_vline(x=28, line_width=2, line_dash="dash", line_color="#7f8c8d", annotation_text="Average (28)" if LANG=="English" else "சராசரி (28)", annotation_position="top right")
            fig_bar.update_layout(yaxis=dict(autorange="reversed"), margin=dict(l=20, r=20, t=40, b=20), height=400)
            st.plotly_chart(fig_bar, use_container_width=True)
            
            c1, c2 = st.columns(2)
            sorted_houses = sorted([(sav_scores[(lagna_rasi-1+i)%12], i+1) for i in range(12)], key=lambda x: x[0], reverse=True)
            with c1:
                st.markdown(f"<h4 style='color: #27ae60; margin-bottom: 10px;'>{'அதிக பலம் பெற்ற பாவங்கள்' if LANG=='Tamil' else 'Top Power Zones'}</h4>", unsafe_allow_html=True)
                for s, h in sorted_houses[:3]: st.markdown(get_house_strength_analysis(h, s, LANG))
            with c2:
                st.markdown(f"<h4 style='color: #e74c3c; margin-bottom: 10px;'>{'கவனம் தேவைப்படும் பாவங்கள்' if LANG=='Tamil' else 'Top Challenge Zones'}</h4>", unsafe_allow_html=True)
                for s, h in sorted_houses[-3:]: st.markdown(get_house_strength_analysis(h, s, LANG))

        # --- TAB 4: THE NEW EXECUTIVE PLAYBOOK ---
        with t4:
            rahu_h = (p_pos["Rahu"] - lagna_rasi + 1) if (p_pos["Rahu"] - lagna_rasi + 1) > 0 else (p_pos["Rahu"] - lagna_rasi + 1) + 12
            ketu_h = (p_pos["Ketu"] - lagna_rasi + 1) if (p_pos["Ketu"] - lagna_rasi + 1) > 0 else (p_pos["Ketu"] - lagna_rasi + 1) + 12

            def format_md(text_list):
                formatted = []
                for line in text_list:
                    line = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', line)
                    # Convert markdown headers into styled HTML so they display cleanly inside the container
                    if line.startswith('### '):
                        line = f"<h5 style='color: #2c3e50; margin-top: 15px; margin-bottom: 5px; font-size: 15px;'>{line.replace('### ', '')}</h5>"
                    elif line.startswith('## '):
                        line = f"<h4 style='color: #2c3e50; margin-top: 15px; margin-bottom: 5px; font-size: 16px;'>{line.replace('## ', '')}</h4>"
                    elif line.startswith('> '):
                        line = f"<div style='border-left: 3px solid #ccc; padding-left: 10px; color: #666; font-style: italic; margin-bottom: 5px;'>{line.replace('> ', '')}</div>"
                    formatted.append(line)
                return "<br>".join(formatted)
            
            # CSS based Concentric Visual, 100% Flush Left to bypass Markdown code block detection
            playbook_html = f"""
<div style="padding: 20px 0; color: #333; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;">

<h2 style="color: #2c3e50; font-size: 24px; border-bottom: 2px solid #eee; padding-bottom: 8px;">Phase 1: The Operating System</h2>

<div style="display: flex; gap: 30px; margin-bottom: 30px; align-items: center;">
    
<div style="flex: 0 0 250px; display: flex; justify-content: center;">
<div style="width: 220px; height: 220px; border-radius: 50%; border: 2px dashed #bdc3c7; display: flex; align-items: center; justify-content: center; position: relative;">
<div style="position: absolute; top: -10px; background: white; padding: 0 5px; font-size: 11px; font-weight: bold; color: #7f8c8d;">Outer Environment</div>
<div style="width: 150px; height: 150px; border-radius: 50%; border: 2px solid #3498db; display: flex; align-items: center; justify-content: center; position: relative; background: #f0f8ff;">
<div style="position: absolute; top: -10px; background: #f0f8ff; padding: 0 5px; font-size: 11px; font-weight: bold; color: #2980b9;">The Wing</div>
<div style="width: 80px; height: 80px; border-radius: 50%; background: #2c3e50; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; text-align: center; font-size: 13px; line-height: 1.2;">
Core<br>{ennea_data['ak_planet']}
</div>
</div>
</div>
</div>
    
<div style="flex: 1;">
<div style="margin-bottom: 15px;">
<div style="font-size: 16px; font-weight: bold; color: #2c3e50;">Core Driver: {ennea_data['ak_planet']} ({ennea_data['ak_type']})</div>
<div style="font-size: 14px; color: #555;"><b>Atmakaraka:</b> The planet with the highest degree in your chart. You act to satisfy this planet's deep desire: <i>{ennea_data['ak_desire']}</i>.</div>
</div>
<div style="margin-bottom: 15px;">
<div style="font-size: 16px; font-weight: bold; color: #2980b9;">The Execution Wing: {ennea_data['amk_planet']}</div>
<div style="font-size: 14px; color: #555;"><b>Amatyakaraka:</b> The second-highest degree. This is your "Prime Minister" that dictates the unique style and strategy you use to achieve your core desire.</div>
</div>
</div>
</div>

<div style="display: flex; gap: 20px; margin-bottom: 30px;">
<div style="flex: 1; background-color: #f9fbf9; border-left: 4px solid #2ecc71; padding: 15px;">
<div style="font-size: 15px; font-weight: bold; color: #27ae60; margin-bottom: 5px;">Growth Path (Ucha): {ennea_data['growth_planet']}</div>
<div style="font-size: 14px; color: #444;">{ennea_data['growth_coaching']}</div>
</div>
<div style="flex: 1; background-color: #fdfaf9; border-left: 4px solid #e74c3c; padding: 15px;">
<div style="font-size: 15px; font-weight: bold; color: #c0392b; margin-bottom: 5px;">Stress Path (Neecha): {ennea_data['stress_planet']}</div>
<div style="font-size: 14px; color: #444;">{ennea_data['stress_coaching']}</div>
</div>
</div>

<h2 style="color: #2c3e50; font-size: 24px; border-bottom: 2px solid #eee; padding-bottom: 8px;">Phase 2: The Zone of Genius</h2>
<div style="margin-bottom: 25px; font-size: 14.5px; line-height: 1.6; color: #444;">
<h4 style="color: #111; margin-bottom: 5px;">Academic & Strategic Intellect</h4>
<p>{format_md(edu_txt)}</p>
<h4 style="color: #111; margin-bottom: 5px; margin-top: 15px;">Career & Authority Execution</h4>
<p>{format_md(career_txt)}</p>
</div>

<h2 style="color: #2c3e50; font-size: 24px; border-bottom: 2px solid #eee; padding-bottom: 8px;">Phase 3: The Karmic Directive</h2>
<div style="display: flex; gap: 20px; margin-bottom: 25px;">
<div style="flex: 1; background-color: #fafafa; border: 1px solid #eee; padding: 15px; border-radius: 6px;">
<h4 style="color: #34495e; margin-top: 0; margin-bottom: 8px;">Zone of Ambition (Rahu in H{rahu_h})</h4>
<p style="font-size: 13.5px; color: #555; margin: 0;">This is where you must actively disrupt your comfort zone. Growth here feels unnatural but yields massive executive returns. Lean heavily into this sector to scale your success.</p>
</div>
<div style="flex: 1; background-color: #fafafa; border: 1px solid #eee; padding: 15px; border-radius: 6px;">
<h4 style="color: #7f8c8d; margin-top: 0; margin-bottom: 8px;">Zone of Detachment (Ketu in H{ketu_h})</h4>
<p style="font-size: 13.5px; color: #555; margin: 0;">This is your area of innate mastery. You are already naturally gifted here, but obsessing over it will stall your career. Delegate these tasks and use them only as a foundation.</p>
</div>
</div>

<h2 style="color: #2c3e50; font-size: 24px; border-bottom: 2px solid #eee; padding-bottom: 8px;">Phase 4: The 3 Rules for Success</h2>
<div style="background-color: #e8f6f3; border: 1px solid #d1f2eb; padding: 20px; border-radius: 8px;">
<ol style="margin: 0; padding-left: 20px; font-size: 15px; color: #111; line-height: 1.6;">
<li style="margin-bottom: 12px;"><b>Protect Your Energy:</b> {coaching_rules[0]}</li>
<li style="margin-bottom: 12px;"><b>Current Focus:</b> {coaching_rules[1]}</li>
<li><b>The Ultimate Metric:</b> {coaching_rules[2]}</li>
</ol>
</div>
</div>
"""
            st.markdown(playbook_html, unsafe_allow_html=True)

        with t5:
            st.markdown(get_south_indian_chart_html(p_d9, d9_lagna, "நவாம்சம்" if LANG=="Tamil" else "Navamsa", LANG), unsafe_allow_html=True)
            st.divider()
            for line in love_txt: st.markdown(line)
            st.divider()
            for line in health_txt: st.markdown(line)

        with t6:
            for y in yogas:
                st.markdown(f"#### {y['Name']}\n> **Type:** {y['Type']}\n\n{y['Description']}")
            st.divider()
            for cat, data in fc.items():
                st.markdown(f"#### {cat}\n{data[0]}\n> **Remedy:** {data[1]}")
            st.divider()
            for txt in transit_texts: st.markdown(txt)

        with t7:
            if pd_info:
                st.markdown(f"#### {'IMMEDIATE FOCUS' if LANG=='English' else 'நடப்பு தசா புக்தி'}")
                st.markdown(f"**{pd_info['Start']} to {pd_info['End']}**: {pd_info['PD']} ({pd_info['MD']} / {pd_info['AD']})")
            
            planet_colors = {"Suriyan": "#d35400", "Chandran": "#95a5a6", "Sevvai": "#c0392b", "Budhan": "#27ae60", "Guru": "#f39c12", "Sukran": "#8e44ad", "Sani": "#2c3e50", "Rahu": "#34495e", "Ketu": "#7f8c8d"}
            dasha_names, start_years, durations = [], [], []
            for row in mahadasha_data:
                dasha_names.append(row['Mahadasha'])
                s_year, e_year = map(int, row['Years'].split(' - '))
                start_years.append(s_year)
                durations.append(e_year - s_year)
                
            fig_timeline = go.Figure()
            fig_timeline.add_trace(go.Bar(
                y=['Life Path']*len(dasha_names), x=durations, base=start_years, name="Mahadashas", orientation='h',
                text=dasha_names, textposition='inside', textangle=0, insidetextfont=dict(color='white', size=14),
                marker=dict(color=[planet_colors.get(d, '#333') for d in dasha_names])
            ))
            fig_timeline.update_layout(barmode='stack', height=150, margin=dict(l=0, r=0, t=10, b=20), xaxis=dict(range=[start_years[0], start_years[0]+120], tickformat="d"), yaxis=dict(showticklabels=False), showlegend=False)
            st.plotly_chart(fig_timeline, use_container_width=True)

            md_table_html = f"<table style='width: 100%; border-collapse: collapse; font-family: sans-serif; font-size: 14px; margin-top: 20px;'><tr style='border-bottom: 2px solid #ddd; background-color: #fdfdfd;'><th style='padding: 10px 8px; text-align: left; width: 10%;'>Age</th><th style='padding: 10px 8px; text-align: left; width: 10%;'>Years</th><th style='padding: 10px 8px; text-align: left; width: 15%;'>Mahadasha</th><th style='padding: 10px 8px; text-align: left; width: 65%;'>Context & Prediction</th></tr>"
            for row in mahadasha_data:
                s_year, e_year = row['Years'].split(' - ')
                md_table_html += f"<tr style='border-bottom: 1px solid #eee;'><td style='padding: 10px 8px; vertical-align: top;'>{row['Age (From-To)']}</td><td style='padding: 10px 8px; vertical-align: top;'>{s_year}<br>{e_year}</td><td style='padding: 10px 8px; vertical-align: top; color: {planet_colors.get(row['Mahadasha'], '#333')};'><b>{row['Mahadasha']}</b></td><td style='padding: 10px 8px; vertical-align: top;'>{row['Prediction']}</td></tr>"
            md_table_html += "</table>"
            st.markdown(md_table_html, unsafe_allow_html=True)

        with t8:
            st.subheader("💬 Ask the AI Astrologer" if LANG == "English" else "💬 AI ஜோதிடரிடம் கேளுங்கள்")
            chat_container = st.container()
            with chat_container:
                for msg in st.session_state.messages:
                    with st.chat_message(msg["role"]): st.markdown(msg["content"])

            if prompt_input := st.chat_input("Ask a question..."):
                st.session_state.messages.append({"role": "user", "content": prompt_input})
                with chat_container:
                    with st.chat_message("user"): st.markdown(prompt_input)
                    with st.chat_message("assistant"):
                        try:
                            genai.configure(api_key=API_KEY)
                            model = genai.GenerativeModel('gemini-1.5-flash')
                            response = model.generate_content(f"Data: Lagna {ZODIAC[lagna_rasi]}, Moon {ZODIAC[moon_rasi]}. User says: {prompt_input}")
                            st.markdown(response.text)
                            st.session_state.messages.append({"role": "assistant", "content": response.text})
                        except Exception as e: st.error(f"Failed: {e}")
                st.rerun()
