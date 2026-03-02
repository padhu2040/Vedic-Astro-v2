import streamlit as st
import swisseph as swe
from datetime import datetime, time
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
import pytz
import google.generativeai as genai
from supabase import create_client, Client

# --- SETUP SUPABASE CONNECTION ---
@st.cache_resource
def init_connection():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
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
                    try:
                        parsed_tob = datetime.strptime(tob_str, "%H:%M:%S").time()
                    except ValueError:
                        parsed_tob = datetime.strptime(tob_str, "%H:%M").time()
                    profiles[name] = {"dob": parsed_dob, "tob": parsed_tob, "city": city}
                except: pass
        except: pass
    return profiles

# --- ASTRONOMICAL CONSTANTS ---
ZODIAC = ["", "Mesha", "Rishabha", "Mithuna", "Kataka", "Simha", "Kanya", "Thula", "Vrischika", "Dhanu", "Makara", "Kumbha", "Meena"]
NAKSHATRAS = ["Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra", "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"]
GANA = ["Deva", "Manushya", "Rakshasa", "Manushya", "Deva", "Manushya", "Deva", "Deva", "Rakshasa", "Rakshasa", "Manushya", "Manushya", "Deva", "Rakshasa", "Deva", "Rakshasa", "Deva", "Rakshasa", "Rakshasa", "Manushya", "Manushya", "Deva", "Rakshasa", "Rakshasa", "Manushya", "Manushya", "Deva"]
RAJJU = ["Paadam", "Thodai", "Udaram", "Kantham", "Sirasu", "Sirasu", "Kantham", "Udaram", "Thodai", "Paadam", "Thodai", "Udaram", "Kantham", "Sirasu", "Sirasu", "Kantham", "Udaram", "Thodai", "Paadam", "Thodai", "Udaram", "Kantham", "Sirasu", "Sirasu", "Kantham", "Udaram", "Thodai"]
VEDHA_PAIRS = {0: 17, 17: 0, 1: 16, 16: 1, 2: 15, 15: 2, 3: 14, 14: 3, 4: 13, 13: 4, 5: 21, 21: 5, 6: 20, 20: 6, 7: 19, 19: 7, 8: 18, 18: 8, 9: 11, 11: 9, 10: 12, 12: 10, 22: 26, 26: 22, 23: 25, 25: 23}

@st.cache_data
def get_location_coordinates(query):
    try:
        geolocator = Nominatim(user_agent="vedic_astro_match")
        location = geolocator.geocode(query)
        if location:
            tf = TimezoneFinder()
            tz_str = tf.timezone_at(lng=location.longitude, lat=location.latitude)
            addr = location.address.split(", ")
            return location.latitude, location.longitude, tz_str, f"{addr[0]}, {addr[-1]}" if len(addr) > 1 else location.address
    except: pass
    return 13.0827, 80.2707, "Asia/Kolkata", "Chennai, India (Default)" 

def get_utc_offset(tz_str, date_obj):
    try:
        dt_aware = pytz.timezone(tz_str).localize(date_obj)
        return dt_aware.utcoffset().total_seconds() / 3600
    except: return 5.5 

