import streamlit as st
import swisseph as swe
from datetime import datetime, time
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

# --- HELPER FUNCTIONS ---
@st.cache_data
def get_location_coordinates(query):
    try:
        geolocator = Nominatim(user_agent="vedic_astro_daily")
        location = geolocator.geocode(query)
        if location:
            tf = TimezoneFinder()
            tz_str = tf.timezone_at(lng=location.longitude, lat=location.latitude)
            return location.latitude, location.longitude, tz_str
    except: pass
    return 13.0827, 80.2707, "Asia/Kolkata" 

def get_utc_offset(tz_str, date_obj):
    try:
        tz = pytz.timezone(tz_str)
        dt_aware = tz.localize(date_obj)
        return dt_aware.utcoffset().total_seconds() / 3600
    except: return 5.5 

def calculate_planetary_positions(calc_date, calc_time, lat, lon, tz_str):
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    dt_combine = datetime.combine(calc_date, calc_time)
    offset = get_utc_offset(tz_str, dt_combine)
    ut_hour = (calc_time.hour + (calc_time.minute/60.0)) - offset
    jd_ut = swe.julday(calc_date.year, calc_date.month, calc_date.day, ut_hour)
    
    planets = {"Sun": swe.SUN, "Moon": swe.MOON, "Mars": swe.MARS, "Mercury": swe.MERCURY, "Jupiter": swe.JUPITER, "Venus": swe.VENUS, "Saturn": swe.SATURN}
    pos = {}
    for p, pid in planets.items():
        lon_val = swe.calc_ut(jd_ut, pid, swe.FLG_SIDEREAL)[0][0]
        pos[p] = {"lon": lon_val, "rasi_idx": int(lon_val / 30) + 1, "rasi": ZODIAC[int(lon_val / 30) + 1]}
        
        if p == "Moon":
            nak_idx = int(lon_val / 13.333333333)
            pos[p]["nakshatra"] = NAKSHATRAS[nak_idx]
            pos[p]["pada"] = int((lon_val % 13.333333333) / 3.333333333) + 1
            
    ascmc = swe.houses_ex(jd_ut, lat, lon, b'P', swe.FLG_SIDEREAL)[1]
    pos["Lagna"] = {"rasi_idx": int(ascmc[0]/30) + 1, "rasi": ZODIAC[int(ascmc[0]/30) + 1]}
    
    return pos

# --- UI LAYOUT ---
st.title(":material/calendar_today: Daily Planetary Insights")
st.markdown("Compare today's live celestial movements against your birth chart for actionable daily guidance.")
st.divider()

col_input, col_today = st.columns([1, 1])

with col_input:
    st.markdown("### :material/account_circle: Your Details")
    # Using your details as the default!
    u_name = st.text_input("Name", "Padmanabhan")
    u_dob = st.date_input("Date of Birth", datetime(1977, 11, 14))
    u_tob = st.time_input("Time of Birth", time(1, 45))
    u_loc = st.text_input("City", "Saidapet, Chennai")

with col_today:
    st.markdown("### :material/schedule: Today's Target")
    today_date = st.date_input("Forecast Date", datetime.now().date())
    st.info("The engine will calculate where the planets are on this exact day and compare them to your natal chart.")

st.divider()
calc_btn = st.button("Generate Daily AI Forecast", type="primary", use_container_width=True)

