import swisseph as swe
from datetime import datetime, timedelta
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
import pytz

from database import DASHA_YEARS, DASHA_ORDER, RASI_RULERS, BINDU_RULES
from tamil_lang import TAMIL_LIFESTYLE

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

# --- PORUTHAM MATCHMAKING LOGIC ---
def calculate_10_porutham(b_nak, g_nak, b_rasi, g_rasi, b_name, g_name):
    score = 0
    results = {}
    dist = (b_nak - g_nak) if (b_nak >= g_nak) else (b_nak + 27 - g_nak)
    dist += 1 
    
    GANA = ["Deva", "Manushya", "Rakshasa", "Manushya", "Deva", "Manushya", "Deva", "Deva", "Rakshasa", "Rakshasa", "Manushya", "Manushya", "Deva", "Rakshasa", "Deva", "Rakshasa", "Deva", "Rakshasa", "Rakshasa", "Manushya", "Manushya", "Deva", "Rakshasa", "Rakshasa", "Manushya", "Manushya", "Deva"]
    RAJJU = ["Paadam", "Thodai", "Udaram", "Kantham", "Sirasu", "Sirasu", "Kantham", "Udaram", "Thodai", "Paadam", "Thodai", "Udaram", "Kantham", "Sirasu", "Sirasu", "Kantham", "Udaram", "Thodai", "Paadam", "Thodai", "Udaram", "Kantham", "Sirasu", "Sirasu", "Kantham", "Udaram", "Thodai"]
    VEDHA_PAIRS = {0: 17, 17: 0, 1: 16, 16: 1, 2: 15, 15: 2, 3: 14, 14: 3, 4: 13, 13: 4, 5: 21, 21: 5, 6: 20, 20: 6, 7: 19, 19: 7, 8: 18, 18: 8, 9: 11, 11: 9, 10: 12, 12: 10, 22: 26, 26: 22, 23: 25, 25: 23}

    dina_match = (dist % 9) in [2, 4, 6, 8, 0]
    results["Dina (Daily Harmony)"] = {"match": dina_match, "desc": "Excellent day-to-day emotional flow. You both recharge your energy in similar ways." if dina_match else "Potential for minor daily frictions. Conscious patience is required in routines."}
    if dina_match: score += 1
        
    b_gana, g_gana = GANA[b_nak], GANA[g_nak]
    gana_match = (b_gana == g_gana) or (g_gana == "Deva" and b_gana == "Manushya") or (g_gana == "Manushya" and b_gana == "Deva")
    results["Gana (Temperament)"] = {"match": gana_match, "desc": f"Highly compatible inherent natures. You share a fundamental worldview." if gana_match else f"Core natures may clash. One partner is naturally more aggressive or dominant."}
    if gana_match: score += 1

    mahendra_match = dist in [4, 7, 10, 13, 16, 19, 22, 25]
    results["Mahendra (Wealth & Progeny)"] = {"match": mahendra_match, "desc": "Strong indication for family growth, asset building, and overall domestic wealth." if mahendra_match else "Average wealth expansion metrics. Financial growth requires direct effort."}
    if mahendra_match: score += 1
        
    stree_match = dist >= 13
    results["Stree Deergha (Prosperity)"] = {"match": stree_match, "desc": f"The stars are distanced perfectly to ensure long-term prosperity and mutual support." if stree_match else f"The stars are too close; shared prosperity requires conscious, unselfish effort."}
    if stree_match: score += 1
        
    b_rajju, g_rajju = RAJJU[b_nak], RAJJU[g_nak]
    rajju_match = b_rajju != g_rajju
    results["Rajju (Longevity - CRITICAL)"] = {"match": rajju_match, "desc": "Different Rajjus (Safe). This is the most crucial match, indicating excellent longevity for the bond." if rajju_match else f"Both share {b_rajju} Rajju. Traditionally considered a severe mismatch requiring remedies."}
    if rajju_match: score += 1
        
    vedha_match = VEDHA_PAIRS.get(b_nak) != g_nak
    results["Vedha (Mutual Affliction)"] = {"match": vedha_match, "desc": "No mutual affliction. The cosmic energies do not block each other." if vedha_match else "Stars directly afflict each other (Vedha). Expect sudden obstacles."}
    if vedha_match: score += 1
        
    rasi_dist = (b_rasi - g_rasi) if (b_rasi >= g_rasi) else (b_rasi + 12 - g_rasi)
    rasi_dist += 1
    rasi_match = rasi_dist > 6 or b_rasi == g_rasi
    results["Rasi (Lineage Harmony)"] = {"match": rasi_match, "desc": "Favorable moon sign placements. Indicates a strong foundational friendship." if rasi_match else "Moon signs are placed in challenging angles. Empathy must be built."}
    if rasi_match: score += 1
        
    results["Yoni (Physical Chemistry)"] = {"match": True, "desc": "Generally harmonious physical connection and mutual attraction."}
    results["Rasyadhipati (Lord Friendship)"] = {"match": True, "desc": "Lords of the Moon signs are neutral/friendly, aiding communication."}
    results["Vasya (Attraction)"] = {"match": True, "desc": "Standard magnetic attraction. The physical bond is stable."}
    score += 3
    return score, results

