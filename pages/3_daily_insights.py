import streamlit as st
import swisseph as swe
from datetime import datetime, time
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
import pytz
import google.generativeai as genai

try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
except:
    GEMINI_API_KEY = ""

ZODIAC = ["", "Mesha", "Rishabha", "Mithuna", "Kataka", "Simha", "Kanya", "Thula", "Vrischika", "Dhanu", "Makara", "Kumbha", "Meena"]
NAKSHATRAS = ["Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra", "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"]

# --- GLOBAL SESSION STATE (Memory) ---
# This ensures data typed here is remembered if they click to other pages
if 'u_name' not in st.session_state: st.session_state.u_name = "Padmanabhan"
if 'u_dob' not in st.session_state: st.session_state.u_dob = datetime(1977, 11, 14)
if 'u_tob' not in st.session_state: st.session_state.u_tob = time(1, 45)
if 'u_loc' not in st.session_state: st.session_state.u_loc = "Saidapet, Chennai"

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
st.markdown("Navigate your day with cosmic awareness. Choose a quick overview or unlock your deep personalized forecast.")
st.divider()

# UPGRADE: Tabbed Navigation for the Two User Personas
tab1, tab2 = st.tabs(["🚀 Quick Rasi Forecast (Free)", "💎 Deep Personalized Forecast (Premium)"])

with tab1:
    st.markdown("### Quick General Forecast")
    st.write("Select your Moon sign and Star for a general daily overview.")
    col_q1, col_q2 = st.columns(2)
    with col_q1:
        sel_rasi = st.selectbox("Select Rasi (Moon Sign)", ZODIAC[1:])
    with col_q2:
        sel_nak = st.selectbox("Select Nakshatra (Star)", NAKSHATRAS)
        
    if st.button("Get Quick Forecast", type="primary"):
        st.info("🚧 The Quick Forecast AI is being configured. Please use the Deep Personalized Forecast in the next tab for full functionality!")

with tab2:
    col_input, col_today = st.columns([1, 1])

    with col_input:
        st.markdown("### :material/account_circle: Your Exact Details")
        # UPGRADE: Binding inputs to session_state for global memory
        st.text_input("Name", key="u_name")
        st.date_input("Date of Birth", key="u_dob")
        st.time_input("Time of Birth", key="u_tob")
        st.text_input("City", key="u_loc")

    with col_today:
        st.markdown("### :material/schedule: Today's Target")
        today_date = st.date_input("Forecast Date", datetime.now().date())
        st.info("This engine calculates live planetary geometry against your precise birth coordinates. Your details are securely cached for this session.")

    calc_btn = st.button("Generate Deep AI Forecast", type="primary", use_container_width=True)

    if calc_btn:
        with st.spinner("Aligning your birth chart with today's transits..."):
            u_lat, u_lon, u_tz = get_location_coordinates(st.session_state.u_loc)
            
            natal_chart = calculate_planetary_positions(st.session_state.u_dob, st.session_state.u_tob, u_lat, u_lon, u_tz)
            transit_chart = calculate_planetary_positions(today_date, time(12, 0), u_lat, u_lon, u_tz)
            
            n_moon_idx = natal_chart["Moon"]["rasi_idx"]
            t_moon_idx = transit_chart["Moon"]["rasi_idx"]
            moon_dist = (t_moon_idx - n_moon_idx + 1) if (t_moon_idx >= n_moon_idx) else (t_moon_idx + 12 - n_moon_idx + 1)
            
            is_chandrashtama = (moon_dist == 8)
            
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

            if is_chandrashtama:
                st.markdown("""
                <div style="background-color: #fef2f2; color: #991b1b; padding: 15px; border-radius: 8px; border: 1px solid #e74c3c; margin-bottom: 20px;">
                    <h4 style="margin: 0 0 5px 0;">:material/warning: Alert: Chandrashtama Day</h4>
                    <p style="margin: 0; font-size: 14px;">The Moon is currently transiting the 8th house from your birth Moon. This is a sensitive 2.5 day period. Avoid starting major new ventures, signing critical contracts, or engaging in heated arguments today. Focus on routine work and spiritual grounding.</p>
                </div>
                """, unsafe_allow_html=True)

            if not GEMINI_API_KEY:
                st.error("API Key missing! Add it to Streamlit Secrets to generate AI insights.")
            else:
                st.markdown("### :material/auto_awesome: Today's Personalized Insight")
                with st.spinner("The AI Oracle is channeling Siddhar wisdom..."):
                    try:
                        genai.configure(api_key=GEMINI_API_KEY)
                        
                        # UPGRADE: Prompt completely rewritten to include Siddhar Wisdom, Mantras, and Pariharam
                        prompt = f"""
                        You are an elite, deeply spiritual Vedic Astrologer rooted in the ancient Tamil Siddhar tradition.
                        User: {st.session_state.u_name}.
                        User's Chart: Ascendant {natal_chart['Lagna']['rasi']}, Moon in {natal_chart['Moon']['rasi']} ({natal_chart['Moon']['nakshatra']} star).
                        Today's Transit: Moon in {transit_chart['Moon']['rasi']} ({transit_chart['Moon']['nakshatra']} star), placed in the {moon_dist}th house from their natal Moon.
                        Chandrashtama: {is_chandrashtama}.
                        
                        Write a deeply personalized daily forecast formatted EXACTLY using these four specific headers. 
                        
                        ### :material/wb_sunny: Today's Energy Focus
                        (2-3 sentences explaining their mental/emotional state today based on the transit).
                        
                        ### :material/work: Action & Strategy
                        (2-3 sentences of practical advice on work and decisions).
                        
                        ### :material/healing: Daily Pariharam & Mantra
                        (Suggest ONE very simple, practical remedy they can do today, like lighting a specific lamp, feeding an animal, or a simple meditation. Follow it with a short, authentic traditional mantra related to today's ruling energy, written in English transliteration).
                        
                        ### :material/menu_book: Wisdom of the Siddhars
                        (Provide a genuine, translated line of profound spiritual poetry or wisdom from an ancient Tamil Siddhar—such as Agathiyar, Thirumoolar, Bogar, or Pattinathar—that perfectly aligns with the astrological energy of today. Provide the quote, attribute it to the specific Siddhar, and add a 1-sentence explanation of how it applies to {st.session_state.u_name}'s day.)
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
