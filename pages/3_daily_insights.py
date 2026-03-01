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

# UPGRADE 1: Mapping Rasi to corresponding Nakshatras for the dependent dropdown
RASI_STAR_MAP = {
    "Mesha": ["Ashwini", "Bharani", "Krittika"],
    "Rishabha": ["Krittika", "Rohini", "Mrigashira"],
    "Mithuna": ["Mrigashira", "Ardra", "Punarvasu"],
    "Kataka": ["Punarvasu", "Pushya", "Ashlesha"],
    "Simha": ["Magha", "Purva Phalguni", "Uttara Phalguni"],
    "Kanya": ["Uttara Phalguni", "Hasta", "Chitra"],
    "Thula": ["Chitra", "Swati", "Vishakha"],
    "Vrischika": ["Vishakha", "Anuradha", "Jyeshtha"],
    "Dhanu": ["Mula", "Purva Ashadha", "Uttara Ashadha"],
    "Makara": ["Uttara Ashadha", "Shravana", "Dhanishta"],
    "Kumbha": ["Dhanishta", "Shatabhisha", "Purva Bhadrapada"],
    "Meena": ["Purva Bhadrapada", "Uttara Bhadrapada", "Revati"]
}

# --- GLOBAL SESSION STATE ---
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
            
    ascmc = swe.houses_ex(jd_ut, lat, lon, b'P', swe.FLG_SIDEREAL)[1]
    pos["Lagna"] = {"rasi_idx": int(ascmc[0]/30) + 1, "rasi": ZODIAC[int(ascmc[0]/30) + 1]}
    return pos

# UPGRADE 2: Mathematical Panchangam & Daily Event Detector
def get_daily_panchangam(calc_date):
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    # Calculate for Noon local time
    jd_ut = swe.julday(calc_date.year, calc_date.month, calc_date.day, 6.5) # Approx 12 PM IST in UT
    
    sun_lon = swe.calc_ut(jd_ut, swe.SUN, swe.FLG_SIDEREAL)[0][0]
    moon_lon = swe.calc_ut(jd_ut, swe.MOON, swe.FLG_SIDEREAL)[0][0]
    
    # Calculate Tithi (Lunar Day)
    tithi_val = (moon_lon - sun_lon) % 360 / 12.0
    tithi_num = int(tithi_val) + 1 # 1 to 30
    
    events = []
    if tithi_num in [11, 26]: events.append("✨ Ekadhasi (Ideal for fasting & spiritual focus)")
    if tithi_num in [13, 28]: events.append("🔱 Pradosham (Auspicious for Lord Shiva worship)")
    if tithi_num in [4, 19]: events.append("🐘 Chaturthi (Auspicious for Lord Ganesha worship)")
    if tithi_num in [6, 21]: events.append("🦚 Sashti (Auspicious for Lord Murugan worship)")
    if tithi_num in [8, 23]: events.append("⚠️ Ashtami (Avoid initiating new material ventures)")
    if tithi_num in [9, 24]: events.append("⚠️ Navami (Avoid initiating new material ventures)")
    if tithi_num == 15: events.append("🌕 Pournami (Full Moon - Peak manifestation energy)")
    if tithi_num == 30: events.append("🌑 Amavasai (New Moon - Ancestral worship)")
    
    nak_idx = int(moon_lon / 13.333333333)
    
    weekday = calc_date.weekday() # 0 = Mon, 6 = Sun
    timings = {
        0: {"Rahu": "07:30 AM - 09:00 AM", "Yama": "10:30 AM - 12:00 PM"}, 
        1: {"Rahu": "03:00 PM - 04:30 PM", "Yama": "09:00 AM - 10:30 AM"}, 
        2: {"Rahu": "12:00 PM - 01:30 PM", "Yama": "07:30 AM - 09:00 AM"}, 
        3: {"Rahu": "01:30 PM - 03:00 PM", "Yama": "06:00 AM - 07:30 AM"}, 
        4: {"Rahu": "10:30 AM - 12:00 PM", "Yama": "03:00 PM - 04:30 PM"}, 
        5: {"Rahu": "09:00 AM - 10:30 AM", "Yama": "01:30 PM - 03:00 PM"}, 
        6: {"Rahu": "04:30 PM - 06:00 PM", "Yama": "12:00 PM - 01:30 PM"}  
    }
    
    return {
        "Star": NAKSHATRAS[nak_idx],
        "Moon_Sign": ZODIAC[int(moon_lon / 30) + 1],
        "Events": events,
        "Timings": timings[weekday],
        "Weekday": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][weekday]
    }