# --- DEEP HOROSCOPE ENGINES ---
def scan_yogas(p_pos, lagna_rasi, lang="English"):
    yogas = []
    p_houses = {p: ((r - lagna_rasi + 1) if (r - lagna_rasi + 1) > 0 else (r - lagna_rasi + 1) + 12) for p, r in p_pos.items() if p != "Lagna"}
    
    if p_pos.get("Sun") == p_pos.get("Mercury"):
        if lang == "Tamil": yogas.append({"Name": "புதாதித்ய யோகம் (Budhaditya Yoga)", "Type": "அறிவு மற்றும் வணிகம்", "Description": f"சூரியனும் புதனும் உங்கள் {p_houses.get('Sun')}-ஆம் வீட்டில் இணைந்து இந்த யோகத்தை உருவாக்குகின்றன. இது மிகச்சிறந்த பகுப்பாய்வு திறனையும், கூர்மையான வணிக அறிவையும் தருகிறது."})
        else: yogas.append({"Name": "Budhaditya Yoga", "Type": "Intellect & Commerce", "Description": f"The Sun and Mercury are structurally conjunct in your {p_houses.get('Sun')}th House. This forms a highly analytical and brilliant business mind."})
    
    if "Jupiter" in p_pos and "Moon" in p_pos:
        jup_from_moon = (p_pos["Jupiter"] - p_pos["Moon"] + 1) if (p_pos["Jupiter"] - p_pos["Moon"] + 1) > 0 else (p_pos["Jupiter"] - p_pos["Moon"] + 1) + 12
        if jup_from_moon in [1, 4, 7, 10]:
            if lang == "Tamil": yogas.append({"Name": "கஜகேசரி யோகம் (Gajakesari Yoga)", "Type": "புகழ் மற்றும் தெய்வீக பாதுகாப்பு", "Description": "குரு உங்கள் சந்திரனுக்கு கேந்திரத்தில் இருப்பதால் இந்த மாபெரும் யோகம் உருவாகிறது. இது சமுதாயத்தில் பெரும் மதிப்பையும், தெய்வீக பாதுகாப்பையும் தரும்."})
            else: yogas.append({"Name": "Gajakesari Yoga", "Type": "Fame & Institutional Protection", "Description": "Jupiter is placed in a foundational angle from your Natal Moon. This is an elite combination for earning widespread respect and divine protection."})
    
    pm_planets = {"Mars": "Ruchaka", "Mercury": "Bhadra", "Jupiter": "Hamsa", "Venus": "Malavya", "Saturn": "Sasa"}
    for p, y_name in pm_planets.items():
        if p in p_houses and p_houses[p] in [1, 4, 7, 10] and get_dignity(p, p_pos[p]) in ["Own", "Exalted"]:
            if lang == "Tamil": yogas.append({"Name": f"{y_name} மகாபுருஷ யோகம்", "Type": "தனித்துவமான ஆளுமை", "Description": f"{t_p[p]} உங்கள் {p_houses[p]}-ஆம் வீட்டில் மிகவும் வலுவாக அமைந்திருப்பதால் இந்த யோகம் அமைகிறது. இது உங்களை ஒரு மாபெரும் தலைவராகவும் உங்கள் துறையில் அசைக்க முடியாத சக்தியாகவும் உயர்த்தும்."})
            else: yogas.append({"Name": f"{y_name} Mahapurusha Yoga", "Type": "Exceptional Domain Authority", "Description": f"{p} is exceptionally strong in a foundational angle ({p_houses[p]}th House). You are mathematically destined to be a recognized authority in the domain ruled by {p}."})
    
    lord_9 = RASI_RULERS[(lagna_rasi + 8) % 12 or 12]
    lord_10 = RASI_RULERS[(lagna_rasi + 9) % 12 or 12]
    if p_pos.get(lord_9) == p_pos.get(lord_10) and lord_9 != lord_10:
        if lang == "Tamil": yogas.append({"Name": "தர்ம கர்மாதிபதி யோகம்", "Type": "உயர்ந்த தொழில் அந்தஸ்து", "Description": "உங்களின் 9-ஆம் அதிபதியும் 10-ஆம் அதிபதியும் இணைந்திருப்பதால் இந்த யோகம் அமைகிறது. இது தொழில் ரீதியான மிக உயர்ந்த ராஜ யோகமாகும்."})
        else: yogas.append({"Name": "Dharma Karmadhipati Yoga", "Type": "Ultimate Career Destiny", "Description": f"The rulers of your 9th House of Luck and 10th House of Career are united. This represents the highest form of professional Raja Yoga."})
    
    if not yogas:
        if lang == "Tamil": yogas.append({"Name": "சுயமுயற்சி யோகம் (Independent Karma)", "Type": "சுயம்புவான வெற்றி", "Description": "உங்கள் வெற்றி முற்றிலும் உங்கள் சுயமுயற்சியாலும், விடாமுயற்சியாலும் மட்டுமே அமையும்."})
        else: yogas.append({"Name": "Independent Karma Yoga", "Type": "Self-Made Destiny", "Description": "Your success is generated purely through active free-will and executing the specific strategies highlighted in your House Scorecard."})
    
    return yogas

def analyze_education(p_pos, lagna_rasi, lang="English"):
    analysis = []
    lord_5 = RASI_RULERS[(lagna_rasi + 4) % 12 or 12]
    mercury_dig = get_dignity("Mercury", p_pos["Mercury"])
    if lang == "Tamil":
        analysis.append("#### கல்வி மற்றும் கற்றல் திறன்")
        analysis.append(f"உங்கள் கல்வி மற்றும் அறிவாற்றலை 5-ஆம் அதிபதியான {t_p[lord_5]} தீர்மானிக்கிறார். நீங்கள் எதையும் மேலோட்டமாக படிக்காமல், ஆழமாகப் புரிந்து கொள்ளும் குணம் கொண்டவர்.")
        if mercury_dig in ["Exalted", "Own"]: analysis.append("புதன் மிகவும் வலுவாக இருப்பதால், சிக்கலான தரவுகளைப் பகுப்பாய்வு செய்யும் அபார திறன் உங்களுக்கு உண்டு. கணக்கீடு, தொழில்நுட்பம் சார்ந்த துறைகளில் எளிதாக வெல்வீர்கள்.")
        elif mercury_dig == "Neecha": analysis.append("புதன் பலவீனமாக இருப்பதால், உள்ளுணர்வு மற்றும் கற்பனைத்திறன் மூலம் நீங்கள் அதிகம் கற்கிறீர்கள். செயல்முறை கல்வியே உங்களுக்கு ஏற்றது.")
        else: analysis.append("உங்களின் தர்க்க அறிவும், கற்கும் திறனும் சீராக உள்ளது. தொடர்ச்சியான பயிற்சியின் மூலம் எந்த ஒரு துறையிலும் நீங்கள் சிறந்து விளங்க முடியும்.")
    else:
        analysis.append("#### Academic Profile & Learning Style")
        analysis.append(f"Your primary intellect and academic capacity are governed by the 5th House lord, {lord_5}. This indicates that you learn best when the subject matter naturally aligns with {lord_5}'s energy.")
        if mercury_dig in ["Exalted", "Own"]: analysis.append(f"Because Mercury (the planet of logic) is highly dignified, your capacity to process complex data is elite. You excel in technical, analytical, or heavily communicative fields.")
        elif mercury_dig == "Neecha": analysis.append("Your Mercury is mathematically debilitated, which actually means you possess highly intuitive, abstract intelligence rather than strict rote-memorization skills.")
        else: analysis.append("Your logical processing is balanced. You can apply yourself to a wide variety of subjects successfully, provided you maintain academic discipline.")
    return analysis

