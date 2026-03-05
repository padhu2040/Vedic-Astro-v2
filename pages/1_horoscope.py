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
    generate_annual_forecast, get_transit_data_advanced, analyze_karmic_axis,
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

# --- UNIQUE HOUSE STRENGTH ANALYSIS ENGINE ---
def get_local_house_analysis(house, score, lang="English"):
    domains = {
        1: "Self, physical vitality, and personal brand",
        2: "Accumulated wealth, speech, and family assets",
        3: "Courage, short-term efforts, and networking",
        4: "Inner peace, real estate, and foundational security",
        5: "Creative intellect, speculation, and advisory roles",
        6: "Daily routines, overcoming competitors, and debt management",
        7: "Strategic partnerships, marriage, and public relations",
        8: "Crisis management, hidden resources, and transformation",
        9: "Long-term vision, higher learning, and natural luck",
        10: "Career execution, public authority, and industry reputation",
        11: "Massive scaling, professional networks, and major gains",
        12: "Deep rest, foreign investments, and letting go of control"
    }
    power_advice = {
        1: "Lean heavily into your personal charisma. You are the brand.",
        2: "Capitalize on your communication skills and aggressively scale your assets.",
        3: "Take calculated risks and expand your immediate network. Boldness wins here.",
        4: "Invest in real estate or foundational infrastructure. Your inner security is your fortress.",
        5: "Trust your creative instincts and intellectual models. Lead through guidance.",
        6: "Tackle operational bottlenecks head-on. You will easily outlast competitors.",
        7: "Form strategic alliances. Joint ventures will yield massive returns.",
        8: "Do not fear sudden market shifts. You have a unique talent for profiting during crises.",
        9: "Trust your intuition and long-term philosophy. The universe actively supports your vision.",
        10: "Assume absolute leadership. You are built to direct and execute at the highest level.",
        11: "Focus on scaling. Tap into large professional networks to multiply your influence.",
        12: "Use isolation and backend strategy as a weapon. Some of your best work happens off-stage."
    }
    challenge_advice = {
        1: "Guard against burnout. Do not let your ego tie your self-worth solely to your output.",
        2: "Enforce strict financial discipline. Avoid impulsive speech that damages key alliances.",
        3: "Do not waste energy on petty conflicts. Focus your drive on structured goals.",
        4: "Actively protect your private time. Do not let professional stress infect your home.",
        5: "Avoid over-analyzing. Delegate tasks instead of trying to control all creative output.",
        6: "Build strict boundaries to avoid absorbing workplace toxicity. Prioritize health routines.",
        7: "Do not compromise your core vision just to avoid conflict in partnerships.",
        8: "Avoid resisting necessary structural changes. Clinging to the past will stall your growth.",
        9: "Stay flexible. Rigid dogmatism or overly optimistic leaps of faith will backfire.",
        10: "Practice extreme patience. True authority here requires enduring delayed gratification.",
        11: "Audit your network. Cut out professional connections that drain energy without ROI.",
        12: "Prioritize sleep and mental health. Do not ignore your need to disconnect and recharge."
    }
    
    domain = domains.get(house, "")
    if score >= 30:
        advice = power_advice.get(house, "Maximize this energy.")
        return f"**Power zone: The {house}th house ({domain}) is exceptionally strong.**<br><span style='color:#666;'><i>Harnessing guide:</i> {advice}</span><br><br>"
    else:
        advice = challenge_advice.get(house, "Requires strict discipline.")
        return f"**Challenge zone: The {house}th house ({domain}) requires conscious effort.**<br><span style='color:#666;'><i>Mitigation guide:</i> {advice}</span><br><br>"

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
    return {"code": mbti_code, "extro_pct": extro_pct, "int_pct": int_pct, "think_pct": think_pct, "judging_pct": judging_pct}

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
        "Saturn": ("Type 1: The Reformer", "building structural perfection and absolute integrity"),
        "Moon": ("Type 2: The Helper", "creating deep emotional bonds and being fundamentally needed"),
        "Sun": ("Type 3: The Achiever", "achieving visible success, immense value, and admiration"),
        "Ketu": ("Type 4: The Individualist", "finding profound, unique personal significance"),
        "Mercury": ("Type 5: The Investigator", "mastering complex knowledge and absolute competence"),
        "Venus": ("Type 6: The Loyalist", "establishing unbreakable security and aligned partnerships"),
        "Rahu": ("Type 7: The Enthusiast", "experiencing limitless freedom and boundary expansion"),
        "Mars": ("Type 8: The Challenger", "maintaining total control and fiercely protecting autonomy"),
        "Jupiter": ("Type 9: The Peacemaker", "sustaining internal peace, high wisdom, and harmony")
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
    
    amk_traits = {
        "Sun": "charismatic authority, unwavering confidence, and commanding visibility",
        "Moon": "intuitive empathy, emotional intelligence, and building deep trust",
        "Mars": "bold initiative, fearless execution, and taking decisive action",
        "Mercury": "flawless communication, data-driven analysis, and strategic networking",
        "Jupiter": "expansive vision, ethical guidance, and high-level philosophical thinking",
        "Venus": "diplomatic alliance-building, aesthetic perfection, and cultivating elite relationships",
        "Saturn": "ironclad discipline, meticulous structuring, and enduring patience",
        "Rahu": "unconventional innovation, disruptive thinking, and breaking established boundaries",
        "Ketu": "profound detachment, deep backend research, and highly specialized mastery"
    }
    
    growth_planet = vd_map.get(ak, {}).get("growth", "Jupiter")
    stress_planet = vd_map.get(ak, {}).get("stress", "Saturn")
    
    g_p_name = t_p_eng.get(growth_planet, growth_planet)
    s_p_name = t_p_eng.get(stress_planet, stress_planet)
    ak_name = t_p_eng.get(ak, ak)
    amk_name = t_p_eng.get(amk, amk)

    growth_coaching = f"Your ultimate path to growth requires you to move toward the highest expression of <b>{g_p_name}</b>. This means actively cultivating {growth_traits.get(growth_planet, 'its highest energy')}. True authority will follow when you stop relying on your baseline instincts and embrace this advanced operating state."
    stress_coaching = f"Under severe executive stress, you disintegrate into the shadow of <b>{s_p_name}</b>. You lose your natural decisive edge and begin operating from fear, adopting toxic traits like {stress_traits.get(stress_planet, 'reactive behavior')}. You must recognize these triggers immediately."
    
    ak_coaching = f"Your fundamental core drive is powered by <b>{ak_name}</b>. At your deepest subconscious level, you are fundamentally driven by the need for {enneagram_map.get(ak)[1]}. Every major executive decision you make is ultimately an attempt to satisfy this core urge. When you align your career directly with this specific energy, you become unstoppable."
    amk_coaching = f"While your Core dictates <i>what</i> you want, your Execution Wing, <b>{amk_name}</b>, dictates <i>how</i> you get it. You naturally rely on {amk_traits.get(amk, 'strategic focus')} to navigate complex professional landscapes. This is your tactical superpower—lean heavily on it to execute your grand vision."

    return {
        "ak_eng": ak, "amk_eng": amk,
        "ak_planet": ak_name, "ak_type": enneagram_map.get(ak)[0], "ak_desire": enneagram_map.get(ak)[1], "ak_coaching": ak_coaching,
        "amk_planet": amk_name, "amk_type": enneagram_map.get(amk)[0], "amk_coaching": amk_coaching,
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

    current_md_eng = "Guru"
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
        
        # PRECOMPUTE RAHU/KETU HOUSES
        rahu_h = (p_pos["Rahu"] - lagna_rasi + 1) if (p_pos["Rahu"] - lagna_rasi + 1) > 0 else (p_pos["Rahu"] - lagna_rasi + 1) + 12
        ketu_h = (p_pos["Ketu"] - lagna_rasi + 1) if (p_pos["Ketu"] - lagna_rasi + 1) > 0 else (p_pos["Ketu"] - lagna_rasi + 1) + 12

        # DATA COMPILATION
        karmic_txt = analyze_karmic_axis(p_pos, lagna_rasi, lang=LANG)
        yogas = scan_yogas(p_pos, lagna_rasi, lang=LANG)
        career_txt = analyze_career_professional(p_pos, d10_lagna, lagna_rasi, sav_scores, bhava_placements, lang=LANG)
        
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
                mahadasha_data=mahadasha_data, master_table=master_table, phases=phases, 
                pd_info=pd_info, guide=guide, transit_texts=transit_texts, 
                mbti_data=mbti_data, ennea_data=ennea_data, coaching_rules=coaching_rules, 
                rahu_h=rahu_h, ketu_h=ketu_h, lang=LANG
            )
            if pdf_bytes:
                st.download_button(label="📄 Download PDF Report" if LANG=="English" else "📄 ஜாதகத்தை பதிவிறக்க", data=pdf_bytes, file_name=f"{name_in}_Astro_Report.pdf", mime="application/pdf", type="primary")

        # --- UI TABS ---
        tb_lbls = ["Profile & Placements", "Destiny Radar", "Executive Playbook", "Love & Health", "Yogas & Forecast", "Roadmap", "💬 Oracle"]
        t1, t2, t3, t4, t5, t6, t7 = st.tabs(tb_lbls)

        # --- TAB 1: PROFILE & PLACEMENTS ---
        with t1:
            st.markdown("### Astrological blueprint")
            st.markdown("This section maps the exact astronomical coordinates of the planets at your moment of birth. In Vedic Astrology, your Ascendant (Lagna) forms your physical self and operating framework, while your Moon Sign (Rasi) dictates your internal emotional processor.")
            
            st.markdown(f"<h3 style='text-align: center; margin-top:20px;'>{'Birth Chart (Rasi)' if LANG=='English' else 'ராசி சக்கரம்'}</h3>", unsafe_allow_html=True)
            st.markdown(get_south_indian_chart_html(p_pos, lagna_rasi, "ராசி சக்கரம்" if LANG=="Tamil" else "Rasi Chart", LANG), unsafe_allow_html=True)
            
            st.markdown("### Core planetary alignments")
            st.markdown("This table displays the exact dignity and status of your planetary placements. 'Exalted' planets act as your superpowers, while 'Neecha' (debilitated) planets show areas requiring conscious development.")
            
            headers = ["கிரகம்", "ராசி", "பாவம்", "பலம்", "நிலை"] if LANG == "Tamil" else ["Planet", "Rasi", "House", "Dignity", "Status"]
            table_md = f"<table style='width: 100%; margin: 20px auto; border-collapse: collapse; font-family: sans-serif; font-size: 15px; text-align: center;'><tr style='background-color: #f8f9fa; border-bottom: 2px solid #ccc;'><th style='padding: 12px 8px;'>{headers[0]}</th><th style='padding: 12px 8px;'>{headers[1]}</th><th style='padding: 12px 8px;'>{headers[2]}</th><th style='padding: 12px 8px;'>{headers[3]}</th><th style='padding: 12px 8px;'>{headers[4]}</th></tr>"
            for row in master_table:
                table_md += f"<tr style='border-bottom: 1px solid #eee;'><td style='padding: 12px 8px;'><b>{row['Planet']}</b></td><td style='padding: 12px 8px;'>{row['Rasi']}</td><td style='padding: 12px 8px;'>{row['House']}</td><td style='padding: 12px 8px;'>{row['Dignity']}</td><td style='padding: 12px 8px;'>{row['Status']}</td></tr>"
            table_md += "</table>"
            st.markdown(table_md, unsafe_allow_html=True)

        # --- TAB 2: DESTINY RADAR ---
        with t2:
            house_meanings_en = ["Self & Vitality", "Wealth & Speech", "Courage & Network", "Home & Peace", "Intellect & Creativity", "Work & Obstacles", "Partnerships", "Transformation", "Wisdom & Luck", "Career & Authority", "Gains & Scaling", "Detachment & Loss"]
            cats_labels = [f"H{i+1}: {house_meanings_en[i]}" for i in range(12)]
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
                for s, h in sorted_houses[:3]: st.markdown(get_local_house_analysis(h, s, LANG), unsafe_allow_html=True)
            with c2:
                st.markdown(f"<h4 style='color: #e74c3c; margin-bottom: 10px;'>{'கவனம் தேவைப்படும் பாவங்கள்' if LANG=='Tamil' else 'Top Challenge Zones'}</h4>", unsafe_allow_html=True)
                for s, h in sorted_houses[-3:]: st.markdown(get_local_house_analysis(h, s, LANG), unsafe_allow_html=True)

        # --- TAB 3: THE EXECUTIVE PLAYBOOK ---
        with t3:
            house_domains = {
                1: "personal identity, physical vitality, and self-projection",
                2: "financial accumulation, verbal communication, and family assets",
                3: "self-directed effort, networking, and calculated risk-taking",
                4: "emotional security, domestic life, and foundational assets",
                5: "creative intelligence, speculative ventures, and guiding subordinates",
                6: "overcoming competition, operational routines, and problem-solving",
                7: "strategic partnerships, negotiations, and public relations",
                8: "managing crises, other people's resources, and deep research",
                9: "high-level philosophy, long-term vision, and global expansion",
                10: "absolute authority, career execution, and public reputation",
                11: "massive scaling, professional networks, and achieving major milestones",
                12: "deep rest, foreign environments, and behind-the-scenes strategy"
            }
            rahu_domain = house_domains.get(rahu_h, "this specific area of life")
            ketu_domain = house_domains.get(ketu_h, "this specific area of life")

            def format_md(text_list):
                formatted = []
                for line in text_list:
                    line = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', line)
                    if line.startswith('#### '):
                        line = f"<div style='color: #2c3e50; margin: 20px 0 8px 0; font-size: 16px; font-weight: 700; border-bottom: 1px solid #eaeaea; padding-bottom: 4px;'>{line.replace('#### ', '')}</div>"
                    elif line.startswith('### '):
                        line = f"<div style='color: #2c3e50; margin: 20px 0 8px 0; font-size: 16px; font-weight: 700; border-bottom: 1px solid #eaeaea; padding-bottom: 4px;'>{line.replace('### ', '')}</div>"
                    elif line.startswith('## '):
                        line = f"<div style='color: #2c3e50; margin: 20px 0 8px 0; font-size: 18px; font-weight: 800; border-bottom: 1px solid #eaeaea; padding-bottom: 4px;'>{line.replace('## ', '')}</div>"
                    elif line.startswith('> '):
                        line = f"<div style='border-left: 3px solid #ccc; padding-left: 10px; color: #666; font-style: italic; margin-bottom: 12px;'>{line.replace('> ', '')}</div>"
                    else:
                        line = f"<div style='margin-bottom: 12px; color: #444; line-height: 1.6;'>{line}</div>"
                    formatted.append(line)
                return "".join(formatted)
            
            en_planet_colors = {
                "Sun": "#d35400", "Moon": "#95a5a6", "Mars": "#c0392b", 
                "Mercury": "#27ae60", "Jupiter": "#f39c12", "Venus": "#8e44ad", 
                "Saturn": "#2c3e50", "Rahu": "#34495e", "Ketu": "#7f8c8d"
            }
            core_color = en_planet_colors.get(ennea_data['ak_eng'], "#2c3e50")
            wing_color = en_planet_colors.get(ennea_data['amk_eng'], "#3498db")
            
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
            
            playbook_html = f"""
<div style="padding: 10px 0; color: #333; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;">
<h2 style="color: #2c3e50; font-size: 24px; border-bottom: 2px solid #eee; padding-bottom: 8px;">Phase 1: The core drive</h2>
<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 30px;">
<div style="background: #fff; border: 1px solid #eaeaea; border-top: 4px solid {core_color}; padding: 20px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.02);">
<div style="font-size: 12px; color: #888; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px;"><b>Atmakaraka:</b> Core Driver</div>
<div style="font-size: 18px; font-weight: bold; color: {core_color}; margin-bottom: 10px;">{ennea_data['ak_planet']} ({ennea_data['ak_type']})</div>
<div style="font-size: 14px; color: #444; line-height: 1.5;">{ennea_data['ak_coaching']}</div>
</div>
<div style="background: #fff; border: 1px solid #eaeaea; border-top: 4px solid {wing_color}; padding: 20px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.02);">
<div style="font-size: 12px; color: #888; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px;"><b>Amatyakaraka:</b> Execution Wing</div>
<div style="font-size: 18px; font-weight: bold; color: {wing_color}; margin-bottom: 10px;">{ennea_data['amk_planet']}</div>
<div style="font-size: 14px; color: #444; line-height: 1.5;">{ennea_data['amk_coaching']}</div>
</div>
<div style="background: #f9fbf9; border: 1px solid #eaeaea; border-left: 4px solid #27ae60; padding: 20px; border-radius: 8px;">
<div style="font-size: 12px; color: #888; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px;"><b>Ucha:</b> Growth Path</div>
<div style="font-size: 16px; font-weight: bold; color: #27ae60; margin-bottom: 10px;">{ennea_data['growth_planet']}</div>
<div style="font-size: 14px; color: #444; line-height: 1.5;">{ennea_data['growth_coaching']}</div>
</div>
<div style="background: #fdfaf9; border: 1px solid #eaeaea; border-left: 4px solid #e74c3c; padding: 20px; border-radius: 8px;">
<div style="font-size: 12px; color: #888; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px;"><b>Neecha:</b> Stress Path</div>
<div style="font-size: 16px; font-weight: bold; color: #c0392b; margin-bottom: 10px;">{ennea_data['stress_planet']}</div>
<div style="font-size: 14px; color: #444; line-height: 1.5;">{ennea_data['stress_coaching']}</div>
</div>
</div>
<h2 style="color: #2c3e50; font-size: 24px; border-bottom: 2px solid #eee; padding-bottom: 8px;">Phase 2: The zone of genius</h2>
<div style="margin-bottom: 30px;">
{format_md(edu_txt)}
{format_md(career_txt)}
</div>
<h2 style="color: #2c3e50; font-size: 24px; border-bottom: 2px solid #eee; padding-bottom: 8px;">Phase 3: The karmic directive</h2>
<div style="display: flex; gap: 20px; margin-bottom: 30px;">
<div style="flex: 1; background-color: #fafafa; border: 1px solid #eee; padding: 20px; border-radius: 6px;">
<h4 style="color: #34495e; margin-top: 0; margin-bottom: 10px; font-size: 16px;">Zone of Ambition (Rahu in H{rahu_h})</h4>
<p style="font-size: 14px; color: #444; margin: 0; line-height: 1.5;">This is where you must actively disrupt your comfort zone. Specifically, this points to <b>{rahu_domain}</b>. Growth here feels unnatural but yields massive executive returns. Lean heavily into this sector to scale your success.</p>
</div>
<div style="flex: 1; background-color: #fafafa; border: 1px solid #eee; padding: 20px; border-radius: 6px;">
<h4 style="color: #7f8c8d; margin-top: 0; margin-bottom: 10px; font-size: 16px;">Zone of Detachment (Ketu in H{ketu_h})</h4>
<p style="font-size: 14px; color: #444; margin: 0; line-height: 1.5;">This is your area of innate mastery. Specifically, this points to <b>{ketu_domain}</b>. You are already naturally gifted here, but obsessing over it will stall your career. Delegate these tasks and use them only as a foundational strength.</p>
</div>
</div>
<h2 style="color: #2c3e50; font-size: 24px; border-bottom: 2px solid #eee; padding-bottom: 8px;">Phase 4: The 3 rules for success</h2>
<div style="background-color: #e8f6f3; border: 1px solid #d1f2eb; padding: 20px; border-radius: 8px; margin-bottom: 30px;">
<ol style="margin: 0; padding-left: 20px; font-size: 15px; color: #111; line-height: 1.6;">
<li style="margin-bottom: 12px;"><b>Protect Your Energy:</b> {coaching_rules[0]}</li>
<li style="margin-bottom: 12px;"><b>Current Focus:</b> {coaching_rules[1]}</li>
<li><b>The Ultimate Metric:</b> {coaching_rules[2]}</li>
</ol>
</div>
<h2 style="color: #2c3e50; font-size: 24px; border-bottom: 2px solid #eee; padding-bottom: 8px;">Phase 5: The cognitive mechanics</h2>
<p style="font-size: 14px; color: #666; margin-bottom: 25px;">While your Core Drive (Phase 1) explains <i>why</i> you act, your Cognitive mechanics (<b>{mbti_data['code']}</b>) explains <i>how</i> your brain naturally processes data to get there.</p>
<div style="max-width: 650px; margin: 0 auto; padding: 10px 0;">
{draw_mbti_bar_html("Energy Orientation", e_txt, "EXTRAVERTED", "INTROVERTED", mbti_data['extro_pct'])}
{draw_mbti_bar_html("Information Processing", s_txt, "SENSING", "INTUITIVE", 100 - mbti_data['int_pct'])}
{draw_mbti_bar_html("Decision Making", t_txt, "THINKING", "FEELING", mbti_data['think_pct'])}
{draw_mbti_bar_html("World Structure", j_txt, "JUDGING", "PERCEIVING", mbti_data['judging_pct'])}
</div>
</div>
"""
            st.markdown(playbook_html, unsafe_allow_html=True)

        # --- TAB 4: LOVE & HEALTH ---
        with t4:
            st.markdown("### Deep Navamsa & Partnerships")
            st.markdown("This chart represents your deep subconscious, the second half of your life, and the fundamental energetic dynamics of your long-term partnerships.")
            st.markdown(f"<h3 style='text-align: center; margin-top:20px;'>{'நவாம்ச சக்கரம் (Navamsa)' if LANG=='Tamil' else 'Destiny Chart (Navamsa)'}</h3>", unsafe_allow_html=True)
            st.markdown(get_south_indian_chart_html(p_d9, d9_lagna, "நவாம்சம்" if LANG=="Tamil" else "Navamsa", LANG), unsafe_allow_html=True)
            st.divider()
            for line in love_txt: st.markdown(line)
            st.divider()
            for line in health_txt: st.markdown(line)

        # --- TAB 5: YOGAS & FORECAST ---
        with t5:
            for y in yogas:
                st.markdown(f"#### {y['Name']}\n> **Type:** {y['Type']}\n\n{y['Description']}")
            st.divider()
            for cat, data in fc.items():
                st.markdown(f"#### {cat}\n{data[0]}\n> **Remedy:** {data[1]}")
            st.divider()
            for txt in transit_texts: st.markdown(txt)

        # --- TAB 6: ROADMAP (Strategic Timeline) ---
        with t6:
            st.markdown("### Strategic timeline & mahadashas")
            
            if pd_info:
                st.markdown(f"""
                <div style='background-color:#e8f6f3; padding:15px; border-left:4px solid #1abc9c; border-radius:4px; margin-bottom:20px; font-size:15px; color:#2c3e50;'>
                    <b>Current Phase (Dasha/Bhukti):</b> You are running the <b>{pd_info['MD']}</b> Mahadasha and <b>{pd_info['AD']}</b> Antardasha until {pd_info['End']}.
                </div>
                """, unsafe_allow_html=True)
            
            planet_colors = {"Suriyan": "#d35400", "Chandran": "#95a5a6", "Sevvai": "#c0392b", "Budhan": "#27ae60", "Guru": "#f39c12", "Sukran": "#8e44ad", "Sani": "#2c3e50", "Rahu": "#34495e", "Ketu": "#7f8c8d"}
            
            dasha_expanded_context = {
                "Suriyan": "This is a phase of intense visibility and authority. You will naturally gravitate towards leadership positions and expect recognition for your efforts. Build your personal brand and take decisive actions. However, you must actively manage your ego to avoid alienating key allies. Your relationship with authority figures takes center stage, requiring diplomacy.",
                "Chandran": "A deeply emotional and intuitive phase. Your focus shifts from external conquest to internal security, home life, and emotional well-being. This is an excellent period for building strong teams, nurturing relationships, and dealing with the public. Adaptability is your greatest asset here. Real estate and domestic affairs often prosper.",
                "Sevvai": "A high-octane period of aggressive execution and rapid scaling. You are infused with warrior energy, making this the perfect time to tackle massive obstacles and outmaneuver competitors. Patience will be extremely low; channel this aggressive energy into structured projects rather than interpersonal conflicts. Success comes through courage.",
                "Rahu": "A karmic phase characterized by unconventional ambition and breaking boundaries. You will feel an intense, almost obsessive drive to succeed and expand your footprint. This period often brings sudden foreign opportunities, tech breakthroughs, and massive leaps in status. Beware of illusions; the growth is real, but you must stay grounded.",
                "Guru": "A golden era of expansion, wisdom, and ethical growth. Wealth, mentorship, and opportunities flow with less resistance. It is a time to scale your vision, act as a strategic counselor, and accumulate assets. Legal and educational pursuits are highly favored. Avoid the trap of over-optimism or taking this luck for granted.",
                "Sani": "The ultimate phase of structural discipline and delayed gratification. Saturn slows things down to test your foundations. Success here is mathematically guaranteed if you put in the grueling, patient work, but shortcuts will be punished. Build unshakeable infrastructure and master your craft through sheer endurance. Do not expect overnight results.",
                "Budhan": "A highly stimulating period focused on intellect, communication, and commercial trade. Your analytical skills will be incredibly sharp, making this the ideal time for strategic planning, writing, and data-driven decision-making. Keep your nervous system in check, as the mental overdrive can lead to anxiety if not balanced with physical grounding.",
                "Ketu": "A profound period of spiritual detachment and highly specialized mastery. You may feel a sudden disinterest in superficial social climbing. This is a time for deep, isolated research, backend development, and letting go of things that no longer serve you. Career pivots are common here as you seek deeper meaning. Let your expertise speak for itself.",
                "Sukran": "A vibrant phase of aesthetic refinement, diplomacy, and material comfort. Your focus shifts to building elite alliances, enjoying the fruits of your labor, and cultivating harmonious environments. Wealth generation is strong, particularly through partnerships or arts. It is an excellent time for deepening relationships, provided you avoid superficial indulgences."
            }

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

            md_table_html = f"<table style='width: 100%; border-collapse: collapse; font-family: sans-serif; font-size: 14px; margin-top: 20px;'><tr style='border-bottom: 2px solid #ddd; background-color: #fdfdfd;'><th style='padding: 12px 8px; text-align: left; width: 10%; white-space: nowrap;'>Age</th><th style='padding: 12px 8px; text-align: left; width: 12%; white-space: nowrap;'>Years</th><th style='padding: 12px 8px; text-align: left; width: 15%;'>Dasha</th><th style='padding: 12px 8px; text-align: left; width: 63%;'>Context & Prediction</th></tr>"
            for row in mahadasha_data:
                years_one_line = row['Years'].replace(' - ', ' &ndash; ')
                rich_context = dasha_expanded_context.get(row['Mahadasha'], row['Prediction'])
                md_table_html += f"<tr style='border-bottom: 1px solid #eee;'><td style='padding: 12px 8px; vertical-align: top; white-space: nowrap;'>{row['Age (From-To)']}</td><td style='padding: 12px 8px; vertical-align: top; white-space: nowrap;'>{years_one_line}</td><td style='padding: 12px 8px; vertical-align: top; color: {planet_colors.get(row['Mahadasha'], '#333')}; font-weight: bold;'>{row['Mahadasha']}</td><td style='padding: 12px 8px; vertical-align: top; line-height: 1.5;'>{rich_context}</td></tr>"
            md_table_html += "</table>"
            st.markdown(md_table_html, unsafe_allow_html=True)

        # --- TAB 7: ORACLE ---
        with t7:
            st.subheader("✦ Ask the AI Astrologer" if LANG == "English" else "✦ AI ஜோதிடரிடம் கேளுங்கள்")
            
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
                            valid_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                            target_model = 'gemini-1.5-flash-latest'
                            for m in valid_models:
                                if 'gemini-2.0-flash' in m:
                                    target_model = m
                                    break
                                elif 'gemini-1.5-flash-latest' in m:
                                    target_model = m
                                    break

                            model = genai.GenerativeModel(target_model)
                            response = model.generate_content(f"Data: Lagna {ZODIAC[lagna_rasi]}, Moon {ZODIAC[moon_rasi]}. User says: {prompt_input}")
                            st.markdown(response.text)
                            st.session_state.messages.append({"role": "assistant", "content": response.text})
                        except Exception as e:
                            if "429" in str(e):
                                st.error("⚠️ **Error 429: AI Quota Exceeded.** You have hit your free-tier limit for the Gemini API today. Please check your Google AI Studio billing limits.")
                            else:
                                st.error(f"⚠️ AI Generation Failed. Details: {e}")
                st.rerun()