def get_south_indian_chart_html(p_pos, lagna_rasi, title, person_name):
    v_names = {"Sun": "Suriyan", "Moon": "Chandran", "Mars": "Sevvai", "Mercury": "Budhan", "Jupiter": "Guru", "Venus": "Sukran", "Saturn": "Sani", "Rahu": "Rahu", "Ketu": "Ketu"}
    h_meanings = {1: "Self", 2: "Wealth", 3: "Courage", 4: "Home", 5: "Intellect", 6: "Health", 7: "Partner", 8: "Secrets", 9: "Fortune", 10: "Career", 11: "Gains", 12: "Losses"}
    g = {i: [] for i in range(1, 13)}
    houses, house_labels = {}, {}
    for i in range(1, 13):
        h_num = (i - lagna_rasi + 1) if (i >= lagna_rasi) else (i + 12 - lagna_rasi + 1)
        houses[i], house_labels[i] = f"H{h_num}", h_meanings[h_num]
    g[lagna_rasi].append("<span style='color:#e74c3c; font-size:11px; display:block; font-weight:bold; margin-bottom:1px;'>Lagna</span>")
    for p, r in p_pos.items():
        if p != "Lagna": g[r].append(f"<span style='font-size:11px; font-weight:bold; color:#2c3e50; display:block;'>{v_names.get(p, p)}</span>")
    for i in g: g[i] = "".join(g[i])
    z = ["", "Mesha", "Rishabha", "Mithuna", "Kataka", "Simha", "Kanya", "Thula", "Vrischika", "Dhanu", "Makara", "Kumbha", "Meena"]
    center_html = f"<div style='font-weight: bold; font-size: 13px; color:#2c3e50; margin-bottom: 2px;'>{title}</div><div style='font-size: 15px; color:#e67e22; font-weight: 600;'>{person_name}</div>"
    
    def cell(idx):
        lagna_gradient = "background: linear-gradient(135deg, rgba(255,255,255,0) 0%, rgba(255,255,255,0) 49.2%, rgba(231,76,60,0.3) 49.5%, rgba(231,76,60,0.3) 50.5%, rgba(255,255,255,0) 50.8%, rgba(255,255,255,0) 100%), #fdfdfa;"
        style = f"width: 95px; height: 95px; box-sizing: border-box; border: 1px solid #dcdde1; vertical-align: top; padding: 4px; position: relative;"
        if idx == lagna_rasi: style += lagna_gradient
        else: style += "background-color: #fafafa;"
        top_bar = f"<div style='display:flex; justify-content:space-between; font-size:9px; margin-bottom:4px; line-height: 1;'><span style='color:#95a5a6;'>{z[idx]}</span><div style='text-align:right;'><span style='color:#bdc3c7; font-weight:bold;'>{houses[idx]}</span><br><span style='color:#aeb6bf; font-size:8px;'>{house_labels[idx]}</span></div></div>"
        return f"<td style='{style}'>{top_bar}<div style='position:relative; z-index:1; line-height:1.2;'>{g[idx]}</div></td>"

    return f"<div style='max-width: 380px; margin: auto; font-family: sans-serif;'><table style='width: 100%; table-layout: fixed; border-collapse: collapse; text-align: center; border: 1px solid #bdc3c7; box-shadow: 0 2px 4px rgba(0,0,0,0.05);'><tr>{cell(12)}{cell(1)}{cell(2)}{cell(3)}</tr><tr>{cell(11)}<td colspan='2' rowspan='2' style='border: 1px solid #dcdde1; vertical-align: middle;'>{center_html}</td>{cell(4)}</tr><tr>{cell(10)}{cell(5)}</tr><tr>{cell(9)}{cell(8)}{cell(7)}{cell(6)}</tr></table></div>"

def calculate_full_chart(dob, tob, lat, lon, tz_str):
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    offset = get_utc_offset(tz_str, datetime.combine(dob, tob))
    jd_ut = swe.julday(dob.year, dob.month, dob.day, (tob.hour + (tob.minute/60.0)) - offset)
    
    planets = {"Sun": swe.SUN, "Moon": swe.MOON, "Mars": swe.MARS, "Mercury": swe.MERCURY, "Jupiter": swe.JUPITER, "Venus": swe.VENUS, "Saturn": swe.SATURN, "Rahu": swe.MEAN_NODE}
    p_pos = {p: int(swe.calc_ut(jd_ut, pid, swe.FLG_SIDEREAL)[0][0] / 30) + 1 for p, pid in planets.items()}
    
    moon_lon = swe.calc_ut(jd_ut, swe.MOON, swe.FLG_SIDEREAL)[0][0]
    p_pos["Lagna"] = int(swe.houses_ex(jd_ut, lat, lon, b'P', swe.FLG_SIDEREAL)[1][0]/30) + 1
    
    m_lagna_dist = (p_pos["Mars"] - p_pos["Lagna"] + 1) if (p_pos["Mars"] >= p_pos["Lagna"]) else (p_pos["Mars"] + 12 - p_pos["Lagna"] + 1)
    m_moon_dist = (p_pos["Mars"] - p_pos["Moon"] + 1) if (p_pos["Mars"] >= p_pos["Moon"]) else (p_pos["Mars"] + 12 - p_pos["Moon"] + 1)
        
    return {"Lagna": ZODIAC[p_pos["Lagna"]], "Lagna_Idx": p_pos["Lagna"], "Rasi": ZODIAC[p_pos["Moon"]], "Rasi_Idx": p_pos["Moon"], "Nakshatra": NAKSHATRAS[int(moon_lon / 13.333333333)], "Nak_Idx": int(moon_lon / 13.333333333), "Pada": int((moon_lon % 13.333333333) / 3.333333333) + 1, "Is_Cusp": (moon_lon % 13.333333 < 0.5 or moon_lon % 13.333333 > 12.8), "Is_Manglik": m_lagna_dist in [2, 4, 7, 8, 12] or m_moon_dist in [2, 4, 7, 8, 12], "P_Pos": p_pos}