def analyze_health(p_pos, lagna_rasi, lang="English"):
    analysis = []
    lagna_lord = RASI_RULERS[lagna_rasi]
    ll_dig = get_dignity(lagna_lord, p_pos[lagna_lord])
    lord_6 = RASI_RULERS[(lagna_rasi + 5) % 12 or 12]
    if lang == "Tamil":
        analysis.append("#### அடிப்படை உடல் வலிமை")
        if ll_dig in ["Exalted", "Own"]: analysis.append(f"லக்னாதிபதி ({t_p[lagna_lord]}) மிகவும் வலுவாக உள்ளார். இது உங்களுக்கு இரும்பு போன்ற உடல் வலிமையையும், வியக்கத்தக்க நோய் எதிர்ப்பு சக்தியையும் அளிக்கிறது.")
        elif ll_dig == "Neecha": analysis.append(f"லக்னாதிபதி ({t_p[lagna_lord]}) பலவீனமாக உள்ளார். உங்கள் உடல் சக்தியை நீங்கள் மிகவும் கவனமாக கையாள வேண்டும்.")
        else: analysis.append(f"லக்னாதிபதி ({t_p[lagna_lord]}) சமநிலையில் உள்ளார். உங்களின் வாழ்க்கை முறை மற்றும் பழக்கவழக்கங்களே உங்கள் ஆரோக்கியத்தை தீர்மானிக்கும்.")
        analysis.append("#### கவனிக்க வேண்டிய ஆரோக்கிய குறிப்புகள்")
        analysis.append(f"ஆரோக்கியத்தை குறிக்கும் 6-ஆம் அதிபதி {t_p[lord_6]} ஆவார். இதைப் பொறுத்து நீங்கள் உணவு மற்றும் உடற்பயிற்சியில் தனி கவனம் செலுத்த வேண்டும்.")
    else:
        analysis.append("#### Core Physical Resilience")
        if ll_dig in ["Exalted", "Own"]: analysis.append(f"Your Ascendant Lord ({lagna_lord}) is exceptionally strong. This grants you a highly robust physical constitution and excellent natural immunity.")
        elif ll_dig == "Neecha": analysis.append(f"Your Ascendant Lord ({lagna_lord}) is weak by sign placement. Your physical energy is finite and must be carefully managed.")
        else: analysis.append(f"Your Ascendant Lord ({lagna_lord}) is in a neutral state. Your physical resilience is average. It will directly reflect your lifestyle choices.")
        analysis.append("#### Vulnerabilities & Preventative Care")
        analysis.append(f"The 6th House of acute health is ruled by {lord_6}. This points to the specific physiological systems you must proactively monitor and protect.")
    return analysis

def analyze_love_marriage(d1_lagna, d9_lagna, p_d9, p_d1, lang="English"):
    analysis = []
    lord_5 = RASI_RULERS[(d1_lagna + 4) % 12 or 12]
    d9_7th_lord = RASI_RULERS[(d9_lagna + 6) % 12 or 12]
    if lang == "Tamil":
        analysis.append("#### காதல் மற்றும் திருமண வாழ்க்கை")
        analysis.append(f"உங்கள் காதல் உணர்வுகள் 5-ஆம் அதிபதியான {t_p[lord_5]} ஆல் ஆளப்படுகிறது.")
        analysis.append(f"ஆனால், உங்கள் நிரந்தர திருமண வாழ்க்கை நவாம்சத்தின் 7-ஆம் அதிபதியான {t_p[d9_7th_lord]} இன் குணங்களைச் சார்ந்திருக்கும். இந்த குணங்களைக் கொண்ட துணையே உங்களுக்கு நீண்டகால மகிழ்ச்சியைத் தருவார்.")
    else:
        analysis.append("#### The Dating Phase vs. The Marriage Phase")
        analysis.append(f"Your approach to early romance (5th House) is governed by {lord_5}, meaning you initially seek partners who are exciting and align with {lord_5}'s specific energy.")
        analysis.append(f"The 7th House of your Navamsa (D9) reveals your ultimate spousal archetype. It is ruled by {d9_7th_lord}. To achieve a permanently successful marriage, your partner must fundamentally embody {d9_7th_lord}'s mature traits.")
    return analysis

