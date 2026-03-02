import swisseph as swe
from datetime import datetime, timedelta
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
import pytz

from database import DASHA_YEARS, DASHA_ORDER, RASI_RULERS, BINDU_RULES
from tamil_lang import TAMIL_LIFESTYLE

# Shared translation dictionaries
t_p = {"Sun": "சூரியன்", "Moon": "சந்திரன்", "Mars": "செவ்வாய்", "Mercury": "புதன்", "Jupiter": "குரு", "Venus": "சுக்கிரன்", "Saturn": "சனி", "Rahu": "ராகு", "Ketu": "கேது"}
ZODIAC_TA = {1: "மேஷம்", 2: "ரிஷபம்", 3: "மிதுனம்", 4: "கடகம்", 5: "சிம்மம்", 6: "கன்னி", 7: "துலாம்", 8: "விருச்சிகம்", 9: "தனுசு", 10: "மகரம்", 11: "கும்பம்", 12: "மீனம்"}

# --- LOCATION & TIME MATH ---
def get_location_coordinates(query):
    try:
        if query.strip().isdigit() and len(query.strip()) == 6: query = f"{query}, India"
        geolocator = Nominatim(user_agent="vedic_astro_ai")
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
        if not isinstance(date_obj, datetime): date_obj = datetime.combine(date_obj, datetime(2000, 1, 1, 12, 0).time())
        dt_aware = tz.localize(date_obj) if date_obj.tzinfo is None else date_obj.astimezone(tz)
        return dt_aware.utcoffset().total_seconds() / 3600
    except: return 5.5 