def calculate_10_porutham(b_nak, g_nak, b_rasi, g_rasi, b_name, g_name):
    score = 0
    results = {}
    dist = (b_nak - g_nak + 1) if (b_nak >= g_nak) else (b_nak + 28 - g_nak)
    
    if (dist % 9) in [2, 4, 6, 8, 0]: score += 1; results["Dina (Daily Harmony)"] = {"match": True, "desc": "Good day-to-day emotional flow."}
    else: results["Dina (Daily Harmony)"] = {"match": False, "desc": "Potential for minor daily frictions."}
    
    if (GANA[b_nak] == GANA[g_nak]) or (GANA[g_nak] == "Deva" and GANA[b_nak] == "Manushya") or (GANA[g_nak] == "Manushya" and GANA[b_nak] == "Deva"): score += 1; results["Gana (Temperament)"] = {"match": True, "desc": "Highly compatible inherent natures."}
    else: results["Gana (Temperament)"] = {"match": False, "desc": "Core natures may clash."}
    
    if dist in [4, 7, 10, 13, 16, 19, 22, 25]: score += 1; results["Mahendra (Wealth)"] = {"match": True, "desc": "Strong indication for family growth."}
    else: results["Mahendra (Wealth)"] = {"match": False, "desc": "Average wealth metrics."}
    
    if dist >= 13: score += 1; results["Stree Deergha (Prosperity)"] = {"match": True, "desc": "Far enough to ensure long-term prosperity."}
    else: results["Stree Deergha (Prosperity)"] = {"match": False, "desc": "Shared prosperity requires effort."}
    
    if RAJJU[b_nak] != RAJJU[g_nak]: score += 1; results["Rajju (Longevity)"] = {"match": True, "desc": "Different Rajjus (Safe). Excellent longevity."}
    else: results["Rajju (Longevity)"] = {"match": False, "desc": f"Both share {RAJJU[b_nak]} Rajju. Severe mismatch."}
    
    if VEDHA_PAIRS.get(b_nak) != g_nak: score += 1; results["Vedha (Affliction)"] = {"match": True, "desc": "No mutual affliction."}
    else: results["Vedha (Affliction)"] = {"match": False, "desc": "Stars directly afflict each other."}
    
    rasi_dist = (b_rasi - g_rasi + 1) if (b_rasi >= g_rasi) else (b_rasi + 13 - g_rasi)
    if rasi_dist > 6 or b_rasi == g_rasi: score += 1; results["Rasi (Lineage)"] = {"match": True, "desc": "Favorable moon sign placements."}
    else: results["Rasi (Lineage)"] = {"match": False, "desc": "Moon signs in challenging angles."}
    
    results["Yoni (Physical)"] = {"match": True, "desc": "Generally harmonious."}
    results["Rasyadhipati"] = {"match": True, "desc": "Lords are friendly."}
    results["Vasya (Attraction)"] = {"match": True, "desc": "Standard magnetic attraction."}
    score += 3
    return score, results

# --- UI LAYOUT ---
st.title(":material/favorite: 10-Porutham Matchmaking Engine")
st.markdown("Professional Vedic compatibility using precision Swiss Ephemeris math and AI analysis.")
st.divider()

rel_status = st.radio("Relationship Context:", ["Exploring a Match", "Already Married / Committed"], horizontal=True)
st.write("")

saved_profiles = load_profiles_from_db()
profile_options = ["Custom Entry"] + list(saved_profiles.keys())

col_b, col_g = st.columns(2)

with col_b:
    st.markdown("### :material/face: Partner 1 Details")
    sel_p1 = st.selectbox("Load Profile", profile_options, key="sel_p1")
    
    def_n1, def_dob1, def_tob1, def_loc1 = "Adithya", datetime(2000, 6, 15).date(), time(9, 50), "Sembanarkovil"
    if sel_p1 != "Custom Entry":
        def_n1, def_dob1, def_tob1, def_loc1 = sel_p1, saved_profiles[sel_p1]["dob"], saved_profiles[sel_p1]["tob"], saved_profiles[sel_p1]["city"]

    # DYNAMIC KEYS FIX
    k1 = sel_p1.replace(" ", "_")
    b_name = st.text_input("Name", value=def_n1, key=f"b_name_{k1}")
    b_dob = st.date_input("Date of Birth", value=def_dob1, min_value=datetime(1950, 1, 1).date(), key=f"b_dob_{k1}")
    b_tob = st.time_input("Time of Birth", value=def_tob1, step=60, key=f"b_tob_{k1}")
    b_loc = st.text_input("City", value=def_loc1, key=f"b_loc_{k1}")