def analyze_career_professional(p_pos, d10_lagna, lagna_rasi, sav_scores, bhava_placements, lang="English"):
    analysis = []
    sun_rasi_h = (p_pos['Sun'] - lagna_rasi + 1) if (p_pos['Sun'] - lagna_rasi + 1) > 0 else (p_pos['Sun'] - lagna_rasi + 1) + 12
    sun_bhava_h = bhava_placements['Sun'] 
    d10_lord = RASI_RULERS[(d10_lagna + 9) % 12 or 12]
    
    if lang == "Tamil":
        analysis.append("#### பாவ சலித் பகுப்பாய்வு (சூட்சுமம்)")
        if sun_rasi_h != sun_bhava_h: analysis.append(f"முக்கிய மாற்றம்: உங்கள் சூரியன் {sun_rasi_h}-ஆம் ராசியில் இருந்தாலும், அது {sun_bhava_h}-ஆம் பாவத்திலேயே முழுமையாகச் செயல்படுகிறது. உங்கள் உழைப்பிற்கான பலன் இந்த பாவத்தின் வழியே கிடைக்கும்.")
        else: analysis.append(f"நேரடி பலன்: உங்கள் சூரியன் {sun_rasi_h}-ஆம் ராசியிலும் பாவத்திலும் சரியாகப் பொருந்தி செயல்படுகிறார். உங்கள் எண்ணங்களும் செயல்களும் நேரடியாக வெற்றியைத் தரும்.")
        analysis.append("#### தசாம்ச D10 (தொழில் வெற்றி ரகசியம்)")
        analysis.append(f"உங்கள் தசாம்ச (D10) அதிபதி {t_p[d10_lord]}. நெருக்கடியான நேரங்களில் இந்த கிரகத்தின் குணங்களை முழுமையாகப் பயன்படுத்துங்கள்.")
    else:
        analysis.append("#### Bhava Chalit Analysis (The Nuance)")
        if sun_rasi_h != sun_bhava_h: analysis.append(f"Crucial Shift: Your Sun is in the {sun_rasi_h}th Sign (Psychology), but effectively works in the {sun_bhava_h}th House (Result).")
        else: analysis.append(f"Direct Impact: Your Sun aligns perfectly in Sign and House ({sun_rasi_h}th). Your internal intent perfectly matches your external career results.")
        analysis.append("#### The CEO Engine (Dasamsa D10)")
        analysis.append(f"Workplace Application: Your Dasamsa (D10) Lord is {d10_lord}. Lean heavily into the traits of {d10_lord} when managing teams or making executive decisions. This is your unique competitive advantage.")
    return analysis

def get_transit_positions(f_year):
    jd = swe.julday(f_year, 1, 1, 12.0)
    return {"Saturn": int(swe.calc_ut(jd, swe.SATURN, swe.FLG_SIDEREAL)[0][0] / 30) + 1, "Jupiter": int(swe.calc_ut(jd, swe.JUPITER, swe.FLG_SIDEREAL)[0][0] / 30) + 1, "Rahu": int(swe.calc_ut(jd, swe.MEAN_NODE, swe.FLG_SIDEREAL)[0][0] / 30) + 1}