# --- UI LAYOUT ---
st.title(":material/calendar_today: Daily Planetary Insights")
st.markdown("Navigate your day with cosmic awareness. Check today's calendar, get a quick free overview, or unlock your deep personalized forecast.")

# --- THE DAILY ALMANAC (PANCHANGAM) ---
st.divider()
col_target, col_empty = st.columns([1, 2])
with col_target:
    today_date = st.date_input("Select Date for Almanac & Forecast", datetime.now().date())

panch = get_daily_panchangam(today_date)

st.markdown(f"### 🗓️ Daily Almanac ({panch['Weekday']})")
col_p1, col_p2, col_p3 = st.columns(3)

with col_p1:
    st.markdown(f"""
    <div style="background-color: #fdfaf0; padding: 15px; border-radius: 8px; border-left: 4px solid #f39c12; height: 100%;">
        <h4 style="margin:0 0 5px 0; color: #2c3e50; font-size:15px;">Cosmic Weather</h4>
        <p style="margin:0; font-size:14px;"><b>Moon Sign:</b> {panch['Moon_Sign']}</p>
        <p style="margin:0; font-size:14px;"><b>Ruling Star:</b> {panch['Star']}</p>
    </div>
    """, unsafe_allow_html=True)
    
with col_p2:
    st.markdown(f"""
    <div style="background-color: #fef2f2; padding: 15px; border-radius: 8px; border-left: 4px solid #e74c3c; height: 100%;">
        <h4 style="margin:0 0 5px 0; color: #2c3e50; font-size:15px;">Time to Avoid</h4>
        <p style="margin:0; font-size:14px;"><b>Rahu Kalam:</b> {panch['Timings']['Rahu']}</p>
        <p style="margin:0; font-size:14px;"><b>Yama Kandam:</b> {panch['Timings']['Yama']}</p>
    </div>
    """, unsafe_allow_html=True)