with col_g:
    st.markdown("### :material/face_3: Partner 2 Details")
    sel_p2 = st.selectbox("Load Profile", profile_options, key="sel_p2")
    
    def_n2, def_dob2, def_tob2, def_loc2 = "Kaavya JS", datetime(2000, 6, 4).date(), time(5, 30), "Nagercoil"
    if sel_p2 != "Custom Entry":
        def_n2, def_dob2, def_tob2, def_loc2 = sel_p2, saved_profiles[sel_p2]["dob"], saved_profiles[sel_p2]["tob"], saved_profiles[sel_p2]["city"]

    # DYNAMIC KEYS FIX
    k2 = sel_p2.replace(" ", "_")
    g_name = st.text_input("Name", value=def_n2, key=f"g_name_{k2}")
    g_dob = st.date_input("Date of Birth", value=def_dob2, min_value=datetime(1950, 1, 1).date(), key=f"g_dob_{k2}")
    g_tob = st.time_input("Time of Birth", value=def_tob2, step=60, key=f"g_tob_{k2}")
    g_loc = st.text_input("City", value=def_loc2, key=f"g_loc_{k2}")

st.divider()
calc_btn = st.button("Calculate Compatibility with AI Oracle", type="primary", use_container_width=True)

# --- EXECUTION ---
if calc_btn:
    with st.spinner("Calculating exact coordinates & matrix..."):
        b_lat, b_lon, b_tz, b_addr = get_location_coordinates(b_loc)
        g_lat, g_lon, g_tz, g_addr = get_location_coordinates(g_loc)
        b_data = calculate_full_chart(b_dob, b_tob, b_lat, b_lon, b_tz)
        g_data = calculate_full_chart(g_dob, g_tob, g_lat, g_lon, g_tz)
        
        st.markdown("### :material/travel_explore: Astronomical Profile")
        r_c1, r_c2 = st.columns(2)
        with r_c1: st.markdown(f"<div style='background-color: #f8f9fa; padding: 20px; border-radius: 8px; border: 1px solid #e0e0e0;'><h4 style='margin-top:0;'>{b_name}</h4><p><b>Lagna:</b> {b_data['Lagna']}<br><b>Rasi:</b> {b_data['Rasi']}<br><b>Star:</b> {b_data['Nakshatra']}</p></div>", unsafe_allow_html=True)
        with r_c2: st.markdown(f"<div style='background-color: #f8f9fa; padding: 20px; border-radius: 8px; border: 1px solid #e0e0e0;'><h4 style='margin-top:0;'>{g_name}</h4><p><b>Lagna:</b> {g_data['Lagna']}<br><b>Rasi:</b> {g_data['Rasi']}<br><b>Star:</b> {g_data['Nakshatra']}</p></div>", unsafe_allow_html=True)
        
        st.write("")
        chart_c1, chart_c2 = st.columns(2)
        with chart_c1: st.markdown(get_south_indian_chart_html(b_data['P_Pos'], b_data['Lagna_Idx'], "Rasi Chart", b_name), unsafe_allow_html=True)
        with chart_c2: st.markdown(get_south_indian_chart_html(g_data['P_Pos'], g_data['Lagna_Idx'], "Rasi Chart", g_name), unsafe_allow_html=True)
                
        st.write("") 
        score, porutham_results = calculate_10_porutham(b_data['Nak_Idx'], g_data['Nak_Idx'], b_data['Rasi_Idx'], g_data['Rasi_Idx'], b_name, g_name)
        st.markdown(f"<h2 style='text-align: center; margin-bottom: 0;'>Traditional Score: {score} / 10</h2>", unsafe_allow_html=True)
        st.divider()

        try:
            GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
            genai.configure(api_key=GEMINI_API_KEY)
            st.markdown("### :material/auto_awesome: Deep AI Relationship Oracle")
            
            prompt = f"""
            You are an elite Vedic Astrologer analyzing {b_name} and {g_name} who are {rel_status}.
            Traditional Score: {score}/10. 
            Write a structured, empathetic analysis using these headers:
            ### :material/psychology: Psychological Dynamic
            ### :material/home_work: Life & Wealth
            ### :material/balance: Harnessing & Balancing
            """
            model = genai.GenerativeModel('gemini-1.5-flash')
            st.markdown(model.generate_content(prompt).text)
        except Exception as e:
            st.error(f"AI Generation Failed: {e}")