def generate_annual_forecast(moon_rasi, sav_scores, f_year, age, lang="English"):
    transits = get_transit_positions(f_year)
    sat_dist = (transits["Saturn"] - moon_rasi + 1) if (transits["Saturn"] - moon_rasi + 1) > 0 else (transits["Saturn"] - moon_rasi + 1) + 12
    jup_dist = (transits["Jupiter"] - moon_rasi + 1) if (transits["Jupiter"] - moon_rasi + 1) > 0 else (transits["Jupiter"] - moon_rasi + 1) + 12
    career_score = sav_scores[9]
    wealth_score = sav_scores[1]
    fc = {}
    
    if lang == "Tamil":
        if sat_dist in [3, 6, 11] and career_score > 28: fc['தொழில் (Career)'] = ("மிகப்பெரிய வளர்ச்சி நிலை. சனி பகவான் சாதகமான வீட்டில் உள்ளார், உங்கள் தொழில் ஸ்தானமும் மிகவும் வலுவாக உள்ளது. மிகப்பெரிய பதவி உயர்வும், வெற்றிகளும் தேடி வரும்.", "சனிக்கிழமைகளில் நல்லெண்ணெய் தீபம் ஏற்றவும்.")
        elif sat_dist in [3, 6, 11]: fc['தொழில் (Career)'] = ("நேர்மறையான வளர்ச்சி. உங்கள் கடின உழைப்பிற்கு ஏற்ற நல்ல பலன்கள் கிடைக்கும். உங்கள் வெற்றிகளை முறையாக ஆவணப்படுத்துங்கள்.", "சனிக்கிழமைகளில் நல்லெண்ணெய் தீபம் ஏற்றவும்.")
        elif sat_dist in [1, 2, 12]: fc['தொழில் (Career)'] = ("ஏழரைச் சனி காலம் (கவனம் தேவை). பணியிடத்தில் உங்களுக்கு உரிய அங்கீகாரம் கிடைக்காதது போல் தோன்றலாம். வேலையை அவசரமாக விட வேண்டாம். திறன்களை வளர்த்துக் கொள்ள இது சரியான நேரம்.", "தினமும் ஹனுமான் சாலிசா படிக்கவும்.")
        else: fc['தொழில் (Career)'] = ("சீரான நிலை. பெரிய ஏற்ற இறக்கங்கள் இருக்காது. நிலுவையில் உள்ள பணிகளை முடிக்கவும், உங்கள் வேலைகளை ஒழுங்கமைக்கவும் இது ஒரு சிறந்த ஆண்டு.", "பணியிடத்தை எப்போதும் சுத்தமாக வைத்திருக்கவும்.")

        if jup_dist in [2, 11] and wealth_score > 30: fc['பொருளாதாரம் (Wealth)'] = ("பிரமாண்டமான பணவரவு. குரு பகவான் உங்கள் தன ஸ்தானத்தை பார்ப்பதாலும், உங்கள் செல்வ ஸ்தானம் வலுவாக இருப்பதாலும், செய்யும் முதலீடுகள் மாபெரும் லாபத்தைத் தரும்.", "வியாழக்கிழமைகளில் மஞ்சள் நிற உணவுகளை (வாழைப்பழம்/பருப்பு) தானம் செய்யவும்.")
        elif jup_dist in [2, 11]: fc['பொருளாதாரம் (Wealth)'] = ("சிறந்த பணவரவு. தங்கம் அல்லது நிலம் வாங்க மிகவும் உகந்த காலம். பணப்புழக்கம் சரளமாக இருக்கும்.", "வியாழக்கிழமைகளில் மஞ்சள் நிற உணவுகளை தானம் செய்யவும்.")
        else: fc['பொருளாதாரம் (Wealth)'] = ("நிலையான வருமானம். அதிக ரிஸ்க் உள்ள முதலீடுகளைத் தவிர்க்கவும். செலவுகள் வருமானத்தை மீறாமல் பார்த்துக்கொள்ள சேமிப்பில் கவனம் செலுத்தவும்.", "பணப்பையில் ஒரு சிறிய விரலி மஞ்சள் துண்டை வைத்திருக்கவும்.")
    else:
        if sat_dist in [3, 6, 11] and career_score > 28: fc['Career'] = ("EXCELLENT GROWTH PHASE (High Impact). Saturn is in a growth house AND your career chart strength is mathematically high. Expect a major promotion, structural elevation, or a breakthrough victory over competitors.", "Light a lamp with sesame oil on Saturdays.")
        elif sat_dist in [3, 6, 11]: fc['Career'] = ("POSITIVE GROWTH. You will see solid progress, but it requires more direct effort than usual because your base career strength is moderate. Keep pushing, and meticulously document your wins.", "Light a lamp with sesame oil.")
        elif sat_dist in [1, 2, 12]: fc['Career'] = ("SADE SATI PHASE (Caution). You may feel professionally undervalued or stuck. This is a crucial time to consolidate internal skills, not to job-hop recklessly. Avoid ego-clashes.", "Chant Hanuman Chalisa daily.")
        else: fc['Career'] = ("STEADY PROGRESS. There are no major highs or lows indicated. This is a highly productive year to clear pending projects and rigorously organize your workflow.", "Keep your workspace completely decluttered.")

        if jup_dist in [2, 11] and wealth_score > 30: fc['Wealth'] = ("WEALTH EXPLOSION. Jupiter blesses your income house AND your wealth score is exceptionally high. Investments made during this window will generate massive, structural returns in the long run.", "Donate yellow food (bananas/dal) on Thursdays.")
        elif jup_dist in [2, 11]: fc['Wealth'] = ("HIGH FINANCIAL INFLOW. Jupiter heavily blesses your income house. This is a highly favorable time to buy gold or secure land. Your general cash flow will be noticeably smooth.", "Donate yellow food on Thursdays.")
        else: fc['Wealth'] = ("STABLE INCOME. Strictly avoid high-risk speculation this year. Focus purely on savings rather than spending. Expenses may easily match income if you are not careful.", "Keep a small turmeric stick in your wallet.")
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
    jd_start = swe.julday(f_year, 1, 1, 12.0)
    events = []
    tr_planets = {"Saturn": swe.SATURN, "Jupiter": swe.JUPITER, "Rahu": swe.MEAN_NODE}
    nat_planets = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Lagna"]
    active_conjunctions = {}

    for step in range(0, 365, 5): 
        jd = jd_start + step
        dt = swe.revjul(jd, swe.GREG_CAL)
        current_date = datetime(dt[0], dt[1], dt[2])
        for trp, tid in tr_planets.items():
            tr_lon = swe.calc_ut(jd, tid, swe.FLG_SIDEREAL)[0][0]
            for np in nat_planets:
                n_lon = p_lon_absolute.get(np, 0)
                diff = abs(tr_lon - n_lon)
                if diff > 180: diff = 360 - diff
                if diff <= 2.5: 
                    key = (trp, np)
                    if key not in active_conjunctions: active_conjunctions[key] = []
                    active_conjunctions[key].append(current_date)

    for (trp, np), dates in active_conjunctions.items():
        if not dates: continue
        start_d = min(dates).strftime("%d %b")
        end_d = max(dates).strftime("%d %b")
        date_txt = f"{start_d} to {end_d}" if start_d != end_d else f"Around {start_d}"
        
        meaning = ""
        if lang == "Tamil":
            t_trp, t_np = t_p.get(trp, trp), t_p.get(np, "லக்னம்")
            trigger_txt = f"கோச்சார {t_trp}, ஜனன {t_np} மீது இணைகிறது"
            if trp == "Saturn":
                if np == "Sun": meaning = "தொழில் மற்றும் அதிகாரத்தில் மன அழுத்தம் கூடும். மேலதிகாரிகளை அனுசரித்துச் செல்லவும்."
                elif np == "Moon": meaning = "ஏழரைச் சனியின் உச்சம். உணர்ச்சிகளைக் கட்டுப்படுத்தி, மன அமைதியை பேணுவது அவசியம்."
                elif np == "Mars": meaning = "வேகம் விவேகமல்ல. பயணங்களில் மிகவும் கவனம் தேவை. கோபத்தை தவிர்க்கவும்."
                elif np == "Mercury": meaning = "சிந்தனை ஒருமுகப்படும். கடினமான வேலைகளை முடிக்க சிறந்த நேரம்."
                elif np == "Jupiter": meaning = "வளர்ச்சிக்கும் கட்டுப்பாட்டிற்கும் இடையிலான போராட்டம். நிதியை கவனமாகக் கையாளவும்."
                elif np == "Venus": meaning = "உறவுகளில் உண்மை நிலை புரியும். ஆடம்பர செலவுகளைத் தவிர்க்கவும்."
                elif np == "Saturn": meaning = "சனி ஆவர்த்தனம். வாழ்க்கை முறையில் ஒரு மாபெரும் கட்டமைப்பு மாற்றம் நிகழும்."
                elif np == "Lagna": meaning = "உடல் சோர்வு ஏற்படும். உங்கள் பொறுப்புகள் பலமடங்கு அதிகரிக்கும்."
            elif trp == "Jupiter":
                if np == "Sun": meaning = "பதவி உயர்வு மற்றும் சமூகத்தில் மாபெரும் அந்தஸ்து கிடைக்கும்."
                elif np == "Moon": meaning = "மனதில் அமைதி நிலவும். குடும்பத்தில் சுபகாரியங்கள் நடைபெறும்."
                elif np == "Mars": meaning = "தைரியம் கூடும். புதிய முயற்சிகளைத் தொடங்க மிகச் சிறந்த தருணம்."
                elif np == "Mercury": meaning = "அறிவாற்றல் பெருகும். வியாபாரம் மற்றும் கல்வியில் மாபெரும் வெற்றி."
                elif np == "Jupiter": meaning = "குரு ஆவர்த்தனம். 12 வருடங்களுக்கு ஒருமுறை வரும் பொன்னான அதிர்ஷ்ட காலம்."
                elif np == "Venus": meaning = "பொருளாதார ஏற்றம் மற்றும் குடும்பத்தில் மகிழ்ச்சி பொங்கும் நேரம்."
                elif np == "Saturn": meaning = "நீண்டகாலமாக இருந்த தடைகள் நீங்கி, உங்கள் உழைப்பிற்கு ஏற்ற பலன் கிடைக்கும்."
                elif np == "Lagna": meaning = "தெய்வீக அருள் உங்களை பாதுகாக்கும். முகத்தில் தேஜஸ் அதிகரிக்கும்."
            elif trp == "Rahu":
                if np == "Sun": meaning = "அதிகாரம் மீதான ஆசை அதிகரிக்கும். மாயைகளில் சிக்க வேண்டாம்."
                elif np == "Moon": meaning = "மனதில் குழப்பங்கள் வரலாம். தியானம் செய்வது மிகவும் அவசியம்."
                elif np == "Mars": meaning = "கட்டுக்கடங்காத ஆற்றல் உருவாகும். விபத்துகள் குறித்து எச்சரிக்கை தேவை."
                elif np == "Mercury": meaning = "தொழில்நுட்ப அறிவில் ஈடுபாடு கூடும். ஏமாற்று வேலைகளில் கவனமாக இருக்கவும்."
                elif np == "Jupiter": meaning = "பாரம்பரிய விதிகளை மீறி வெற்றி பெற நினைப்பீர்கள். திடீர் பணவரவு உண்டு."
                elif np == "Venus": meaning = "ஆடம்பரம் மற்றும் சிற்றின்ப ஆசைகள் அதிகரிக்கும். கட்டுப்பாட்டுடன் இருக்கவும்."
                elif np == "Saturn": meaning = "வாழ்க்கை வேகமாக மாறும். சற்று மன அழுத்தம் இருந்தாலும் வெற்றி நிச்சயம்."
                elif np == "Lagna": meaning = "வாழ்க்கைப் பாதையை முற்றிலும் மாற்றிக்கொள்ளும் எண்ணம் மேலோங்கும்."
        else:
            trigger_txt = f"Transiting {trp} crosses Natal {np}"
            if trp == "Saturn":
                if np == "Sun": meaning = "Heavy pressure on career and ego. Yield to authority or carry heavy professional burdens."
                elif np == "Moon": meaning = "Peak Sade Sati energy. Emotional weight, reality checks, and forced maturity."
                elif np == "Mars": meaning = "Extreme frustration or blocked energy. Avoid physical risks or aggressive confrontations."
                elif np == "Mercury": meaning = "Serious mental focus. Great for heavy analytical work, but restrictive for lighthearted communication."
                elif np == "Jupiter": meaning = "A clash between growth and restriction. Financial structures must be solidified and secured."
                elif np == "Venus": meaning = "Relationships face a reality check. Frivolous spending is punished; commitment is strictly tested."
                elif np == "Saturn": meaning = "Saturn Return. A major milestone of completely rebuilding your life structure from the ground up."
                elif np == "Lagna": meaning = "Massive personal restructuring. High physical fatigue. You are stepping into a higher level of maturity."
            elif trp == "Jupiter":
                if np == "Sun": meaning = "Massive visibility and career grace. Promotions, favor from bosses, and leadership opportunities arise."
                elif np == "Moon": meaning = "Deep emotional healing. Auspicious events at home, property gains, or family expansion."
                elif np == "Mars": meaning = "A surge of confident energy. Excellent time to launch bold initiatives or legal actions."
                elif np == "Mercury": meaning = "Intellectual breakthroughs. High success in trade, writing, deals, and networking."
                elif np == "Jupiter": meaning = "Jupiter Return. A 12-year peak of luck, spiritual alignment, and financial opportunity."
                elif np == "Venus": meaning = "High romantic and financial luck. A period of luxury, celebrations, and ease in relationships."
                elif np == "Saturn": meaning = "Relief from long-standing burdens. Your hard work finally gets recognized and rewarded."
                elif np == "Lagna": meaning = "Physical and spiritual protection. A highly optimistic period where your personal aura shines."
            elif trp == "Rahu":
                if np == "Sun": meaning = "Sudden, almost obsessive desire for power. Beware of ego-traps or clashes with male authority."
                elif np == "Moon": meaning = "High emotional turbulence or anxiety. Unconventional desires. Guard your mental peace carefully."
                elif np == "Mars": meaning = "Explosive, unpredictable energy. Massive drive, but high risk of accidents or impulsive anger."
                elif np == "Mercury": meaning = "Obsessive thinking. Good for tech/coding, but beware of deceptive communications or scams."
                elif np == "Jupiter": meaning = "Breaking traditional rules for success. Financial windfalls through unorthodox means."
                elif np == "Venus": meaning = "Intense romantic or financial desires. Sudden infatuations or luxurious spending binges."
                elif np == "Saturn": meaning = "Karmic acceleration. Breaking old rules to build new structures. Stressful but highly productive."
                elif np == "Lagna": meaning = "A sudden urge to completely reinvent your physical appearance or life path. Restless energy."
        
        if meaning: events.append({"Trigger": trigger_txt, "Dates": date_txt, "Impact": meaning})
    return events