# --- ASTRONOMY MATH ---
def get_nakshatra_details(lon):
    nak_names = ["Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra", "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"]
    lords = ["Ketu", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury", "Venus"]
    nak_idx = int(lon / 13.333333333)
    return nak_names[nak_idx], lords[nak_idx % 9]

def get_navamsa_chart(lon):
    rasi_num, pada = int(lon / 30) + 1, int((lon % 30) / 3.333333333) + 1
    if rasi_num in [1, 5, 9]: start = 1
    elif rasi_num in [2, 6, 10]: start = 10
    elif rasi_num in [3, 7, 11]: start = 7
    else: start = 4
    return (start + pada - 2) % 12 + 1

def get_dasamsa_chart(lon):
    rasi_num, part = int(lon / 30) + 1, int((lon % 30) / 3.0) + 1
    start = rasi_num if rasi_num % 2 != 0 else (rasi_num + 8) % 12 or 12
    return (start + part - 2) % 12 + 1

def get_dignity(p, r):
    own = {"Sun": [5], "Moon": [4], "Mars": [1,8], "Mercury": [3,6], "Jupiter": [9,12], "Venus": [2,7], "Saturn": [10,11]}
    exalted = {"Sun": 1, "Moon": 2, "Mars": 10, "Mercury": 6, "Jupiter": 4, "Venus": 12, "Saturn": 7, "Rahu": 2, "Ketu": 8}
    neecha = {"Sun": 7, "Moon": 8, "Mars": 4, "Mercury": 12, "Jupiter": 10, "Venus": 6, "Saturn": 1, "Rahu": 8, "Ketu": 2}
    if r in own.get(p, []): return "Own"
    if exalted.get(p) == r: return "Exalted"
    if neecha.get(p) == r: return "Neecha"
    return "Neutral"

def calculate_sav_score(p_pos, lagna):
    scores = [0] * 12
    curr = p_pos.copy(); curr['Lagna'] = lagna
    for p, rules in BINDU_RULES.items():
        if p not in curr: continue
        for ref, offsets in rules.items():
            if ref not in curr: continue
            for off in offsets: scores[(curr[ref] - 1 + off - 1) % 12] += 1
    return scores

def get_bhava_chalit(jd, lat, lon):
    return swe.houses_ex(jd, lat, lon, b'P', swe.FLG_SIDEREAL)[0]

def determine_house(planet_lon, cusps):
    p_lon = planet_lon % 360
    for i in range(12):
        lower, upper = cusps[i], cusps[(i+1)%12]
        if lower < upper:
            if lower <= p_lon < upper: return i + 1
        else:
            if p_lon >= lower or p_lon < upper: return i + 1
    return 1

# --- DEEP ANALYSIS ENGINES ---
def scan_yogas(p_pos, lagna_rasi, lang="English"):
    yogas = []
    p_houses = {p: ((r - lagna_rasi + 1) if (r - lagna_rasi + 1) > 0 else (r - lagna_rasi + 1) + 12) for p, r in p_pos.items() if p != "Lagna"}
    
    if p_pos.get("Sun") == p_pos.get("Mercury"):
        if lang == "Tamil": yogas.append({"Name": "புதாதித்ய யோகம்", "Type": "அறிவு மற்றும் வணிகம்", "Description": f"சூரியனும் புதனும் உங்கள் {p_houses.get('Sun')}-ஆம் வீட்டில் இணைந்து இந்த யோகத்தை உருவாக்குகின்றன. இது மிகச்சிறந்த பகுப்பாய்வு திறனையும், கூர்மையான வணிக அறிவையும் தருகிறது."})
        else: yogas.append({"Name": "Budhaditya Yoga", "Type": "Intellect & Commerce", "Description": f"The Sun and Mercury are structurally conjunct in your {p_houses.get('Sun')}th House. This forms a highly analytical and brilliant business mind."})
    
    if "Jupiter" in p_pos and "Moon" in p_pos:
        jup_from_moon = (p_pos["Jupiter"] - p_pos["Moon"] + 1) if (p_pos["Jupiter"] - p_pos["Moon"] + 1) > 0 else (p_pos["Jupiter"] - p_pos["Moon"] + 1) + 12
        if jup_from_moon in [1, 4, 7, 10]:
            if lang == "Tamil": yogas.append({"Name": "கஜகேசரி யோகம்", "Type": "புகழ் மற்றும் தெய்வீக பாதுகாப்பு", "Description": "குரு உங்கள் சந்திரனுக்கு கேந்திரத்தில் இருப்பதால் இந்த மாபெரும் யோகம் உருவாகிறது."})
            else: yogas.append({"Name": "Gajakesari Yoga", "Type": "Fame & Institutional Protection", "Description": "Jupiter is placed in a foundational angle from your Natal Moon. This is an elite combination for earning widespread respect."})
    
    pm_planets = {"Mars": "Ruchaka", "Mercury": "Bhadra", "Jupiter": "Hamsa", "Venus": "Malavya", "Saturn": "Sasa"}
    for p, y_name in pm_planets.items():
        if p in p_houses and p_houses[p] in [1, 4, 7, 10] and get_dignity(p, p_pos[p]) in ["Own", "Exalted"]:
            if lang == "Tamil": yogas.append({"Name": f"{y_name} மகாபுருஷ யோகம்", "Type": "தனித்துவமான ஆளுமை", "Description": f"{t_p[p]} உங்கள் {p_houses[p]}-ஆம் வீட்டில் மிகவும் வலுவாக அமைந்திருப்பதால் இந்த யோகம் அமைகிறது."})
            else: yogas.append({"Name": f"{y_name} Mahapurusha Yoga", "Type": "Exceptional Domain Authority", "Description": f"{p} is exceptionally strong in a foundational angle ({p_houses[p]}th House). You are mathematically destined to be a recognized authority."})
    
    lord_9 = RASI_RULERS[(lagna_rasi + 8) % 12 or 12]
    lord_10 = RASI_RULERS[(lagna_rasi + 9) % 12 or 12]
    if p_pos.get(lord_9) == p_pos.get(lord_10) and lord_9 != lord_10:
        if lang == "Tamil": yogas.append({"Name": "தர்ம கர்மாதிபதி யோகம்", "Type": "உயர்ந்த தொழில் அந்தஸ்து", "Description": "உங்களின் 9-ஆம் அதிபதியும் 10-ஆம் அதிபதியும் இணைந்திருப்பதால் இந்த யோகம் அமைகிறது."})
        else: yogas.append({"Name": "Dharma Karmadhipati Yoga", "Type": "Ultimate Career Destiny", "Description": f"The rulers of your 9th House of Luck and 10th House of Career are united."})
    
    if not yogas:
        if lang == "Tamil": yogas.append({"Name": "சுயமுயற்சி யோகம்", "Type": "சுயம்புவான வெற்றி", "Description": "உங்கள் வெற்றி முற்றிலும் உங்கள் சுயமுயற்சியாலும், விடாமுயற்சியாலும் மட்டுமே அமையும்."})
        else: yogas.append({"Name": "Independent Karma Yoga", "Type": "Self-Made Destiny", "Description": "Your success is generated purely through active free-will and executing specific strategies."})
    
    return yogas

def analyze_education(p_pos, lagna_rasi, lang="English"):
    analysis = []
    lord_5 = RASI_RULERS[(lagna_rasi + 4) % 12 or 12]
    mercury_dig = get_dignity("Mercury", p_pos["Mercury"])
    
    if lang == "Tamil":
        analysis.append("#### கல்வி மற்றும் கற்றல் திறன்")
        analysis.append(f"உங்கள் கல்வி மற்றும் அறிவாற்றலை 5-ஆம் அதிபதியான {t_p[lord_5]} தீர்மானிக்கிறார்.")
        if mercury_dig in ["Exalted", "Own"]: analysis.append("புதன் மிகவும் வலுவாக இருப்பதால், சிக்கலான தரவுகளைப் பகுப்பாய்வு செய்யும் அபார திறன் உங்களுக்கு உண்டு.")
        elif mercury_dig == "Neecha": analysis.append("புதன் பலவீனமாக இருப்பதால், வெறும் மனப்பாடம் செய்வதை விட, உள்ளுணர்வு மூலம் நீங்கள் அதிகம் கற்கிறீர்கள்.")
        else: analysis.append("உங்களின் தர்க்க அறிவும், கற்கும் திறனும் சீராக உள்ளது.")
    else:
        analysis.append("#### Academic Profile & Learning Style")
        analysis.append(f"Your primary intellect and academic capacity are governed by the 5th House lord, {lord_5}.")
        if mercury_dig in ["Exalted", "Own"]: analysis.append(f"Because Mercury is highly dignified, your capacity to process complex data is elite.")
        elif mercury_dig == "Neecha": analysis.append("Your Mercury is mathematically debilitated, meaning you possess highly intuitive, abstract intelligence.")
        else: analysis.append("Your logical processing is balanced.")
    return analysis

def analyze_health(p_pos, lagna_rasi, lang="English"):
    analysis = []
    lagna_lord = RASI_RULERS[lagna_rasi]
    ll_dig = get_dignity(lagna_lord, p_pos[lagna_lord])
    lord_6 = RASI_RULERS[(lagna_rasi + 5) % 12 or 12]
    
    if lang == "Tamil":
        analysis.append("#### அடிப்படை உடல் வலிமை")
        if ll_dig in ["Exalted", "Own"]: analysis.append(f"லக்னாதிபதி ({t_p[lagna_lord]}) மிகவும் வலுவாக உள்ளார். இது உங்களுக்கு இரும்பு போன்ற உடல் வலிமையைத் தரும்.")
        elif ll_dig == "Neecha": analysis.append(f"லக்னாதிபதி ({t_p[lagna_lord]}) பலவீனமாக உள்ளார். உங்கள் உடல் சக்தியை நீங்கள் கவனமாக கையாள வேண்டும்.")
        else: analysis.append(f"லக்னாதிபதி ({t_p[lagna_lord]}) சமநிலையில் உள்ளார்.")
    else:
        analysis.append("#### Core Physical Resilience")
        if ll_dig in ["Exalted", "Own"]: analysis.append(f"Your Ascendant Lord ({lagna_lord}) is exceptionally strong, granting you a robust physical constitution.")
        elif ll_dig == "Neecha": analysis.append(f"Your Ascendant Lord ({lagna_lord}) is weak by sign placement. Your physical energy is finite.")
        else: analysis.append(f"Your Ascendant Lord ({lagna_lord}) is in a neutral state.")
    return analysis

def analyze_love_marriage(d1_lagna, d9_lagna, p_d9, p_d1, lang="English"):
    analysis = []
    lord_5 = RASI_RULERS[(d1_lagna + 4) % 12 or 12]
    d9_7th_lord = RASI_RULERS[(d9_lagna + 6) % 12 or 12]
    
    if lang == "Tamil":
        analysis.append("#### காதல் மற்றும் திருமண வாழ்க்கை")
        analysis.append(f"உங்கள் காதல் உணர்வுகள் 5-ஆம் அதிபதியான {t_p[lord_5]} ஆல் ஆளப்படுகிறது.")
        analysis.append(f"உங்கள் நிரந்தர திருமண வாழ்க்கை நவாம்சத்தின் 7-ஆம் அதிபதியான {t_p[d9_7th_lord]} இன் குணங்களைச் சார்ந்திருக்கும்.")
    else:
        analysis.append("#### The Dating Phase vs. The Marriage Phase")
        analysis.append(f"Your approach to early romance (5th House) is governed by {lord_5}.")
        analysis.append(f"The 7th House of your Navamsa (D9) reveals your ultimate spousal archetype. It is ruled by {d9_7th_lord}.")
    return analysis

def analyze_career_professional(p_pos, d10_lagna, lagna_rasi, sav_scores, bhava_placements, lang="English"):
    analysis = []
    sun_rasi_h = (p_pos['Sun'] - lagna_rasi + 1) if (p_pos['Sun'] - lagna_rasi + 1) > 0 else (p_pos['Sun'] - lagna_rasi + 1) + 12
    sun_bhava_h = bhava_placements['Sun'] 
    
    if lang == "Tamil":
        analysis.append("#### பாவ சலித் பகுப்பாய்வு (சூட்சுமம்)")
        if sun_rasi_h != sun_bhava_h: analysis.append(f"முக்கிய மாற்றம்: உங்கள் சூரியன் {sun_rasi_h}-ஆம் ராசியில் இருந்தாலும், அது {sun_bhava_h}-ஆம் பாவத்திலேயே முழுமையாகச் செயல்படுகிறது.")
        else: analysis.append(f"நேரடி பலன்: உங்கள் சூரியன் {sun_rasi_h}-ஆம் ராசியிலும் பாவத்திலும் சரியாகப் பொருந்தி செயல்படுகிறார்.")
    else:
        analysis.append("#### Bhava Chalit Analysis (The Nuance)")
        if sun_rasi_h != sun_bhava_h: analysis.append(f"Crucial Shift: Your Sun is in the {sun_rasi_h}th Sign, but effectively works in the {sun_bhava_h}th House.")
        else: analysis.append(f"Direct Impact: Your Sun aligns perfectly in Sign and House ({sun_rasi_h}th).")
    return analysis

def get_transit_positions(f_year):
    jd = swe.julday(f_year, 1, 1, 12.0)
    return {"Saturn": int(swe.calc_ut(jd, swe.SATURN, swe.FLG_SIDEREAL)[0][0] / 30) + 1, "Jupiter": int(swe.calc_ut(jd, swe.JUPITER, swe.FLG_SIDEREAL)[0][0] / 30) + 1, "Rahu": int(swe.calc_ut(jd, swe.MEAN_NODE, swe.FLG_SIDEREAL)[0][0] / 30) + 1}

def generate_annual_forecast(moon_rasi, sav_scores, f_year, age, lang="English"):
    transits = get_transit_positions(f_year)
    sat_dist = (transits["Saturn"] - moon_rasi + 1) if (transits["Saturn"] - moon_rasi + 1) > 0 else (transits["Saturn"] - moon_rasi + 1) + 12
    career_score = sav_scores[(lagna_rasi + 8) % 12] if 'lagna_rasi' in locals() else 28 # Safe fallback
    fc = {}
    
    if lang == "Tamil":
        if sat_dist in [3, 6, 11]: fc['தொழில் (Career)'] = ("மிகப்பெரிய வளர்ச்சி நிலை.", "சனிக்கிழமைகளில் நல்லெண்ணெய் தீபம் ஏற்றவும்.")
        else: fc['தொழில் (Career)'] = ("சீரான நிலை.", "பணியிடத்தை எப்போதும் சுத்தமாக வைத்திருக்கவும்.")
    else:
        if sat_dist in [3, 6, 11]: fc['Career'] = ("EXCELLENT GROWTH PHASE.", "Light a lamp with sesame oil on Saturdays.")
        else: fc['Career'] = ("STEADY PROGRESS.", "Keep your workspace completely decluttered.")
    return fc

def get_next_transit_date(planet_id, current_rasi, start_date):
    search_date = start_date
    for _ in range(1200):
        search_date += timedelta(days=2)
        jd = swe.julday(search_date.year, search_date.month, search_date.day, 12.0)
        new_rasi = int(swe.calc_ut(jd, planet_id, swe.FLG_SIDEREAL)[0][0] / 30) + 1
        if new_rasi != current_rasi: return search_date.strftime("%d %b %Y"), new_rasi
    return "Long Term", current_rasi

def get_transit_data_advanced(f_year):
    jd = swe.julday(f_year, 1, 1, 12.0)
    current_date = datetime(f_year, 1, 1)
    data = {}
    for p_name, p_id in [("Saturn", swe.SATURN), ("Jupiter", swe.JUPITER), ("Rahu", swe.MEAN_NODE)]:
        curr_rasi = int(swe.calc_ut(jd, p_id, swe.FLG_SIDEREAL)[0][0] / 30) + 1
        next_date, next_sign_idx = get_next_transit_date(p_id, curr_rasi, current_date)
        data[p_name] = {"Rasi": curr_rasi, "NextDate": next_date, "NextSignIdx": next_sign_idx}
    return data

def get_micro_transits(f_year, p_lon_absolute, lang="English"):
    return []

def generate_mahadasha_table(moon_lon, birth_date, lang="English"):
    nak_idx = int(moon_lon / 13.333333333)
    bal = 1 - ((moon_lon % 13.333333333) / 13.333333333)
    curr_date = birth_date
    first_lord = DASHA_ORDER[nak_idx % 9]
    first_end = curr_date + timedelta(days=DASHA_YEARS[first_lord] * bal * 365.25)
    timeline = [{"Age (From-To)": f"0 - {int((first_end - birth_date).days/365.25)}", "Years": f"{curr_date.year} - {first_end.year}", "Mahadasha": t_p.get(first_lord, first_lord) if lang=="Tamil" else first_lord, "Prediction": "Starting Phase"}]
    return timeline

def generate_current_next_bhukti(moon_lon, birth_date, planet_bhava_map, lang="English"):
    return [], {"Start": "Today", "End": "Future", "PD": "Mars", "MD": "Jupiter", "AD": "Venus"}