# --- EXECUTION ---
if calc_btn:
    with st.spinner("Aligning your birth chart with today's transits..."):
        u_lat, u_lon, u_tz = get_location_coordinates(u_loc)
        
        # 1. Calculate Natal Chart
        natal_chart = calculate_planetary_positions(u_dob, u_tob, u_lat, u_lon, u_tz)
        
        # 2. Calculate Transit Chart (Today at 12:00 PM for general daily energy)
        transit_chart = calculate_planetary_positions(today_date, time(12, 0), u_lat, u_lon, u_tz)
        
        # 3. Chandrashtama Check (Transit Moon is 8th from Natal Moon)
        n_moon_idx = natal_chart["Moon"]["rasi_idx"]
        t_moon_idx = transit_chart["Moon"]["rasi_idx"]
        moon_dist = (t_moon_idx - n_moon_idx + 1) if (t_moon_idx >= n_moon_idx) else (t_moon_idx + 12 - n_moon_idx + 1)
        
        is_chandrashtama = (moon_dist == 8)
        
        # Display Quick Dashboards
        col_n, col_t = st.columns(2)
        with col_n:
            st.markdown(f"""
            <div style="background-color: #f8f9fa; padding: 15px; border-radius: 8px; border-left: 4px solid #2980b9;">
                <h4 style="margin:0 0 5px 0; color: #2c3e50;">Your Core Energy</h4>
                <p style="margin:0; font-size:14px;"><b>Rasi:</b> {natal_chart['Moon']['rasi']}</p>
                <p style="margin:0; font-size:14px;"><b>Star:</b> {natal_chart['Moon']['nakshatra']}</p>
                <p style="margin:0; font-size:14px;"><b>Lagna:</b> {natal_chart['Lagna']['rasi']}</p>
            </div>
            """, unsafe_allow_html=True)
            
        with col_t:
            st.markdown(f"""
            <div style="background-color: #fdfaf0; padding: 15px; border-radius: 8px; border-left: 4px solid #f39c12;">
                <h4 style="margin:0 0 5px 0; color: #2c3e50;">Today's Weather ({today_date.strftime('%b %d')})</h4>
                <p style="margin:0; font-size:14px;"><b>Moon is transiting:</b> {transit_chart['Moon']['rasi']}</p>
                <p style="margin:0; font-size:14px;"><b>Today's Star:</b> {transit_chart['Moon']['nakshatra']}</p>
            </div>
            """, unsafe_allow_html=True)
            
        st.write("")

        # Chandrashtama Warning Banner
        if is_chandrashtama:
            st.markdown("""
            <div style="background-color: #fef2f2; color: #991b1b; padding: 15px; border-radius: 8px; border: 1px solid #e74c3c; margin-bottom: 20px;">
                <h4 style="margin: 0 0 5px 0;">:material/warning: Alert: Chandrashtama Day</h4>
                <p style="margin: 0; font-size: 14px;">The Moon is currently transiting the 8th house from your birth Moon. This is a sensitive 2.5 day period. Avoid starting major new ventures, signing critical contracts, or engaging in heated arguments today. Focus on routine work and spiritual grounding.</p>
            </div>
            """, unsafe_allow_html=True)

        # 4. THE AI ORACLE
        if not GEMINI_API_KEY:
            st.error("API Key missing! Add it to Streamlit Secrets to generate AI insights.")
        else:
            st.markdown("### :material/auto_awesome: Today's Personalized Insight")
            with st.spinner("The AI Oracle is reading today's transits against your chart..."):
                try:
                    genai.configure(api_key=GEMINI_API_KEY)
                    
                    # Build prompt with exact transit data relative to user's chart
                    prompt = f"""
                    You are an elite, modern Vedic Astrologer providing a daily reading.
                    User: {u_name}.
                    User's Natal Chart: Ascendant is {natal_chart['Lagna']['rasi']}, Moon is in {natal_chart['Moon']['rasi']} ({natal_chart['Moon']['nakshatra']} star).
                    
                    Today's Transits: 
                    The Moon is currently in {transit_chart['Moon']['rasi']} ({transit_chart['Moon']['nakshatra']} star). 
                    This means the transiting Moon is in the {moon_dist}th house from their natal Moon.
                    Chandrashtama Status: {is_chandrashtama}.
                    
                    Write a highly structured, deeply personalized daily horoscope for them. 
                    
                    CRITICAL FORMATTING RULES:
                    - Address {u_name} directly by name.
                    - Keep the tone encouraging, practical, and highly specific to today's transits.
                    - Format EXACTLY using these three headers, with short, punchy, 2-3 sentence paragraphs under each. Do not use generic filler.
                    
                    ### :material/wb_sunny: Today's Energy Focus
                    (Explain how today's transiting Moon interacts with their Natal Moon/Lagna. What is their mood or mental state likely to be?)
                    
                    ### :material/work: Action & Strategy
                    (Practical advice on work, decisions, and interactions for today based on the {moon_dist}th house transit. Tell them exactly what to tackle and what to avoid.)
                    
                    ### :material/self_improvement: Daily Mantra
                    (A single, powerful sentence or affirmation they should keep in mind today to maximize success and peace.)
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
                    st.error(f"AI Generation Failed: {e}")