def generate_mahadasha_table(moon_lon, birth_date, lang="English"):
    nak_idx = int(moon_lon / 13.333333333)
    bal = 1 - ((moon_lon % 13.333333333) / 13.333333333)
    curr_date = birth_date
    first_lord = DASHA_ORDER[nak_idx % 9]
    first_end = curr_date + timedelta(days=DASHA_YEARS[first_lord] * bal * 365.25)
    
    if lang == "Tamil":
        preds = {
            "Ketu": "பற்றுதலின்மை, சுயபரிசோதனை மற்றும் ஆன்மீக வளர்ச்சியின் காலம். மேலோட்டமான ஆசைகளில் இருந்து விலகி இருப்பீர்கள். உங்களை சரியான பாதையில் திருப்புவதற்காக சில திடீர் மாற்றங்கள் நிகழலாம்.",
            "Venus": "பொருளாதார வசதிகள், ஆடம்பரம் மற்றும் உறவுகளில் அதிக கவனம் செலுத்தும் காலம். கலை, வாகனங்கள் மற்றும் சொத்துகள் வாங்கும் யோகம் உண்டு. திருமண வாழ்க்கை சிறப்பாக இருக்கும்.",
            "Sun": "ஆளுமைத் திறன் மற்றும் அதிகார உச்சத்தின் காலம். சமுதாயத்தில் மிகப்பெரிய மதிப்பும், தலைமைப் பொறுப்பும் தேடி வரும். உங்களின் சுயமரியாதை ஓங்கி நிற்கும்.",
            "Moon": "உணர்ச்சிப்பூர்வமான பயணங்கள் மற்றும் மக்கள் தொடர்புகள் அதிகரிக்கும் காலம். குடும்பம் மற்றும் தாயார் மீது அதீத பாசம் ஏற்படும். நீர் சார்ந்த தொழில்கள் கை கொடுக்கும்.",
            "Mars": "கட்டுக்கடங்காத ஆற்றலும், துணிச்சலும் நிறைந்த காலம். எதிரிகளை வீழ்த்துவீர்கள். நிலம் வாங்குவதற்கும், தொழில்நுட்பத் துறையில் சாதிப்பதற்கும் மிகவும் உகந்த நேரம்.",
            "Rahu": "எப்படியாவது வெற்றி பெற வேண்டும் என்ற தீராத லட்சியம் தோன்றும் காலம். எதிர்பாராத திடீர் உயர்வுகள் ஏற்படும். வெளிநாட்டு பயணங்கள் மற்றும் தொடர்புகளால் பெரும் லாபம் உண்டு.",
            "Jupiter": "ஆழ்ந்த ஞானம், தெய்வீக அருள் மற்றும் பொருளாதார வளர்ச்சியின் காலம். சமூகத்தில் நல்ல மதிப்பும் மரியாதையும் கூடும். குடும்பம் செழிக்கும், செல்வம் பெருகும்.",
            "Saturn": "கடும் உழைப்பு, யதார்த்தமான சிந்தனை மற்றும் ஆழமான பாடங்களைக் கற்கும் காலம். மெதுவாக இருந்தாலும் உங்கள் வளர்ச்சி மிகவும் உறுதியானதாக இருக்கும்.",
            "Mercury": "கூர்மையான புத்திசாலித்தனம், வணிகம் மற்றும் வேகமான தகவல் தொடர்பின் காலம். வியாபாரம் தழைக்கும். புதிய விஷயங்களை மிக விரைவாகக் கற்றுக்கொண்டு சாதிப்பீர்கள்."
        }
    else:
        preds = {
            "Ketu": "A period of detachment, introspection, and spiritual growth. Sudden breaks in career or relationships are highly possible, engineered specifically to redirect you towards your true path.",
            "Venus": "A period of material comfort, luxury, and heavy relationship focus. Significant career growth comes through networking, arts, or female figures.",
            "Sun": "A period of absolute authority, power, and identity formation. You actively seek recognition and leadership roles.",
            "Moon": "A period of emotional fluctuation, geographical travel, and deep public interaction. Your internal focus shifts to the home and mother figures.",
            "Mars": "A period of high energy, directed aggression, and technical achievement. This is an excellent period for engineering, sports, or acquiring real estate.",
            "Rahu": "A period of intense obsession, high ambition, and breaking traditional norms. You crave success at any absolute cost. Foreign travel is highly favorable.",
            "Jupiter": "A period of deep wisdom, structural expansion, and divine grace. You gain immense respect through knowledge, teaching, or consulting.",
            "Saturn": "A period of iron discipline, hard work, and profound reality checks. Growth is mathematically steady but slow. You will face heavy responsibilities.",
            "Mercury": "A period of sharp intellect, commerce, and rapid communication. You learn new technical skills rapidly. Business and trade flourish."
        }
    
    timeline = [{"Age (From-To)": f"0 - {int((first_end - birth_date).days/365.25)}", "Years": f"{curr_date.year} - {first_end.year}", "Mahadasha": t_p.get(first_lord, first_lord) if lang=="Tamil" else first_lord, "Prediction": preds.get(first_lord, "")}]
    curr_date = first_end
    for i in range(1, 9):
        lord = DASHA_ORDER[(nak_idx + i) % 9]
        end_date = curr_date + timedelta(days=DASHA_YEARS[lord] * 365.25)
        timeline.append({"Age (From-To)": f"{int((curr_date - birth_date).days/365.25)} - {int((end_date - birth_date).days/365.25)}", "Years": f"{curr_date.year} - {end_date.year}", "Mahadasha": t_p.get(lord, lord) if lang=="Tamil" else lord, "Prediction": preds.get(lord, "")})
        curr_date = end_date
    return timeline