with col_p3:
    event_str = "<br>".join([f"• {e}" for e in panch['Events']]) if panch['Events'] else "• Regular day (No major special Tithi)"
    st.markdown(f"""
    <div style="background-color: #f4f6f6; padding: 15px; border-radius: 8px; border-left: 4px solid #9b59b6; height: 100%;">
        <h4 style="margin:0 0 5px 0; color: #2c3e50; font-size:15px;">Auspicious Events</h4>
        <p style="margin:0; font-size:13px; line-height:1.4;">{event_str}</p>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# --- TABS ---
tab1, tab2 = st.tabs(["🚀 Quick Free Forecast", "💎 Deep Personalized Forecast"])

with tab1:
    st.markdown("### Quick General Forecast")
    st.write("Select your Moon sign and Star for an instant, high-level summary of your day.")
    
    col_q1, col_q2 = st.columns(2)
    with col_q1:
        # Dynamic Rasi Selection
        sel_rasi = st.selectbox("Select Rasi (Moon Sign)", list(RASI_STAR_MAP.keys()))
    with col_q2:
        # Dynamic Star selection based on Rasi!
        sel_nak = st.selectbox("Select Nakshatra (Star)", RASI_STAR_MAP[sel_rasi])
        
    if st.button("Generate Quick Forecast", type="primary"):
        if not GEMINI_API_KEY:
            st.error("API Key missing! Add it to Streamlit Secrets.")
        else:
            with st.spinner("Channeling quick daily guidance..."):
                try:
                    genai.configure(api_key=GEMINI_API_KEY)
                    q_prompt = f"""
                    Provide a fast, highly structured daily astrological forecast for a person born with the Moon in {sel_rasi} Rasi and {sel_nak} Nakshatra.
                    Today, the Moon is transiting {panch['Moon_Sign']} Rasi ({panch['Star']} star).
                    
                    Format exactly like this with short, punchy sentences:
                    **Today's Cosmic Alignment:** (1 sentence summary)
                    * **Focus Area:** (1 practical sentence on what to do)
                    * **Caution:** (1 practical sentence on what to avoid)
                    * **Quick Tip:** (1 sentence action for success today)
                    """
                    
                    # Safe Model Fallback
                    try:
                        model = genai.GenerativeModel('gemini-1.5-flash')
                        response = model.generate_content(q_prompt)
                    except:
                        model = genai.GenerativeModel('gemini-pro')
                        response = model.generate_content(q_prompt)
                        
                    st.success(response.text)
                except Exception as e:
                    st.error(f"AI Generation Failed: {e}")

with tab2:
    col_input, _ = st.columns([1, 1])

    with col_input:
        st.markdown("### :material/account_circle: Your Exact Details")
        st.text_input("Name", key="u_name")
        st.date_input("Date of Birth", key="u_dob")
        st.time_input("Time of Birth", key="u_tob")
        st.text_input("City", key="u_loc")

    calc_btn = st.button("Generate Deep AI Forecast", type="primary", use_container_width=True)

    if calc_btn:
        with st.spinner("Aligning your exact birth chart with today's complex transits..."):
            u_lat, u_lon, u_tz = get_location_coordinates(st.session_state.u_loc)
            
            natal_chart = calculate_planetary_positions(st.session_state.u_dob, st.session_state.u_tob, u_lat, u_lon, u_tz)
            transit_chart = calculate_planetary_positions(today_date, time(12, 0), u_lat, u_lon, u_tz)
            
            n_moon_idx = natal_chart["Moon"]["rasi_idx"]
            t_moon_idx = transit_chart["Moon"]["rasi_idx"]
            moon_dist = (t_moon_idx - n_moon_idx + 1) if (t_moon_idx >= n_moon_idx) else (t_moon_idx + 12 - n_moon_idx + 1)
            
            is_chandrashtama = (moon_dist == 8)
            
            st.markdown(f"""
            <div style="background-color: #e8f4f8; padding: 15px; border-radius: 8px; border-left: 4px solid #2980b9;">
                <h4 style="margin:0 0 5px 0; color: #2c3e50;">{st.session_state.u_name}'s Core Energy</h4>
                <p style="margin:0; font-size:14px;"><b>Rasi:</b> {natal_chart['Moon']['rasi']} | <b>Star:</b> {natal_chart['Moon']['nakshatra']} | <b>Lagna:</b> {natal_chart['Lagna']['rasi']}</p>
            </div><br>
            """, unsafe_allow_html=True)

            if is_chandrashtama:
                st.markdown("""
                <div style="background-color: #fef2f2; color: #991b1b; padding: 15px; border-radius: 8px; border: 1px solid #e74c3c; margin-bottom: 20px;">
                    <h4 style="margin: 0 0 5px 0;">:material/warning: Alert: Chandrashtama Day</h4>
                    <p style="margin: 0; font-size: 14px;">The Moon is currently transiting the 8th house from your birth Moon. This is a highly sensitive 2.5 day period. Avoid starting major new ventures, signing critical contracts, or engaging in heated arguments today. Focus purely on routine work and spiritual grounding.</p>
                </div>
                """, unsafe_allow_html=True)

            if not GEMINI_API_KEY:
                st.error("API Key missing! Add it to Streamlit Secrets to generate AI insights.")
            else:
                st.markdown("### :material/auto_awesome: Today's Personalized Insight")
                with st.spinner("The AI Oracle is channeling Siddhar wisdom..."):
                    try:
                        genai.configure(api_key=GEMINI_API_KEY)
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
                        
                        try:
                            model = genai.GenerativeModel('gemini-1.5-flash')
                            response = model.generate_content(prompt)
                        except:
                            model = genai.GenerativeModel('gemini-pro')
                            response = model.generate_content(prompt)
                            
                        st.markdown(response.text)
                    except Exception as e:
                        st.error(f"AI Generation Failed: {e}")