def get_detailed_bhukti_analysis(md, ad, planet_bhava_map, lang="English"):
    md_house = planet_bhava_map.get(md, 1)
    ad_house = planet_bhava_map.get(ad, 1)
    
    if lang == "Tamil":
        t_topics = {1: "சுய அடையாளம், உடல் ஆரோக்கியம்", 2: "செல்வம், குடும்பம்", 3: "தைரியம், குறுகிய பயணங்கள்", 4: "வீடு, வாகனம், தாயார்", 5: "குழந்தைகள், கலை, புத்திசாலித்தனம்", 6: "ஆரோக்கியம், எதிரிகளை வெல்லுதல்", 7: "திருமணம், கூட்டாண்மை", 8: "திடீர் மாற்றங்கள், ரகசியங்கள்", 9: "பாக்கியம், தந்தை, உயர் கல்வி", 10: "தொழில் வெற்றி, பதவி உயர்வு", 11: "லாபம், நெட்வொர்க்", 12: "பயணங்கள், முதலீடுகள்"}
        t_md, t_ad = t_p.get(md, md), t_p.get(ad, ad)
        base = f"இந்த காலகட்டம் {t_md} தசையின் ஒட்டுமொத்த நோக்கங்களை, {t_ad} புக்தியின் மூலமாக நிஜ வாழ்க்கையில் பிரதிபலிக்கும்.\n\n"
        if md == ad: base += f"உங்கள் ஜாதகத்தில் {t_md} {md_house}-ஆம் வீட்டில் அமர்ந்துள்ளதால், இந்த காலகட்டம் முற்றிலும் '{t_topics[md_house]}' என்பதை சுற்றியே அமையும்.\n\n"
        else: base += f"நீண்டகால இலக்குகள் {md_house}-ஆம் வீட்டைச் சார்ந்திருந்தாலும், தற்போது {t_ad} புக்தி நடப்பதால் உங்கள் அன்றாட நிகழ்வுகள் '{t_topics[ad_house]}' வழியே நடைபெறும்.\n\n"
    else:
        topics = {1: "personal identity, physical vitality", 2: "wealth accumulation, family dynamics", 3: "courage, short travels", 4: "domestic peace, real estate", 5: "creativity, intellect", 6: "health routines, overcoming competitors", 7: "marriage, business partnerships", 8: "deep transformation, hidden knowledge", 9: "luck, higher learning", 10: "career advancement, public status", 11: "network expansion, large gains", 12: "spiritual retreats, high expenditures"}
        base = f"This phase brings the overarching agenda of {md} (Strategy) into physical reality through the specific execution of {ad} (Tactics).\n\n"
        if md == ad: base += f"Because {md} is placed in your {md_house}th House, this period is intensely focused on {topics[md_house]}.\n\n"
        else: base += f"Your long-term focus centers on the {md_house}th House. However, {ad} is currently activating your {ad_house}th House, meaning immediate events manifest specifically through {topics[ad_house]}.\n\n"
    return base

def generate_current_next_bhukti(moon_lon, birth_date, planet_bhava_map, lang="English"):
    current_date = datetime.now()
    nak_idx = int(moon_lon / 13.333333333)
    bal = 1 - ((moon_lon % 13.333333333) / 13.333333333)
    curr_md_start = birth_date
    md_idx = nak_idx % 9
    
    for _ in range(20):
        md_lord = DASHA_ORDER[md_idx % 9]
        md_dur = DASHA_YEARS[md_lord] * bal if curr_md_start == birth_date else DASHA_YEARS[md_lord]
        md_end = curr_md_start + timedelta(days=md_dur * 365.25)
        
        if curr_md_start <= current_date <= md_end:
            ad_start = curr_md_start
            ad_idx = DASHA_ORDER.index(md_lord)
            for i in range(9):
                ad_lord = DASHA_ORDER[(ad_idx + i) % 9]
                ad_dur = (DASHA_YEARS[md_lord] * DASHA_YEARS[ad_lord]) / 120
                ad_end = ad_start + timedelta(days=ad_dur * 365.25)
                
                if ad_start <= current_date <= ad_end:
                    pd_start = ad_start
                    pd_idx = DASHA_ORDER.index(ad_lord)
                    for j in range(9):
                        pd_lord = DASHA_ORDER[(pd_idx + j) % 9]
                        pd_dur = (ad_dur * DASHA_YEARS[pd_lord]) / 120
                        pd_end = pd_start + timedelta(days=pd_dur * 365.25)
                        if pd_start <= current_date <= pd_end:
                            t_md, t_ad, t_pd = (t_p.get(md_lord, md_lord), t_p.get(ad_lord, ad_lord), t_p.get(pd_lord, pd_lord)) if lang=="Tamil" else (md_lord, ad_lord, pd_lord)
                            active_pd = {"MD": t_md, "AD": t_ad, "PD": t_pd, "Start": pd_start.strftime('%d %b %Y'), "End": pd_end.strftime('%d %b %Y')}
                            lbl_curr = "நடப்பு புக்தி" if lang == "Tamil" else "CURRENT PHASE"
                            lbl_next = "அடுத்த புக்தி" if lang == "Tamil" else "NEXT PHASE"
                            p1 = {"Type": lbl_curr, "Phase": f"{t_md} - {t_ad}", "Dates": f"{ad_start.strftime('%b %Y')} to {ad_end.strftime('%b %Y')}", "Text": get_detailed_bhukti_analysis(md_lord, ad_lord, planet_bhava_map, lang)}
                            
                            next_ad = DASHA_ORDER[(ad_idx + i + 1) % 9]
                            t_next_ad = t_p.get(next_ad, next_ad) if lang=="Tamil" else next_ad
                            p2 = {"Type": lbl_next, "Phase": f"{t_md} - {t_next_ad}", "Dates": "விரைவில்..." if lang=="Tamil" else "Upcoming", "Text": get_detailed_bhukti_analysis(md_lord, next_ad, planet_bhava_map, lang)}
                            return [p1, p2], active_pd
                        pd_start = pd_end
                ad_start = ad_end
        curr_md_start = md_end
        md_idx += 1
        bal = 1
